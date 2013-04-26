from bukget.api import get_slug, get_plugin
import zipfile, bukget.api, yaml


class NotZipFile(Exception):
    pass


class MissingPluginYml(Exception):
    pass


def get_plugin_from_jar(jarfile):
    """ Get the plugin from the jar file
    """
    if not zipfile.is_zipfile(jarfile):
        raise NotZipFile("%s is not a zip file!" % jarfile.name)
    with zipfile.ZipFile(jarfile) as plugin_file:
        if not "plugin.yml" in plugin_file.namelist():
            raise MissingPluginYml("%s Does not contain a file name plugin.yml" 
                % jarfile.name)
        plugininfo = yaml.load(plugin_file.open("plugin.yml"))
        plugin = get_plugin(get_slug(plugininfo['name']))
        plugin.local_version = plugin.versions[plugininfo['version']]
        plugin.local_file = jarfile.name
        return plugin
