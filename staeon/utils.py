from __future__ import print_function

from staeon.consensus import get_epoch_range
from staeon.emission import emission, total_supply_at

def make_emission_table(to_epoch=100000, accurate=False):
    """
    Make emission table including completely accurate supply.
    """
    cumm = 0
    last = 0

    headers = ['epoch', 'time', 'reward', 'supply', 'added to supply']
    if accurate:
        headers += ['accurate', 'error']

    for x in headers:
        print(x.ljust(19), end="")
    print("", end="\n")

    if not accurate:
        to_iterate = xrange(1, to_epoch, to_epoch/10)
        make_print = lambda epoch: True
    else:
        to_iterate = xrange(1, to_epoch)
        make_print = lambda epoch: epoch % (to_epoch/10.0) == 0

    for epoch in to_iterate:
        if accurate: cumm += emission(epoch)

        if make_print(epoch):
            reward = emission(epoch)
            tsa = total_supply_at(epoch)

            if epoch > 419750000:
                time = "?/?/%d" % ((epoch / 52560.0) + 2019)
            else:
                time = get_epoch_range(epoch)[1].strftime("%m/%d/%Y")

            data = [
                epoch,
                time,
                "%.8f" % reward,
                tsa,
                tsa - last
            ]
            if accurate:
                data += [cumm, tsa - cumm]

            for x in data:
                print(str(x).ljust(19), end="")
            print("", end="\n")

            if accurate:
                last = cumm
            else:
                last = tsa


def get_decimal_activation_epochs(start_epoch=1, end_epoch=9999999):
    """
    Find the epoch at which each decimal place is activated.
    """
    activation_emissions = [
        [8, 100],
        [9, 1.0],
        [10, 0.1],
        [11, 0.01],
        [12, 0.001],
        [13, 0.0001],
        [14, 0.00001]
    ]
    activations = []
    for epoch in xrange(start_epoch, end_epoch):
        target_decimals, target_emission = activation_emissions[len(activations)]
        if raw_emission(epoch) < target_emission:
            print("[%d, %d]" % (target_decimals, epoch))
            activations.append([target_decimals, epoch])
            if len(activations) == len(activation_emissions):
                break
    return activations
