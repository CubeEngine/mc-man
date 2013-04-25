import bukget.api, bukget.plugin
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('plugins', metavar='Plugin', type=str, nargs='+', help='Plugin to process')
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-D", "--Download", help="Download and install the plugin(s)", action="store_true")
    group.add_argument("-U", "--Update", help="Update the plugin(s)", action="store_true")
    group.add_argument("-R", "--Remove", help="Remove the plugin(s)", action="store_true")
    group.add_argument("-I", "--Info", help="Get info about the plugin(s)", action="store_true")
    parser.add_argument("--verbose", help="increase output verbosity", action="store_true")
    parser.add_argument("-f", "--force", help="Force install a plugin, even if the dependencies is not found",
                        action="store_true")
    parser.add_argument("--ignore-deps", help="Ignore the dependencies", action="store_true")
    args = parser.parse_args()

