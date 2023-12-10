import sys
import sha3
import json

from ast_mapper import AstMapper

def ast_from_config(build_path):
    f = open(build_path, 'rb')
    build_config = json.load(f)
    f.close()

    tree = build_config.get('ast')
    if not tree:
        sources = build_config['sources']
        tree = sources[list(sources.keys())[0]]['AST']

    return AstMapper(tree)

build_path = './data/build.json'
ast = ast_from_config(build_path)

# find storage identifiers
# find VariableDeclaration with "stateVariable": true, cache the contract context (eg. ContractName[:28] + function

def next_node_id():
    return ast.next_node_id()

def get_literal_node(value):
    hex_val = hex(value)[2:]
    if len(hex_val) % 2 != 0:
        hex_val = '0' + hex_val

    return {
        "hexValue": hex_val,
        "id": next_node_id(),
        "isConstant": False, # TODO: can probably be true
        "isLValue": False,
        "isPure": True,
        "kind": "number",
        "lValueRequested": False,
        "nodeType": "Literal",
        #"src": "30048:1:0",
        "typeDescriptions": {
            "typeIdentifier": "t_rational_0_by_1",
            "typeString": "int_const 1" # TODO: omit?
        },
        "value": 'bytes32(uint256(0x%x))' % value
    }

def get_map_slot_node(key_id_node, slot_id_node):
    key_id_node = key_id_node.copy()
    key_id_node['id'] = next_node_id()

    return {
        "arguments": [
            {
                "arguments": [
                    key_id_node,
                    slot_id_node
                ],
                "expression": {
                    "argumentTypes": [
                        {
                            "typeIdentifier": "t_rational_6_by_1",
                            "typeString": "int_const 6"
                        },
                        {
                            "typeIdentifier": "t_uint256",
                            "typeString": "uint256"
                        }
                    ],
                    "expression": {
                        "id": next_node_id(),
                        "name": "abi",
                        "nodeType": "Identifier",
                        "overloadedDeclarations": [],
                        "referencedDeclaration": -1,
                        "src": "1123:3:18",
                        "typeDescriptions": {
                            "typeIdentifier": "t_magic_abi",
                            "typeString": "abi"
                        }
                    },
                    "id": next_node_id(),
                    "isConstant": False,
                    "isLValue": False,
                    "isPure": False,
                    "lValueRequested": False,
                    "memberLocation": "1127:6:18",
                    "memberName": "encode",
                    "nodeType": "MemberAccess",
                    "src": "1123:10:18",
                    "typeDescriptions": {
                        "typeIdentifier": "t_function_abiencode_pure$__$returns$_t_bytes_memory_ptr_$",
                        "typeString": "function () pure returns (bytes memory)"
                    }
                },
                "id": next_node_id(),
                "isConstant": False,
                "isLValue": False,
                "isPure": False,
                "kind": "functionCall",
                "lValueRequested": False,
                "nameLocations": [],
                "names": [],
                "nodeType": "FunctionCall",
                "src": "1123:20:18",
                "tryCall": False,
                "typeDescriptions": {
                    "typeIdentifier": "t_bytes_memory_ptr",
                    "typeString": "bytes memory"
                }
            }
        ],
        "expression": {
            "argumentTypes": [
                {
                    "typeIdentifier": "t_bytes_memory_ptr",
                    "typeString": "bytes memory"
                }
            ],
            "id": next_node_id(),
            "name": "keccak256",
            "nodeType": "Identifier",
            "overloadedDeclarations": [],
            "referencedDeclaration": -8,
            "src": "1113:9:18",
            "typeDescriptions": {
                "typeIdentifier": "t_function_keccak256_pure$_t_bytes_memory_ptr_$returns$_t_bytes32_$",
                "typeString": "function (bytes memory) pure returns (bytes32)"
            }
        },
        "id": next_node_id(),
        "isConstant": False,
        "isLValue": False,
        "isPure": False,
        "kind": "functionCall",
        "lValueRequested": False,
        "nameLocations": [],
        "names": [],
        "nodeType": "FunctionCall",
        "src": "1113:31:18",
        "tryCall": False,
        "typeDescriptions": {
            "typeIdentifier": "t_bytes32",
            "typeString": "bytes32"
        }
    }

