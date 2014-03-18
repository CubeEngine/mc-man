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

