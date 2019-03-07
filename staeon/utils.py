from __future__ import print_function

from staeon.consensus import get_epoch_range
from staeon.network import emission, total_supply_at

def make_emission_table(to_epoch=100000, fast=True):
    """
    Make emission table including completely accurate supply.
    """
    cumm = 0
    last = 0

    headers = ['epoch', 'time', 'reward', 'supply', 'added to supply']
    if not fast:
        headers += ['accurate', 'error']

    for x in headers:
        print(x.ljust(19), end="")
    print("", end="\n")

    if fast:
        to_iterate = xrange(1, to_epoch, to_epoch/10)
        make_print = lambda epoch: True
    else:
        to_iterate = xrange(1, to_epoch)
        make_print = lambda epoch: epoch == 1 or epoch % (to_epoch/10.0) == 0

    for epoch in to_iterate:
        if not fast: cumm += emission(epoch)

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
            if not fast:
                data += [cumm, tsa - cumm]

            for x in data:
                print(str(x).ljust(19), end="")
            print("", end="\n")
            if not fast:
                last = cumm
            else:
                last = tsa
