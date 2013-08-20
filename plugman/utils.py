import os, sys, traceback
import zipfile, bukget.api, yaml
import bukget.api as bkapi
import bukget.orm as bkorm

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
        jarfile should be a string with the path to the file
    """
    if not zipfile.is_zipfile(jarfile):
        raise NotZipFile("{} is not a zip file!".format(jarfile))
    with zipfile.ZipFile(jarfile) as plugin_file:
        if not "plugin.yml" in plugin_file.namelist():
            raise MissingPluginYml("{} Does not contain a file name plugin.yml".format(jarfile))
        plugininfo = yaml.load(plugin_file.open("plugin.yml"))
        slug = bkapi.find_by_name('bukkit', plugininfo['name'])
        plugin = bkorm.plugin_details('bukkit', slug)
        version_number = plugininfo['version']
        for version in plugin.versions:
            if version.version == version_number:
                plugin.local_version = version
        if not hasattr(plugin, 'local_version'):
            plugin.local_version = None
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
    
def download(plugin, version=None):
    if version == None:
        version = get_best_version(plugin)
    remote_filename = version.filename
    if hasattr(plugin, 'local_file'):
        local_filename = plugin.local_file;
    else:
        for p in get_all_plugins_cwd():
            if p.slug == plugin.slug:
                plugin.local_file = p.local_file
                local_filename = p.local_file
                break
        if not 'local_filename' in locals():
            local_filename = plugin.plugin_name+'.jar'
        
    if remote_filename.endswith('.jar'):
        with open(local_filename, 'wb') as jarfile:
            jarfile.write(bkapi.plugin_download('bukkit', plugin.slug, get_best_version(plugin).version))
        print("Downloaded {}, version {}, to file {}".format(plugin.plugin_name, get_best_version(plugin).version, local_filename))
    elif remote_filename.endswith('.zip'):
        with open(local_filename+'.zip', 'wb') as zipped_plugin:
            zipped_plugin.write(bkapi.plugin_download('bukkit', plugin.slug, get_best_version(plugin).version))
        if not zipfile.is_zipfile(local_filename+'.zip'):
            print("Downloaded an zip file for %s that was invalid, aborting...")
            return   
        print("Downloaded {}, version {}, to file {}".format(plugin.plugin_name, get_best_version(plugin).version, local_filename))
        with zipfile.ZipFile(local_filename+'.zip') as zipped_plugin:
            for member in zipped_plugin.namelist():
                if '/' in member or member.endswith('.jar'):
                    zipped_plugin.extract(member)
        os.remove(local_filename+'.zip')
        print("Extracted the zip archive")
    else:
        print("Could not download {}, version {}. It's a uknown filetype!".format(plugin.plugin_name, version.version))
    
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

