import bukget.api
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
        slug = bukget.api.get_slug(plugin_name)
        if slug is None or len(slug) < 1:
            print("Could not find %s on BukGet!" % plugin_name)
            continue
        plugin = bukget.api.get_plugin(slug, size=1)
        if plugin is None:
            print("Could not find %s on BukGet!" % plugin_name)
            continue
        to_install.add(plugin)
        to_install = to_install.union(plugin.get_hard_dependencies())
    print("These plugins will be installed: " + " ".join([i.name for i in to_install]))
    if not plugman.utils.confirm(prompt_str="Are you sure you want to install them?"):
        exit(0)
    for plugin in to_install:
        print("Pretending to install %s" % plugin.name)
    print("Done!")
     

def update(args):
    pass

def remove(args):
    pass

def info(args):
    for plugin_name in args.plugins:
        slug = bukget.api.get_slug(plugin_name)
        if slug is None or len(slug) < 1:
            print("Could not find %s on BukGet!" % plugin_name)
            continue
        plugin = bukget.api.get_plugin(slug, size=1)
        if plugin is None:
            print("Could not find %s on BukGet!" % plugin_name)
            continue
        
        print (plugin_info_message % (plugin.name, plugin.newest_version.number,
                ", ".join(plugin.authors), 
                ", ".join(plugin.categories), plugin.website, 
                ", ".join(plugin.newest_version.hard_dependencies), 
                ", ".join(plugin.newest_version.soft_dependencies)))

