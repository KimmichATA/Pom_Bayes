
#Get DiscreteDistribution Running

#Demonstrate has same values as Netica


import random
import string
import json
import functools
import pomegranate as pmg
# from pomegranate import *
#from pomegranate import BayesianNetwork as bn
import pandas as pd


def MHmakeRandomString(n=1, length=12):
    """Makes a random string of letters for node names
    Param:
    ------------
    length: number of character in the word
    n: number of random words
    Return
    -------------
    List: list of words with specified length"""

    return [''.join(random.choices(string.ascii_uppercase, k=length)) for _ in range(n)]

def _healthcheck(msg=''):
    """Echo back the input
    param
    ---------
    msg: The message to echo
    return
    -------
    msg: the message"""
    return 'The message is: {}'.format(msg)


def _decomposed_network(network):
    """We want to make sure that the nework is well ordeered before starting to build it
    return: node_list: list ordered in a way that """
    arr = network[1:-1].split('][')
    nodes_list=[ar.split('|')  for ar in arr]
    # we need to sort node_list so we only treat conditional nodes after independent or parents' ones
    sorted_list = []
    for _ in nodes_list:
        for n in nodes_list:
            if len(n) == 1:
                nodes_list.remove(n)
                nodes_list.insert(0, n)
                sorted_list.append(n[0])
            else:
                if n[1] in sorted_list:
                    sorted_list.append(n[0])
                else:
                    nodes_list.remove(n)
                    nodes_list.append(n)
    return nodes_list

def _solve_bayes_network(cpts, conditionals=None):
    print(f'cpts: {cpts}')
    print(f'conditionals: {cpts}')
    model = pmg.BayesianNetwork("User Produced Model")
    states = []
    distributions = []
    cond = []
    _cond_stage = []
    def _translator(string):
        if string == 0 or string == '0':
            return 'True'
        elif string == 1 or string == '1':
            return 'False'
        else:
            return None
    counter = 0
    for i,name in enumerate(cpts.keys()):
        temp_dict =cpts[name].to_dict()
        if name not in conditionals:
            for k in temp_dict.keys():
                distributions.append(pmg.DiscreteDistribution(temp_dict[k]))
                states.append(pmg.State(distributions[counter], name=name))
                counter += 1
        else:
            _cond_stage.append(i)
            for col in temp_dict.keys():
                for val in temp_dict[col].keys():
                    arr = [_translator(col), val, temp_dict[col][val]]
                    cond.append(arr)

            print(f'cond: {cond}')
            states.append(pmg.State(pmg.ConditionalProbabilityTable(cond, distributions), name=name))
    for i,s in enumerate(states):
        print(f'i: {i}')
        print(f's: {s}')
        model.add_states(s)
        if i not in _cond_stage and _cond_stage:
            model.add_edge(s,states[_cond_stage[0]])
    model.bake()
    return model


"""This function is written to support more and more nodes in the network.
However, it looks like there is a bug in the implementation of the module pomegrenate"""

# def _solve_bayes_network(network, cpts, conditionals=None):
#     """ Solves the basian and return the baked model
#     return: model: Baysian Network
#     """
#     model = pmg.BayesianNetwork("User Produced Model")
#     states = []
#     distributions = []

#     _cond_stage = []
#     nodes_list = _decomposed_network(network)
#     def _translator(string):
#         if string == 0 or string == '0':
#             return 'True'
#         elif string == 1 or string == '1':
#             return 'False'
#         else:
#             return None
#     counter = 0
#     for i,node in enumerate(nodes_list):
#         cond = []
#         dis = []
#         name = node[0]
#         temp_dict = cpts[name].to_dict()
#         if name not in conditionals:
#             for k in temp_dict.keys():
#                 distributions.append(pmg.DiscreteDistribution(temp_dict[k]))
#                 states.append(pmg.State(distributions[counter], name=name))
#                 counter += 1
#         else:
#             _cond_stage.append(i)
#             for col in temp_dict.keys():
#                 for val in temp_dict[col].keys():
#                     arr = [_translator(col), val, temp_dict[col][val]]
#                     cond.append(arr)
#             dis.append(distributions[len(distributions) - 1])
#             distributions.append(pmg.ConditionalProbabilityTable(cond, dis))
#             states.append(pmg.State(distributions[len(distributions) - 1], name=name))

#     for i,s in enumerate(states):
#         model.add_states(s)
#         if s.name in conditionals:
#             model.add_edge(s,states[i-1])
#     model.bake()
#     return model



