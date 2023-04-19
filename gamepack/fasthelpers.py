import math
import time

from gamepack.DiceParser import DiceParser


def montecarlo(roll, run_for=10):
    p = DiceParser()
    occurences = {}
    time0 = time.time()
    while time.time() - time0 < run_for:
        for _ in range(1000):
            r = p.do_roll(roll).result
            occurences[r] = occurences.get(r, 0) + 1
    return f"from {sum(occurences.values())} results:\n{plot(occurences)}"


def plot(
    data: dict[int, int],
    showsucc: bool = False,
    showgraph: bool = True,
    showdmgmods: bool = False,
    grouped: int = 1,
) -> str:
    """
    Plots data as a text-based histogram.

    Args:
        data (dict): Dictionary with integer keys representing the rolls and
            values representing the count of each roll.
        showsucc (bool, optional): If True, prints the number of successes,
            failures and botches, and the percentage of each. Default is False.
        showgraph (bool, optional): If True, prints the histogram. Default is True.
        showdmgmods (bool, optional): If True, prints the damage modifiers. Default is False.
        grouped (int, optional): Groups the data in ranges of specified size. Default is 1.

    Returns:
        str: Text-based histogram of the data.
    """
    success = sum(v for k, v in data.items() if k > 0)
    zeros = sum(v for k, v in data.items() if k == 0)
    botches = sum(v for k, v in data.items() if k < 0)
    total = sum(data.values())
    result = ""
    percent_total = total / 100
    width = 1
    highest = 0
    if showsucc:
        result += (
            f"Of the {total} rolls, {success} were successes, {zeros} were failures and {botches} were botches, "
            f"averaging {sum(k * v for k, v in data.items()) / total:.2f}\n"
            f"The percentages are:\n+ : {success/total:.3%}\n0 : {zeros/total:.3%}\n- : {botches/total:.3%}\n"
        )
        bar_portion_success = int((success / percent_total) / width)
        bar_portion_botch = int((botches / percent_total) / width)
        bar_portion_neutral = int(100 / width - bar_portion_success - bar_portion_botch)
        result += (
            "+" * bar_portion_success
            + "0" * bar_portion_neutral
            + "-" * bar_portion_botch
            + "\n"
        )
    if showgraph:
        lowest = min(data.keys())
        highest = max(data.keys())
        width = (1 / 60) * max(
            int(data.get(i, 0) / percent_total) for i in range(lowest, highest + 1)
        )
        for i in range(lowest // grouped, highest // grouped + 1):
            if i == 0 and showsucc:
                result += "\n"
            group_start = i * grouped
            group_end = (i + 1) * grouped - 1
            group_total = sum(data.get(j, 0) for j in range(group_start, group_end + 1))
            if grouped == 1:
                if data.get(i) or data.get(i + 1) or data.get(i - 1):
                    result += f"{i:2d} : {(group_total / percent_total):7.3f}% "
            else:
                result += f"{group_start:2d}-{group_end:2d} : {(group_total / percent_total):7.3f}% "
            result += "#" * int((group_total / percent_total) / width) + "\n"
            if i == 0 and showsucc:
                result += "\n"
    if showdmgmods:
        result += "damage modifiers (adjusted):\n"
        result += (
            ", ".join(str(data.get(i, 0) / success) for i in range(1, highest + 1))
            + "\n"
        )
    return result


def ascii_graph(occurrences: dict, mode: int) -> tuple[str, float, float]:
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
    avg, dev = avgdev(occurrences)
    return res, avg, dev


def avgdev(occurrences) -> tuple[float, float]:
    total = sum(occurrences.values())
    avg = sum(int(k) * int(v) for k, v in occurrences.items()) / total
    dev = math.sqrt(
        sum(((int(k) - avg) ** 2) * v for k, v in occurrences.items()) / total
    )
    return avg, dev
