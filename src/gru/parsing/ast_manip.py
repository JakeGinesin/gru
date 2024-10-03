from gru.parsing.utils import extract_function_defs, extract_pbts_with_dirs_and_context
from typing import List, Tuple, Dict, Set
import ast, os

class NodeReplacer(ast.NodeTransformer):
    def __init__(self, target_name, replacement_node):
        self.target_name = target_name
        self.replacement_node = replacement_node

    def visit_FunctionDef(self, node):
        if node.name == self.target_name:
            return self.replacement_node
        return node

def replace_function_signatures_in_file(filepath : str, function_defs : List[ast.AST]):
    """
    Replaces matching function signatures in a single file with those from the given function definitions.

    Note: this function works for PBTs with function decorators
    """
    with open(filepath, 'r') as file:
        source_code = file.read()

    function_map = {func.name: func for func in function_defs}

    arq = {}
    tree = ast.parse(source_code)

    tree_c = ast.parse(source_code)
    for name, fdef in function_map.items():
        replacer = NodeReplacer(name, fdef)
        tree_c = replacer.visit(tree_c)

    new_source_code = ast.unparse(tree_c)
    
    # Write the new source code back to the file
    with open(filepath, 'w') as file:
        file.write(new_source_code)

def replace_function_signatures_in_directory(directory : str, function_defs : List[ast.AST]):
    """
    Iterates through a Python project directory, replacing all matching function signatures with those from the input array.
    """
    for subdir, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(subdir, file)
                replace_function_signatures_in_file(filepath, function_defs)

if __name__ == '__main__':
    # example

    test=f"""
@given(st.integers(min_value=2, max_value=20))
def test_factorial_positive_integers(n):
    from math import factorial as math_factorial
    assert factorial(n) == math_factorial(n)
    """

    pbt_ast = extract_function_defs(test)

    replace_function_signatures_in_file("/home/synchronous/code/pbt-auto-refiner/examples/pbt_example.py", pbt_ast)