def patch_node(id_type, return_type, node, slot_id, key_id_node=None, rhs=None):
    slot_id_node = get_literal_node(slot_id)
    args = []
    if key_id_node:
        args.append(get_map_slot_node(key_id_node, slot_id_node))
    else:
        args.append(slot_id_node)

    if rhs:
        rhs = rhs.copy()
        rhs['id'] = next_node_id()
        args.append(rhs)
        if key_id_node:
            method_name = '_sstore_' + return_type.replace('.', '_')
        else:
            method_name = '_sstore_' + id_type.replace('.', '_')
    else:
        # load id_type and return return_type?
        method_name = '_sload_' + id_type.replace('.', '_')

    # TODO: simplify
    template = {
        'parent_id': node['parent_id'],
        'patched': True,
        "arguments": args,
        "expression": {
            "argumentTypes": [
                {
                    "typeIdentifier": "t_uint256",
                    "typeString": "uint256" # TODO: correct types..?
                }
            ],
            "id": next_node_id(),
            "name": method_name,
            "nodeType": "Identifier",
            "overloadedDeclarations": [],
            "referencedDeclaration": 82200,
            "src": "29774:11:0",
            "typeDescriptions": {
                "typeIdentifier": "t_function_internal_view$_t_address_$returns$_t_uint256_$",
                "typeString": "function (address) view returns (uint256)"
            }
        },
        "id": next_node_id(),
        "isConstant": False,
        "isLValue": False,
        "isPure": False,
        "kind": "functionCall",
        "lValueRequested": False,
        "nameLocations": [],
        "names": [],
        "nodeType": "FunctionCall",
        "src": "29774:20:0",
        "tryCall": False,
        "typeDescriptions": {
            "typeIdentifier": "t_uint256",
            "typeString": "uint256"
        }
    }

    node.clear()
    node.update(template)


# TODO: this does not work; need to enumerate sstore/sload all fields???
def make_type(type_def):
    template = \
    """
    function _sload_{{{type_u}}}(bytes32 ptr) view returns ({{{type}}} storage value) {
        assembly {
            value.slot := ptr
        }
    }

    function _sstore_{{{type_u}}}(bytes32 ptr, {{{type}}} storage value) returns ({{{type}}} storage) {
        {{{type}}} storage item;
        assembly {
            item.slot := ptr
        }

        item = value;
        return value;
    }
    """

    return template.replace('{{{type}}}', type_def).replace('{{{type_u}}}', type_def.replace('.', '_'))

def map_variable_declarations():
    # var name to storage slot
    var_maps = {}
    for var in ast.by_type['VariableDeclaration']:
        # go up the tree until we find the context (contract or function)
        node = var
        while node['parent_id']:
            node = ast.by_id[node['parent_id']]
            if node['nodeType'] == 'ContractDefinition':
                break

            if node['nodeType'] == 'FunctionDefinition':
                node = None
                break

        # if it's a contract variable, cache it
        if node:
            if 'functionSelector' in var:
                # if it's a mapping it's easier to take it from the AST if available...
                selector = var['functionSelector']
            else:
                # if it's not a mapping, raise an error for now?
                if var['typeDescriptions']['typeString'].startswith('mapping'):
                    raise Exception('mapping without selector')
                
                selector = sha3.keccak_256(var['name'].encode('utf-8') + b'()').hexdigest()[:8]

            var_maps[var['name']] = { 'context': node['name'], 'name': var['name'], 'selector': selector }

    return var_maps

def patch_storage_slots():
    var_maps = map_variable_declarations()
    #print(var_maps)

    types_set = set()
    for id_node in ast.by_type['Identifier']:
        if id_node['name'] not in var_maps:
            continue

        # TODO: test complex types like structs, tuples, contracts, enums, mappings..?
        # TODO: is there a memory ref, calldata ref?
        id_type = id_node['typeDescriptions']['typeString'].replace('struct ', '').replace('enum ', '').replace('contract ', '').replace(' storage ref', '')
        if id_type.startswith('mapping'):
            # take the key as the type for mappings
            return_type = id_type.split(' => ')[1].replace(')', '')
            id_type = id_type.replace('mapping(', '').split(' => ')[0]
        else:
            return_type = id_type

        types_set.add(id_type)

        decl = var_maps[id_node['name']]
        contract_name = decl['context'][:28]
        slot_id = int(contract_name.ljust(28, ' ').encode('utf8').hex() + decl['selector'], 16)
        parent = ast.by_id[id_node['parent_id']]
        if parent['nodeType'] == 'Assignment' and id_node == parent['leftHandSide']:
            # identifier is being assigned to (store)
            # need to replace Assignment with a function call to _sstore(id_node, <rightHandSide>)
            #print('assignment')
            rhs = parent['rightHandSide']
            patch_node(id_type, return_type, parent, slot_id, key_id_node=None, rhs=rhs)
        else:
            # if key is None then it's a simple read, otherwise it's a mapping
            key_id_node = parent.get('indexExpression')
            if key_id_node:
                # also if there's a key then need to replace the index expression itself
                grandparent = ast.by_id[parent['parent_id']]
                rhs = None
                if grandparent['nodeType'] == 'Assignment': # TODO: check it is lhs?
                    rhs = grandparent['rightHandSide']
                    parent = grandparent

                patch_node(id_type, return_type, parent, slot_id, key_id_node, rhs)
            else:
                patch_node(id_type, return_type, id_node, slot_id)

    #print(types_set)
    # for type_id in types_set:
    #     if type_id not in ['uint256', 'address', 'bytes32', 'bool']:
    #         print(make_type(type_id))

