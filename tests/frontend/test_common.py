""" Tests for frontend.common.py. """
from unittest import TestCase
from unittest.mock import MagicMock
from mcman.frontend import common


class TestCommand(TestCase):

    """ Tests for mcman.frontend.common.Command. """

    def setUp(self):
        self.command = common.Command(printer=self.printer)
        self.line = None

    def printer(self, *value, sep=' ', end='\n'):
        if self.line is None or self.line.endswith('\n'):
            self.line = sep.join(value) + end
        else:
            self.line += sep.join(value) + end

    def test_printers(self):
        """ Test the print functions in Command. """
        self.command.p_main('Hello {}', 'there')
        assert self.line == ' :: Hello there\n'

        self.command.p_sub('Hello {}', 'there')
        assert self.line == '    Hello there\n'

        self.command.p_blank()
        assert self.line == '\n'

        self.command.p_raw('Herp, derp')
        assert self.line == 'Herp, derp\n'

    def test_sub_commands_normal(self):
        """ Test the sub command behaviour of Command with a normal run. """
        mock = MagicMock()
        self.command.register_subcommand('herp', mock)
        self.command.invoke_subcommand('herp')
        mock.assert_called_once_with()

    def test_sub_commands_owerride(self):
        """ Test the sub command behaviour of Command with overriding. """
        mock1 = MagicMock()
        mock2 = MagicMock()
        self.command.register_subcommand('herp', mock1)
        self.command.register_subcommand('herp', mock2)
        self.command.invoke_subcommand('herp')
        assert not mock1.called
        mock2.assert_called_once_with()

    def test_subcommands_not_found(self):
        """ Test the sub command behaviour of Command when command doesn't \
        exist. """
        try:
            self.command.invoke_subcommand('not_found', True)
        except common.UknownSubcommandException:
            assert True
        else:
            assert False

    def test_subcommands_expected_exceptions(self):
        """ Test the sub command behaviour of Command with expected \
        exceptions. """
        exception = KeyError('herp, derp')
        mock = MagicMock(side_effect=exception)
        self.command.register_subcommand('herp', mock)
        self.command.invoke_subcommand('herp', type(exception))
        assert self.line.endswith(str(exception) + '\n')
