from collections import defaultdict
import json, random, ast, astor, copy
from typing import Set

# ast.compare
mut_compare = {"Eq", "NotEq", "Lt", "LtE", "Gt", "GtE"}
mut_set_compare = {"In", "NotIn"} # also a compare

# ast.BinOp
mut_binop = {"Add", "Sub", "Mult", "Div", "FloorDiv", "Mod", "Pow"}
mut_bitop = {"BitOr", "BitXor", "BitAnd"}  # also a binop
mut_shiftop = {"LShift", "RShift"}  # also a binop

# ast.BoolOp
mut_boolop = {"And", "Or"}

# ast.UnaryOp
mut_unaryop = {"UAdd", "USub", "Not", "Invert", "If"}

# ast.AugAssign
mut_augassign = {"Add", "Sub", "Mult", "Div", "FloorDiv", "Mod", "Pow",
                 "BitOr", "BitXor", "BitAnd", "LShift", "RShift"}

name_constant_mut = {True, False, None}

def ast_to_dict(node) -> dict:
    """
    Translate AST node to a dict.
    Typical fields include 'ops', 'type', 'left', 'right'
    """
    if isinstance(node, ast.AST):
        fields = {key: ast_to_dict(value) for key, value in ast.iter_fields(node)}
        return {'type': node.__class__.__name__, **fields}
    elif isinstance(node, list):
        return [ast_to_dict(item) for item in node]
    else:
        return node

def dict_to_ast(d : dict) -> ast.AST:
    """
    Translate dict into AST node in inverse with the previous function
    """
    if not isinstance(d, dict):
        return d
    
    node_type = getattr(ast, d['type'], None)
    if not node_type:
        return d
    
    fields = {}
    for key, value in d.items():
        if key != 'type':
            if isinstance(value, list):
                fields[key] = [dict_to_ast(item) for item in value]
            else:
                fields[key] = dict_to_ast(value)
    return node_type(**fields)

# NodeCollector, NodeFinder, NodeReplacer helpers for reasoning about the AST
# ngl could probably do it in a better format, but it's ok for now i suppose
class NodeCollector(ast.NodeVisitor):
    def __init__(self):
        self.nodes_by_type = defaultdict(list)
    
    def generic_visit(self, node):
        node_type = type(node).__name__
        self.nodes_by_type[node_type].append(node)
        super().generic_visit(node)

class NodeFinder(ast.NodeVisitor):
    def __init__(self, condition):
        self.condition = condition
        self.target_node = None
    
    def generic_visit(self, node):
        if self.condition(node):
            self.target_node = node
        super().generic_visit(node)

class NodeReplacer(ast.NodeTransformer):
    def __init__(self, target_node, new_node):
        self.target_node = target_node
        self.new_node = new_node
    
    def generic_visit(self, node):
        if node == self.target_node:
            return self.new_node
        return super().generic_visit(node)

def mutate_ast(tree : ast.AST) -> ast.AST:
    """
    does a single syntactic mutation on the inputted AST
    """
    collector = NodeCollector()
    collector.visit(tree)

    # set of tuples; (node_type, node)
    node_list = set()

    for node_type, nodes in collector.nodes_by_type.items():
        #if node_type in ["Compare", "BinOp", "BoolOp", "UnaryOp", "AugAssign", "Subscript", "Slice", "NameConstant", "If"]:
        if node_type in ["Compare", "BinOp", "BoolOp", "UnaryOp", "AugAssign", "Subscript", "NameConstant", "If"]:
            for node in nodes : node_list.add((node_type, node))

    assert isinstance(collector.nodes_by_type, dict), "Expected nodes_by_type to be a dictionary"
    assert all(isinstance(nodes, list) for nodes in collector.nodes_by_type.values()), "Expected nodes to be lists"
    assert len(node_list) > 0, "node_list should not be empty"

    node_type, node = random.choice(list(node_list))
    nd = ast_to_dict(node)
    if 'op' in nd:
        op = nd['op']['type']
    elif 'ops' in nd:
        op = nd['ops'][0]['type']

    # just lots of cases to properly mutate, could look prettier with a lambda idk
    samp = None
    match node_type:
        case "Compare":
            op = nd['ops'][0]['type']
            if op in mut_compare:
                samp = random.choice(list(mut_compare - {op}))
            elif op in mut_set_compare:
                samp = random.choice(list(mut_set_compare - {op}))
            elif op == "Is" : samp = op
            else:
                samp = op
        case "BinOp":
            op = nd['op']['type']
            if op in mut_binop:
                samp = random.choice(list(mut_binop - {op}))
            elif op in mut_bitop:
                samp = random.choice(list(mut_bitop - {op}))
            elif op in mut_shiftop:
                samp = random.choice(list(mut_shiftop - {op}))
            else:
                samp = op
        case "BoolOp":
            op = nd['op']['type']
            if op in mut_boolop:
                samp = random.choice(list(mut_boolop - {op}))
            else:
                samp = op
        case "UnaryOp":
            op = nd['op']['type']
            if op in mut_unaryop:
                samp = random.choice(list(mut_unaryop - {op}))
            else:
                samp = op
        case "AugAssign":
            op = nd['op']['type']
            if op in mut_augassign:
                samp = random.choice(list(mut_augassign - {op}))
            else:
                samp = op
        case "Subscript":
            if 'slice' in nd:
                if isinstance(nd['slice'], dict) and 'type' in nd['slice'] and nd['slice']['type'] == 'Constant':
                    current_index = nd['slice']['value']
                    samp = random.choice([current_index + 1, current_index - 1, -1])
                    nd['slice']['value'] = samp
        case "Slice":
            if not (nd['lower'] != None or nd['upper'] != None):
                tmp = nd['lower']
                nd['lower'] = nd['upper']
                nd['upper'] = tmp
            else:
                lower_value = nd['lower']['value'] if nd['lower'] else None
                upper_value = nd['upper']['value'] if nd['upper'] else None

                if random.random() > 0.5:
                    nd['lower']['value'] = lower_value + random.choice([-1, 1])
                else:
                    nd['upper']['value'] = upper_value + random.choice([-1, 1])
        case "NameConstant":
            if 'value' in nd:
                current_value = nd['value']
                samp = random.choice(list(name_constant_mut - {current_value}))
                nd['value'] = samp
        case "If":
            if 'test' in nd:
                samp = random.choice([True, False])
                nd['test'] = {'type': 'NameConstant', 'value': samp}
        case _:
            pass

    if 'op' in nd:
        nd['op']['type'] = samp
    elif 'ops' in nd:
        nd['ops'][0]['type'] = samp

    try:
        repl = dict_to_ast(nd)
        replacer = NodeReplacer(node, repl)
        modified_tree = replacer.visit(tree)
    except Exception as e: 
        return tree # if parsing fails, just bail

    return modified_tree


