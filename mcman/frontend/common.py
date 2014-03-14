""" Common things for plugins_command and servers_command.

This module contains the classes 'UknownSubcommandException' and 'Command'.

The Command class is intended to be subclassed by all commands in mcman. The
class provides basic output methods, and handling of subcommands.

The UknownSubcommandException is an Exception that may be raised by certain
methods in the Command class.

"""


class UknownSubcommandException(BaseException):

    """ An exception raised by Command when a subcommand isn't found. """

    def __init__(self, subcommand):
        """ Initialize an exception.

        This initializer requires one parameter:
            subcommand    The subcommand that was not found.

        """
        BaseException.__init__('Could not find subcommand {}'
                               .format(subcommand))
        self.subcommand = subcommand


class Command(object):

    """ A common Command class.

    Intended for use by the servers and plugins commands. It provieds methods
    to output things nicely, and registering and invoking of sub commands.

    """

    def __init__(self, prefix=' :: ', printer=print):
        """ Initialize this command.

        This method sets the prefix, and creates a matching empty prefix,
        that just contains spaces.

        Up to two parameters are accepted:
            prefix=' :: '    The prefix.
            printer=print    The method used to build. This must support some
                             of the same parameters as python's built in print
                             most notably: A named 'sep', passing of multiple
                             strings.

        """
        self.printer = printer

        self.f_prefix = prefix
        self.e_prefix = ' ' * len(prefix)

        self.subcommands = dict()

    def p_main(self, message, frmt=None):
        """ Print a main line.

        A main line has the prefix before it.
        This method takes up to to arguments:
            message      The message to print.
            frmt=None    A format to format the message by.
                         This is passed to message.format()

        """
        self.p_raw(self.f_prefix, message.format(frmt), sep='')

    def p_sub(self, message, frmt=None):
        """ Print a sub line.

        A sub line is the 'child' of a main line. It is intended with the same
        lenght as the prefix, but with tabs.
        This method takes up to to arguments:
            message      The message to print.
            frmt=None    A format to format the message by.
                         This is passed to message.format()

        """
        self.p_raw(self.e_prefix, message.format(frmt), sep='')

    def p_blank(self):
        """ Print a blank line. """
        self.p_raw()

    def p_raw(self, *args, **kwargs):
        """ Print directly to the printer. """
        self.printer(*args, **kwargs)

    def register_subcommand(self, name, method):
        """ Register a subcommand.

        It will be stored by the name, and it can later be invoked by doing
        'self.invoke_subcommand(name)'.

        This method accepts two parameters:
            name      The name of the subcommand.
            method    The method that contains this subcommand.
                      The  method may only accept the 'self' parameter.

        """
        self.subcommands[name] = method

    def invoke_subcommand(self, name, exceptions):
        """ Invoke a subcommand.

        This method will invoke a previously registered subcommand, by the
        name. It will also catch the specified tuple of exceptions and just
        display them as errors, without a stack trace.

        two parameters are accepted:
            name          The name of the subcommand to invoke.
            exceptions    A tuple of exceptions to be catched

        Exceptions raised:
            UknownSubcommandException    If the subcommand wasn't found or
                                         registered.

        Additionally any exception may be raised by the subcommand invoked.

        """
        if not name in self.subcommands:
            raise UknownSubcommandException(name)
        else:
            try:
                self.subcommands[name]()
            except UknownSubcommandException as err:
                self.p_main('Could not find subcommand {}'.format(
                    err.subcommand))
            except exceptions as err:
                self.p_sub('Error: {}'.format(str(err)))
