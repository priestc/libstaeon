import datetime
from math import atan as arctan, sqrt, log as ln

# network-wide settings
GENESIS = datetime.datetime(2019, 2, 14, 10, 0)
EPOCH_LENGTH_SECONDS = 600
EPOCH_CLOSING_SECONDS = 10
PROPAGATION_WINDOW_SECONDS = 10
SEED_NODES = ['staeon.com', 'staeon.org']

def emission(epoch):
    """
    returns the block reward for given epoch.
    """
    return 139899456000000000.0 / (
        10000 * epoch**2 + 18779955400 * epoch + 2897490120649729.0
    )

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
