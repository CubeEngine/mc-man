import bukget
from plugman.utils import get_best_version
import argparse, plugman.utils

verbose = False
force = False
ignore_dependencies = False

plugin_info_message = \
"""
Name:               %s
Version:            %s
Developer:          %s
Categories:         %s
Website:            %s
Hard dependencies:  %s
Soft dependencies:  %s
"""

def _levenshtein(s1, s2):
    """ Get the levenshtein edit distance between two strings
    """
    if len(s1) < len(s2):
        return _levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[
                             j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('plugins', metavar='Plugin', type=str, nargs='+', 
                        help='Plugin to process')
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-D", "--Download", help="Download and install the \
                        plugin(s)", action="store_true")
    group.add_argument("-U", "--Update", help="Update the plugin(s)", 
                       action="store_true")
    group.add_argument("-R", "--Remove", help="Remove the plugin(s)", 
                       action="store_true")
    group.add_argument("-I", "--Info", help="Get info about the plugin(s)", 
                       action="store_true")
    parser.add_argument("--verbose", help="increase output verbosity", 
                        action="store_true")
    parser.add_argument("-f", "--force", help="Force install a plugin, even if\
                        the dependencies is not found", action="store_true")
    parser.add_argument("--ignore-deps", help="Ignore the dependencies", 
                        action="store_true")
    args = parser.parse_args()
    
    global verbose
    verbose = args.verbose
    global force
    force = args.force
    global ignore_dependencies
    ignore_dependencies = args.ignore_deps
    
    if args.Download:
        download(args)
    elif args.Update:
        update(args)
    elif args.Remove:
        remove(args)
    elif args.Info:
        info(args)
    else:
        pass # This will never happen
    
def download(args):
    print("Calculating which plugins to install...")
    to_install = set()
    for plugin_name in args.plugins:
        slug = bukget.find_slug('bukkit', plugin_name)
        if slug is None or len(slug) < 1:
            print("Could not find %s on BukGet!" % plugin_name)
            continue
        plugin = bukget.plugin_details('bukkit', slug, size=1)
        if plugin is None:
            print("Could not find %s on BukGet!" % plugin_name)
            continue
        to_install.add(plugin)
        to_install = to_install.union([bukget.plugin_details('bukkit', 
                                        bukget.find_slug('bukkit', p)) for p in 
                                        get_best_version(plugin).hard_dependencies])
    print("These plugins will be installed: " + ", ".join([i.plugin_name for i in to_install]))
    if not plugman.utils.confirm(prompt_str="Are you sure you want to install them?"):
        exit(0)
    for plugin in to_install:
        plugman.utils.download(plugin)
    print("Done!")
     

def update(args):
    print("Checking plugins...")
    to_update = set()
    for plugin in plugman.utils.get_all_plugins_cwd():
        if not args.plugins[0].lower() == "all":
            _continue = True
            for name in args.plugins:
                if _levenshtein(name.lower(), plugin.plugin_name.lower()) < 3:
                    _continue = False
                    break
            if _continue:
                continue
        if not hasattr(plugin, "local_version"):
            to_update.add(plugin)
            continue
        if plugin.local_version.version != get_best_version(plugin).version:
            to_update.add(plugin)
    if len(to_update) < 1:
        print("Found no plugins to update!")
        exit(0)
    print("These plugins will be updated:")
    
    
    names_local_newest_version = {} # should contain tuples with three values
    longest_name = 0
    longest_version = 0
    for plugin in to_update:
        if len(plugin.plugin_name) > longest_name:
            longest_name = len(plugin.plugin_name)
        if hasattr(plugin, "local_version"):
            local_version = plugin.local_version.version
        else:
            local_version = "custom"
        if len(local_version) > longest_version:
            longest_version = len(local_version)
        names_local_newest_version[plugin] = (plugin.plugin_name, local_version, get_best_version(plugin).version)
                                            
    for plugin, (name, local_version, newest_version) in names_local_newest_version.items():
        new_name = name + ':' + ' ' * (longest_name - len(name))
        new_version = local_version + ' ' * (longest_version - len(local_version))
        names_local_newest_version[plugin] = (new_name, new_version, newest_version)
        
        
    for plugin, (name, local_version, newest_version) in names_local_newest_version.items():
        print("%s current version: %s\tnewest release: %s" % (name, local_version, newest_version))
        
    if not plugman.utils.confirm(prompt_str="Are you sure you want to update these plugins?"):
        exit(0)
    for plugin in to_update:
        plugman.utils.download(plugin)
    print("Done!")

def remove(args):
    pass # TODO
                
            
def info(args):
    for plugin_name in args.plugins:
        slug = bukget.find_slug('bukkit', plugin_name)
        if slug is None or len(slug) < 1:
            print("Could not find %s on BukGet!" % plugin_name)
            continue
        plugin = bukget.plugin_details('bukkit', slug, size=1)
        if plugin is None:
            print("Could not find %s on BukGet!" % plugin_name)
            continue
        
        print (plugin_info_message % (plugin.plugin_name, get_best_version(plugin).version,
                ", ".join(plugin.authors), 
                ", ".join(plugin.categories), plugin.website, 
                ", ".join(get_best_version(plugin).hard_dependencies), 
                ", ".join(get_best_version(plugin).soft_dependencies)))

