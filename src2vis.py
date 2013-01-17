#!/usr/bin/env python

#
# Author: Sinan Nalkaya <sardok@gmail.com>
# See LICENSE file.
#

import sys
import networkx as nx
from re import match
from os import getcwd, remove
from os.path import basename, isfile

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
    cscope_line = { 'file':'', 'func':'', 'xref':'' }

    def cscope_line_validator(item, regex):
        def parser(line):
            m = match(regex, line)
            if m: return item, m.groups()[0]
        return parser

    def file_tag_parser(entry):
        for dir in entry.split('\\'):
            sym_table[dir] = {}

    def func_tag_parser(entry):
        return 1

    def xref_tag_parser(entry):
        return 1

    def insert(cscope_line):
        file = cscope_line['file']
        if not file: return
        if not sym_table.has_key(file):
            sym_table[file] = {'lines':0, 'defs':{}}
            return

        sym_table[file]['lines'] += 1
        func = cscope_line['func']
        if not func: return
        if not sym_table[file]['defs'].has_key(func):
            sym_table[file]['defs'][func] = set([])
            return

        xref = cscope_line['xref']
        if not xref: return
        if not xref in sym_table[file]['defs'][func]:
            sym_table[file]['defs'][func].add(xref)

    validators = [cscope_line_validator('file', '\s@(.*\.[ch])'),
                  cscope_line_validator('func', '\s\$(.*)'),
                  cscope_line_validator('xref', '\s\`(.*)')]

    parsers = {'file':file_tag_parser, 'func':func_tag_parser,
               'xref':xref_tag_parser}
    
    with open(input_file) as f:
        sym = None

        # First iteration to generate source symbols
        for line in f:
            parser = filter(lambda x: x(line), parsers)
            if parser:
                func = parser[0]
                key, entry = func(line)
                parsers[key](entry)
                
    return sym_table
    
if __name__ == '__main__':
    cscope_file = sys.argv[1]
    symbols = create_symbol_table(cscope_file)
    graph = create_graph(symbols)
    output = basename(getcwd()) + '.gml'
    if isfile(output):
        remove(output)
    nx.write_gml(graph, output)
