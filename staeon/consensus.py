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

def validate_sig(sig, msg, address, type="transaction"):
    try:
        pubkey = ecdsa_recover(msg, sig)
    except:
        raise InvalidSignature("Can't recover pubkey from %s signature" % type)

    valid_sig = ecdsa_verify(msg, sig, pubkey)
    valid_address = pubtoaddr(pubkey) == address

    if not valid_sig or not valid_address:
        raise InvalidSignature("%s signature not valid" % type.title())

    return True

def make_transaction_rejection(tx, exc, my_domain, my_pk):
    msg = "%s%s" % (tx['txid'], my_domain)
    return {
        'domain': my_domain,
        'txid': tx['txid'],
        'signature': ecdsa_sign(msg, my_pk),
        'reason': exc.display()
    }

def validate_rejection_authorization(domain, txid, sig, payout_address):
    return validate_sig(
        sig, "%s%s" % (txid, domain), payout_address, "rejection"
    )

def deterministic_shuffle(items, seed, n=0, sort_key=lambda x: x):
    sorter = lambda x: hashlib.sha256(sort_key(x) + seed + str(n)).hexdigest()
    return sorted(items, key=sorter)

def make_matrix(items, seed, sort_key=lambda x: x, width=5, n=5):
    rows = []
    for x in range(n):
        rows.append([
            deterministic_shuffle(items, seed, i, sort_key)
            for i in range(width * x, width * (x+1))
        ])

    return rows

def make_ledger_push(epoch, my_domain, my_pk, mini_hashes):
    msg = "%s%s%s" % (my_domain, "".join(mini_hashes), epoch)
    return {
        'epoch': epoch,
        'domain': my_domain,
        'hashes': mini_hashes,
        'signature': ecdsa_sign(msg, my_pk)
    }

def validate_ledger_push(domain, epoch, hashes, sig, payout_address, now=None):
    msg = "%s%s%s" % (domain, "".join(hashes), epoch)
    if not now: now = datetime.datetime.now()
    epoch_start = get_epoch_range(epoch)[0]
    if now < epoch_start:
        raise InvalidObject("Epoch Hash too early")
    if now > epoch_start + EPOCH_HASH_PUSH_WINDOW_SECONDS:
        raise InvalidObject("Epoch Hash too late")
    return validate_sig(sig, msg, payout_address, "ledger push")

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

def make_epoch_seed(epoch_tx_count, ledger_count, sorted_ledger, address_from_ledger):
    """
    epoch_tx_count = number of transactions made in a given epoch
    ledger_count = the total number of ledger entries in the ledger database.
    sorted_ledger = iterable that returns the nth ledger item. Must be sorted by
                    amount and then address.
    address_from_ledger = callable that returns the address from the ledger entry
                          returned by sorted_ledger
    """
    index = epoch_tx_count % ledger_count
    return hashlib.sha256(
        str(epoch_tx_count) + address_from_ledger(sorted_ledger[index])
    ).hexdigest()