# TODO: need to merge constructors and such
# TODO: leave documentation comment saying which contract it was inlined from
def delinearize(contract_name):
    node = None
    for id_node in ast.by_type['ContractDefinition']:
        if id_node['name'] == contract_name:
            node = id_node
            break

    if not node:
        return False
    
    # inline inherited contract bodies (as is for now)
    base_ids = reversed(node['linearizedBaseContracts'][1:])
    for base_id in base_ids:
        base = ast.by_id[base_id]
        # TODO: check parent_id is ok
        node['nodes'] = ast.clone(base['nodes'], node['id']) + node['nodes']

    # remove inherited contracts
    node['linearizedBaseContracts'] = node['linearizedBaseContracts'][:1]
    node['baseContracts'] = []
    return True

def make_block(*statements):
    return {
        "id": 0,
        #"parent_id": parent_id, # TODO: pass this..
        "nodeType": "Block",
        "src": "29254:584:0",
        "statements": statements
    }

def reparent(parent_id, *nodes):
    for node in nodes:
        node['parent_id'] = parent_id,

def make_tuple(components):
    new_id = next_node_id()
    return {
        "components": ast.clone(components, new_id),
        "id": new_id,
        "isConstant": False,
        "isInlineArray": False,
        "isLValue": False,
        "isPure": False,
        "lValueRequested": False,
        "nodeType": "TupleExpression",
        "src": "27149:6:0",
        "typeDescriptions": {
            "typeIdentifier": "t_tuple$_t_rational_1_by_1_$_t_rational_2_by_1_$",
            "typeString": "tuple(int_const 1,int_const 2)"
        }
    }

# make VariableDeclarationStatement ie. (params) = (args) from FunctionDefinition(params), FunctionCall(args)
def make_var_dec_st_from_func_call(params_decl, arg_values):
    new_id = next_node_id()
    cloned_decl = ast.clone(params_decl, new_id)
    # for d in cloned_decl:
    #     # it's ok to rename here because it was cloned above
    #     d['name'] += '_' + d['id']

    # TODO: need to return the remapping and do it outside of this function
    # rename_map = { decl[i]['id']: cloned_decl[i]['id'] for i in range(len(decl)) }
    # def rename_ids(node, parent):
    #     # if node['nodeType'] == 'VariableDeclaration':
    #     #     node['name'] += '_2'

    #     if node['nodeType'] == 'Identifier':
    #         if node['referencedDeclaration'] in rename_map:
    #             node['name'] += '_2'
    #             node['referencedDeclaration'] = rename_map[node['referencedDeclaration']]

    # for d in cloned_decl:
    #     ast.walk_tree(d, callback=rename_ids)

    tuple_expr = make_tuple(arg_values)
    assignment_ids = [d['id'] for d in cloned_decl]
    var_dec = {
        "assignments": assignment_ids,
        "declarations": cloned_decl,
        "id": new_id,
        "initialValue": tuple_expr,
        "nodeType": "VariableDeclarationStatement",
        "src": "29624:70:0"
    }

    return var_dec

