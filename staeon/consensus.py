from __future__ import print_function

import sys
import datetime
import hashlib
from concurrent import futures
import json
import requests

from bitcoin import ecdsa_verify, ecdsa_recover, ecdsa_sign, pubtoaddr, privtoaddr
from .exceptions import *

from .network import *

def get_epoch_range(n=None):
    """
    Given an epoch number, returns the start and end times for that epoch.
    """
    if not n: n = get_epoch_number()
    start =  GENESIS + datetime.timedelta(seconds=EPOCH_LENGTH_SECONDS * n)
    return start, start + datetime.timedelta(minutes=10)

def get_epoch_number(time=None):
    """
    For a given time, returns which epoch number that date falls in.
    """
    if not time: time = datetime.datetime.now()
    delta = time - GENESIS
    return int("%d" % (delta.total_seconds() / EPOCH_LENGTH_SECONDS))

def seconds_til_next_epoch(t):
    """
    How many seconds from passed in datetime object does the next epoch start?
    """
    assert EPOCH_LENGTH_SECONDS == 600
    return EPOCH_LENGTH_SECONDS - (
        ((t.minute % 10) * 60) + t.second + (t.microsecond / 1000000.0)
    )

def validate_timestamp(ts, now=None):
    assert type(ts) == datetime.datetime, "Timestamp must be datetime object"
    if seconds_til_next_epoch(ts) < EPOCH_CLOSING_SECONDS:
        raise InvalidTimestamp("Within closing interval")
    if not now:
        now = datetime.datetime.now()
    if now - ts > datetime.timedelta(seconds=PROPAGATION_WINDOW_SECONDS):
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

def propagate_rejection(tx, exc, my_node, nodes):
    my_domain = my_node['domain']
    msg = "%s%s" % (tx['txid'], my_domain)
    rejection = json.dumps({
        'domain': my_domain,
        'txid': tx['txid'],
        'signature': ecdsa_sign(msg, my_node['private_key']),
        'reason': exc.display()
    })
    for node in nodes:
        url = "https://%s/staeon/rejection" % (node['domain'])
        try:
            response = requests.post(url, rejection)
        except:
            print("%s failed" % url)

def validate_rejection_authorization(authorization):
    message = "%s%s" % (authorization['txid'], authorization['domain'])
    sig = authorization['signature']
    try:
        pubkey = ecdsa_recover(message, sig)
    except:
        raise InvalidSignature("Can't recover pubkey from rejection signature")

    valid_sig = ecdsa_verify(message, sig, pubkey)
    valid_address = pubtoaddr(pubkey) == authorization['payout_address']

    if not valid_sig or not valid_address:
        raise InvalidSignature("Rejection signature not valid" % i)

    return True


def deterministic_shuffle(items, seed, n=0, sort_key=lambda x: x):
    sorter = lambda x: hashlib.sha256(sort_key(x) + seed + str(n)).hexdigest()
    return sorted(items, key=sorter)


def propagate_to_peers(domains, obj=None, type="tx"):
    url_template = "http://%s/%s"
    post_data = {'obj': json.dumps(obj)}
    sender = lambda url: requests.post(url, post_data)
    
    with futures.ThreadPoolExecutor(max_workers=len(domains)) as executor:
        fetches = {}
        for domain in domains:
            url = url_template % (domain, type)
            fetches[executor.submit(sender, url=url)] = url

    return fetches
