#!/usr/bin/env python
'''
Author: Sinan Nalkaya <sardok@gmail.com>
See LICENSE file.
'''

import sys
from re import match
from copy import deepcopy
from os import getcwd, remove
from os.path import basename, isfile
import networkx as nx
import matplotlib.pyplot as plt

def draw_graph(graph):
    nodedata = [(v['weight'], {n:v['label']}) for (n,v) in graph.nodes(data=True)]
    nodelabels={}
    nodeweights=[]
    for weight, label in nodedata:
        nodeweights.append(weight)
        nodelabels.update(label)
    # maxweight = max(nodeweights)
    # minweight = min(nodeweights)
    # ratio = maxweight/minweight
    # nodeweights = map(lambda x: x/ratio, nodeweights)
    #pos = nx.random_layout(graph)
    pos = nx.fruchterman_reingold_layout(graph)
    nx.draw_networkx_nodes(graph, pos, node_size=nodeweights, node_color='w', alpha=0.4)
    nx.draw_networkx_labels(graph, pos, nodelabels)
    nx.draw_networkx_edges(graph, pos)
    output = basename(getcwd()) + '.gml'
    if isfile(output):
        remove(output)
    nx.write_gml(graph, output)
    plt.show() # display

    
def create_graph(syms_table):
    graph = nx.DiGraph()

    def find_by_func(entry, func, parent=None):
        if not isinstance(entry, dict):
            return
        if entry.has_key(func):
            return parent
        for item in entry:
            ret = find_by_func(entry[item], func, item)
            if ret: return ret
        
    def create_edge(entry, parent=None):
        for key in entry:
            if graph.has_node(key):
                # It is a graph node rather than function
                create_edge(entry[key], key)
            else:
                # The key may not be an iterable
                # for example 'weight'
                try:
                    # this key is a function definition
                    for xref in entry[key]:
                        to = find_by_func(syms_table, xref)
                        if parent and to and graph.has_node(to) \
                                and parent != to:
                            if graph.has_edge(parent, to):
                                graph[parent][to]['weight'] += 1
                            else:
                                graph.add_edge(parent, to, {'weight':1})
                except TypeError:
                    pass
                
    def create_node(entry, parent=None):
        for key in entry:
            if key == 'weight':
                continue
            if not (isinstance(entry[key], dict) and \
                        entry[key].has_key('weight')):
                continue
            graph.add_node(key, {\
                    'weight':entry[key]['weight'],\
                        'label':'%s:%d' % (key,entry[key]['weight'])})
            #if parent:
            #    graph.add_edge(parent, key)
            create_node(entry[key], key)
            
    create_node(syms_table)
    create_edge(syms_table)
    return graph

def create_symbol_table(input_file):
    sym_table = {}
    cur_refs = {'index':[], 'func':''}

    def dict_merge(a, b, update_existing=True):
        if not isinstance(b, dict):
            return b
        res = deepcopy(a)
        for k,v in b.iteritems():
            if k in res:
                if isinstance(res[k], dict):
                    res[k] = dict_merge(res[k], v, update_existing)
                elif update_existing == True:
                    res[k] = deepcopy(v)
            else:
                res[k] = deepcopy(v)
        return res
    
    def update(db, key, val):
        if isinstance(db[key], dict):
            db[key].update(val)
        elif isinstance(db[key], list):
            db[key].append(val)
        elif isinstance(db[key], set):
            db[key].add(val)
        else:
            db[key] = val
        
    def deep_update(db, keys, val):
        key = keys[0]
        if keys[1:].__len__() > 0:
            deep_update(db[key], keys[1:], val)
        else:
            update(db, key, val)
            
    def deep_get(db, keys):
        key = keys[0]
        if keys[1:].__len__() > 0:
            return deep_get(db[key], keys[1:])
        else:
            return db[key]
            
    def add_weight(db):
        db.update(dict_merge(db, {'weight':0}))
        
    def file_tag_parser(entry):
        # entries = entry.split('/')
        # entries = filter(lambda x: x != '', entries)
        # cur_refs['index'] = deepcopy(entries)
        # cur_refs['func'] = ''
        # entries.reverse()
        entries = [entry]
        cur_refs['index'] = deepcopy(entries)
        cur_refs['func'] = ''
        
        tmp = {}
        for dir in entries:
            add_weight(tmp)
            tmp = {dir:tmp}
        merged = dict_merge(sym_table, tmp, False)
        sym_table.update(merged)
        
    def func_tag_parser(entry):
        if not cur_refs['index']:
            return
        deep_update(sym_table, cur_refs['index'], {entry:set([])})
        cur_refs['func'] = entry

    def xref_tag_parser(entry):
        if not (cur_refs['index'] and cur_refs['func']):
            return
        index = deepcopy(cur_refs['index'])
        index.append(cur_refs['func'])
        deep_update(sym_table, index, entry)

    def cscope_line_validator(item, regex):
        def parser(line):
            m = match(regex, line)
            if m: return item, m.groups()[0]
        return parser

    # This function is called on every iteration
    # and  increments 'weight' for each of source
    # file.
    def update_weights():
        refs = []
        for ref in cur_refs['index']:
            refs.append(ref)
            weight_ref = refs + ['weight']
            weight = deep_get(sym_table, weight_ref)
            deep_update(sym_table, weight_ref, weight + 1)

    validators = [cscope_line_validator('file', '\s@(.*\.[ch])'),
                  cscope_line_validator('func', '\s\$(.*)'),
                  cscope_line_validator('xref', '\s\`(.*)')]

    parsers = {'file':file_tag_parser,
               'func':func_tag_parser,
               'xref':xref_tag_parser}
    
    with open(input_file) as f:
        weight = 0
        for line in f:
            valids = filter(lambda x: x(line), validators)
            if valids:
                validator = valids[0]
                key, entry = validator(line)
                parsers[key](entry)

            update_weights()
    return sym_table
    
if __name__ == '__main__':
    cscope_file = sys.argv[1]
    symbols = create_symbol_table(cscope_file)
    graph = create_graph(symbols)
    print graph.nodes()
    print graph.edges(data=True)
    draw_graph(graph)
