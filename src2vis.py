#!/usr/bin/env python
import sys
import networkx as nx
from re import match
from os import getcwd, remove
from os.path import basename, isfile

def create_graph(syms):
    graph = nx.Graph()

    for key1 in syms.keys():
        graph.add_node(key1)
        for key2 in syms[key1].keys():
            graph.add_node(key2)
            graph.add_edge(key1, key2)
    
    # Add Cross references
    for key1 in syms.keys():
        for key2 in syms[key1].keys():
            for xref in syms[key1][key2]:
                graph.add_edge(key2, xref)
    
    return graph

def create_symbol_table(input_file):
    syms = {}
    db = { 'file':'', 'func':'', 'xref':'' }

    def cscope_line_parser(item, regex):
        def parser(line):
            m = match(regex, line)
            if m: return item, m.groups()[0]
        return parser

    def insert(db):
        key1 = db['file']
        if not key1: return
        if not syms.has_key(key1): syms[key1] = {}
        
        key2 = db['func']
        if not key2: return
        if not syms[key1].has_key(key2): syms[key1][key2] = set([])

        key3 = db['xref']
        if not key3: return
        if not key3 in syms[key1][key2]: syms[key1][key2].add(key3)
    
    parsers = [cscope_line_parser('file', '\s@(.*)'),
               cscope_line_parser('func', '\s\$(.*)'),
               cscope_line_parser('xref', '\s\`(.*)')]

    with open(input_file) as f:
        sym = None

        # First iteration to generate source symbols
        for line in f:
            parser = filter(lambda x: x(line), parsers)
            if parser:
                func = parser[0]
                key, val = func(line)
                db[key] = val
                insert(db)
                #graph.add_node(db['func'], packet=db['file'])
                # Remove inserted entry
        #             graph.add_edge(xref, fnc)
    return syms
    
if __name__ == '__main__':
    cscope_file = sys.argv[1]
    symbols = create_symbol_table(cscope_file)
    graph = create_graph(symbols)
    output = basename(getcwd()) + '.gml'
    if isfile(output):
        remove(output)
    nx.write_gml(graph, output)
