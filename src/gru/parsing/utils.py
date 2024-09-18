"""
various util functions for parsing/unparsing PBTs
"""
import ast, os, re, astor, json, sys, importlib.util, pkgutil
from parsing.std_list import stdlib_list
from typing import List, Tuple, Dict, Set

def get_full_function_name(node: ast.AST) -> str:
    """Recursively retrieve the full function name from an AST node."""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        return get_full_function_name(node.value) + '.' + node.attr
    return ""

def unparse_decorator(decorator: ast.AST) -> str:
    """Unparse a decorator to a string."""
    if isinstance(decorator, ast.Call):
        func_name = get_full_function_name(decorator.func)
        args = [ast.unparse(arg) for arg in decorator.args]
        kwargs = [f"{kw.arg}={ast.unparse(kw.value)}" for kw in decorator.keywords]
        all_args = ", ".join(args + kwargs)
        return f"{func_name}({all_args})"
    return ""

def find_pbt_functions(code: str) -> List[Tuple[str, str]]:
    """Extract PBT functions from code, returning a list of (name, code) tuples."""
    tree = ast.parse(code)
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            decorator_code = ""
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call):
                    full_func_name = get_full_function_name(decorator.func)
                    if "given" in full_func_name.split('.'):
                        decorator_code = "@" + unparse_decorator(decorator)
            if decorator_code:
                function_code = decorator_code + "\n" + astor.to_source(node)
                functions.append((node.name, function_code))
    return functions

def find_pbt_function_names(code: str) -> List[str]:
    """Extract the PBT function names from a given block of code"""
    tree = ast.parse(code)
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                try:
                    # notably, our heuristic for determining if a function definition is 
                    # a hypothesis function definition is if it has the decorator "given"
                    if isinstance(decorator, ast.Call) and decorator.func.id == "given":
                        functions.append(node.name)
                        break
                except Exception as e:
                    # this will be hit if we have no decorators
                    continue
    return functions

def get_all_function_names(code: str) -> List[str]:
    """Extract all function names from the given AST."""
    tree = ast.parse(code)
    function_names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            function_names.append(node.name)
    return function_names

def get_function_definition(func_name: str, code: str) -> str:
    """Extract the full function definition given its name."""
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            return ast.unparse(node)
    return None

def get_called_function_names(func_name: str, code: str) -> Set[str]:
    """Find all function names called within the given function's body."""
    tree = ast.parse(code)
    called_functions = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            for sub_node in ast.walk(node):
                if isinstance(sub_node, ast.Call) and isinstance(sub_node.func, ast.Name):
                    called_functions.add(sub_node.func.id)
    return called_functions

def get_full_function_name(node: ast.AST) -> str:
    """Recursively retrieve the full function name from an AST node."""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        return get_full_function_name(node.value) + '.' + node.attr
    return ""

def unparse_decorator(decorator: ast.AST) -> str:
    """Unparse a decorator to a string."""
    if isinstance(decorator, ast.Call):
        func_name = get_full_function_name(decorator.func)
        args = [ast.unparse(arg) for arg in decorator.args]
        kwargs = [f"{kw.arg}={ast.unparse(kw.value)}" for kw in decorator.keywords]
        all_args = ", ".join(args + kwargs)
        return f"{func_name}({all_args})"
    return ""


def extract_function_defs(code_str) -> List[ast.AST]:
    """
    Takes a string block of code and returns an array of all ast node function definitions.
    """
    # Parse the string into an AST
    tree = ast.parse(code_str)
    
    # Extract all function definition nodes
    func_defs = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    
    return func_defs

def find_pbt_functions(code: str) -> List[Tuple[str, str]]:
    """Extract PBT functions from code, returning a list of (name, code) tuples."""
    tree = ast.parse(code)
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            decorator_code = ""
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call):
                    full_func_name = get_full_function_name(decorator.func)
                    if "given" in full_func_name.split('.'):
                        decorator_code = "@" + unparse_decorator(decorator)
            if decorator_code:
                function_code = decorator_code + "\n" + astor.to_source(node)
                functions.append((node.name, function_code))
    return functions

def find_pbt_function_names(code: str) -> List[str]:
    tree = ast.parse(code)
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                try:
                    if isinstance(decorator, ast.Call) and decorator.func.id == "given":
                        functions.append(node.name)
                        break
                except Exception as e:
                    continue
    return functions

def get_all_function_names(code: str) -> List[str]:
    """Extract all function names from the given AST."""
    tree = ast.parse(code)
    function_names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            function_names.append(node.name)
    return function_names

def get_function_definition(func_name: str, code: str) -> str:
    """Extract the full function definition given its name."""
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            return ast.unparse(node)
    return None


