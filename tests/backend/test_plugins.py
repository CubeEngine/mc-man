""" Tests for mcman.backend.plugins. """
from mcman.backend import plugins
from unittest.mock import MagicMock, patch
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
    result = plugins.search('Foo', 3)
    assert result[0]['slug'] == 'foo'
    assert result[1]['slug'] == 'herp'
    assert result[2]['slug'] == 'first'
    assert result[3]['slug'] == 'lololol'


@patch('bukget.find_by_name', return_value='this.is-the_slug')
@patch('bukget.plugin_details', return_value={'everything': 42})
def test_info(fake_info, fake_find_slug):
    plugin = plugins.info('tha-server', 'This is the Name')
    assert plugin['everything'] == 42
    fake_find_slug.assert_called_once_with('tha-server', 'This is the Name')
    fake_info.assert_called_once_with('tha-server', 'this.is-the_slug',
                                      fields='website,dbo_page,description,'
                                             + 'versions.type,'
                                             + 'versions.game_versions,'
                                             + 'versions.version,plugin_name,'
                                             + 'server,authors,categories,'
                                             + 'stage,slug')


@patch('bukget.find_by_name', return_value=None)
def test_info_plugin_not_found(fake_find_slug):
    plugin = plugins.info('herp', 'derp')
    assert plugin == None
