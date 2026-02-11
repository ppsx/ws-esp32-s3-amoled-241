# coding: utf8
# Copyright (C) 2019 Maciej Dems <maciej.dems@p.lodz.pl>
# CircuitPython port: Copyright (c) 2025 Przemyslaw Patrick Socha
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of GNU General Public License as published by the
# Free Software Foundation; either version 3 of the license, or (at your
# opinion) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

import os
import re

from .defs import DATA_DIRS

file_section_re = re.compile(r'\[(\w+)\]\s*')


# List of symbols with descriptions
RICH = '&@*^}LlM=,'

_TRANS = {'E': 0, 'S': 1, 'W': 2, 'N': 3, '*': 1, '.': 0}


def trans(i):
    try:
        return _TRANS[i]
    except KeyError:
        try:
            return int(i)
        except ValueError:
            return i


def load_levels(name='original'):
    levels = []
    for data_dir in DATA_DIRS:
        try:
            # os.path.join replacement
            path = data_dir + "/levels/" + name + ".dat"
            source = open(path).read()
        except OSError:
            continue
        else:
            break
    else:
        # source = resource_string('robbo', 'levels/'+name+'.dat').decode('utf8')
        # Simplified fallback for games/ structure
        try:
             with open('/games/robbo/levels/' + name + '.dat', 'r') as f:
                 source = f.read()
        except OSError:
             print(f"Level {name} not found")
             return []
    level = {}
    section = None
    data = ''
    for lineno, line in enumerate(source.splitlines()):
        try:
            if not line.strip() or (line.startswith('#') and section != 'data'): continue
            m = file_section_re.match(line)
            if m is not None:
                s = m.group(1)
                if section is not None:
                    level[section] = data.rstrip()
                data = ''
                if s == 'end':
                    if 'screws' in level:
                        level['screws'] = int(level['screws'])
                    additional = {}
                    if 'additional' in level:
                        for item in level['additional'].splitlines()[1:]:
                            data = item.split('.')
                            p = tuple(int(n) for n in data[:2])
                            t = data[2]
                            data = tuple(int(n) for n in data[3:])
                            additional.setdefault(t, {})[p] = data
                    else:
                        rows = []
                        for y, row in enumerate(level['data'].splitlines()):
                            row, *info = row.split()
                            rows.append(row)
                            for x, c in enumerate(row):
                                if c in RICH:
                                    p = x, y
                                    for n,val in enumerate(info):
                                        if val.startswith(c): break
                                    else:
                                        raise ValueError("No info for {} in row {}".format(c, y))
                                    data = tuple(trans(i) for i in info.pop(n)[1:])
                                    additional.setdefault(c, {})[p] = data
                        level['data'] = '\n'.join(rows)
                    level['additional'] = additional
                    levels.append(level)
                    level = {}
                    section = None
                else:
                    section = s
            else:
                data += line + '\n'
        except Exception as err:
            raise type(err)("line {}: {}".format(lineno, str(err)))
    return levels
