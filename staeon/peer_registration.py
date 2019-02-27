import datetime
from bitcoin import ecdsa_verify, ecdsa_recover, ecdsa_sign, pubtoaddr, privtoaddr

from .exceptions import InvalidSignature
from .consensus import validate_timestamp
import dateutil.parser

def make_peer_registration(pk, domain):
    timestamp = datetime.datetime.now().isoformat()
    address = privtoaddr(pk)
    to_sign = "%s%s%s" % (domain, address, timestamp)
    return {
        'domain': domain,
        'payout_address': address,
        'timestamp': timestamp,
        'signature': ecdsa_sign(to_sign, pk)
    }

def validate_peer_registration(reg, now=None):
    ts = dateutil.parser.parse(reg['timestamp'])
    validate_timestamp(ts, now=now)

    to_sign = "{domain}{payout_address}{timestamp}".format(**reg)
    try:
        pubkey = ecdsa_recover(to_sign, reg['signature'])
    except:
        raise InvalidSignature("Can't recover pubkey from signature")

    valid_address = pubtoaddr(pubkey) == reg['payout_address']
    valid_sig = ecdsa_verify(to_sign, reg['signature'], pubkey)

    if not valid_sig or not valid_address:
        raise InvalidSignature("Invalid Signature")
    return True
