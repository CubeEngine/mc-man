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

""" Tests for mcman.backend.plugins. """
from mcman.backend import plugins
from unittest.mock import patch
from unittest import TestCase


@patch('mcman.backend.plugins.bukget')
def test_init(fake_bukget):
    plugins.init('BasE', 'UseragenT')
    assert fake_bukget.BASE == 'BasE'
    assert fake_bukget.USER_AGENT == 'UseragenT'


@patch('bukget.search',
       return_value=[{
           'slug': 'first',
           'plugin_name': 'first',
           'description': 'The first plugin.',
           'popularity': {'monthly': 10}
       }, {
           'slug': 'herp',
           'plugin_name': 'derp',
           'description': 'Herp derp.',
           'popularity': {'monthly': 10}
       }, {
           'slug': 'foo',
           'plugin_name': 'bar',
           'description': 'baz',
           'popularity': {'monthly': 100}
       }, {
           'slug': 'lololol',
           'plugin_name': 'Trolol-plugin',
           'description': 'Troll, lol!',
           'popularity': {'monthly': 0}
       }])
def test_search(fake_search):
    """ Test plugins.search. """
    plugins.init(None, None)
    result = plugins.search('Foo', 3)
    assert result[0]['slug'] == 'foo'
    assert result[1]['slug'] == 'herp'
    assert result[2]['slug'] == 'first'
    assert result[3]['slug'] == 'lololol'


@patch('bukget.find_by_name', return_value='this.is-the_slug')
@patch('bukget.plugin_details', return_value={'everything': 42})
def test_info(fake_info, fake_find_slug):
    """ Test plugins.info. """
    plugins.init(None, None)
    plugin = plugins.info('tha-server', 'This is the Name')
    assert plugin['everything'] == 42
    fake_find_slug.assert_called_once_with('tha-server', 'This is the Name')
    fake_info.assert_called_once_with('tha-server', 'this.is-the_slug',
                                      version='',
                                      fields='website,dbo_page,description,'
                                             + 'versions.type,'
                                             + 'versions.game_versions,'
                                             + 'versions.version,plugin_name,'
                                             + 'server,authors,categories,'
                                             + 'stage,slug')


@patch('bukget.find_by_name', return_value=None)
def test_info_plugin_not_found(fake_find_slug):
    """ Test plugins.info with a non-existing plugin. """
    plugins.init(None, None)
    plugin = plugins.info('herp', 'derp')
    assert plugin is None


@patch('bukget.plugin_details',
       return_value={'versions': [{'version': '1.0'}]})
def test_find_newest_versions_one(fake_plugin_details):
    """ Test one for plugins.find_newest_versions. """
    plugins.init(None, None)
    returned = plugins.find_newest_versions([('herp', '0.1', 'Herp')],
                                            'derp').__next__()
    assert returned[1] == '1.0'


@patch('bukget.plugin_details',
       return_value={'versions': [{'version': '1.0'}]})
def test_find_newest_versions__two(fake_plugin_details):
    """ Test two for plugins.find_newest_versions. """
    plugins.init(None, None)
    try:
        plugins.find_newest_versions([('herp', '1.0', 'Herp')],
                                     'derp').__next__()
    except StopIteration:
        assert True
    else:
        assert False


@patch('bukget.plugin_details',
       return_value=None)
def test_find_newest_versions__three(fake_plugin_details):
    """ Test three for plugins.find_newest_versions. """
    plugins.init(None, None)
    returned = plugins.find_newest_versions([('herp', '0.1', 'Herp')],
                                            'derp').__next__()
    assert returned == 'Herp'
