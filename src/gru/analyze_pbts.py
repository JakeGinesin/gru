import tempfile, os, subprocess, json, random, shutil, argparse
from gru.mutator.harness import mutate_map
from gru.parsing.utils import *
from tqdm import tqdm

from gru.parsing.ast_manip import (
    replace_function_signatures_in_directory,
)

def find_pbts_in_repo(repo_dir : str) -> list:
    pbts_data = extract_pbts_with_dirs_and_context(repo_dir)

    ret = []
    for pbt, data in pbts_data.items():
        pbt_name = data[0]
        ret.append(pbt_name)

    return ret

def analyze_pbts_in_repo(repo_dir : str, mutant_num : int):

    pbts_data = extract_pbts_with_dirs_and_context(repo_dir)

    with tempfile.TemporaryDirectory() as tmpdir:
        """ step 1: copy dir to tmpdir """
        dst_dir = os.path.join(tmpdir, os.path.basename(repo_dir))
        shutil.copytree(repo_dir, dst_dir)

        results = []

        for pbt, data in tqdm(pbts_data.items()): 
            pbt_name = data[0]
            dependency_names = data[1]
            pbt_definition = data[2]
            dependency_definitions = data[3]
            import_reqs = data[4]
            external_pkg_reqs = data[5]
            pbt_path = data[6]
            dependency_filenames = data[7]

            if dependency_names == []:
                print("no dependencies, so nothing to mutate! skipping")
                continue

            print("analyzing property-based test " + str(pbt_name) + " located at " + str(pbt_path) + "!")
            report_file_path = os.path.join(dst_dir, 'report.json')

            env = os.environ.copy()
            env['PYTHONPATH'] = dst_dir

            result = subprocess.run(
                ['pytest', '-q', '--json-report', '--json-report-file=' + report_file_path, 
                 pbt_path + "::" + pbt_name],
                env=env,  # pass the modified environment to the subprocess
            )

            with open(report_file_path, 'r') as f:
                ret_data = json.loads(f.read())

                if len(ret_data["tests"]) == 0: 
                    print("PBT " + str(pbt_name) + " failed to be detected by pytest... skipping")
                    continue

                for test in ret_data["tests"]:
                    name = test["nodeid"][test["nodeid"].index("::")+2:]
                    outcome = test["outcome"]
                    if outcome == "failed": 
                        print("PBT " + str(pbt_name) + " did not pass with pytest... skipping")
                        continue

            print(str(pbt_name) + " passed with pytest, doing mutant analysis now ...")

            dep_list = ""
            for dep_def in dependency_definitions : dep_list += dep_def + "\n\n"
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
                    ['pytest', '-q', '--json-report', '--json-report-file=' + report_file_path, 
                     pbt_path + "::" + pbt_name],
                    env=env
                )

                with open(report_file_path, 'r') as f:
                    data = json.loads(f.read())

                    # if len(data["tests"]) == 0 : return None

                    for test in data["tests"]:
                        name = test["nodeid"][test["nodeid"].index("::")+2:]
                        outcome = test["outcome"]
                        if outcome == "passed":
                            passed_tests.add(mutant)

                        elif outcome == "failed":
                            failed_tests.add(mutant)

                replace_function_signatures_in_directory(dst_dir, op_def_nodes)
            
            results.append((pbt_name, 
                            pbt_path, 
                            (100 * len(passed_tests) / (len(passed_tests) + len(failed_tests)))
                            ))

        print("RESULTS: \n")
        for pbt_name, pbt_path, ratio in results:
            print(str(pbt_name) + " at " + str(pbt_path) + " scored " + str(ratio) + "%")

def analyze_pbt_in_repo(repo_dir: str, mutant_num: int, pbt_name_filter: str):
    pbts_data = extract_pbts_with_dirs_and_context(repo_dir)

    if pbt_name_filter not in pbts_data:
        print(f"Property-based test {pbt_name_filter} not found in repository.")
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        """ step 1: copy dir to tmpdir """
        dst_dir = os.path.join(tmpdir, os.path.basename(repo_dir))
        shutil.copytree(repo_dir, dst_dir)

        data = pbts_data[pbt_name_filter]
        pbt_name = data[0]
        dependency_names = data[1]
        pbt_definition = data[2]
        dependency_definitions = data[3]
        import_reqs = data[4]
        external_pkg_reqs = data[5]
        pbt_path = data[6]
        dependency_filenames = data[7]

        if dependency_names == []:
            print("no dependencies, so nothing to mutate! skipping")
            return

        print("analyzing property-based test " + str(pbt_name) + " located at " + str(pbt_path) + "!")
        report_file_path = os.path.join(dst_dir, 'report.json')

        env = os.environ.copy()
        env['PYTHONPATH'] = dst_dir

        result = subprocess.run(
            ['pytest', '-q', '--json-report', '--json-report-file=' + report_file_path, 
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

        print(str(pbt_name) + " passed with pytest, doing mutant analysis now ...")

        dep_list = ""
        for dep_def in dependency_definitions:
            dep_list += dep_def + "\n\n"
        op_def_nodes = extract_function_defs(dep_list)

        mutation_set = mutate_map(dep_list, mutant_num, 2)
        mutants = list(random.sample(list(mutation_set), mutant_num))

        passed_tests = set()
        failed_tests = set()

        for mutant in tqdm(mutants):
            def_nodes = extract_function_defs(mutant)

            replace_function_signatures_in_directory(dst_dir, def_nodes)

            env = os.environ.copy()
            env['PYTHONPATH'] = dst_dir

            report_file_path = os.path.join(dst_dir, 'report.json')
            result = subprocess.run(
                ['pytest', '-q', '--json-report', '--json-report-file=' + report_file_path, 
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

        score = 100 * len(passed_tests) / (len(passed_tests) + len(failed_tests)) if (len(passed_tests) + len(failed_tests)) > 0 else 0

        print(f"{pbt_name} at {pbt_path} scored {score}%")

    return {pbt_name_filter: score}

def main():
    parser = argparse.ArgumentParser(description='Analyze property-based tests.')
    parser.add_argument('--repo_dir', help='Path to the repository directory', required=True)
    parser.add_argument('--pbt_name', help='name of PBT to analyze')
    parser.add_argument('--mutant_num', type=int, default=10, help='Number of mutants')
    args = parser.parse_args()

    # Directly call the function since it's the primary purpose of this script
    import sys
    if sys.argv[0].endswith('analyze-pbts'):
        result = analyze_pbts_in_repo(
            args.repo_dir,
            mutant_num=args.mutant_num,
        )

    elif sys.argv[0].endswith('analyze-pbt'):
        result = analyze_pbt_in_repo(
            args.repo_dir,
            mutant_num=args.mutant_num,
            pbt_name_filter=args.pbt_name,
        )

    elif sys.argv[0].endswith('find-pbts'):
        result = find_pbts_in_repo(
            args.repo_dir,
        )

    else:
        print("unrecognized argument")
        sys.exit(0)
        """
        result = analyze_pbt_in_repo(
            args.repo_dir,
            mutant_num=args.mutant_num,
            pbt_name_filter=pbt_name,
        )
        """
        """
        result = analyze_pbts_in_repo(
            args.repo_dir,
            mutant_num=args.mutant_num,
        )
        """
        
        """
        result = analyze_pbt_in_repo(
            args.repo_dir,
            mutant_num=args.mutant_num,
            pbt_name_filter="test_parsing_spaced_ender_arrow"
        )
        """

    print(result)

if __name__ == '__main__':
    main()
