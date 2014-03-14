""" Status Handler. """


class StatusHandler(object):

    """ Status Handler.

    A status handler can register functions to run when a status is sent.

    """

    def __init__(self):
        """ Initialize. """
        self.statuses = dict()

    def register_handler(self, key, function):
        """ Register a handler. """
        self.statuses[key] = function

    def get_hook(self):
        """ Get the status hook. """
        def invoke(key, arguments):
            """ Invoke an handler. """
            if key in self.statuses:
                self.statuses[key](arguments)
            else:
                print('No handler found for key {}'.format(key))

        return invoke
