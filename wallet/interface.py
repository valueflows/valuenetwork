from abc import ABCMeta, abstractmethod, abstractproperty

class AbstractGateway(object):
    """
    This properties and methods must be rewritten:
    gateway_name, currency, get_balance, get_history, send_funds
    """

    __metaclass__ = ABCMeta

    @classmethod
    def get(cls):
        return cls()

    @abstractproperty
    def gateway_name(self): pass

    @abstractproperty
    def currency(self): pass

    # About @abstractmethod decorator: when this abstract class is extended,
    # this method must be rewritten, but it doesn't freeze the prototype,
    # so it can be implemented with any argument list.

    @abstractmethod
    def get_balance(self):
        """
        Define how the gateway gets the current balance.
        """
        pass

    @abstractmethod
    def get_history(self):
        """
        Define how the gateway gets last bank movements.
        """
        pass

    @abstractmethod
    def send_funds(self):
        """
        Define how the gateway sends funds.
        """
        pass
