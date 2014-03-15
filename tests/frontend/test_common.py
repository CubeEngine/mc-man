""" Tests for frontend.common.py. """
from mcman.frontend import common


class PrintFetcher(object):

    def __init__(self):
        self.line = None

    def print(self, *value, sep=' ', end='\n'):
        self.line = sep.join(value) + end

    def get_line(self):
        return self.line


def test_command_printers():
    printer = PrintFetcher()
    command = common.Command(printer=printer.print)

    command.p_main('Hello {}', 'there')
    assert printer.get_line() == ' :: Hello there\n'

    command.p_sub('Hello {}', 'there')
    assert printer.get_line() == '    Hello there\n'

    command.p_blank()
    assert printer.get_line() == '\n'

    command.p_raw('Herp, derp')
    assert printer.get_line() == 'Herp, derp\n'


def test_command_commands():
    # TODO
    pass
