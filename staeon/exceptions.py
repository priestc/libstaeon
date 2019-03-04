class BaseException(Exception):
    def display(self):
        return "%s: %s" % (self.__class__, str(self))

class InvalidObject(BaseException):
    pass

class RejectedObject(BaseException):
    pass

class InvalidTransaction(InvalidObject):
    pass

class RejectedTransaction(RejectedObject):
    pass

class PotentialDoubleSpend(RejectedTransaction):
    pass

class ExpiredTimestamp(RejectedObject):
    pass

class InvalidSignature(InvalidObject):
    pass

class InvalidAmounts(InvalidTransaction):
    pass

class InvalidAddress(InvalidTransaction):
    pass

class InvalidFee(InvalidTransaction):
    pass

class InvalidTimestamp(InvalidObject):
    pass