def runBayes(bayesian_model, evidence_json):
    model = bayesian_model
    dimnames_default = ['dead grass', 'yellow grass', 'green grass']
    print('Set Default States (Dimension Names): {}'.format(dimnames_default))
    network = model['bayesian_network']['node_map']
    print('Getting Evidence from Payload')
    ev = {}
    if evidence_json:
        evidence = evidence_json['modelEvidenceMap']
    else:
        evidence = {}

    if evidence:
        for model_id in evidence.keys():
            print('Evidence on Model : {}'.format(model_id))
            nodeMap = evidence[model_id]['nodeEvidenceMap']
            for node_id in nodeMap.keys():
                if node_id != 'modelId':
                    evidence_list = nodeMap[node_id]['evidenceList']
                    print(evidence_list)
                    index = [idx for idx, s in enumerate(evidence_list) if 'stateLikelihoods' in s][0]
                    likelihoods = evidence_list[index]['stateLikelihoods']
                    ll = likelihoods[0]['likelihood']
                    ss = likelihoods[0]['state']
                    l = []
                    s = []
                    if isinstance(ll, int) or isinstance(ll, float):
                        l.append(ll)
                    else:
                        l.extend(ll)
                    if isinstance(ss, str):
                        s.append(ss)
                    else:
                        s.extend(ss)
                    for i in range(len(s)):
                        if s[i]:
                            ev[node_id] = l[i]
    else:
        print('Evidence is null')
    print('Parsing Network...')
    print('Number of Network Nodes: {}'.format(len(network)))
    cpt_full = {}
    map_ids = {}
    net_full = ''
    conditional_nodes = []
    nodes_list = []
    nodes_parent_pointers = []
    for node_ in network:
        node = network[node_]
        id_raw = node['id']
        if id_raw not in map_ids.keys():
            id = MHmakeRandomString(1,3)
            map_ids [id_raw] = id
        else:
            id = map_ids[id_raw]
        id = id[0]
        print('Map of [Id, Mapped ID]: [{},{}]'.format(id_raw, id))
        nodes_list.append(id)
        cptTable = node['cpt']['table']
        print(cptTable)
        cpt = pd.DataFrame(cptTable)
        dimnames_list= {}
        dimnames_list[id] = dimnames_default
        parent_ids = ''

        for parent_id_raw in node['parentOrderList']:
            if parent_id_raw not in map_ids.keys():
                map_ids[parent_id_raw] = MHmakeRandomString(1,3)
            parent_id = map_ids[parent_id_raw][0]
            dimnames_list[parent_id] = dimnames_default
            if parent_ids == '':
                parent_ids = '{}{}'.format(parent_ids, parent_id)
                #nodes_parent_pointers.append(-1)  # this means the node has no parent

            else:
                parent_ids = '{}:{}'.format(parent_ids, parent_id)
                #index_parent = nodes_list.index(parent_id)
                #nodes_parent_pointers.append(index_parent)

        if parent_ids == '':
            net_full = '[{}]{}'.format(id, net_full)
            nodes_parent_pointers.append(-1)
            nodes_list.append(id)
        else:
            net_full = '{}[{}|{}]'.format(net_full, id, parent_ids)
            conditional_nodes.append(id)

        #dim(cpt) <- dim_i
        cpt.index = dimnames_list[id]
        cpt_full[id] = cpt

    print("Network:", net_full)
    print("CPTs:",str(cpt_full))

    print('Applying Evidence if not NULL')

    evidence_string_list = {}
    count_ev = 1
    for ev_id in ev.keys():
        prob = ev[ev_id]
        node_evidence = map_ids[ev_id][0]
        evidence_string_list[count_ev] = '({} == {})'.format(node_evidence, prob)
        temp_table = cpt_full[node_evidence]
        # temp_table[temp_table.columns[0]]['True'] = prob
        # temp_table[temp_table.columns[0]]['False'] = 1 - prob
        print('Evidence:{}->{}'.format(map_ids[ev_id], prob))

    dfit = _solve_bayes_network(cpt_full, conditional_nodes)


    conditionals = {}
    posteriors = {}
    print("Calculating Posterior Probabilities...")
    def get_index(l):
        for ind, val in enumerate(l):
            if val is None:
                return ind
        return 0
    for i,target_id in enumerate(map_ids.keys()):
        conditionals[target_id] = {}
        global_target_id = map_ids[target_id][0]
        envent_str_global_id = '({} =="dead grass")'.format(global_target_id)
        event_str = [None for _ in range(len(network))]
        #print(dfit.predict_proba(event_str))
        posteriors[target_id] = dfit.predict_proba(event_str)[i].parameters[0]['dead grass']
        print('P{}               ={:.3}'.format(envent_str_global_id, posteriors[target_id]))
        for j,id in enumerate(map_ids.keys()):
            global_id = map_ids[id][0]
            conditionals[target_id][id] = {}
            envent_str_global_id = '({} =="True")'.format(global_id)
            envent_str_true = '({}=="True")'.format(global_target_id)
            envent_str_false = '({}=="False")'.format(global_target_id)

            envent_str_true_position = ['True' if _ == j else None for _ in range(len(network))]
            envent_str_false_position = ['False' if _ == j else None for _ in range(len(network))]

            if len(network) <= 1:
                conditionals[target_id][id]['True'] = 1.
                conditionals[target_id][id]['False'] = 0.
            elif target_id == id:
                conditionals[target_id][id]['False'] = 0.
                conditionals[target_id][id]['True'] = 1.
            else:
                conditionals[target_id][id]['True'] =                         dfit.predict_proba(envent_str_true_position
                                          )[get_index(envent_str_true_position)].parameters[0]['True']
                conditionals[target_id][id]['False'] =                         dfit.predict_proba(envent_str_false_position
                                          )[get_index(envent_str_true_position)].parameters[0]['True']
            print('P{}|{}={:.3}'.format(envent_str_global_id, envent_str_true, conditionals[target_id][id]['True']))
            print('P{}|{}={:.3}'.format(envent_str_global_id, envent_str_false, conditionals[target_id][id]['False']))
    print("...Done Calculating")
    print("Constructing Response Object...")
    execution_results_full = {}
    execution_results_full['execution_list'] = {}
    count = 1
    for target_node in posteriors.keys():
        prob ={}
        prob['modelId'] = target_node
        prob['targetNodeId'] = target_node
        prob['timeCalculated'] = '2019-01-30T14:50:29.848Z'
        prob['modelVersion'] = 0
        prob['probabilities'] = {}
        for node in conditionals.keys():
            post = posteriors[node]
            post_false = 1 - post
            conditional_true_true = conditionals[target_node][node]['True']
            conditional_true_false = 1 - conditional_true_true
            conditional_false_true = conditionals[target_node][node]['False']
            conditional_false_false = 1 - conditional_false_true
            prob["probabilities"][node] = {}
            prob["probabilities"][node]["nodeType"] = "COMPONENT"
            prob["probabilities"][node]["nipfPriority"] = 0.0
            prob["probabilities"][node]["harmLevelTrue"] = 1.0
            prob["probabilities"][node]["harmLevelFalse"] = 1.0
            prob["probabilities"][node]["confidence"] = -1.0
            prob["probabilities"][node]["supplierConfidence"] = -1.7
            prob["probabilities"][node]["confidence"] = -1.0
            prob["probabilities"][node]["prior"] = [post, post_false]
            prob["probabilities"][node]["post"] = [post, post_false]
            prob["probabilities"][node]["postWithoutDecay"] = [post, post_false]
            prob["probabilities"][node]["conditional"] = {}
            prob["probabilities"][node]["conditional"][0]=[conditional_true_true, conditional_true_false]
            prob["probabilities"][node]["conditional"][1]= [conditional_false_true, conditional_false_false]
        execution_results_full["execution_list"][count] = prob
        count += 1
    print("...Response Object Constructed")
    object_json = json.dumps(execution_results_full)
    #print(object_json)
    return object_json


