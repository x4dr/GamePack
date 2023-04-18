import math
import time

from gamepack.DiceParser import DiceParser


def montecarlo(roll):
    p = DiceParser()
    occurences = {}
    time0 = time.time()
    while time.time() - time0 < 10:
        for _ in range(1000):
            r = p.do_roll(roll).result
            occurences[r] = occurences.get(r, 0) + 1
    return f"from {sum(occurences.values())} results:\n{plot(occurences)}"


def plot(data, showsucc=False, showgraph=True, showdmgmods=False, grouped=1):
    success = sum(v for k, v in data.items() if k > 0)
    zeros = sum(v for k, v in data.items() if k == 0)
    botches = sum(v for k, v in data.items() if k < 0)
    total = sum(v for k, v in data.items())
    res = ""
    pt = total / 100
    width = 1
    highest = 0
    if showsucc:
        res += (
            "Of the %d rolls, %d were successes, "
            "%d were failures and %d were botches, averaging %.2f\n"
            % (
                total,
                success,
                zeros,
                botches,
                (sum(k * v for k, v in data.items()) / total),
            )
        )
        res += "The percentages are:\n+ : %f.3%%\n0 : %f.3%%\n- : %f.3%%\n" % (
            success / pt,
            zeros / pt,
            botches / pt,
        )

        barsuc = int((success / pt) / width)
        barbot = int((botches / pt) / width)
        barzer = int(100 / width - barsuc - barbot)
        res += "+" * barsuc + "0" * barzer + "-" * barbot + "\n"
    if showgraph:
        lowest = min(data.keys())
        highest = max(data.keys())
        width = (
            1
            / 60
            * max(
                int(data[i] / pt) if i in data else 0
                for i in range(lowest, highest + 1)
            )
        )
        for i in range(lowest, highest + 1):
            if i == 0 and showsucc:
                res += "\n"
            if i not in data.keys():
                data[i] = 0
            if grouped == 1:
                if data[i] or data.get(i + 1, None) or data.get(i - 1, None):
                    res += "%2d : %7.3f%% " % (i, data[i] / pt)
            else:
                res += "%2d-%2d : %7.3f%% " % (
                    i * grouped,
                    (i + 1) * grouped - 1,
                    data[i] / pt,
                )
            if data[i] or data.get(i + 1, None) or data.get(i - 1, None):
                res += "#" * int((data[i] / pt) / width) + "\n"
            if i == 0 and showsucc:
                res += "\n"
    if showdmgmods:
        res += "dmgmods(adjusted):\n"
        res += str(data[i] / success for i in range(1, highest + 1)) + "\n"
    return res


def ascii_graph(occurrences: dict, mode: int):
    res = ""
    mode = int(mode)
    max_val = max(list(occurrences.values()))
    total = sum(occurrences.values())
    if not mode:
        for k in sorted(int(x) for x in occurrences):
            if occurrences[k]:
                res += (
                    f"{int(k):5d} {100 * occurrences[k] / total: >5.2f} "
                    f"{'#' * int(40 * occurrences[k] / max_val)}\n"
                )
    elif mode > 0:
        runningsum = 0
        for k in sorted(occurrences):
            if occurrences[k]:
                runningsum += occurrences[k]
                res += (
                    f"{k:5d} {100 * runningsum / total: >5.2f} "
                    f"{'#' * int(40 * runningsum / total)}\n"
                )
    elif mode < 0:
        runningsum = sum(occurrences.values())
        for k in sorted(occurrences):
            if occurrences[k]:
                res += (
                    f"{k:5d} {100 * runningsum / total: >5.2f} "
                    f"{'#' * int(40 * runningsum / total)}\n"
                )
                runningsum -= occurrences[k]
    return res, *avgdev(occurrences)


def avgdev(occurrences):
    total = sum(occurrences.values())
    avg = sum(int(k) * int(v) for k, v in occurrences.items()) / total
    dev = math.sqrt(
        sum(((int(k) - avg) ** 2) * v for k, v in occurrences.items()) / total
    )
    return avg, dev
