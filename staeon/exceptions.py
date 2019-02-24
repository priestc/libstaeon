class BaseException(Exception):
    def display(self):
        return "%s: %s" % (self.__class__, str(self))

class InvalidTransaction(BaseException):
    pass

class RejectedTransaction(BaseException):
    pass

class PotentialDoubleSpend(RejectedTransaction):
    pass

class ExpiredTransaction(RejectedTransaction):
    pass

class InvalidSignature(InvalidTransaction):
    pass

class InvalidAmounts(InvalidTransaction):
    pass

class InvalidAddress(InvalidTransaction):
    pass

class InvalidFee(InvalidTransaction):
    pass

class InvalidTimestamp(InvalidTransaction):
    pass
