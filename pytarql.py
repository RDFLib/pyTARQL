# -*- coding: utf-8 -*-
"""
Python implementation of TARQL (https://tarql.github.io/)
"""

from collections import OrderedDict
import csv
import argparse
import sys
import re

import rdflib
from rdflib.plugins.sparql import prepareQuery


class SingleCharType:
    """
    Supports single char arguments or special strings translated to single
    char values.
    """

    def __init__(self, description, mappings):
        self._description = description
        self._mappings = mappings

    def __call__(self, value):
        if value in self._mappings:
            return self._mappings[value]
        if isinstance(value, str) and len(value) == 1:
            return value
        raise argparse.ArgumentTypeError(
            "'{}' is not a valid {} - not a single character or one of {}".format(
                value, self._description, str(list(self._mappings.keys()))))


class NoHeaderReader:
    """Automatically assigns field names ?a, ?b, ?c, ... to row values."""

    def __init__(self, f, dialect="excel", *args, **kwds):
        self._fieldnames = []   # list of keys for the dict
        self.reader = csv.reader(f, dialect, *args, **kwds)
        self.dialect = dialect
        self.line_num = 0

    def __iter__(self):
        return self

    @staticmethod
    def _toletters(num):
        letters = ''
        while num > 26:
            div, mod = divmod(num, 26)
            letters = chr(ord('a') + mod) + letters
            num = int(div)

        return chr(ord('a') + num) + letters

    def fieldnames(self, length):
        """Return headers for given row length, generating as needed."""
        for add in range(len(self._fieldnames), length):
            self._fieldnames.append(self._toletters(add))
        return self._fieldnames[:length]

    def __next__(self):
        row = next(self.reader)

        # unlike the basic reader, we prefer not to return blanks,
        # because we will typically wind up with a dict full of None
        # values
        while row == []:
            row = next(self.reader)
        self.line_num = self.reader.line_num
        return OrderedDict(zip(self.fieldnames(len(row)), row))


class PyTarql:
    """Transform CSV to RDF."""

    def __init__(self):
        """Initialize transform."""
        # Used to translate invalid characters in column headers
        self._cached_headers = None
        self._reader = None
        self._namespaces_printed = False
        self._args = None
        self._graph = None

    def var_mapping(self, row):
        if isinstance(self._reader, NoHeaderReader):
            return dict(zip(row.keys(), row.keys()))

        invalid_pattern = re.compile(r'[^\w_]+')
        return dict((k, invalid_pattern.sub('_', k)) for k in row)

    def create_reader(self):
        delimiter = '\t' if self._args.tab else self._args.delimiter
        if self._args.no_header_row:
            self._reader = NoHeaderReader(self._args.input,
                                          delimiter=delimiter,
                                          escapechar=self._args.escapechar,
                                          quotechar=self._args.quotechar)
        else:
            self._reader = csv.DictReader(self._args.input,
                                          delimiter=delimiter,
                                          escapechar=self._args.escapechar,
                                          quotechar=self._args.quotechar)

    def bindings(self):
        for row in self._reader:
            if self._cached_headers is None:
                self._cached_headers = self.var_mapping(row)
            yield dict((self._cached_headers[k], rdflib.Literal(row[k])) for k in row)

    @staticmethod
    def parse_args(arguments):
        """Command line arguments."""
        parser = argparse.ArgumentParser(description="pytarql CSV to RDF converter")
        sep_group = parser.add_mutually_exclusive_group()
        sep_group.add_argument('-d', '--delimiter', action='store', default=',',
                               type=SingleCharType('delimiter', {
                                   'comma': ',',
                                   'tab': '\t'
                               }),
                               help='Delimiting character of the input file')
        sep_group.add_argument('-t', '--tab', action='store_true',
                               help='Input is tab-separated (TSV)')

        parser.add_argument('-p', '--escapechar', action='store', default='\\',
                            type=SingleCharType('escape char', {
                                'backslash': "\\",
                                'none': None
                            }),
                            help='Escape character of the input file')
        parser.add_argument('--quotechar', action='store', default='"',
                            type=SingleCharType('quote char', {
                                'singlequote': "'",
                                'doublequote': '"',
                                'none': None
                            }),
                            help='Quote character of the input file')

        parser.add_argument('--dedup', type=int, action="store",
                            help="Window size in which to remove duplicate triples")
        parser.add_argument('--ntriples', action="store_const", dest='output_format',
                            const='nt', default='turtle',
                            help="Emit N-Triples (default is turtle)")
        parser.add_argument('-H', '--no-header-row', action='store_true',
                            help='Input file has no header row; '
                            'use variable names ?a, ?b, ...')

        parser.add_argument('query', type=argparse.FileType('r'),
                            help='File containing a SPARQL query to be '
                            'applied to an input file')
        parser.add_argument('input', type=argparse.FileType('r'), nargs='?',
                            default=sys.stdin,
                            help="CSV to be processed, omit to use STDIN")

        return parser.parse_args(args=arguments)

    def emit(self, output, trips):
        for triple in trips:
            self._graph.add(triple)
        serialized = self._graph.serialize(
            format=self._args.output_format).decode('utf-8')
        # When writing turtle, only emit the namespaces first time
        if self._namespaces_printed and self._args.output_format == 'turtle':
            serialized = serialized.split('\n\n', 1)[1]
        else:
            self._namespaces_printed = True
        output.write(serialized.strip())
        for triple in self._graph.triples((None, None, None)):
            self._graph.remove(triple)

    def transform(self, arguments, output):
        """Transform CSV to RDF."""
        self._args = self.parse_args(arguments)
        self._graph = rdflib.Graph()

        # Pre-parse query
        query = prepareQuery(self._args.query.read())
        # Transfer namespaces from query to graph for serialization
        for prefix, uri in query.prologue.namespace_manager.namespaces():
            self._graph.bind(prefix, uri)

        self._namespaces_printed = False
        trips = []

        self.create_reader()

        for row in self.bindings():
            results = self._graph.query(query, initBindings=row)
            trips.extend(results)

            if not trips:
                continue

            # Dump triples when dedup window is full (or every row if not specified)
            if not self._args.dedup or len(trips) > self._args.dedup:
                self.emit(output, trips)
                trips = []

        # Any left over?
        if trips:
            self.emit(output, trips)

if __name__ == '__main__':
    PyTarql().transform(sys.argv[1:], output=sys.stdout)
