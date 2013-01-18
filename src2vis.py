#!/usr/bin/env python

#
# Author: Sinan Nalkaya <sardok@gmail.com>
# See LICENSE file.
#

import sys
from re import match
from copy import deepcopy
from os import getcwd, remove
from os.path import basename, isfile
import networkx as nx

def create_graph(syms):
    graph = nx.Graph()

    for file in syms.keys():
        graph.add_node(file)
        funcs = syms[file]['defs'].keys()
        print 'funcs of ' + file
        print funcs
        paired = [(file, x) for x in funcs]
        graph.add_edges_from(paired)
        # for func in syms[file]['defs'].keys():
        #     graph.add_node(func)
        #     graph.add_edge(file, func)
    
    # Add Cross references
    # for file in syms.keys():
    #     for func in syms[file]['defs'].keys():
    #         for xref in syms[file]['defs'][func]:
    #             graph.add_edge(func, xref)
    
    return graph

def create_symbol_table(input_file):
    sym_table = {}
    cur_refs = {'index':[], 'func':''}

    def dict_merge(a, b):
        if not isinstance(b, dict):
            return b
        res = deepcopy(a)
        for k,v in b.iteritems():
            if k in res and isinstance(res[k], dict):
                res[k] = dict_merge(res[k], v)
            else:
                res[k] = deepcopy(v)
        return res

    def update(entry, val):
        if isinstance(entry, dict):
            entry.update(val)
        elif isinstance(entry, list):
            entry.append(val)
        elif isinstance(entry, set):
            entry.add(val)
        else:
            entry = val
        
    def deep_update(db, keys, val):
        key = keys[0]
        if keys[1:].__len__() > 0:
            deep_update(db[key], keys[1:], val)
        else:
            update(db[key], val)
            
    def deep_get(db, keys):
        key = keys[0]
        if keys[1:].__len__() > 0:
            return deep_get(db[key], keys[1:])
        else:
            return db[key]
        
    def file_tag_parser(entry):
        entries = entry.split('/')
        entries = filter(lambda x: x != '', entries)
        cur_refs['index'] = deepcopy(entries)
        cur_refs['func'] = ''
        entries.reverse()
        tmp = {}
        for dir in entries:
            tmp = {dir:tmp}
        merged = dict_merge(sym_table, tmp)
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

    validators = [cscope_line_validator('file', '\s@(.*\.[ch])'),
                  cscope_line_validator('func', '\s\$(.*)'),
                  cscope_line_validator('xref', '\s\`(.*)')]

    parsers = {'file':file_tag_parser,
               'func':func_tag_parser,
               'xref':xref_tag_parser}
    
    with open(input_file) as f:
        for line in f:
            valids = filter(lambda x: x(line), validators)
            if valids:
                validator = valids[0]
                key, entry = validator(line)
                parsers[key](entry)
    print sym_table
    return sym_table
    
if __name__ == '__main__':
    cscope_file = sys.argv[1]
    symbols = create_symbol_table(cscope_file)
    #graph = create_graph(symbols)
    # output = basename(getcwd()) + '.gml'
    # if isfile(output):
    #     remove(output)
    # nx.write_gml(graph, output)
