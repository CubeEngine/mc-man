from urllib.request import urlopen
from urllib.parse import urlencode
import json
from bukget.objects import Plugin
from bukget.utils import get_best_match

BUKGET_BASE_URL = "http://api.bukget.org/3/"
BUKGET_PLUGIN_URL = BUKGET_BASE_URL + "plugins/bukkit/"
BUKGET_SEARCH_URL = BUKGET_BASE_URL + "search/%s/%s/%s"
plugins = {} # This dict contains all plugins that have been downloaded


def get_slug(name):
    """ Find the slug for a plugin with the name
    """
    # First we are testing if the name is the same as the slug
    response = urlopen(BUKGET_PLUGIN_URL + name.lower().replace(' ', '-') + "?" + urlencode({"fields": "slug"}))
    if json.loads(response.readall().decode("utf-8")):
        return name.lower().replace(' ', '-')

    # Then we search for a plugin with name that matches
    response = urlopen(BUKGET_SEARCH_URL % ("plugin_name", "=", name) + "?" + urlencode({"fields": "slug"}))
    json_object = json.loads(response.readall().decode("utf-8"))
    if len(json_object) > 0:
        slug = json_object[0]['slug']
        return slug

    # Then we search for a plugin with a name like it
    response = urlopen(BUKGET_SEARCH_URL % ("plugin_name", "like", name) + "?" + urlencode({"fields": "slug"}))
    json_object = json.loads(response.readall().decode("utf-8"))
    if len(json_object) > 0:
        return get_best_match(name, [x['slug'] for x in json_object])
        #No plugin found =(
    return None


def get_plugin(slug, size=5, fields="-logo_full,-server,-logo,-main,-versions.commands,-versions.permissions,-versions.changelog,-versions.status,-versions.dbo_version,-versions.slug"):
    """ Create a Plugin object from Bukget or return the already created object
    """
    if plugins.get(slug, None):
        return plugins[slug]
    else:
        plugin = Plugin(slug, fields, size)
        plugins[plugin.slug] = plugin
        return plugin
