#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains utilities functions to work with Shaders
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import json


class MayaParserBase(object):

    def on_requires_maya(self, version):
        pass

    def on_requires_plugin(self, plugin, version):
        pass

    def on_file_info(self, key, value):
        pass

    def on_current_unit(self, angle, linear, time):
        pass

    def on_file_reference(self, path):
        pass

    def on_create_node(self, nodetype, name, parent):
        pass

    def on_select(self, name):
        pass

    def on_add_attr(self, node, name):
        pass

    def on_set_attr(self, name, value, type):
        pass

    def on_set_attr_flags(self, plug, keyable=None, channelbox=None, lock=None):
        pass

    def on_connect_attr(self, src_plug, dst_plug):
        pass


class MayaAsciiError(ValueError):
    pass


class MayaAsciiParserBase(MayaParserBase):
    def __init__(self):
        self.__command_handlers = {
            "requires": self._exec_requires,
            "fileInfo": self._exec_file_info,
            "file": self._exec_file,
            "createNode": self._exec_create_node,
            "setAttr": self._exec_set_attr,
        }

    def on_comment(self, value):
        pass

    def register_handler(self, command, handler):
        self.__command_handlers[command] = handler

    def exec_command(self, command, args):
        handler = self.__command_handlers.get(command, None)
        if handler is not None:
            handler(args)

    def has_command(self, command):
        return command in self.__command_handlers

    def _exec_requires(self, args):
        if args[0] == "maya":
            self.on_requires_maya(args[1])
        else:
            self.on_requires_plugin(args[0], args[1])

    def _exec_file_info(self, args):
        self.on_file_info(args[0], args[1])

    def _exec_file(self, args):
        reference = False
        reference_depth_info = None
        namespace = None
        defer_reference = False
        reference_node = None

        argptr = 0
        while argptr < len(args):
            arg = args[argptr]
            if arg in ("-r", "--reference"):
                reference = True
                argptr += 1
            elif arg in ("-rdi", "--referenceDepthInfo"):
                reference_depth_info = int(args[argptr + 1])
                argptr += 2
            elif arg in ("-ns", "--namespace"):
                namespace = args[argptr + 1]
                argptr += 2
            elif arg in ("-dr", "--deferReference"):
                defer_reference = bool(int(args[argptr + 1]))
                argptr += 2
            elif arg in ("-rfn", "--referenceNode"):
                reference_node = args[argptr + 1]
                argptr += 2
            elif arg in ('-op'):
                argptr += 2
            elif arg in ('-typ', '--type'):
                argptr += 2
            else:
                break

        if argptr < len(args):
            path = args[argptr]
            self.on_file_reference(path)

    def _exec_create_node(self, args):
        nodetype = args[0]

        name = None
        parent = None

        argptr = 1
        while argptr < len(args):
            arg = args[argptr]
            if arg in ("-n", "--name"):
                name = args[argptr + 1]
                argptr += 2
            elif arg in ("-p", "--parent"):
                parent = args[argptr + 1]
                argptr += 2
            elif arg in ("-s", "--shared"):
                argptr += 1
            else:
                raise MayaAsciiError("Unexpected argument: %s" % arg)

        self.on_create_node(nodetype, name, parent)

    def _exec_set_attr(self, args):
        name = args.pop(0)[1:]
        attrtype = None
        value = None

        argptr = 1
        while argptr < len(args):
            arg = args[argptr]
            if arg in ("-type", "--type"):
                attrtype = args[argptr + 1]
                value = args[argptr + 2:]
                argptr += 2
            else:
                # FIXME this is a catch-all; explicitly support flags
                argptr += 1

        if not value:
            value = args[-1]

        if not attrtype:
            # Implicitly convert between Python types
            # FIXME this isn't particularly safe?
            types = {
                str: "string",
                float: "double",
                int: "integer"
            }

            try:
                attrtype = types[type(json.loads(value))]

            except KeyError:
                attrtype = "string"

            except ValueError:
                attrtype = types.get(type(value), "string")

        self.on_set_attr(name, value, attrtype)


class MayaAsciiParser(MayaAsciiParserBase):

    def __init__(self, stream):
        super(MayaAsciiParser, self).__init__()
        self.__stream = stream

    def parse(self):
        while self.__parse_next_command():
            pass

    def __parse_next_command(self):
        lines = []

        line = self.__stream.readline()
        while True:
            # Check if we've reached the end of the file
            if not line:
                break

            # Handle comments
            elif line.startswith("//"):
                self.on_comment(line[2:].strip())

            # Handle commands
            # A command may span multiple lines
            else:
                line = line.rstrip("\r\n")
                if line and line.endswith(";"):
                    # Remove trailing semicolon here so the command line
                    # processor doesn't have to deal with it.
                    lines.append(line[:-1])
                    break
                elif line:
                    lines.append(line)
            line = self.__stream.readline()

        if lines:
            self.__parse_command_lines(lines)
            return True

        return False

    def __parse_command_lines(self, lines):
        # Pop command name from the first line
        command, _, lines[0] = lines[0].partition(" ")
        command = command.lstrip()

        # Only process arguments if we handle this command
        if self.has_command(command):

            # Tokenize arguments
            args = []
            for line in lines:
                while True:
                    line = line.strip()
                    if not line:
                        break

                    # Handle strings
                    if line[0] in "'\"":
                        string_delim = line[0]
                        escaped = False
                        string_end = len(line)

                        for i in range(1, len(line)):

                            # Check for end delimeter
                            if not escaped and line[i] == string_delim:
                                string_end = i
                                break

                            # Check for start of escape sequence
                            elif not escaped and line[i] == "\\":
                                escaped = True

                            # End escape sequence
                            else:
                                escaped = False

                        # Partition string argument from the remainder
                        # of the command line.
                        arg, line = line[1:string_end], line[string_end + 1:]

                    # Handle other arguments
                    # These, unlike strings, may be tokenized by whitespace
                    else:
                        arg, _, line = line.partition(" ")

                    args.append(arg)

            # Done tokenizing arguments, call command handler
            self.exec_command(command, args)


class ArtellaMayaParser(MayaAsciiParser, object):
    def __init__(self, stream):

        self._references = list()

        super(ArtellaMayaParser, self).__init__(stream=stream)

    @property
    def references(self):
        """
        Returns list of references found in Maya ASCII
        :return: list(str)
        """

        return self._references

    def on_file_reference(self, path):
        if path not in self._references:
            self._references.append(path)


def retrieve_references_recursively(project, file_path, parent_path=None, found_files=None):
    if not found_files:
        found_files = dict()

    if parent_path:
        if parent_path not in found_files:
            found_files[parent_path] = list()
        if file_path not in found_files[parent_path]:
            found_files[parent_path].append(file_path)

    if not os.path.isfile(file_path):
        file_path = project.fix_path(file_path)
        if not os.path.isfile(file_path):
            return

    ext = os.path.splitext(file_path)[-1]
    if ext != '.ma':
        return

    with open(file_path, 'r') as f:
        if file_path not in found_files:
            found_files[file_path] = list()
        parser = ArtellaMayaParser(f)
        parser.parse()
        for ref in parser.references:
            ref = project.fix_path(ref)
            retrieve_references_recursively(project=project, file_path=ref, parent_path=file_path, found_files=found_files)

    return found_files