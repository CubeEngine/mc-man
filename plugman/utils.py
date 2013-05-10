import os, sys, traceback
from bukget import find_slug, plugin_details
import zipfile, bukget.api, yaml


class NotZipFile(Exception):
    pass


class MissingPluginYml(Exception):
    pass

def get_best_version(plugin):
    ''' Get the newest release verions of the plugin
    If no release version is found It'll go over to Beta, then Alpha then just
    latest
    '''
    for version_type in ['Release', 'Beta', 'Alpha']:
        for version in plugin.versions:
            if version.type == version_type:
                return version
    return plugin.versions[0]

def get_plugin_from_jar(jarfile):
    """ Get the plugin from the jar file
        jarfile should be a string
    """
    if not zipfile.is_zipfile(jarfile):
        raise NotZipFile("%s is not a zip file!" % jarfile)
    with zipfile.ZipFile(jarfile) as plugin_file:
        if not "plugin.yml" in plugin_file.namelist():
            raise MissingPluginYml("%s Does not contain a file name plugin.yml" 
                % jarfile)
        plugininfo = yaml.load(plugin_file.open("plugin.yml"))
        slug = find_slug('bukkit', plugininfo['name'])
        plugin = plugin_details('bukkit', slug)
        version_number = plugininfo['version']
        for version in plugin.versions:
            if version.version == version_number:
                plugin.local_version = version
        plugin.local_file = jarfile
        return plugin

def get_all_plugins_cwd():
    """ Get all plugins in the current working directory
    """
    files = [f for f in os.listdir('.') if os.path.isfile(f)]
    for plugin_filename in files:
        try:
            plugin = get_plugin_from_jar(plugin_filename)
            yield plugin
        except Exception:
            pass
            #exc_type, exc_value, exc_traceback = sys.exc_info()
            #traceback.print_exception(exc_type, exc_value, exc_traceback,
            #                  limit=2, file=sys.stdout)
    
def download(plugin, version=None):
    if version == None:
        version = plugin.versions[0]
    print("Pretending to download %s" % plugin.plugin_name)
    
# Modified from this: http://log.brandonthomson.com/2011/01/python-console-prompt-yesno.html
def confirm(prompt_str="Confirm", default=True):
    fmt = (prompt_str, 'Y', 'n') if default else (prompt_str, 'y', 'N')
    prompt = '%s [%s/%s]: ' % fmt
 
    while True:
        ans = input(prompt).lower()
        if ans == '':
            return default
        elif ans == 'y':
            return True
        elif ans == 'n':
            return False
        else:
            print('Please enter y or n.')