"""
IDEA: to embed modifiers, maybe use embed_inline BEFORE said function is inlined
and also embed_inline THE FUNCTION into THE MODIFIER
that is embed_inline(modifier, PlaceholderStatement = the function)

we have:
fd = FunctionDefinition
fd.modifiers = ModifierInvocation[]
fd.body = Block with fcs = FunctionCall[]

need to replace fd like so:
while fd.modifiers:
    mod = fd.modifiers.pop()
    fd.update such that fd.body = unmodify(mod, fd.body)
    where
    unmodify is mod.update such that PlaceholderStatement = fd.body
"""
# TODO: this does not embed parameters :(
def embed_modifiers_inplace(fd_node):
    # kind = baseConstructorSpecifier  is implied Super.Body + This.body
    # kind = modifierInvocation depends on the PlaceholderStatement
    def replace_placeholder(node, parent):
        if node['nodeType'] == 'PlaceholderStatement':
            # TODO: by now it's really clear I need a library to update parent_id and such hotswap/inject/attach/etc.
            clone_body = ast.clone(fd_node['body'], node['parent_id'])
            node.clear()
            node.update(clone_body)

    while fd_node.get('modifiers'):
        mod = fd_node['modifiers'].pop()
        mod_dec = ast.by_id[mod['modifierName']['referencedDeclaration']]
        mod_body = ast.clone(mod_dec['body'], fd_node['id'])
        ast.walk_tree(mod_body, callback=replace_placeholder)
        fd_node['body'] = mod_body
        
    return True


def embed_inline_func_inplace(fc_node):
    if 'referencedDeclaration' not in fc_node['expression']: # ['nodeType'] == 'MemeberAccess':
        return False # this is likely an external call (TODO: test Super.func and I guess public funcs)
    
    ref_id = fc_node['expression']['referencedDeclaration']
    func_dec = ast.by_id.get(ref_id)
    if not func_dec:
        return False

    if 'body' not in func_dec:
        return False # TODO: check when body is empty (calls on interfaces?)
    
    # TODO: walk the body to replace identifiers referncing the func_dec params
    # TODO: embed modifiers first?
    inline_body = ast.clone(func_dec['body'], fc_node['parent_id'])
    #embed_modifiers_inplace(inline_body) # TODO: need to replace func_dec not func_dec['body']
    # create VariableDeclarations (decl_params) = (passed_args)
    vds = make_var_dec_st_from_func_call(func_dec['parameters']['parameters'], fc_node['arguments'])
    vds['documentation'] = '@inlined from ' + func_dec['name']
    vds['parent_id'] = inline_body['id']
    inline_body['statements'].insert(0, vds)

    # for some reason documentation does not work on block bodies :(
    # if 'documentation' not in inline_body:
    #     inline_body['documentation'] = { 'id': ast.next_node_id(), 'nodeType': 'StructuredDocumentation', 'text': '', 'src': '0:0:0' }
    # inline_body['documentation']['text'] = ' @dev PATCHED!!!'

    fc_node.clear()
    fc_node.update(inline_body)
    return True


# TODO: should embed a single function, then before the call
# instead of contract_name pass the FunctionCall node to embed?
# NOTE: must inline modifiers too
def embed_inline(contract_name, method_name, embed_modifiers=True, max_depth=-1):
    """
    embed inline functions
    work on level of <contract>.<method> (method could be internal itself)
    scan all FunctionCalls where first_parent is (the desired) FunctionDefinition
    replace the call with Block wrapping the FunctionCall.body
    and replace all Identifiers referencing FunctionCall->FunctionDefinition.arguments
    """
    target_func = None
    target_contract = None
    for func_node in ast.by_type['FunctionDefinition']:
        # TODO: it is possible to lookup FuncDef['scope'] to get the contract node id
        if func_node['name'] != method_name:
            continue

        tmp = ast.first_parent(func_node, 'ContractDefinition')
        if tmp and tmp['name'] == contract_name:
            target_func = func_node
            target_contract = tmp
            break

    if not target_func:
        return False
        
    # first, embed modifiers (TODO: need to embed modifiers for FunctionCall too)
    # TODO: fix reparenting here
    if embed_modifiers:
        embed_modifiers_inplace(target_func)

    # while there are FunctionCalls, inline them
    while max_depth != 0:
        # TODO: get all FunctionCalls, recursively replace them (wrap them in Block)
        func_calls = []
        def find_related_func_call(node, parent):
            if node['nodeType'] != 'FunctionCall':
                return
        
            if node['kind'] == 'typeConversion':
                return

            # if no parent, it's just a type conversion on global scope..
            func_def = ast.first_parent(node, 'FunctionDefinition')
            if func_def != target_func:
               return

            tmp = ast.first_parent(node, 'ContractDefinition')
            if tmp['id'] in target_contract['linearizedBaseContracts']:
                func_calls.append(node)

        ast.walk_tree(ast.root, callback=find_related_func_call)
        #print(func_calls)
        #last_call = func_calls[-1]
        #parent = ast.by_id[last_call['parent_id']]

        count = 0
        for fc in func_calls:
            if embed_inline_func_inplace(fc):
                count += 1

        if count == 0:
            break

        max_depth -= 1

    return True

