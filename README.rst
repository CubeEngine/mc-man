==========
mc-man
==========

    *The Minecraft server jar and plugin manager, downloader and updater*

mc-man is a terminal program for managing server jars and plugins for Minecraft
servers. It is created with simplicity in mind, and aims to be the definitive
tool to use for server maintenance, for example when updating a server. mc-man
can download and update Spigot, CraftBukkit, MCPC+, BungeeCord and the Mojang
server. It can also download and update plugins, with regards to dependencies.
With *one* command you can update *all* your plugins. There is also features to
export and import servers. They work by saving references to all plugins and
server jars in a json-file, which can later be used to recreate the server.

1.1 - Features
--------

* Update all plugins with one command
* Download plugins with dependency resolution
* All downloads are checked with checksum
* Download and update server jars.

1.2 - Installing
----------
mc-man is programmed in Python for Linux. It can **only** run on Python 3.3 or
newer. This might be a problem on some Linux distributions, but it should
always be possible to build Python from source, if it is not present in your
package manager. Together with python you need the python header files, which
you normally can get through a package called something like ``python3-dev``.
In addition to python you are recommended to have pip - the Python package
manager. Once you have Python 3.3 or newer, and pip for your version of Python,
you can run this command to install mc-man::

    sudo pip3.3 install mc-man

If you are running Python 3.4, ``pip3.3`` should be replaced with ``pip3.4``.
If neither of those commands exists, you can try ``pip3``, but you have to
verify that it leads to a pip version for Python 3.3 or newer.

mc-man has some dependencies which will be installed automatically when
installing using pip:

* ``PyYaml`` - For parsing the yaml files in plugins
* ``pyBukGet`` - For access to the BukGet API
* ``pySpaceGDN`` - For access to the SpaceGDN API

If you install mc-man without pip, you will have to install these dependencies
manually.

1.3 - Usage
-----
The base command for mc-man is ``mcman``, all of mc-man's functionality is
accessible through that command. The command is expected to be run from the
root folder of the server. The functionality is divided into four sub commands:

server
    The server command is used for managing server jars. It can be used to find
    versions and builds, identify jars existing locally and downloading new
    jars.

plugin
    The plugin command is used for managing plugins. It can be used to search
    for plugins, display info about them and their versions, list downloaded
    plugins and check which of them are out of date, update the plugins and, of
    course, download new plugins.

export
    The export command is used for exporting the servers state. It will find
    all downloaded servers and plugins and save their placement, relative to
    the server root, and their versions to a json file. This file can later be
    used by the ``import`` command to create a new server with the same server
    version and plugins.

import
    The import command is used for importing a previously exported server
    state. It will recreate a server with the info from the json file it is
    passed.

These commands can be called with ``mcman <command>``, to manage plugins for
example: ``mcman plugin``. The commands can also be shortened to the first
letter: ``mcman p``. In addition to this comprehensive documentation, a lighter
documentation is included in the program, it can be accessed by adding
``--help`` at the end of any command or subcommand, for example:
``mcman p --help``, to get quick help for the ``plugin`` command.'

1.3.1 - Often used commands
~~~~~~~~~~~~~~~~~~~

Here are some commands that are used often:

``mcman p download <plugin> [<plugin> ...]``
    Download the plugins.

``mcman p update``
    To update all the plugins

``mcman p list``
    To list the installed plugins, and check if any are out of date.

``mcman s identify <server.jar>``
    To check what version and build a server jar is, and see if there are any
    updates to it.

``mcman s download <server> [<channel>] [<version>] [<build>]``
    To download a server, optionally a version from the specified channel, the
    specified version, or even a specific build.

1.3.2 - Common optional arguments for all commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These arguments can be used for all commands in mc-man, but they might not be
implemented where they are not useful. It is noted in the documentation for the
commands when an argument is not implemented.

``-h`` or ``--help``
    To show the help for the current sub command or command.

``--version``
    To print the version of mc-man before the command is executed. If the
    command line is effectless without this argument, the help message will not
    be printed, for example with ``mcman plugin --version`` only the version
    will be printed before the program quits.

``--use-agent <user agent>``
    This argument changes what user agent mc-man reports to the online APIs it
    uses(BukGet and SpaceGDN). It is not recommended to change this for normal
    use, as it gives good statistics to the author about the usage of mc-man.
    However, if you are using mc-man in an auto running script, it is suggested
    to change this.

``--head [<size>]`` or ``--size [<size>]`` and ``--tail [<size>]``
    These arguments will limit how many results that are returned. The usage
    changes a bit between different commands, but the general rule is that
    ``--tail`` will sort bottom -> up, and ``--head`` or ``--size`` will sort
    top -> bottom. ``--head`` and ``--tail`` can be used without an argument to
    use the default value 5.

``--no-confirm``
    Will skip all confirmation. Works everywhere you are asked to confirm
    something in mc-man.

1.3.3 - The server command
~~~~~~~~~~~~~~~~~~

Comprehensive documentation is coming, for now you are advised to use the built
in help. For example ``mcman server --help`` or ``mcman server servers --help``

1.3.4 - The plugin command
~~~~~~~~~~~~~~~~~~

Comprehensive documentation is coming, for now you are advised to use the built
in help. For example ``mcman plugin --help`` or ``mcman plugin search --help``

1.3.5 - The import command
~~~~~~~~~~~~~~~~~~

Comprehensive documentation is coming, for now you are advised to use the built
in help. For example ``mcman import --help``

The export command
~~~~~~~~~~~~~~~~~~

Comprehensive documentation is coming, for now you are advised to use the built
in help. For example ``mcman export --help``
