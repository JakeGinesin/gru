import tempfile, os, subprocess, json, random, shutil, argparse

from gru.mutator.harness import mutate_map
from gru.parsing.utils import (
    extract_pbts_with_dirs_and_context,
    extract_function_defs,
    get_all_function_names,
)
from gru.parsing.ast_manip import (
    replace_function_signatures_in_directory,
)
from gru.llm.prompts import (
    gen_tighten_prompt_from_pbt_and_mutant,
    gen_generalize_prompt_from_pbt_and_mutant,
    extract_python_code,
)
from gru.llm.models import model

def tighten_repo_pbt(repo_dir : str, pbt_name : str, threshhold : float = 0.8, mutant_num : int = 10, max_iters : int = 10) -> str:
    pbts_data = extract_pbts_with_dirs_and_context(repo_dir)

    with tempfile.TemporaryDirectory() as tmpdir:

        dst_dir = os.path.join(tmpdir, os.path.basename(repo_dir))
        shutil.copytree(repo_dir, dst_dir)

        if not pbt_name in pbts_data:
            print("pbt not found...")
            return

        data = pbts_data[pbt_name]

        pbt_name = data[0]
        dependency_names = data[1]
        pbt_definition = data[2]
        dependency_definitions = data[3]
        import_reqs = data[4]
        external_pkg_reqs = data[5]
        pbt_path = data[6]
        dependency_filenames = data[7]

        """ assert the PBT passes """

        report_file_path = os.path.join(dst_dir, 'report.json')

        env = os.environ.copy()
        env['PYTHONPATH'] = dst_dir

        result = subprocess.run(
            ['pytest', '--json-report', '--json-report-file=' + report_file_path, 
             pbt_path + "::" + pbt_name],
            env=env,  # pass the modified environment to the subprocess
        )

        with open(report_file_path, 'r') as f:
            ret_data = json.loads(f.read())

            if len(ret_data["tests"]) == 0: 
                print("PBT " + str(pbt_name) + " failed to be detected by pytest... skipping")
                return

            for test in ret_data["tests"]:
                name = test["nodeid"][test["nodeid"].index("::")+2:]
                outcome = test["outcome"]
                if outcome == "failed": 
                    print("PBT " + str(pbt_name) + " did not pass with pytest... skipping")
                    return

        """ evaluate the pbt against mutants """
        print(str(pbt_name) + " passed with pytest, doing mutant analysis now ...")

        dep_list = ""
        for dep_def in dependency_definitions : dep_list += dep_def + "\n"
        op_def_nodes = extract_function_defs(dep_list)

        mutation_set = mutate_map(dep_list, mutant_num, 2)
        mutants = list(random.sample(list(mutation_set), mutant_num))

        passed_tests = set()
        failed_tests = set()

        for mutant in mutants:
            def_nodes = extract_function_defs(mutant)

            replace_function_signatures_in_directory(dst_dir, def_nodes)

            env = os.environ.copy()
            env['PYTHONPATH'] = dst_dir

            report_file_path = os.path.join(dst_dir, 'report.json')
            result = subprocess.run(
                ['pytest', '--json-report', '--json-report-file=' + report_file_path, 
                 pbt_path + "::" + pbt_name],
                env=env
            )

            with open(report_file_path, 'r') as f:
                data = json.loads(f.read())
                for test in data["tests"]:
                    name = test["nodeid"][test["nodeid"].index("::")+2:]
                    outcome = test["outcome"]
                    if outcome == "passed":
                        passed_tests.add(mutant)

                    elif outcome == "failed":
                        failed_tests.add(mutant)

            replace_function_signatures_in_directory(dst_dir, op_def_nodes)

        """ refine the PBT """

        # default condition: does this PBT kill enough mutants?
        if (len(failed_tests)/len(mutants)) >= threshhold : return pbt_definition

        # if not, we iteratively improve the PBT with the LLM

        iters = max_iters
        op_pbt = extract_function_defs(pbt_definition)

        current_pbt = pbt_definition
        while iters > 0:
            # pick a mutant to refine against
            ref_mutant = random.choice(list(passed_tests))

            # modify the PBT
            generate_lim = 5 # arbitrary choice
            while generate_lim > 0:

                # generate the modified PBT based on reflection 
                prompt = gen_tighten_prompt_from_pbt_and_mutant(dep_list, current_pbt, ref_mutant)
                res = model.generate_full(prompt)
                pbt_res = extract_python_code(res)
                
                print("NEW PBTS!!\n\n")
                print(pbt_res)

                new_pbt_name = get_all_function_names(pbt_res)[0]

                # assert the generated pbt has the same name as the original
                if new_pbt_name != pbt_name:
                    generate_lim-=1
                    continue

                pbt_res_ast = extract_function_defs(pbt_res)

                # make sure the new pbt actually passes
                replace_function_signatures_in_directory(dst_dir, pbt_res_ast)

                report_file_path = os.path.join(dst_dir, 'report.json')

                env = os.environ.copy()
                env['PYTHONPATH'] = dst_dir

                result = subprocess.run(
                    ['pytest', '--json-report', '--json-report-file=' + report_file_path, 
                     pbt_path + "::" + pbt_name],
                    env=env,  # pass the modified environment to the subprocess
                )

                with open(report_file_path, 'r') as f:
                    ret_data = json.loads(f.read())

                    if len(ret_data["tests"]) == 0: 
                        generate_lim-=1
                        print("this pbt failed to compile...")
                        continue

                    for test in ret_data["tests"]:
                        name = test["nodeid"][test["nodeid"].index("::")+2:]
                        outcome = test["outcome"]
                        if outcome == "failed": 
                            generate_lim-=1
                            print("this pbt failed to pass...")
                            continue

                current_pbt = pbt_res
                replace_function_signatures_in_directory(dst_dir, op_pbt)
                break


            # if we failed to generate a new pbt based off the mutant, just skip it
            if generate_lim == 0 : continue

            # assess the new PBT (current_pbt) against the mutants, generate a new passed_tests and failed_tests set (based on original mutants)

            current_pbt_ast = extract_function_defs(current_pbt)
            replace_function_signatures_in_directory(dst_dir, current_pbt_ast)

            passed_tests = set()
            failed_tests = set()

            for mutant in mutants:
                def_nodes = extract_function_defs(mutant)

                replace_function_signatures_in_directory(dst_dir, def_nodes)

                env = os.environ.copy()
                env['PYTHONPATH'] = dst_dir

                report_file_path = os.path.join(dst_dir, 'report.json')
                result = subprocess.run(
                    ['pytest', '--json-report', '--json-report-file=' + report_file_path, 
                     pbt_path + "::" + pbt_name],
                    env=env
                )

                with open(report_file_path, 'r') as f:
                    data = json.loads(f.read())
                    for test in data["tests"]:
                        name = test["nodeid"][test["nodeid"].index("::")+2:]
                        outcome = test["outcome"]
                        if outcome == "passed":
                            passed_tests.add(mutant)

                        elif outcome == "failed":
                            failed_tests.add(mutant)

                replace_function_signatures_in_directory(dst_dir, op_pbt)


            # re-determine if PBT passes threshhold
            if (len(failed_tests)/len(mutants)) >= threshhold : return current_pbt

            iters-=1

        return "failed to tighten pbt..."

