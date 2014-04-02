# "mcman" - An utility for managing Minecraft server jars and plugins.
# Copyright (C) 2014  Tobias Laundal <totokaka>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

""" The import command of mcman.

This module is the home of the front end part of the command. This means that
as little as possible logic should go here.

"""

import json

import mcman.logic.servers as s_backend
from mcman.logic.plugins import plugins as p_backend
from mcman.logic.plugins import utils as p_utils
from mcman.logic import common
from mcman.command import Command


class ImportCommand(Command):

    """ The import command of mcman. """

    def __init__(self, args):
        """ Parse command and execute tasks. """
        Command.__init__(self)
        self.args = args

        self.run()

    def run(self):
        """ Run the command. """
        document = json.loads('\n'.join(self.args.input))
