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

""" Status Handler. """


class StatusHandler(object):

    """ Status Handler.

    A status handler can register functions to run when a status is sent.

    """

    def __init__(self):
        """ Initialize. """
        self.statuses = dict()

    def register_handler(self, key, function):
        """ Register a handler. """
        self.statuses[key] = function

    def get_hook(self):
        """ Get the status hook. """
        def invoke(key, arguments):
            """ Invoke an handler. """
            if key in self.statuses:
                self.statuses[key](arguments)
            else:
                raise ValueError('No handler found for key {}'.format(key))

        return invoke