def generalize_repo_pbt(repo_dir : str, pbt_name : str, threshhold : float = 0.3, mutant_num : int = 10, max_iters : int = 10) -> str:
    pbts_data = extract_pbts_with_dirs_and_context(repo_dir)

    with tempfile.TemporaryDirectory() as tmpdir:

        dst_dir = os.path.join(tmpdir, os.path.basename(repo_dir))
        shutil.copytree(repo_dir, dst_dir)

        if not pbt_name in pbts_data:
            print("pbt not found...")
            return

        data = pbts_data[pbt_name]

        pbt_name = data[0]
        dependency_names = data[1]
        pbt_definition = data[2]
        dependency_definitions = data[3]
        import_reqs = data[4]
        external_pkg_reqs = data[5]
        pbt_path = data[6]
        dependency_filenames = data[7]

        """ assert the PBT passes """

        report_file_path = os.path.join(dst_dir, 'report.json')

        env = os.environ.copy()
        env['PYTHONPATH'] = dst_dir

        result = subprocess.run(
            ['pytest', '--json-report', '--json-report-file=' + report_file_path, 
             pbt_path + "::" + pbt_name],
            env=env,  # pass the modified environment to the subprocess
        )

        with open(report_file_path, 'r') as f:
            ret_data = json.loads(f.read())

            if len(ret_data["tests"]) == 0: 
                print("PBT " + str(pbt_name) + " failed to be detected by pytest... skipping")
                return

            for test in ret_data["tests"]:
                name = test["nodeid"][test["nodeid"].index("::")+2:]
                outcome = test["outcome"]
                if outcome == "failed": 
                    print("PBT " + str(pbt_name) + " did not pass with pytest... skipping")
                    return

        """ evaluate the pbt against mutants """
        print(str(pbt_name) + " passed with pytest, doing mutant analysis now ...")

        dep_list = ""
        for dep_def in dependency_definitions : dep_list += dep_def + "\n"
        op_def_nodes = extract_function_defs(dep_list)

        mutation_set = mutate_map(dep_list, mutant_num, 2)
        mutants = list(random.sample(list(mutation_set), mutant_num))

        passed_tests = set()
        failed_tests = set()

        for mutant in mutants:
            def_nodes = extract_function_defs(mutant)

            replace_function_signatures_in_directory(dst_dir, def_nodes)

            env = os.environ.copy()
            env['PYTHONPATH'] = dst_dir

            report_file_path = os.path.join(dst_dir, 'report.json')
            result = subprocess.run(
                ['pytest', '--json-report', '--json-report-file=' + report_file_path, 
                 pbt_path + "::" + pbt_name],
                env=env
            )

            with open(report_file_path, 'r') as f:
                data = json.loads(f.read())
                for test in data["tests"]:
                    name = test["nodeid"][test["nodeid"].index("::")+2:]
                    outcome = test["outcome"]
                    if outcome == "passed":
                        passed_tests.add(mutant)

                    elif outcome == "failed":
                        failed_tests.add(mutant)

            replace_function_signatures_in_directory(dst_dir, op_def_nodes)

        """ refine the PBT """

        # default condition: does this PBT kill enough mutants?
        if (len(failed_tests)/len(mutants)) <= threshhold : return pbt_definition

        # if not, we iteratively improve the PBT with the LLM

        iters = max_iters
        op_pbt = extract_function_defs(pbt_definition)

        current_pbt = pbt_definition
        while iters > 0:
            # pick a mutant to refine against
            ref_mutant = random.choice(list(passed_tests))

            # modify the PBT
            generate_lim = 5 # arbitrary choice
            while generate_lim > 0:

                # generate the modified PBT based on reflection 
                prompt = gen_generalize_prompt_from_pbt_and_mutant(dep_list, current_pbt, ref_mutant)
                res = model.generate_full(prompt)
                pbt_res = extract_python_code(res)

                new_pbt_name = get_all_function_names(pbt_res)[0]

                # assert the generated pbt has the same name as the original
                if new_pbt_name != pbt_name:
                    generate_lim-=1
                    continue

                pbt_res_ast = extract_function_defs(pbt_res)

                # make sure the new pbt actually passes
                replace_function_signatures_in_directory(dst_dir, pbt_res_ast)

                report_file_path = os.path.join(dst_dir, 'report.json')

                env = os.environ.copy()
                env['PYTHONPATH'] = dst_dir

                result = subprocess.run(
                    ['pytest', '--json-report', '--json-report-file=' + report_file_path, 
                     pbt_path + "::" + pbt_name],
                    env=env,  # pass the modified environment to the subprocess
                )

                with open(report_file_path, 'r') as f:
                    ret_data = json.loads(f.read())

                    if len(ret_data["tests"]) == 0: 
                        generate_lim-=1
                        continue

                    for test in ret_data["tests"]:
                        name = test["nodeid"][test["nodeid"].index("::")+2:]
                        outcome = test["outcome"]
                        if outcome == "failed": 
                            generate_lim-=1
                            continue

                current_pbt = pbt_res
                replace_function_signatures_in_directory(dst_dir, op_pbt)
                break


            # if we failed to generate a new pbt based off the mutant, just skip it
            if generate_lim == 0 : continue

            # assess the new PBT (current_pbt) against the mutants, generate a new passed_tests and failed_tests set (based on original mutants)

            current_pbt_ast = extract_function_defs(current_pbt)
            replace_function_signatures_in_directory(dst_dir, current_pbt_ast)

            passed_tests = set()
            failed_tests = set()

            for mutant in mutants:
                def_nodes = extract_function_defs(mutant)

                replace_function_signatures_in_directory(dst_dir, def_nodes)

                env = os.environ.copy()
                env['PYTHONPATH'] = dst_dir

                report_file_path = os.path.join(dst_dir, 'report.json')
                result = subprocess.run(
                    ['pytest', '--json-report', '--json-report-file=' + report_file_path, 
                     pbt_path + "::" + pbt_name],
                    env=env
                )

                with open(report_file_path, 'r') as f:
                    data = json.loads(f.read())
                    for test in data["tests"]:
                        name = test["nodeid"][test["nodeid"].index("::")+2:]
                        outcome = test["outcome"]
                        if outcome == "passed":
                            passed_tests.add(mutant)

                        elif outcome == "failed":
                            failed_tests.add(mutant)

                replace_function_signatures_in_directory(dst_dir, [op_pbt])


            # re-determine if PBT passes threshhold
            if (len(failed_tests)/len(mutants)) <= threshhold : return current_pbt

            iters-=1

        return "failed to generalize pbt..."

