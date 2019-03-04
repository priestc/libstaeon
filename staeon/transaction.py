import datetime
import random
import hashlib

import dateutil.parser
from bitcoin import (
    ecdsa_verify, ecdsa_recover, ecdsa_sign, pubtoaddr, privtoaddr, is_address
)

from .consensus import validate_timestamp
from .exceptions import *
from .network import PROPAGATION_WINDOW_SECONDS

def _cut_to_8(amount):
    "Cut decimals to 8 places"
    return float("%.8f" % amount)

def _process_outputs(outputs, timestamp):
    total_out = 0
    outs = []
    for out in sorted(outputs, key=lambda x: x[0]):
        address, amount = out
        if amount != _cut_to_8(amount):
            raise InvalidAmounts(
                "Output amounts limited to 8 decimal places: %s" % amount
            )

        if amount <= 0:
            raise InvalidAmounts("Output can't be zero or negative")
        total_out += amount

        outs.append("%s,%s" % (address, amount))

        if not is_address(address) or not address.startswith("1"):
            raise InvalidAddress("Invalid address: %s" % address)

    if type(timestamp) == datetime.datetime:
        timestamp = timestamp.isoformat()

    return total_out, ";".join(outs + [timestamp])

def make_transaction(inputs, outputs):
    timestamp = datetime.datetime.now().isoformat()
    out_total, out_msg = _process_outputs(outputs, timestamp)

    tx = {'inputs': [], 'outputs': [], 'timestamp': timestamp}

    in_total = 0
    for in_ in inputs:
        try:
            address, amount, privkey = in_
        except ValueError:
            raise Exception("Transaction inputs must be a 3 item list: [address, amount, privkey]")

        if amount <= 0:
            raise InvalidAmounts("Input can't be zero or negative")
        amount = _cut_to_8(amount)
        msg = "%s%s%s" % (address, amount, out_msg)
        sig = ecdsa_sign(msg, privkey)
        in_total += amount
        tx['inputs'].append([address, amount, sig])

    if in_total < out_total:
        raise InvalidAmounts(
            "Not enough inputs for outputs: %s in, %s out" % (in_total, out_total)
        )

    random.shuffle(outputs)
    tx['outputs'] = outputs
    return tx

def validate_transaction(tx, ledger=None, min_fee=0.01, now=None):
    """
    Validates that the passed in transaction object is valid in terms of
    cryptography. UTXO validation does not happen here.
    `ledger` is a callable that returns the address's balance and last spend timestamp.
    """
    ts = dateutil.parser.parse(tx['timestamp'])
    out_total, out_msg = _process_outputs(tx['outputs'], ts)
    validate_timestamp(ts, now=now)

    in_total = 0
    for i, input in enumerate(tx['inputs']):
        address, amount, sig = input
        amount = _cut_to_8(amount)
        if amount <= 0:
            raise InvalidAmounts("Input %s can't be zero or negative" % i)

        message = "%s%s%s" % (address, amount, out_msg)
        in_total += amount
        try:
            pubkey = ecdsa_recover(message, sig)
        except:
            raise InvalidSignature("Signature %s not valid" % i)

        if ledger:
            address_balance, last_spend = ledger(address)
            delt = datetime.timedelta(seconds=PROPAGATION_WINDOW_SECONDS)
            if last_spend + delt > ts:
                raise InvalidTransaction("Input too young")
            if address_balance < amount:
                raise InvalidAmounts("Not enough balance in %s" % address)

        valid_sig = ecdsa_verify(message, sig, pubkey)
        valid_address = pubtoaddr(pubkey) == address
        if not valid_sig or not valid_address:
            raise InvalidSignature("Signature %s not valid" % i)

    if in_total < out_total:
        raise InvalidAmounts("Input amount does not exceed output amount")

    fee = in_total - out_total
    if fee < min_fee:
        raise InvalidFee("Fee of %.8f below min fee of %.8f" % (fee, min_fee))

    return True

def make_txid(tx):
    msg = tx['timestamp']
    for output in tx['outputs']:
        address, amount = output
        msg += address + "%.8f" % amount

    for input in tx['inputs']:
        address, amount, sig = input
        msg += "%s%s" % (address, amount)

    return hashlib.sha256(msg).hexdigest()
