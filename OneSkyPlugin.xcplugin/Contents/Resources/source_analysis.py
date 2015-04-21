#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Copyright (c) 2012 Markus Chmelar / Innovaptor OG

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Modified by Bret Cheng / OneSky Inc.
'''
# -- Import --------------------------------------------------------------------
# Regular Expressions
import re
# Operation Systems and Path Operations
import os
# System Utilities
import sys
# Creating and using Temporal File
import tempfile
# Running Commands on the Commandline
import subprocess
# Opening Files with different Encodings
import codecs
# Commandline Options parser
import optparse
# High Level File Operations
import shutil
# Logging
import logging
# IO
import io
# JSON
import json
# XML
import xml.etree.ElementTree as ET

# -- Class ---------------------------------------------------------------------


class LocalizedStringLineParser(object):
    ''' Parses single lines and creates LocalizedString objects from them'''
    def __init__(self):
        # Possible Parsing states indicating what is waited for
        self.ParseStates = {'COMMENT': 1, 'STRING': 2, 'TRAILING_COMMENT': 3,
                            'STRING_MULTILINE': 4, 'COMMENT_MULTILINE' :5}
        # The parsing state indicates what the last parsed thing was
        self.parse_state = self.ParseStates['COMMENT']
        self.key = None
        self.value = None
        self.comment = None

    def parse_line(self, line):
        ''' Parses a single line. Keeps track of the current state and creates
        LocalizedString objects as appropriate

        Keyword arguments:

            line
                The next line to be parsed

        Examples

            >>> parser = LocalizedStringLineParser()
            >>> string = parser.parse_line('    ')
            >>> string

            >>> string = parser.parse_line('/* Comment1 */')
            >>> string

            >>> string = parser.parse_line('    ')
            >>> string

            >>> string = parser.parse_line('"key1" = "value1";')
            >>> string.key
            'key1'
            >>> string.value
            'value1'
            >>> string.comment
            'Comment1'

            >>> string = parser.parse_line('/* Comment2 */')
            >>> string

            >>> string = parser.parse_line('"key2" = "value2";')
            >>> string.key
            'key2'
            >>> string.value
            'value2'
            >>> string.comment
            'Comment2'


            >>> parser = LocalizedStringLineParser()
            >>> string = parser.parse_line('"KEY3" = "VALUE3"; /* Comment3 */')
            >>> string.key
            'KEY3'
            >>> string.value
            'VALUE3'
            >>> string.comment
            'Comment3'



            >>> parser = LocalizedStringLineParser()
            >>> string = parser.parse_line('/* Comment4 */')
            >>> string

            >>> string = parser.parse_line('"KEY4" = "VALUE4')
            >>> string

            >>> string = parser.parse_line('VALUE4_LINE2";')
            >>> string.key
            'KEY4'
            >>> string.value
            'VALUE4\\nVALUE4_LINE2'

            >>> parser = LocalizedStringLineParser()
            >>> string = parser.parse_line('/* Line 1')

            >>> string = parser.parse_line(' Line 2')

            >>> string = parser.parse_line(' Line 3 */')

            >>> string = parser.parse_line('"key" = "value";')

            >>> string.key
            'key'
            >>> string.value
            'value'
            >>> string.comment
            'Line 1\\n Line 2\\n Line 3 '
        '''
        if self.parse_state == self.ParseStates['COMMENT']:
            (self.key, self.value, self.comment) = LocalizedString.parse_trailing_comment(line)
            if self.key is not None and self.value is not None and self.comment is not None:
                return self.build_localizedString()
            self.comment = LocalizedString.parse_comment(line)
            if self.comment is not None:
                self.parse_state = self.ParseStates['STRING']
                return None
            # Maybe its a multiline comment
            self.comment_partial = LocalizedString.parse_multiline_comment_start(line)
            if self.comment_partial is not None:
                self.parse_state = self.ParseStates['COMMENT_MULTILINE']
            return None

        elif self.parse_state == self.ParseStates['COMMENT_MULTILINE']:
            comment_end = LocalizedString.parse_multiline_comment_end(line)
            if comment_end is not None:
                self.comment = self.comment_partial + '\n' + comment_end
                self.comment_partial = None
                self.parse_state = self.ParseStates['STRING']
                return None
            # Or its just an intermediate line
            comment_line = LocalizedString.parse_multiline_comment_line(line)
            if comment_line is not None:
                self.comment_partial = self.comment_partial + '\n' + comment_line
            return None

        elif self.parse_state == self.ParseStates['TRAILING_COMMENT']:
            self.comment = LocalizedString.parse_comment(line)
            if self.comment is not None:
                self.parse_state = self.ParseStates['COMMENT']
                return self.build_localizedString()
            return None

        elif self.parse_state == self.ParseStates['STRING']:
            (self.key, self.value) = LocalizedString.parse_localized_pair(
                line
            )
            if self.key is not None and self.value is not None:
                self.parse_state = self.ParseStates['COMMENT']
                return self.build_localizedString()
            # Otherwise, try if the Value is multi-line
            (self.key, self.value_partial) = LocalizedString.parse_multiline_start(
                line
            )
            if self.key is not None and self.value_partial is not None:
                self.parse_state = self.ParseStates['STRING_MULTILINE']
                self.value = None
            return None
        elif self.parse_state == self.ParseStates['STRING_MULTILINE']:
            value_part = LocalizedString.parse_multiline_end(line)
            if value_part is not None:
                self.value = self.value_partial + '\n' + value_part
                self.value_partial = None
                self.parse_state = self.ParseStates['COMMENT']
                return self.build_localizedString()
            value_part = LocalizedString.parse_multiline_line(line)
            if value_part is not None:
                self.value_partial = self.value_partial + '\n' +  value_part
            return None


    def build_localizedString(self):
        localizedString = LocalizedString(
            self.key,
            self.value,
            self.comment
        )
        self.key = None
        self.value = None
        self.comment = None
        return localizedString

class LocalizedString(object):
    ''' A localizes string entry with key, value and comment'''
    COMMENT_EXPR = re.compile(
        # Line start
        '^\w*'
        # Comment
        '/\* (?P<comment>.+) \*/'
        # End of line
        '\w*$'
    )
    COMMENT_MULTILINE_START = re.compile(
        # Line start
        '^\w*'
        # Comment
        '/\* (?P<comment>.+)'
        # End of line
        '\w*$'
    )
    COMMENT_MULTILINE_LINE = re.compile(
        # Line start
        '^'
        # Value
        '(?P<comment>.+)'
        # End of line
        '$'
    )
    COMMENT_MULTILINE_END = re.compile(
        # Line start
        '^'
        # Comment
        '(?P<comment>.+)\*/'
        # End of line
        '\s*$'
    )
    LOCALIZED_STRING_EXPR = re.compile(
        # Line start
        '^'
        # Key
        '"(?P<key>.+)"'
        # Equals
        ' ?= ?'
        # Value
        '"(?P<value>.+)"'
        # Whitespace
        ';'
        # End of line
        '$'
    )
    LOCALIZED_STRING_MULTILINE_START_EXPR = re.compile(
        # Line start
        '^'
        # Key
        '"(?P<key>.+)"'
        # Equals
        ' ?= ?'
        # Value
        '"(?P<value>.+)'
        # End of line
        '$'
    )
    LOCALIZED_STRING_MULTILINE_LINE_EXPR = re.compile(
        # Line start
        '^'
        # Value
        '(?P<value>.+)'
        # End of line
        '$'
    )
    LOCALIZED_STRING_MULTILINE_END_EXPR = re.compile(
        # Line start
        '^'
        # Value
        '(?P<value>.+)"'
        # Whitespace
        ' ?; ?'
        # End of line
        '$'
    )
    LOCALIZED_STRING_TRAILING_COMMENT_EXPR = re.compile(
        # Line start
        '^'
        # Key
        '"(?P<key>.+)"'
        # Equals
        ' ?= ?'
        # Value
        '"(?P<value>.+)"'
        # Whitespace
        ' ?; ?'
        # Comment
        '/\* (?P<comment>.+) \*/'
        # End of line
        '$'

    )

    @classmethod
    def parse_multiline_start(cls, line):
        ''' Parse the beginning of a multi-line entry, "KEY"="VALUE_LINE1

        Keyword arguments:

            line
                The line to be parsed

        Returns
            ``tuple`` with key, value and comment
            ``None`` when the line was no comment

        Examples

            >>> line = '"key" = "value4'
            >>> LocalizedString.parse_multiline_start(line)
            ('key', 'value4')

        '''
        result = cls.LOCALIZED_STRING_MULTILINE_START_EXPR.match(line)
        if result is not None:
            return (result.group('key'),
                    result.group('value'))
        else:
            return (None, None)

    @classmethod
    def parse_multiline_line(cls, line):
        ''' Parse an intermediate line of a multi-line entry, only value

        Keyword arguments:

            line
                The line to be parsed

        Returns
            ``String`` with the value
            ``None`` when the line was no comment

        Examples

            >>> line = 'value4, maybe something else'
            >>> LocalizedString.parse_multiline_line(line)
            'value4, maybe something else'
        '''
        result = cls.LOCALIZED_STRING_MULTILINE_LINE_EXPR.match(line)
        if result is not None:
            return result.group('value')
        return None


    @classmethod
    def parse_multiline_end(cls, line):
        ''' Parse an end line of a multi-line entry, only value

        Keyword arguments:

            line
                The line to be parsed

        Returns
            ``String`` the value
            ``None`` when the line was no comment

        Examples

            >>> line = 'value4, maybe something else";'
            >>> LocalizedString.parse_multiline_end(line)
            'value4, maybe something else'
        '''
        result = cls.LOCALIZED_STRING_MULTILINE_END_EXPR.match(line)
        if result is not None:
            return result.group('value')
        return None


    @classmethod
    def parse_trailing_comment(cls, line):
        '''Extract the content of a line with a trailing comment.

        Keyword arguments:

            line
                The line to be parsed

        Returns
            ``tuple`` with key, value and comment
            ``None`` when the line was no comment

        Examples

            >>> line = '"key3" = "value3";/* Bla */'
            >>> LocalizedString.parse_trailing_comment(line)
            ('key3', 'value3', 'Bla')
        '''
        result = cls.LOCALIZED_STRING_TRAILING_COMMENT_EXPR.match(line)
        if result is not None:
            return (
                result.group('key'),
                result.group('value'),
                result.group('comment')
            )
        else:
            return (None, None, None)

    @classmethod
    def parse_multiline_comment_start(cls, line):
        '''
        Example:

            >>> LocalizedString.parse_multiline_comment_start('/* Hello ')
            'Hello '
        '''
        result = cls.COMMENT_MULTILINE_START.match(line)
        if result is not None:
            return result.group('comment')
        else:
            return None


    @classmethod
    def parse_multiline_comment_line(cls, line):
        '''
        Example:

            >>> LocalizedString.parse_multiline_comment_line(' Line ')
            ' Line '
        '''
        result = cls.COMMENT_MULTILINE_LINE.match(line)
        if result is not None:
            return result.group('comment')
        else:
            return None


    @classmethod
    def parse_multiline_comment_end(cls, line):
        '''
        Example:

            >>> LocalizedString.parse_multiline_comment_end(' End */ ')
            ' End '
        '''
        result = cls.COMMENT_MULTILINE_END.match(line)
        if result is not None:
            return result.group('comment')
        else:
            return None

    @classmethod
    def parse_comment(cls, line):
        '''Extract the content of a comment line from a line.

        Keyword arguments:

            line
                The line to be parsed

        Returns
            ``string`` with the Comment or
            ``None`` when the line was no comment

        Examples

            >>> LocalizedString.parse_comment('This line is no comment')
            >>> LocalizedString.parse_comment('')
            >>> LocalizedString.parse_comment('/* Comment */')
            'Comment'
        '''
        result = cls.COMMENT_EXPR.match(line)
        if result is not None:
            return result.group('comment')
        else:
            return None

    @classmethod
    def parse_localized_pair(cls, line):
        '''Extract the content of a key/value pair from a line.

        Keyword arguments:

            line
                The line to be parsed

        Returns
            ``tupple`` with key and value as strings
            ``tupple`` (None, None) when the line was no match

        Examples

            >>> LocalizedString.parse_localized_pair('Some Line')
            (None, None)
            >>> LocalizedString.parse_localized_pair('/* Comment */')
            (None, None)
            >>> LocalizedString.parse_localized_pair('"key1" = "value1";')
            ('key1', 'value1')
        '''
        result = cls.LOCALIZED_STRING_EXPR.match(line)
        if result is not None:
            return (
                result.group('key'),
                result.group('value')
            )
        else:
            return (None, None)

    def __eq__(self, other):
        '''Tests Equality of two LocalizedStrings

        >>> s1 = LocalizedString('key1', 'value1', 'comment1')
        >>> s2 = LocalizedString('key1', 'value1', 'comment1')
        >>> s3 = LocalizedString('key1', 'value2', 'comment1')
        >>> s4 = LocalizedString('key1', 'value1', 'comment2')
        >>> s5 = LocalizedString('key1', 'value2', 'comment2')
        >>> s1 == s2
        True
        >>> s1 == s3
        False
        >>> s1 == s4
        False
        >>> s1 == s5
        False
        '''
        if isinstance(other, LocalizedString):
            return (self.key == other.key and self.value == other.value and
                    self.comment == other.comment)
        else:
            return NotImplemented

    def __neq__(self, other):
        result = self.__eq__(other)
        if(result is NotImplemented):
            return result
        return not result

    def __init__(self, key, value=None, comment=None):
        super(LocalizedString, self).__init__()
        self.key = key
        self.value = value
        self.comment = comment

    def is_raw(self):
        '''
        Return True if the localized string has not been translated.

        Examples
            >>> l1 = LocalizedString('key1', 'valye1', 'comment1')
            >>> l1.is_raw()
            False
            >>> l2 = LocalizedString('key2', 'key2', 'comment2')
            >>> l2.is_raw()
            True
        '''
        return self.value == self.key

    def __str__(self):
        if self.comment:
            return '/* %s */\n"%s" = "%s";\n' % (
                self.comment, self.key or '', self.value or '',
            )
        else:
            return '"%s" = "%s";\n' % (self.key or '', self.value or '')

# -- Methods -------------------------------------------------------------------
ENCODINGS = ['utf-8', 'utf-16', 'utf-16-le', 'utf-16-be']

CLASS_NAME_PATTERN = r'@implementation\s+(.+)'

def try_encoding(file_path, encoding):
    try:
        f = io.open(file_path, 'r', encoding=encoding).read()
        return encoding
    except (UnicodeDecodeError, UnicodeError):
        return False


def read_file_encoding(file_path):

    for encoding in ENCODINGS:
        enc = try_encoding(file_path, encoding)
        if enc:
            return enc

    return False


def parse_file(file_path):
    ''' Parses a file and creates a dictionary containing all LocalizedStrings
        elements in the file

        Keyword arguments:

        file_path
        path to the file that should be parsed

        encoding
        encoding of the file

        Returns:    ``dict``
        '''

    encoding = read_file_encoding(file_path)

    with io.open(file_path, mode='r', encoding=encoding) as file_contents:
        logging.debug("Parsing File: {}".format(file_path))
        parser = LocalizedStringLineParser()
        localized_strings = {}
        for line in file_contents:
            localized_string = parser.parse_line(line)
            if localized_string is not None:
                localized_strings[localized_string.key] = localized_string.value
    return localized_strings


def find_sources(folder_path, extensions=None, ignore_patterns=None):
    '''Finds all source-files in the path that fit the extensions and
    ignore-patterns

    Keyword arguments:

        folder_path
            The path to the folder, all files in this folder will recursively
            be searched

        extensions
            If this parameter is different to None, only files with the given
            extension will be used
            If None, defaults to [c, m, mm]

        ignore_patterns
            If this parameter is different to None, files which path match the
            ignore pattern will be ignored

    Returns:

        Array with paths to all files that have to be used with genstrings

    Examples:

        >>> find_sources('TestInput')
        ['TestInput/test.m', 'TestInput/3rdParty/test2.m']

        >>> find_sources('TestInput', ['h', 'm'])
        ['TestInput/test.h', 'TestInput/test.m', 'TestInput/3rdParty/test2.h', 'TestInput/3rdParty/test2.m']

        >>> find_sources('TestInput', ['h', 'm'], ['3rdParty'])
        ['TestInput/test.h', 'TestInput/test.m']

        >>> find_sources('TestInput', ignore_patterns=['3rdParty'])
        ['TestInput/test.m']
    '''
    # First run genstrings on all source-files
    code_file_paths = []
    if extensions is None:
        extensions = frozenset(['c', 'm', 'mm'])

    for dir_path, dir_names, file_names in os.walk(folder_path):
        ignorePath = False
        if ignore_patterns is not None:
            for ignore_pattern in ignore_patterns:
                if ignore_pattern in dir_path:
                    logging.debug('IGNORED Path: {}'.format(dir_path))
                    ignorePath = True
        if ignorePath is False:
            logging.debug('DirPath: {}'.format(dir_path))
            for file_name in file_names:
                extension = file_name.rpartition('.')[2]
                if extension in extensions:
                    code_file_path = os.path.join(dir_path, file_name)
                    code_file_paths.append(code_file_path)
    logging.info('Found %d files', len(code_file_paths))
    return code_file_paths

def parse_class_name(file_path):
    encoding = read_file_encoding(file_path)
    source = io.open(file_path, mode='r', encoding=encoding).read()
    p = re.compile(CLASS_NAME_PATTERN, re.I)
    class_names = re.findall(p, source)
    if len(class_names) > 0:
        return class_names[0]
    return None

def find_strings_in_ib_file(node, filename, out_items):

    #Look for buttons
    for button in node.iter('button'):
        for state in button.findall('state'):
            title = state.get('title')
            if title:
                key = button.get('id') + '.' + state.get('key') + 'Title'
                string_item = {'key':key, 'value':title, 'file':filename}
                out_items.append(string_item)
    #Look for labels
    for label in node.iter('label'):
        text = label.get('text')
        if text:
            key = label.get('id') + '.text'
            string_item = {'key':key, 'value':text, 'file':filename}
            out_items.append(string_item)
    #Look for textfields
    for text_field in node.iter('textField'):
        text = text_field.get('text')
        if text:
            key = text_field.get('id') + '.text'
            string_item = {'key':key, 'value':text, 'file':filename}
            out_items.append(string_item)
        placeholder = text_field.get('placeholder')
        if placeholder:
            key = text_field.get('id') + '.placeholder'
            string_item = {'key':key, 'value':text, 'file':filename}
            out_items.append(string_item)
    #Look for segmented controls
    for segmented_control in node.iter('segmentedControl'):
        segments = segmented_control.find('segments')
        for index in range(len(segments)):
            segment = segments[index]
            key = segmented_control.get('id') + '.segmentTitles[' + `index` + ']'
            string_item = {'key':key, 'value':segment.get('title'), 'file':filename}
            out_items.append(string_item)
    #Look for textviews
    for text_view in node.iter('textView'):
        string_element = text_view.find('string')
        if string_element.text:
            key = text_view.get('id') + '.text'
            string_item = {'key':key, 'value':string_element.text, 'file':filename}
            out_items.append(string_item)
    #Look for search bars
    for search_bar in node.iter('searchBar'):
        text = search_bar.get('text')
        if text:
            key = search_bar.get('id') + '.text'
            string_item = {'key':key, 'value':text, 'file':filename}
            out_items.append(string_item)
        placeholder = search_bar.get('placeholder')
        if placeholder:
            key = search_bar.get('id') + '.placeholder'
            string_item = {'key':key, 'value':placeholder, 'file':filename}
            out_items.append(string_item)
        prompt = search_bar.get('prompt')
        if prompt:
            key = search_bar.get('id') + '.prompt'
            string_item = {'key':key, 'value':prompt, 'file':filename}
            out_items.append(string_item)
    #Look for bar button items
    for bar_button_item in node.iter('barButtonItem'):
        title = bar_button_item.get('title')
        if title:
            key = bar_button_item.get('id') + '.title'
            string_item = {'key':key, 'value':title, 'file':filename}
            out_items.append(string_item)
    #Look for tab bar items
    for tab_bar_item in node.iter('tabBarItem'):
        title = tab_bar_item.get('title')
        if title:
            key = tab_bar_item.get('id') + '.title'
            string_item = {'key':key, 'value':title, 'file':filename}
            out_items.append(string_item)
    #Look for navigation bar items
    for navigation_item in node.iter('navigationItem'):
        title = navigation_item.get('title')
        if title:
            key = navigation_item.get('id') + '.title'
            string_item = {'key':key, 'value':title, 'file':filename}
            out_items.append(string_item)
     #Look for bar button items
    for bar_button_item in node.iter('barButtonItem'):
        title = bar_button_item.get('title')
        if title:
            key = bar_button_item.get('id') + '.title'
            string_item = {'key':key, 'value':title, 'file':filename}
            out_items.append(string_item)

def analyse_source(folder_path, gen_path=None):

      #Dictionary to store all strings
    code_file_paths = find_sources(folder_path, ['c', 'm', 'mm'], None)

    if not gen_path:
        gen_path = folder_path

    #dict for source usage
    classes = {}

    #Loop through each source file
    for code_file_path in code_file_paths:
        logging.debug('Running genstrings')
        #Make temp folder
        temp_folder_path = tempfile.mkdtemp()
        #Prepare genstrings
        arguments = ['genstrings', '-u', '-o', temp_folder_path]
        paths = [code_file_path];
        arguments.extend(paths)
        subprocess.call(arguments)
        #Get class name of current source
        class_name = parse_class_name(code_file_path)
        if class_name:
            class_strings = []
            #Read strings generated in the temp folder
            for temp_file in os.listdir(temp_folder_path):
                current_file_path = os.path.join(temp_folder_path, temp_file)
                #Get strings from .strings file
                strings = parse_file(current_file_path)
                #Save strings as array of dicts
                for key, value in strings.iteritems():
                    string_item = {'key':key, 'value':value, 'file':temp_file}
                    class_strings.append(string_item)
            #Store class strings in master dictionary
            if len(class_strings) > 0:
                classes[class_name] = class_strings
        #Remove files
        shutil.rmtree(temp_folder_path)

    #Loop through each storyboard/xib files
    extensions = ['xib', 'storyboard']
    code_file_paths = find_sources(folder_path, extensions, None)

    #See if the ib is localized
    ib_strings_file_paths = find_sources(folder_path, ['strings'], None);
    ib_table_to_strings_file_paths = {}
    for ib_strings_file_path in ib_strings_file_paths:
        head, tail = os.path.split(ib_strings_file_path)
        filename = tail
        ib_table_to_strings_file_paths[filename] = ib_strings_file_path

    for code_file_path in code_file_paths:
        #Parse XML
        tree = ET.parse(code_file_path)
        root = tree.getroot()
        #Get file name
        head, tail = os.path.split(code_file_path)
        extension = tail.split('.')[1]
        filename = tail.replace(extension, "strings")

        #Look for view controllers
        localized_file = ib_table_to_strings_file_paths.get(filename)
        if localized_file is None:
            continue

        if extension == 'xib':

            class_name = None
            for placeholder in root.iter('placeholder'):
                placeholder_id = placeholder.get('placeholderIdentifier')
                if placeholder_id == 'IBFilesOwner':
                    class_name = placeholder.get('customClass')
                    break

            if class_name is None:
                continue

            class_strings = classes.get(class_name)
            if class_strings is None:
                class_strings = []

            find_strings_in_ib_file(root, filename, class_strings)

        else:

            for view_controller in root.iter('viewController'):

                class_name = view_controller.get('customClass')

                if class_name is None:
                    restore_id = view_controller.get('restorationIdentifier')
                    if restore_id is None:
                        use_storyboard_as_restore_id = view_controller.get('useStoryboardIdentifierAsRestorationIdentifier')
                        if use_storyboard_as_restore_id == 'YES':
                            restore_id = view_controller.get('storyboardIdentifier')
                    if restore_id is not None:
                        class_name = 'UIViewController(' + restore_id + ')'

                if class_name is None:
                    continue

                class_strings = classes.get(class_name)
                if class_strings is None:
                    class_strings = []

                find_strings_in_ib_file(view_controller, filename, class_strings)

                #Only save if we have found strings
                if len(class_strings) > 0:
                    classes[class_name] = class_strings

    #remap classes to table:{key:[strings]}
    groupings = []
    #iterate class_name:[string_items]
    for class_name, class_strings in classes.iteritems():
        class_item = {}
        class_item["name"] = class_name
        phrases = []
        for string_item in class_strings:
            phrase_item = {}
            phrase_item["key"] = string_item.get("key")
            phrase_item["file"] = string_item.get("file")
            phrases.append(phrase_item)
        class_item["phrases"] = phrases
        groupings.append(class_item)

    json_dict = {}
    json_dict['groupings'] = groupings
    if os.path.isdir(gen_path):
        file_path = os.path.join(gen_path, 'source_analysis_result.json')
    else:
        file_path = gen_path
    with io.open(file_path, 'w', encoding='utf-8') as f:
        f.write(unicode(json.dumps(json_dict, ensure_ascii=False)))


def main():
    ''' Parse the command line and execute the program with the parameters '''

    parser = optparse.OptionParser(
        'usage: %prog [options] [output folder] [source folders] [ignore patterns]'
    )
    parser.add_option(
        '-i',
        '--input',
        action='store',
        dest='input_path',
        default='.',
        help='Input Path where the Source-Files are'
    )
    parser.add_option(
        '-o',
        '--output',
        action='store',
        dest='output_path',
        default=None,
        help='Output Path where the analysis result is saved'
    )
    parser.add_option(
        '-v',
        '--verbose',
        action='store_true',
        dest='verbose',
        default=False,
        help='Show debug messages'
    )

    (options, args) = parser.parse_args()

    # Create Logger
    logging.basicConfig(
        format='%(message)s',
        level=options.verbose and logging.DEBUG or logging.INFO
    )

    analyse_source(folder_path=options.input_path,
                gen_path=options.output_path)
    return 0

if __name__ == '__main__':
    sys.exit(main())