def main():
    parser = argparse.ArgumentParser(description='Refine property-based tests.')
    parser.add_argument('--repo_dir', help='Path to the repository directory')
    parser.add_argument('--pbt_name', help='Name of the property-based test')
    parser.add_argument('--threshhold', type=float, default=0.8, help='Threshold value')
    parser.add_argument('--mutant_num', type=int, default=10, help='Number of mutants')
    parser.add_argument('--max_iters', type=int, default=10, help='Maximum iterations')
    args = parser.parse_args()

    # Call the desired function based on the script name
    import sys
    if sys.argv[0].endswith('tighten-pbt'):
        result = tighten_repo_pbt(
            args.repo_dir,
            args.pbt_name,
            threshhold=args.threshhold,
            mutant_num=args.mutant_num,
            max_iters=args.max_iters
        )
    elif sys.argv[0].endswith('generalize-pbt'):
        result = generalize_repo_pbt(
            args.repo_dir,
            args.pbt_name,
            threshhold=args.threshhold,
            mutant_num=args.mutant_num,
            max_iters=args.max_iters
        )
    else:

        print("unrecognized argument")
        sys.exit(0)
        """
        result = tighten_repo_pbt(
            args.repo_dir,
            args.pbt_name,
            threshhold=args.threshhold,
            mutant_num=args.mutant_num,
            max_iters=args.max_iters
        )
        """

    print(result)

if __name__ == '__main__':
    main()