def get_called_function_names(func_name: str, code: str) -> Set[str]:
    """Find all function names called within the given function's body, excluding those in decorators."""
    tree = ast.parse(code)
    called_functions = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            # Loop through nodes in the function body
            for sub_node in ast.walk(node):
                # Skip if the sub_node is part of any decorator
                if any(sub_node in ast.walk(decorator) for decorator in node.decorator_list):
                    continue
                
                # Collect function calls that are within the function body
                if isinstance(sub_node, ast.Call):
                    if isinstance(sub_node.func, ast.Name):
                        called_functions.add(sub_node.func.id)
                    elif isinstance(sub_node.func, ast.Attribute):
                        called_functions.add(sub_node.func.attr)

    return called_functions

def is_standard_library(module_name: str) -> bool:
    """Check if the module is part of the Python standard library using a precomputed list."""
    if module_name is None:
        return False
    
    root_module_name = module_name.split('.')[0]  # Get the root module name
    return root_module_name in stdlib_list

def get_import_statements(code: str) -> List[Tuple[str, str]]:
    """Extract all import statements from the given code and determine if they are from the standard library."""
    tree = ast.parse(code)
    import_statements = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                is_std = is_standard_library(alias.name)
                import_statements.append((astor.to_source(node).strip(), "standard" if is_std else "third-party"))
                
        elif isinstance(node, ast.ImportFrom):
            is_std = is_standard_library(node.module)
            import_statements.append((astor.to_source(node).strip(), "standard" if is_std else "third-party"))
    
    return import_statements

def extract_pbts_from_project(directory: str) -> List[Tuple[str, str]]:
    """Recursively parse a directory for Python files and extract PBT functions."""
    all_pbts = set()  # Changed to a set to avoid duplicates and correctly use .add()
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        content = f.read()
                        pbts = find_pbt_functions(content)
                        all_pbts.update(pbts)  # Changed to update() for adding multiple items
                    except Exception as e:
                        print("failed to parse at " + str(file_path) + " due to " + str(e))
                        continue
    return list(all_pbts)  # Convert set back to list if necessary

def extract_pbts_from_project_with_filenames(directory: str) -> List[Tuple[str, str, str]]:
    """Recursively parse a directory for Python files and extract PBT functions."""
    all_pbts = set()  # Changed to a set to avoid duplicates and correctly use .add()
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        content = f.read()
                        pbts = find_pbt_functions(content)
                        for pbt_name, pbt in pbts:
                            all_pbts.add((pbt_name, pbt, file_path))

                    except Exception as e:
                        print("failed to parse at " + str(file_path) + " due to " + str(e))
                        continue

    return list(all_pbts)  # Convert set back to list if necessary

def extract_pbts_with_context(directory: str) -> List[Tuple[str, List[str], str, List[str]]]:
    """Extracts all PBTs from a project, then acquires the minimum amount of context for the PBT."""
    pbts = extract_pbts_from_project(directory)
    pbt_deps: Dict[str, Set[str]] = {}
    pbt_import_deps: Dict[str, Set[str]] = {} # track which imports are required for a PBT
    functions: Dict[str, str] = {}  # Track function names to function definitions
    function_deps: Dict[str, Set[str]] = {}  # Track function names to called functions called within the function
    import_statements: Dict[str, Set[str]] = {} # track function import requirements, also whether all standard or not
    pbt_requires_external_pkgs: Dict[str, bool] = {}
    filenames = set()
    for name, pbt in pbts:
        pbt_deps[name] = set()

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filenames.add(file[0:file.index(".py")])
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    func_names = get_all_function_names(content)
                    imports = get_import_statements(content)
                    for func_name in func_names:
                        try:
                            # This is very inefficient since we parse and walk the AST a ton, but it's fine for now I guess
                            func_def = get_function_definition(func_name, content)
                            called_funcs = get_called_function_names(func_name, content)

                            functions[func_name] = func_def
                            function_deps[func_name] = called_funcs
                            import_statements[func_name] = imports

                        except Exception as e:
                            continue
        
    # Now, we want to get _all_ dependent functions such that we can add them as context
    prog_defs = set(functions.keys()) - set(pbts)
    for name, pbt in pbts:
        deps = set()
        new_deps = set(get_called_function_names(name, pbt))
        deps = new_deps.union(deps)
        to_add = new_deps.copy()

        imports = set()
        imports = imports.union(set(import_statements[name]))

        while to_add != set():  # While there are things to add
            proc = set()
            for func in to_add:
                if func in function_deps:
                    imports = imports.union(set(import_statements[func]))
                    proc = proc.union(set(function_deps[func]))

            to_add = proc - deps
            deps = deps.union(proc)

        deps = deps.intersection(prog_defs)
        pbt_deps[name] = deps

        # go through imports
        requires_external = False
        imports_res = list(imports)
        for import_statement, state in imports_res:
            # want to see if any dep appears in the import statement
            # if the state is third party, and appears in a dep, remove it
            if state == "third-party" and (
                    any(dep in import_statement for dep in deps) or
                    any(filename in import_statement for filename in filenames)):
                imports.remove((import_statement, state))
            elif state == "third-party" and not "hypothesis" in import_statement: requires_external = True

        import_statements[name] = imports
        pbt_requires_external_pkgs[name] = requires_external
    

    full_pbt_deps = []
    for pbts, deps in pbt_deps.items():
        ret = [None] * 6
        ret[0] = pbts # pbt name
        ret[1] = list(deps) # list of the dependency names
        ret[2] = functions[pbts] # get the function definition for the pbt
        ret[3] = [functions[dep] for dep in deps] # get the function definitions for all dependent functions
        ret[4] = import_statements[pbts] # all import statements required by pbt and deps
        ret[5] = pbt_requires_external_pkgs[pbts] # does this pbt require external packages, besides hypothesis?
        full_pbt_deps.append(tuple(ret))

    return full_pbt_deps

