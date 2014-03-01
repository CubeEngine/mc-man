""" mcman servers module. """


class Servers(object):

    """ The servers command for mcman. """

    def __init__(self, args):
        """ Parse commands, and execute tasks. """
        self.args = args
        if args.subcommand is 'servers':
            self.servers()
        elif args.subcommand is 'channels':
            self.channels()
        elif args.subcommand is 'versions':
            self.versions()
        elif args.subcommand is 'download':
            self.download()
        elif args.subcommand is 'identify':
            self.identify()
        else:
            return

    def servers(self):
        """ List servers. """
        print('The SpaceGDN API is not yet stable, '
              + 'and therefore not implemented yet.')
        print(self.args)

    def channels(self):
        """ List channels. """
        print('The SpaceGDN API is not yet stable, '
              + 'and therefore not implemented yet.')
        print(self.args)

    def versions(self):
        """ List versions. """
        print('The SpaceGDN API is not yet stable, '
              + 'and therefore not implemented yet.')
        print(self.args)

    def download(self):
        """ Download a server. """
        print('The SpaceGDN API is not yet stable, '
              + 'and therefore not implemented yet.')
        print(self.args)

    def identify(self):
        """ Identify what server a jar is. """
        print('The SpaceGDN API is not yet stable, '
              + 'and therefore not implemented yet.')
        print(self.args)
