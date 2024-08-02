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
        # assume dot file - valid? or should it be a snakemake and we should create the dot? 
        G = nx.DiGraph(nx.nx_pydot.read_dot(file_path))
        # generations = [sorted(generation) for generation in nx.topological_generations(G)]
        for generation in nx.topological_generations(G):
            generation_with_labels = [(node, G.nodes[node].get('label', node)) for node in sorted(generation)]
            print(generation_with_labels)

        
