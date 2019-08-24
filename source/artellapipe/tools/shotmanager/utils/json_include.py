#!/usr/bin/env python
# coding: utf-8

import os
import re
import json
from collections import OrderedDict
import argparse


OBJECT_TYPES = (dict, list)

INCLUDE_KEY = '...'

INCLUDE_VALUE_PATTERN = re.compile(r'^<([\w\-\:.\\]+)>$')

_included_cache = {}


def read_file(filepath):
    with open(filepath, 'r') as f:
        return f.read()


def get_include_name(value):
    if isinstance(value, basestring):
        rv = INCLUDE_VALUE_PATTERN.search(value)
        if rv:
            return rv.groups()[0]
    return None


def walk_through_to_include(o, dirpath):
    if isinstance(o, dict):
        is_include_exp = False
        if set(o) == set([INCLUDE_KEY]):
            include_name = get_include_name(o.values()[0])
            if include_name:
                is_include_exp = True
                o.clear()
                if include_name not in _included_cache:
                    _included_cache[include_name] = parse_json_include(dirpath, include_name, True)
                o.update(_included_cache[include_name])

        if is_include_exp:
            return

        for k, v in o.iteritems():
            if isinstance(v, OBJECT_TYPES):
                walk_through_to_include(v, dirpath)
    elif isinstance(o, list):
        for i in o:
            if isinstance(i, OBJECT_TYPES):
                walk_through_to_include(i, dirpath)


def parse_json_include(dirpath, filename, is_include=False):

    if os.path.isfile(filename):
        filepath = filename
        dirpath = os.path.dirname(filepath)
    else:
        filepath = os.path.join(dirpath, filename)

    json_str = read_file(filepath)
    d = json.loads(json_str, object_pairs_hook=OrderedDict)

    if is_include:
        assert isinstance(d, dict),\
            'The JSON file being included should always be a dict rather than a list'

    walk_through_to_include(d, dirpath)

    return d


def build_json_include(dirpath, filename, indent=4):
    """Parse a json file and build it by the include expression recursively.

    :param str dirpath: The directory path of source json files.
    :param str filename: The name of the source json file.
    :return: A json string with its include expression replaced by the indicated data.
    :rtype: str
    """

    d = parse_json_include(dirpath, filename)
    return json.dumps(d, indent=indent, separators=(',', ': '))


def build_json_include_to_files(dirpath, filenames, target_dirpath, indent=4):
    """Build a list of source json files and write the built result into
    target directory path with the same file name they have.

    Since all the included JSON will be cached in the parsing process,
    this function will be a better way to handle multiple files than build each
    file seperately.

    :param str dirpath: The directory path of source json files.
    :param list filenames: A list of source json files.
    :param str target_dirpath: The directory path you want to put built result into.
    :rtype: None
    """
    assert isinstance(filenames, list), '`filenames must be a list`'

    if not os.path.exists(target_dirpath):
        os.makedirs(target_dirpath)

    for i in filenames:
        json = build_json_include(dirpath, i, indent)
        target_filepath = os.path.join(target_dirpath, i)
        with open(target_filepath, 'w') as f:
            f.write(json)


def main():
    parser = argparse.ArgumentParser(description='Command line tool to build JSON file by include syntax.')

    parser.add_argument('dirpath', metavar="DIR", help="The directory path of source json files")
    parser.add_argument('filename', metavar="FILE", help="The name of the source json file")

    args = parser.parse_args()

    print build_json_include(args.dirpath, args.filename)


if __name__ == '__main__':
    main()
