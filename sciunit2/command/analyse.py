from __future__ import absolute_import

from sciunit2.command import AbstractCommand
from sciunit2.command.context import CheckoutContext
from sciunit2.exceptions import CommandLineError
from sciunit2.util import quoted_format
import sciunit2.core
import pydot
import networkx as nx
from getopt import getopt
import sys
import os


class AnalyseCommand(AbstractCommand):
    name = 'analyse'

    @property
    def usage(self):
        return [('Analyse <dag>',
                 "Analyse dag")]

    def run(self, args):
        optlist, args = getopt(args, '')
        if len(args) != 1:
            raise CommandLineError
        file_path = args[0]
        if not os.path.exists(file_path):
            print("File not found")
            raise CommandLineError
        
        # assuming dag file is provided
        G = nx.DiGraph(nx.nx_pydot.read_dot(file_path))
        
        # for node, data in G.nodes(data=True):
        #     print(f"Node: {node}, Data: {data}")
        
        idx = 1
        for generation in nx.topological_generations(G):
            print("Step", idx)
            for node in generation: 
                print(G.nodes[node].get('label', node))
            idx += 1

        
