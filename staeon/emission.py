from math import atan as arctan, sqrt, log as ln

def offline_penalty(percentile):
    return 5 + (percent ** 2) / 146

def online_reward(percentile):
    return 30 - (percent ** 2) / 546

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
    template = "%%.%df" % get_decimals_for_epoch(epoch)
    return float(template % raw_emission(epoch))

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

def get_decimals_for_epoch(epoch=None, reward=None):
    """
    Given an epoch or reward amount, return the amount of decimals that
    reward should be cut to.
    """
    if not reward: reward = raw_emission(epoch)
    if reward >= 1.0:
        return 8

    target = 0.1
    decimals = 9
    for x in range(100):
        if reward >= target:
            return decimals
        decimals += 1
        target /= 10
