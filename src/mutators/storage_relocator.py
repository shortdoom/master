import sha3

ast = None

def make_literal(value):
    hex_val = hex(value)[2:]
    if len(hex_val) % 2 != 0:
        hex_val = '0' + hex_val

    return {
        "hexValue": hex_val,
        "id": ast.next_node_id(),
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
    key_id_node['id'] = ast.next_node_id()

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
                        "id": ast.next_node_id(),
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
                    "id": ast.next_node_id(),
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
                "id": ast.next_node_id(),
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
            "id": ast.next_node_id(),
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
        "id": ast.next_node_id(),
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
    slot_id_node = make_literal(slot_id)
    args = []
    if key_id_node:
        args.append(get_map_slot_node(key_id_node, slot_id_node))
    else:
        args.append(slot_id_node)

    if rhs:
        # TODO: use ast.clone(rhs) instead
        rhs = rhs.copy()
        rhs['id'] = ast.next_node_id()
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
            "id": ast.next_node_id(),
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
        "id": ast.next_node_id(),
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

def patch_storage_slots(_ast):
    global ast
    ast = _ast

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