def make_identifier(name, parent_id, referencedDeclaration=-1):
    return {
        "id": next_node_id(),
        "name": name,
        "nodeType": "Identifier",
        #"overloadedDeclarations": [],
        "referencedDeclaration": referencedDeclaration,
        "src": "0:0:0",
        "typeDescriptions": {
            "typeIdentifier": "t_todo",
            "typeString": "type(TODO)"
        },
        "parent_id": parent_id
    }

# embed "using .. for .." statements BECAUSE THEY SUCK
def embed_using_for():
    lib_funcs_to_lib_id = {}
    lib_ids = {}
    for func_def in ast.by_type.get('FunctionDefinition'):
        contract = ast.first_parent(func_def, 'ContractDefinition')
        if contract.get('contractKind') != 'library':
            continue

        lib_ids[contract['id']] = contract['name']
        lib_funcs_to_lib_id[func_def['id']] = contract['name']

    for mem_acc in ast.by_type.get('MemberAccess'):
        ref_id = mem_acc.get('referencedDeclaration')
        if ref_id not in lib_funcs_to_lib_id:
            continue

        # note: structure should be FunctionCall(MemberAccess(expression), args..)
        # and translated to FunctionCall(expression, MemberAccess(Identifier(library)) + args)
        func_call = ast.by_id[mem_acc['parent_id']]
        if func_call['nodeType'] != 'FunctionCall':
            continue

        first_arg = mem_acc['expression']
        
        # check that the accessed member isn't already the lib
        exp_ref_id = first_arg.get('referencedDeclaration')
        if exp_ref_id in lib_ids:
            continue

        # replace with a lib Identifier
        id_node = make_identifier(lib_funcs_to_lib_id[ref_id], mem_acc['parent_id'])
        mem_acc['expression'] = id_node
        func_call['arguments'] = [first_arg] + func_call['arguments']

    for using in ast.by_type.get('UsingForDirective'):
        ast.by_id[using['parent_id']]['nodes'].remove(using)


DEBUG = False
if DEBUG:
    # FOR DEBUGGING - rename all identifiers to include the respective id
    # note: this actually seems to fix var shadowing issues, for now; but it's not the correct solution
    # for the long term as the tree is out of sync
    def rename_var_decs(node, parent):
        if node['nodeType'] == 'VariableDeclaration':
            node['name'] += '_' + str(node['id'])

    def rename_ids(node, parent):
        if node['nodeType'] == 'Identifier':
            # TODO: YulIdentifier doesn't seem to have referencedDeclaration so will have to search up the scope to
            # (probably best preprocess this to add [guessed] referencedDeclaration to YulIdentifier)
            ref_node = ast.by_id.get(node['referencedDeclaration'])
            if ref_node:
                node['name'] = ref_node['name']

    ast.walk_tree(ast.root, callback=rename_var_decs)
    ast.walk_tree(ast.root, callback=rename_ids)

embed_using_for()
#patch_storage_slots()
#delinearize('Zapper_Matic_Bridge_V1_1')
# try:
#     embed_inline('Zapper_Matic_Bridge_V1_1', 'ZapBridge', embed_modifiers=True, max_depth=int(sys.argv[-1]))
# except:
#     print('error: possibly too deep?', file=sys.stderr)

data = { "sources": { build_path: { "AST": ast.root } } }
print(json.dumps(data)) #, indent=4))

"""

IERC20(fromToken).safeTransferFrom(
    msg.sender,
    address(this),
    swapAmounts[0] + (swapAmounts[1])
);

is tranlated as:

(IERC20 token_529, address from_531, address to_533, uint256 value_535)
    =
(msg.sender, address(this), swapAmounts_1600[0] + (swapAmounts_1600[1]));


and it should be, ideally, first converted to:

SafeERC20.safeTransferFrom(
    IERC20(fromToken),
    msg.sender,
    address(this),
    swapAmounts[0] + (swapAmounts[1])
);

and then inlined normally (only if library is attached though?)

=> hence, need to run a UsingForInliner FIRST

"""
