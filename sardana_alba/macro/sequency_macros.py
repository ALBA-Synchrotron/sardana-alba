##############################################################################
#
# This file is part of Sardana
#
# http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
#
# Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
#
# Sardana is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sardana is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Sardana.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

"""Examples of macro to execute sequencies in a file"""


__all__ = ['seq_path', 'seq_run']

__docformat__ = 'restructuredtext'

import os
from sardana.macroserver.macro import Type, Macro


class seq_path(Macro):
    """
    Macro to set the environment variable SequencyPath used on seq_run macro.
    """
    param_def = [['path', Type.String, None, 'Path to load the sequence '
                                             'files']]

    def run(self, path):
        if os.path.isfile(path):
            raise ValueError('The path is for a directory. It is not a '
                             'filename')
        if not os.path.exists(path):
            msg = 'The path does not exist or it is not on the storage.'
            raise ValueError(msg)

        self.setEnv('SequencyPath', path)


class seq_run(Macro):
    """
    Macro to run a sequence of macros by using execMacro method.

    The macro use the environment variable SequencyPath in case of not use
    absolute path on the filename.

    The sequence file is an ASCII file. It can have commends by start the
    line with "#" and empties line. Example:

    .....
    # Scans for sample 1
    mv mot13 10
    ascanct mot14 0 10 10 0.1
    ct

    # Sample 2
    #mv mot13 12
    .....
    """
    env = ('SequencyPath',)

    param_def = [
        ['filename', Type.String,   None, 'Absolute/Relative filename ('
                                          'path/file) with sequency of '
                                          'macros.'],
        ['skip_errors', Type.Boolean, False, 'Skip error on the macro '
                                             'execution and continue the '
                                             'sequence']
        ]

    def run(self, filename, skip_error):

        if filename[0] not in ['/', '~']:
            seq_path = self.getEnv('SequencyPath')
            filename = os.path.join(seq_path, filename)
        filename = os.path.abspath(filename)

        self.output('Running sequency: "{}"'.format(filename))
        errors = []
        with open(filename, 'r') as f:
            for ln, line in enumerate(f):
                line = line.strip('\r\n')
                line = line.strip()
                if len(line) == 0 or line[0] == '#':
                    continue
                try:
                    self.output('\nRunning macro: "{0}"'.format(line))
                    if line[0] == '%':
                        line = line[1:]
                    self.execMacro(line)
                except Exception as e:
                    errors.append((ln, line, e))
                    if skip_error:
                        self.warning('Skip error: {0}'.format(e))
                    else:
                        break

        self.output('\n{0}\nResume:'.format('*' * 80))
        if len(errors) > 0:
            self.warning('There was(were) some error(s) during the '
                         'execution.\n')
            for ln, line, error in errors:
                self.warning('Line {0:3d}: {1}\n{2}\n'.format(ln, line,
                                                              error))
        else:
            self.output('Done!')


class run_seq(seq_run):
    """
    Alias of macro seq_run. To more information check the seq_run help
    """

    pass

