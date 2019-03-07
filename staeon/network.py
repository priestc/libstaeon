import datetime
from math import atan as arctan, sqrt, log as ln

# network-wide settings
GENESIS = datetime.datetime(2019, 2, 14, 10, 0)
EPOCH_LENGTH_SECONDS = 600
EPOCH_CLOSING_SECONDS = 10
PROPAGATION_WINDOW_SECONDS = 10
SEED_NODES = ['staeon.com', 'staeon.org']
DECIMAL_ACTIVATION_POINTS = [
    [8, 1], # 2019 AD
    [9, 2879631], # 2073 AD
    [10, 10913911], # 2226 AD
    [11, 36472052], # 2712 AD
    [12, 117342635], # 4250 AD
    [13, 373093151], # 9112 AD
    [14, 1181852257] # 24504 AD
]
def raw_emission(epoch):
    """
    Returns the block reward for given epoch,
    not catenated with appropriate decimals
    """
    return 139899456000000000.0 / (
        10000 * epoch**2 + 18779955400 * epoch + 2897490120649729.0
    )

def emission(epoch):
    """
    Epoch award, catenated to the appropriate decimal places.
    """
    raw = raw_emission(epoch)
    template = "%%.%df" % get_decimals_for_epoch(epoch)
    return float(template % raw)

def total_supply_at(epoch):
    """
    Calculates the approximate total amount of staeon in existence at passed
    in epoch.
    """
    sq = sqrt(4555)
    return 21000007.03472 + (
        11658288000.0 * ln(
            abs(100 * epoch - 1140000 * sq + 93899777) / abs(100 * epoch + 1140000 * sq + 93899777)
        )
    ) / (19 * sq) + (emission(epoch) / 2)

def get_decimals_for_epoch(epoch):
    ret = None
    for decimal_count, activation_epoch in DECIMAL_ACTIVATION_POINTS:
        if epoch >= activation_epoch:
            ret = decimal_count
        else:
            break
    return ret