def compute(bayesian_model, evidenceList):
    """#* Return the posterior probabilities
    #* @param bayesian_model Bayesian Model
    #* @post /bayes/computeConditionalParallel
    """
    print('POST to /bayes/computeConditionalParallel')
    print('Converting Payload to JSON')
#     bayesian_model_json = json.loads(json.dumps(bayesian_model))
#     evidence_json = json.loads(json.dumps(evidenceList))
    print('Running Bayes Analytic')
    my_json = runBayes(bayesian_model, evidenceList)
    #excecution_results = json.dumps(my_json)
    return my_json


# print("Running Pre-Tests...")
# print("=======================================================================")
# print("TEST 1: A without Evidence")
# bayesian_model = '{"bayesian_network":{"node_map":{"resource:f3b8606d-0af5-46cd-bad3-699536a0b969":{"id":"resource:f3b8606d-0af5-46cd-bad3-699536a0b969","cpt":{"table":{"":[0.55,0.45]}},"parentOrderList":[]}}}}'
# evidence = '{}'
# bayesian_model_from = json.loads(bayesian_model)
# evidence_from = json.loads(evidence)
# results = compute(bayesian_model_from, evidence_from)

# print("=======================================================================")
# print("TEST 2: A with Evidence")
# # bayesian_model = '{"bayesian_network":{"node_map":{"resource:f3b8606d-0af5-46cd-bad3-699536a0b969":{"id":"resource:f3b8606d-0af5-46cd-bad3-699536a0b969","cpt":{"table":{"":[0.55,0.45]}},"parentOrderList":[]}}}}'
# # evidence = '{"modelEvidenceMap":{"MODEL_ID":{"nodeEvidenceMap":{"resource:f3b8606d-0af5-46cd-bad3-699536a0b969":{"nodeId":"resource:f3b8606d-0af5-46cd-bad3-699536a0b969","evidenceList":[{"nodeId":"resource:f3b8606d-0af5-46cd-bad3-699536a0b969","stateLikelihoods":[{"state":"True","likelihood":1},{"state":"False","likelihood":0}]}]}}}}}'
# bayesian_model_from = json.load(open('resources/test2_bayesian_model.json'))
# evidence_from = json.load(open('resources/test2_evidence.json'))
# results = compute(bayesian_model_from, evidence_from)
# print("=======================================================================")

