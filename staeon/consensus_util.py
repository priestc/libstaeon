import datetime
from bitcoin import ecdsa_verify, ecdsa_recover, ecdsa_sign, pubtoaddr, privtoaddr
from .exceptions import *

from .network import *

def get_epoch_range(n):
    """
    Given an epoch number, returns the start and end times for that epoch.
    """
    start =  GENESIS + datetime.timedelta(seconds=EPOCH_LENGTH_SECONDS * n)
    return start, start + datetime.timedelta(minutes=10)

def get_epoch_number(time):
    """
    For a given time, returns which epoch number that date falls in.
    """
    delta = time - GENESIS
    return int("%d" % (delta.total_seconds() / EPOCH_LENGTH_SECONDS))

def seconds_til_next_epoch(t):
    """
    How many seconds from passed in datetime object does the next epoch start?
    """
    return EPOCH_LENGTH_SECONDS - (
        ((t.minute % 10) * 60) + t.second + (t.microsecond / 1000000.0)
    )

def validate_timestamp(ts, now=None):
    if seconds_til_next_epoch(ts) < EPOCH_CLOSING_SECONDS:
        raise InvalidTimestamp("Within closing interval")
    if not now:
        now = datetime.datetime.now()
    if ts - now < datetime.timedelta(seconds=PROPAGATION_WINDOW_SECONDS):
        raise ExpiredTimestamp("Propagation window exceeded")
    return True


def validate_ledger_hash_push(payout_address, ledger_hash, domain, sig):
    """
    Validates that the ledger hash push is indeed signed by the pusher.
    """
    msg = "%s%s" % (ledger_hash, domain)
    try:
        pubkey = ecdsa_recover(msg, sig)
    except:
        raise Exception("Can't recover pubkey from signature")

    if not pubtoaddr(pubkey) == payout_address:
        raise Exception("Incorrect signing key")

    if not ecdsa_verify(msg, sig, pubkey):
        raise Excception("Invalid Signature")

    return True