def extract_pbts_with_dirs_and_context(directory: str):
    """Extracts all PBTs from a project, then acquires the minimum amount of context, including dirs, for the PBT.
        the motivation for this function's existence is so we can find and replace modified versions of the PBT into the original project!
    """
    pbts = extract_pbts_from_project_with_filenames(directory)

    pbt_deps: Dict[str, Set[str]] = {}
    pbt_filenames: Dict[str, str] = {}
    pbt_import_deps: Dict[str, Set[str]] = {} # track which imports are required for a PBT
    functions: Dict[str, str] = {}  # Track function names to function definitions
    function_deps: Dict[str, Set[str]] = {}  # Track function names to called functions called within the function
    import_statements: Dict[str, Set[str]] = {} # track function import requirements, also whether all standard or not
    pbt_requires_external_pkgs: Dict[str, bool] = {}
    function_filenames: Dict[str, str] = {}

    filenames = set()
    for name, pbt, filename in pbts:
        pbt_deps[name] = set()
        pbt_filenames[name] = filename


    # categorize all functions by what they call etc, this can probably be done more efficiently
    # through some DP-esque thing but it's ok
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filenames.add(file[0:file.index(".py")])
                file_path = os.path.join(root, file)

                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    func_names = get_all_function_names(content)
                    imports = get_import_statements(content)
                    for func_name in func_names:
                        try:
                            # This is very inefficient since we parse and walk the AST a ton, but it's fine for now I guess
                            func_def = get_function_definition(func_name, content)
                            called_funcs = get_called_function_names(func_name, content)

                            functions[func_name] = func_def
                            function_deps[func_name] = called_funcs
                            function_filenames[func_name] = file_path
                            import_statements[func_name] = imports

                        except Exception as e:
                            continue
        
    # Now, we want to get _all_ dependent functions such that we can add them as context
    prog_defs = set(functions.keys()) - set(pbts)
    for name, pbt, filename in pbts:
        deps = set()
        new_deps = set(get_called_function_names(name, pbt))
        deps = new_deps.union(deps)
        to_add = new_deps.copy()

        imports = set()
        imports = imports.union(set(import_statements[name]))

        while to_add != set():  # While there are things to add
            proc = set()
            for func in to_add:
                if func in function_deps:
                    imports = imports.union(set(import_statements[func]))
                    proc = proc.union(set(function_deps[func]))

            to_add = proc - deps
            deps = deps.union(proc)

        deps = deps.intersection(prog_defs)
        pbt_deps[name] = deps

        # go through imports
        requires_external = False
        imports_res = list(imports)
        for import_statement, state in imports_res:
            # want to see if any dep appears in the import statement
            # if the state is third party, and appears in a dep, remove it
            if state == "third-party" and (
                    any(dep in import_statement for dep in deps) or
                    any(filename in import_statement for filename in filenames)):
                imports.remove((import_statement, state))
            elif state == "third-party" and not "hypothesis" in import_statement: requires_external = True

        import_statements[name] = imports
        pbt_requires_external_pkgs[name] = requires_external
    

    full_pbt_deps = {}
    for pbts, deps in pbt_deps.items():
        ret = [None] * 8
        ret[0] = pbts # pbt name
        ret[1] = list(deps) # list of the dependency names
        ret[2] = functions[pbts] # get the function definition for the pbt
        ret[3] = [functions[dep] for dep in deps] # get the function definitions for all dependent functions
        ret[4] = import_statements[pbts] # all import statements required by pbt and deps
        ret[5] = pbt_requires_external_pkgs[pbts] # does this pbt require external packages, besides hypothesis?
        ret[6] = pbt_filenames[pbts] # filename for the pbt
        ret[7] = {dep : function_filenames[dep] for dep in deps} # get all the function filenames for each dependency
        full_pbt_deps[pbts] = tuple(ret)

    return full_pbt_deps