#
# print("=======================================================================")
# print("TEST 3: A -> B without Evidence")
# bayesian_model = '{"bayesian_network":{"node_map":{"resource:f3b8606d-0af5-46cd-bad3-699536a0b969":{"id":"resource:f3b8606d-0af5-46cd-bad3-699536a0b969","cpt":{"table":{"":[0.55,0.45]}},"parentOrderList":[]}, "resource:4275dae1-12d4-4f07-8aa5-3599b1ade29b":{"id":"resource:4275dae1-12d4-4f07-8aa5-3599b1ade29b","cpt":{"table":{"0":[0.8,0.2], "1":[0.1,0.9]}},"parentOrderList":["resource:f3b8606d-0af5-46cd-bad3-699536a0b969"]}}}}'
# evidence = '{}'
# bayesian_model_from = json.loads(bayesian_model)
# evidence_from = json.loads(evidence)
# results = compute(bayesian_model_from, evidence_from)
# print("=======================================================================")
# print("TEST 4: A -> B with Evidence")
# bayesian_model = '{"bayesian_network":{"node_map":{"resource:f3b8606d-0af5-46cd-bad3-699536a0b969":{"id":"resource:f3b8606d-0af5-46cd-bad3-699536a0b969","cpt":{"table":{"":[0.55,0.45]}},"parentOrderList":[]}, "resource:4275dae1-12d4-4f07-8aa5-3599b1ade29b":{"id":"resource:4275dae1-12d4-4f07-8aa5-3599b1ade29b","cpt":{"table":{"0":[0.8,0.2], "1":[0.1,0.9]}},"parentOrderList":["resource:f3b8606d-0af5-46cd-bad3-699536a0b969"]}}}}'
# evidence = '{"modelEvidenceMap":{"MODEL_ID":{"nodeEvidenceMap":{"resource:f3b8606d-0af5-46cd-bad3-699536a0b969":{"nodeId":"resource:f3b8606d-0af5-46cd-bad3-699536a0b969","evidenceList":[{"nodeId":"resource:f3b8606d-0af5-46cd-bad3-699536a0b969","stateLikelihoods":[{"state":"True","likelihood":1},{"state":"False","likelihood":0}]}]}}}}}'
# bayesian_model_from = json.loads(bayesian_model)
# evidence_from = json.loads(evidence)
# results = compute(bayesian_model_from, evidence_from)
# print("=======================================================================")
# # print("TEST 5: A -> B -> C with Evidence A")
# # bayesian_model = '{"id":"resource:4275dae1-12d4-4f07-8aa5-3599b1ade29b","revision_number":0,"directed_graph":{"id":"resource:4275dae1-12d4-4f07-8aa5-3599b1ade29b","edge_list":[{"id":"resource:25e8b5c8-ea86-4bae-830c-53405de5212f","source_id":"resource:f3b8606d-0af5-46cd-bad3-699536a0b969","destination_id":"resource:d96a869b-acf6-4e1d-b700-3e7b23b4180c","meta_data":{"id":"resource:25e8b5c8-ea86-4bae-830c-53405de5212f","name":"resource:25e8b5c8-ea86-4bae-830c-53405de5212f","description":"No description","created_by":"resource:836f3fd1-b565-4785-b5d2-59d6d47fa3cb","created_date":"2018-11-15T13:06:25.883+0000","changed_by":"resource:836f3fd1-b565-4785-b5d2-59d6d47fa3cb","changed_date":"2018-11-15T13:06:25.883+0000","comment":"No comment","json_metadata":"{}","securityLabel":null,"countryCode":null}},{"id":"resource:77e79268-f8f2-4e10-a543-38b5fcacdbd8","source_id":"resource:4275dae1-12d4-4f07-8aa5-3599b1ade29b","destination_id":"resource:f3b8606d-0af5-46cd-bad3-699536a0b969","meta_data":{"id":"resource:77e79268-f8f2-4e10-a543-38b5fcacdbd8","name":"resource:77e79268-f8f2-4e10-a543-38b5fcacdbd8","description":"No description","created_by":"resource:836f3fd1-b565-4785-b5d2-59d6d47fa3cb","created_date":"2018-11-15T13:05:23.473+0000","changed_by":"resource:836f3fd1-b565-4785-b5d2-59d6d47fa3cb","changed_date":"2018-11-15T13:05:23.473+0000","comment":"No comment","json_metadata":"{}","securityLabel":null,"countryCode":null}},{"id":"38cbf507-82a9-4163-8c89-e14df13ba100","source_id":"resource:f3b8606d-0af5-46cd-bad3-699536a0b969","destination_id":"resource:d96a869b-acf6-4e1d-b700-3e7b23b4180c","meta_data":{"id":"38cbf507-82a9-4163-8c89-e14df13ba100","name":"38cbf507-82a9-4163-8c89-e14df13ba100","description":"No description","created_by":null,"created_date":"2019-02-01T21:46:45.922+0000","changed_by":"resource:836f3fd1-b565-4785-b5d2-59d6d47fa3cb","changed_date":"2018-11-15T18:56:07.601+0000","comment":"No comment","json_metadata":"{}","securityLabel":null,"countryCode":null}}],"node_list":[{"id":"resource:f3b8606d-0af5-46cd-bad3-699536a0b969","meta_data":{"id":"resource:f3b8606d-0af5-46cd-bad3-699536a0b969","name":"(U)Default","description":null,"created_by":"resource:836f3fd1-b565-4785-b5d2-59d6d47fa3cb","created_date":"2018-11-15T13:05:17.620+0000","changed_by":"resource:836f3fd1-b565-4785-b5d2-59d6d47fa3cb","changed_date":"2018-11-15T18:55:27.704+0000","comment":"No comment","json_metadata":"{}","securityLabel":"U","countryCode":null}},{"id":"resource:d96a869b-acf6-4e1d-b700-3e7b23b4180c","meta_data":{"id":"resource:d96a869b-acf6-4e1d-b700-3e7b23b4180c","name":"default","description":"No description","created_by":null,"created_date":"2019-02-01T21:46:45.922+0000","changed_by":"resource:836f3fd1-b565-4785-b5d2-59d6d47fa3cb","changed_date":"2018-11-15T18:56:07.601+0000","comment":"No comment","json_metadata":"{}","securityLabel":null,"countryCode":null}},{"id":"resource:4275dae1-12d4-4f07-8aa5-3599b1ade29b","meta_data":{"id":"resource:4275dae1-12d4-4f07-8aa5-3599b1ade29b","name":"(U) CompEvidTest","description":null,"created_by":"resource:836f3fd1-b565-4785-b5d2-59d6d47fa3cb","created_date":"2018-11-15T13:05:17.620+0000","changed_by":"resource:836f3fd1-b565-4785-b5d2-59d6d47fa3cb","changed_date":"2018-11-15T13:05:23.506+0000","comment":"No comment","json_metadata":"{}","securityLabel":"U","countryCode":[]}}],"meta_data":{"id":"resource:4275dae1-12d4-4f07-8aa5-3599b1ade29b","name":null,"description":null,"created_by":null,"created_date":null,"changed_by":null,"changed_date":null,"comment":"No comment","json_metadata":"{}","securityLabel":null,"countryCode":null}},"bayesian_network":{"id":"resource:4275dae1-12d4-4f07-8aa5-3599b1ade29b","node_map":{"resource:f3b8606d-0af5-46cd-bad3-699536a0b969":{"id":"resource:f3b8606d-0af5-46cd-bad3-699536a0b969","stateNames":["False","True"],"nodeType":"COMPONENT","cpt":{"table":{"0":[0.55,0.45],"1":[0.25,0.75]},"sigma":[0.05,0.05]},"parentOrderList":["resource:4275dae1-12d4-4f07-8aa5-3599b1ade29b"],"metaData":{"id":"resource:f3b8606d-0af5-46cd-bad3-699536a0b969","name":"(U)Default","description":null,"created_by":"resource:836f3fd1-b565-4785-b5d2-59d6d47fa3cb","created_date":"2018-11-15T13:05:17.620+0000","changed_by":"resource:836f3fd1-b565-4785-b5d2-59d6d47fa3cb","changed_date":"2018-11-15T18:55:27.704+0000","comment":"No comment","json_metadata":"{}","securityLabel":"U","countryCode":null},"informationDecay":null,"harmLevelTrue":1.0,"harmLevelFalse":1.0,"confidence":-1.0,"nipfPriority":0.0,"supplierConfidence":-1.7976931348623157E308,"supplierError":-1.7976931348623157E308},"resource:d96a869b-acf6-4e1d-b700-3e7b23b4180c":{"id":"resource:d96a869b-acf6-4e1d-b700-3e7b23b4180c","stateNames":["False","True"],"nodeType":"INDICATOR","cpt":{"table":{"0":[0.75,0.25],"1":[0.05,0.95]},"sigma":[0.05,0.05]},"parentOrderList":["resource:f3b8606d-0af5-46cd-bad3-699536a0b969"],"metaData":{"id":"resource:d96a869b-acf6-4e1d-b700-3e7b23b4180c","name":"default","description":"No description","created_by":null,"created_date":"2019-02-01T21:46:45.922+0000","changed_by":"resource:836f3fd1-b565-4785-b5d2-59d6d47fa3cb","changed_date":"2018-11-15T18:56:07.601+0000","comment":"No comment","json_metadata":"{}","securityLabel":null,"countryCode":null},"informationDecay":null,"harmLevelTrue":1.0,"harmLevelFalse":1.0,"confidence":-1.0,"nipfPriority":0.0,"supplierConfidence":-1.7976931348623157E308,"supplierError":-1.7976931348623157E308},"resource:4275dae1-12d4-4f07-8aa5-3599b1ade29b":{"id":"resource:4275dae1-12d4-4f07-8aa5-3599b1ade29b","stateNames":["False","True"],"nodeType":"MODEL","cpt":{"table":{"":[0.5,0.5]},"sigma":[0.05]},"parentOrderList":[],"metaData":{"id":"resource:4275dae1-12d4-4f07-8aa5-3599b1ade29b","name":"(U) CompEvidTest","description":null,"created_by":"resource:836f3fd1-b565-4785-b5d2-59d6d47fa3cb","created_date":"2018-11-15T13:05:17.620+0000","changed_by":"resource:836f3fd1-b565-4785-b5d2-59d6d47fa3cb","changed_date":"2018-11-15T13:05:23.506+0000","comment":"No comment","json_metadata":"{}","securityLabel":"U","countryCode":[]},"informationDecay":null,"harmLevelTrue":1.0,"harmLevelFalse":1.0,"confidence":-1.0,"nipfPriority":0.0,"supplierConfidence":-1.7976931348623157E308,"supplierError":-1.7976931348623157E308}},"meta_data":null,"rootNodeId":"resource:4275dae1-12d4-4f07-8aa5-3599b1ade29b"},"activated_by":null,"activated_on":null,"activation_status":null,"security_label":null,"notifications":false,"name":null,"description":null,"created_by":null,"created_on":null,"modified_by":null,"modified_on":null}'
# # evidence = '{"modelEvidenceMap":{"resource:9d573369-5636-4bae-9881-461a1afe043a":{"nodeEvidenceMap":{"resource:4275dae1-12d4-4f07-8aa5-3599b1ade29b":{"nodeId":"resource:4275dae1-12d4-4f07-8aa5-3599b1ade29b","evidenceList":[{"source":{"dataId":"resource:4275dae1-12d4-4f07-8aa5-3599b1ade29b","systemId":"Manual"},"nodeId":"resource:4275dae1-12d4-4f07-8aa5-3599b1ade29b","modelId":"resource:9d573369-5636-4bae-9881-461a1afe043a","evidenceElementModelVersions":[{"modelVersion":0}],"stateLikelihoods":[{"state":"True","likelihood":1},{"state":"False","likelihood":0}],"timeObserved":"2019-01-16T19:50:51.212Z","informationDecay":null}]}},"modelId":"resource:9d573369-5636-4bae-9881-461a1afe043a"}}}'
# # bayesian_model_from = json.loads(bayesian_model)
# # evidence_from = json.loads(evidence)
# # results = compute(bayesian_model_from, evidence_from)
# # print("=======================================================================")
# # print("TEST 6: A -> B -> C without Evidence")
# # bayesian_model = '{"id":"resource:4275dae1-12d4-4f07-8aa5-3599b1ade29b","revision_number":0,"directed_graph":{"id":"resource:4275dae1-12d4-4f07-8aa5-3599b1ade29b","edge_list":[{"id":"resource:25e8b5c8-ea86-4bae-830c-53405de5212f","source_id":"resource:f3b8606d-0af5-46cd-bad3-699536a0b969","destination_id":"resource:d96a869b-acf6-4e1d-b700-3e7b23b4180c","meta_data":{"id":"resource:25e8b5c8-ea86-4bae-830c-53405de5212f","name":"resource:25e8b5c8-ea86-4bae-830c-53405de5212f","description":"No description","created_by":"resource:836f3fd1-b565-4785-b5d2-59d6d47fa3cb","created_date":"2018-11-15T13:06:25.883+0000","changed_by":"resource:836f3fd1-b565-4785-b5d2-59d6d47fa3cb","changed_date":"2018-11-15T13:06:25.883+0000","comment":"No comment","json_metadata":"{}","securityLabel":null,"countryCode":null}},{"id":"resource:77e79268-f8f2-4e10-a543-38b5fcacdbd8","source_id":"resource:4275dae1-12d4-4f07-8aa5-3599b1ade29b","destination_id":"resource:f3b8606d-0af5-46cd-bad3-699536a0b969","meta_data":{"id":"resource:77e79268-f8f2-4e10-a543-38b5fcacdbd8","name":"resource:77e79268-f8f2-4e10-a543-38b5fcacdbd8","description":"No description","created_by":"resource:836f3fd1-b565-4785-b5d2-59d6d47fa3cb","created_date":"2018-11-15T13:05:23.473+0000","changed_by":"resource:836f3fd1-b565-4785-b5d2-59d6d47fa3cb","changed_date":"2018-11-15T13:05:23.473+0000","comment":"No comment","json_metadata":"{}","securityLabel":null,"countryCode":null}},{"id":"38cbf507-82a9-4163-8c89-e14df13ba100","source_id":"resource:f3b8606d-0af5-46cd-bad3-699536a0b969","destination_id":"resource:d96a869b-acf6-4e1d-b700-3e7b23b4180c","meta_data":{"id":"38cbf507-82a9-4163-8c89-e14df13ba100","name":"38cbf507-82a9-4163-8c89-e14df13ba100","description":"No description","created_by":null,"created_date":"2019-02-01T21:46:45.922+0000","changed_by":"resource:836f3fd1-b565-4785-b5d2-59d6d47fa3cb","changed_date":"2018-11-15T18:56:07.601+0000","comment":"No comment","json_metadata":"{}","securityLabel":null,"countryCode":null}}],"node_list":[{"id":"resource:f3b8606d-0af5-46cd-bad3-699536a0b969","meta_data":{"id":"resource:f3b8606d-0af5-46cd-bad3-699536a0b969","name":"(U)Default","description":null,"created_by":"resource:836f3fd1-b565-4785-b5d2-59d6d47fa3cb","created_date":"2018-11-15T13:05:17.620+0000","changed_by":"resource:836f3fd1-b565-4785-b5d2-59d6d47fa3cb","changed_date":"2018-11-15T18:55:27.704+0000","comment":"No comment","json_metadata":"{}","securityLabel":"U","countryCode":null}},{"id":"resource:d96a869b-acf6-4e1d-b700-3e7b23b4180c","meta_data":{"id":"resource:d96a869b-acf6-4e1d-b700-3e7b23b4180c","name":"default","description":"No description","created_by":null,"created_date":"2019-02-01T21:46:45.922+0000","changed_by":"resource:836f3fd1-b565-4785-b5d2-59d6d47fa3cb","changed_date":"2018-11-15T18:56:07.601+0000","comment":"No comment","json_metadata":"{}","securityLabel":null,"countryCode":null}},{"id":"resource:4275dae1-12d4-4f07-8aa5-3599b1ade29b","meta_data":{"id":"resource:4275dae1-12d4-4f07-8aa5-3599b1ade29b","name":"(U) CompEvidTest","description":null,"created_by":"resource:836f3fd1-b565-4785-b5d2-59d6d47fa3cb","created_date":"2018-11-15T13:05:17.620+0000","changed_by":"resource:836f3fd1-b565-4785-b5d2-59d6d47fa3cb","changed_date":"2018-11-15T13:05:23.506+0000","comment":"No comment","json_metadata":"{}","securityLabel":"U","countryCode":[]}}],"meta_data":{"id":"resource:4275dae1-12d4-4f07-8aa5-3599b1ade29b","name":null,"description":null,"created_by":null,"created_date":null,"changed_by":null,"changed_date":null,"comment":"No comment","json_metadata":"{}","securityLabel":null,"countryCode":null}},"bayesian_network":{"id":"resource:4275dae1-12d4-4f07-8aa5-3599b1ade29b","node_map":{"resource:f3b8606d-0af5-46cd-bad3-699536a0b969":{"id":"resource:f3b8606d-0af5-46cd-bad3-699536a0b969","stateNames":["False","True"],"nodeType":"COMPONENT","cpt":{"table":{"0":[0.55,0.45],"1":[0.25,0.75]},"sigma":[0.05,0.05]},"parentOrderList":["resource:4275dae1-12d4-4f07-8aa5-3599b1ade29b"],"metaData":{"id":"resource:f3b8606d-0af5-46cd-bad3-699536a0b969","name":"(U)Default","description":null,"created_by":"resource:836f3fd1-b565-4785-b5d2-59d6d47fa3cb","created_date":"2018-11-15T13:05:17.620+0000","changed_by":"resource:836f3fd1-b565-4785-b5d2-59d6d47fa3cb","changed_date":"2018-11-15T18:55:27.704+0000","comment":"No comment","json_metadata":"{}","securityLabel":"U","countryCode":null},"informationDecay":null,"harmLevelTrue":1.0,"harmLevelFalse":1.0,"confidence":-1.0,"nipfPriority":0.0,"supplierConfidence":-1.7976931348623157E308,"supplierError":-1.7976931348623157E308},"resource:d96a869b-acf6-4e1d-b700-3e7b23b4180c":{"id":"resource:d96a869b-acf6-4e1d-b700-3e7b23b4180c","stateNames":["False","True"],"nodeType":"INDICATOR","cpt":{"table":{"0":[0.75,0.25],"1":[0.05,0.95]},"sigma":[0.05,0.05]},"parentOrderList":["resource:f3b8606d-0af5-46cd-bad3-699536a0b969"],"metaData":{"id":"resource:d96a869b-acf6-4e1d-b700-3e7b23b4180c","name":"default","description":"No description","created_by":null,"created_date":"2019-02-01T21:46:45.922+0000","changed_by":"resource:836f3fd1-b565-4785-b5d2-59d6d47fa3cb","changed_date":"2018-11-15T18:56:07.601+0000","comment":"No comment","json_metadata":"{}","securityLabel":null,"countryCode":null},"informationDecay":null,"harmLevelTrue":1.0,"harmLevelFalse":1.0,"confidence":-1.0,"nipfPriority":0.0,"supplierConfidence":-1.7976931348623157E308,"supplierError":-1.7976931348623157E308},"resource:4275dae1-12d4-4f07-8aa5-3599b1ade29b":{"id":"resource:4275dae1-12d4-4f07-8aa5-3599b1ade29b","stateNames":["False","True"],"nodeType":"MODEL","cpt":{"table":{"":[0.5,0.5]},"sigma":[0.05]},"parentOrderList":[],"metaData":{"id":"resource:4275dae1-12d4-4f07-8aa5-3599b1ade29b","name":"(U) CompEvidTest","description":null,"created_by":"resource:836f3fd1-b565-4785-b5d2-59d6d47fa3cb","created_date":"2018-11-15T13:05:17.620+0000","changed_by":"resource:836f3fd1-b565-4785-b5d2-59d6d47fa3cb","changed_date":"2018-11-15T13:05:23.506+0000","comment":"No comment","json_metadata":"{}","securityLabel":"U","countryCode":[]},"informationDecay":null,"harmLevelTrue":1.0,"harmLevelFalse":1.0,"confidence":-1.0,"nipfPriority":0.0,"supplierConfidence":-1.7976931348623157E308,"supplierError":-1.7976931348623157E308}},"meta_data":null,"rootNodeId":"resource:4275dae1-12d4-4f07-8aa5-3599b1ade29b"},"activated_by":null,"activated_on":null,"activation_status":null,"security_label":null,"notifications":false,"name":null,"description":null,"created_by":null,"created_on":null,"modified_by":null,"modified_on":null}'
# # evidence = '{}'
# # bayesian_model_from = json.loads(bayesian_model)
# # evidence_from = json.loads(evidence)
# # results = compute(bayesian_model_from, evidence_from)
# # print("=======================================================================")

print("=======================================================================")
print("TEST 7: A with multi state evidence")
# bayesian_model = '{"bayesian_network":{"node_map":{"resource:f3b8606d-0af5-46cd-bad3-699536a0b969":{"id":"resource:f3b8606d-0af5-46cd-bad3-699536a0b969","cpt":{"table":{"":[0.55,0.45]}},"parentOrderList":[]}}}}'
# evidence = '{"modelEvidenceMap":{"MODEL_ID":{"nodeEvidenceMap":{"resource:f3b8606d-0af5-46cd-bad3-699536a0b969":{"nodeId":"resource:f3b8606d-0af5-46cd-bad3-699536a0b969","evidenceList":[{"nodeId":"resource:f3b8606d-0af5-46cd-bad3-699536a0b969","stateLikelihoods":[{"state":"True","likelihood":1},{"state":"False","likelihood":0}]}]}}}}}'
bayesian_model_from = json.load(open('resources/multistate_evidence_model.json'))
evidence_from = json.load(open('resources/multistate_evidence.json'))
results = compute(bayesian_model_from, evidence_from)
print("=======================================================================")
