""" Test for status_handler.py. """
from mcman.status_handler import StatusHandler


def test_handler_tuple():
    """ Test StatusHandler with tuples. """
    def one(arguments):
        """ First handler. """
        assert arguments[0] == 'test'
        assert arguments[1] == 'tset'

    def two(arguments):
        """ Second handler. """
        assert arguments[0] == 'herp'
        assert arguments[1] == 'preh'

    handler = StatusHandler()
    handler.register_handler(2, two)
    handler.register_handler(1, one)

    hook = handler.get_hook()
    hook(1, ('test', 'tset'))
    hook(2, ('herp', 'preh'))


def test_handler_single_value():
    """ Test StatusHandler with single value. """
    def one(arguments):
        """ First handler. """
        assert arguments == 'test'

    def two(arguments):
        """ Second handler. """
        assert arguments == 'herp'

    handler = StatusHandler()
    handler.register_handler(1, one)
    handler.register_handler(2, two)

    hook = handler.get_hook()
    hook(1, 'test')
    hook(2, 'herp')


def test_handler_overwrite():
    """ Test StatusHandler with overwriting of handlers. """
    def overwritten(arguments):
        """ Handler that should be overwritten. """
        assert False

    success = lambda arguments: None

    handler = StatusHandler()
    handler.register_handler(1, overwritten)
    handler.register_handler(1, success)

    hook = handler.get_hook()
    hook(1, None)


def test_handler_no_handler():
    """ Test StatusHandler with missing handler. """
    handler = StatusHandler()
    try:
        handler.get_hook()(1, None)
    except ValueError:
        assert True
    else:
        assert False
