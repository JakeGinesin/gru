from typing import Set

if __name__ == '__main__':
    from mutator import mutate_ast
else:
    from gru.mutator.mutator import mutate_ast

def mutate_map(code : str, num_mutants : int, num_layers : int) -> Set[str]:
    """
    takes some python code and returns a set of mutants

    does some naive separation between operation types to ensure syntactic correctness is maintained
    """
    if depth == 0 : return {}
    mutants = set()

    for i in range(num_mutants):
        tree = ast.parse(code)
        modified_tree = mutate_ast(tree)
        mutants.add(astor.to_source(modified_tree))

    ret = set()
    for mutant in mutants:
        # recurse
        mut_depth_add = mutate_map(str(mutant), mutant_num, depth - 1) 
        
        # add result to ret
        ret.add(mutant)
        ret = ret.union(mut_depth_add)

    ret = ret - {code} # remove non-mutated code
    return ret
