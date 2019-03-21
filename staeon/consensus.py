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

class EpochHashPush(object):
    @classmethod
    def make(cls, epoch, from_domain, to_domain, from_pk, hashes):
        msg = "%s%s%s%s" % (from_domain, to_domain, "".join(hashes), epoch)
        return {
            'epoch': epoch,
            'from_domain': from_domain,
            'to_domain': to_domain,
            'hashes': hashes,
            'signature': ecdsa_sign(msg, from_pk)
        }

    def __init__(self, obj, payout_address):
        self.obj = obj
        self.payout_address = payout_address

    def validate(self, validate_expired=True):
        if validate_expired:
            self._validate_expired()
        msg = "%s%s%s%s" % (
            self.obj['from_domain'], self.obj['to_domain'],
            "".join(self.obj['hashes']), self.obj['epoch']
        )
        return validate_sig(
            self.obj['signature'], msg, self.payout_address, "ledger push"
        )

    def _validate_expired(self, now=None):
        delt = datetime.timedelta(seconds=EPOCH_HASH_PUSH_WINDOW_SECONDS)
        if not now: now = datetime.datetime.now()
        epoch_start = get_epoch_range(self.obj['epoch'])[0]
        if now < epoch_start:
            raise InvalidObject("Epoch Hash too early")
        if now > epoch_start + delt:
            raise InvalidObject("Epoch Hash too late")

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

def make_mini_hashes(seed, limit=5):
    mini_hashes = []
    for x in range(limit):
        seed = hashlib.sha256(seed).hexdigest()
        mini_hashes.append(seed[:8])
    return mini_hashes

class NodePenalization(object):
    @classmethod
    def _make_reason(self, wrong):
        return "%s%s%s%s" % (
            wrong['from_domain'], wrong['to_domain'], wrong['hashes'],
            wrong['epoch'], wrong['signature'],
        ) if wrong else "No Push"

    @classmethod
    def make(cls, real_hash, wrong_push, my_pk):
        msg = "%s%s" % (
            real_hash, cls._make_reason(wrong_push)
        )
        return {
            'epoch': epoch,
            'real_hash': real_hash,
            'wrong': wrong_push,
            'signature': ecdsa_sign(msg, my_pk)
        }

    def __init__(self, obj, payout_address, from_payout_address):
        self.obj = obj
        self.from_payout_address = from_payout_address
        self.payout_address = payout_address

    def validate(self):
        if obj['wrong']:
            EpochHashPush(obj['wrong'], self.from_payout_address).validate()
        reason = NodePenalization._make_reason(self.wrong_push)
        msg = "%s%s%s%s" % (self.epoch, self.real_hash, reason)
        return validate_sig(
            obj['signature'], msg, self.payout_address, "node penalization"
        )
