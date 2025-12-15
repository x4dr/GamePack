import collections
import io
import logging
import math
import pathlib
from collections import Counter
from itertools import combinations_with_replacement
from math import ceil, factorial
from typing import Dict

import matplotlib.pyplot as plt
import requests

from gamepack import dicecache_db
from gamepack.Dice import DescriptiveError

from gamepack.fasthelpers import ascii_graph

log = logging.Logger("fengraph")


def fastdata(selector: tuple[int, ...], mod: int) -> dict[int, int]:
    if mod not in freq_dicts or not all(0 < s < 6 for s in selector):
        return {}
    selector = tuple(
        sorted(selector)
    )  # cuts down on cache size since order doesn't matter
    db = dicecache_db()
    res = db.execute(
        "SELECT res, occ FROM occurences WHERE sel = ? AND mod = ?",
        [str(selector), mod],
    ).fetchall()
    if res:
        return {int(r[0]): r[1] for r in res}
    for mod in range(-5, 6):
        occ: dict[int, int] = collections.defaultdict(int)
        for roll, occurence_count in freq_dicts[mod].items():
            result = sum(roll[s - 1] for s in selector)
            occ[int(result)] += int(occurence_count)
        for result, occurence_count in occ.items():
            db.execute(
                "INSERT INTO occurences VALUES (?,?,?,?)",
                [str(selector), int(mod), int(result), int(occurence_count)],
            )
    db.commit()
    raise DescriptiveError(
        "Cache Updated, try again! I could just continue but I am no longer trusted to do my job!"
    )


def fastversus(
    selector1: tuple[int, ...], selector2: tuple[int, ...], mod1: int, mod2: int
) -> Dict[int, int]:
    db = dicecache_db()
    res = db.execute(
        "SELECT res, occ FROM versus WHERE sel1 = ? AND sel2 = ? AND mod1 = ? AND mod2 = ?",
        [str(selector1), str(selector2), mod1, mod2],
    ).fetchall()
    if res:
        return {int(r[0]): int.from_bytes(r[1], "big") for r in res}
    # ensure all elements of both selectors are within the range of the dice
    if any(s < 0 or s > 6 for s in selector1 + selector2):
        raise ValueError("selector out of range")

    occ: dict[int, int] = collections.defaultdict(int)
    for roll1, frequency1 in freq_dicts[mod1].items():
        for roll2, frequency2 in freq_dicts[mod2].items():
            k = sum(roll1[s - 1] for s in selector1) - sum(
                roll2[s - 1] for s in selector2
            )
            occ[int(k)] += int(frequency1 * frequency2)
    for result, occurrence in occ.items():
        db.execute(
            "INSERT INTO versus VALUES (?,?,?,?,?,?)",
            [
                str(selector1),
                str(selector2),
                int(mod1),
                int(mod2),
                result,
                occurrence.to_bytes(24, "big").lstrip(b"\x00"),
            ],
        )
    db.commit()
    return fastversus(selector1, selector2, mod1, mod2)


def versus(
    selectors1: tuple[int, ...],
    selectors2: tuple[int, ...],
    mod1: int = 0,
    mod2: int = 0,
    mode: int = 0,
):
    occurences = fastversus(selectors1, selectors2, mod1, mod2)
    return ascii_graph(occurences, mode)


def modify_dmg(specific_modifiers, dmg, damage_type, armor):
    total_damage = 0
    effectivedmg = []
    dmg = dmg[1:-1]  # first and last should be 0
    for damage_instance in dmg:
        if len(damage_instance) > 1:
            effective_dmg = damage_instance[0] - max(0, armor - damage_instance[1])
            effectivedmg.append(effective_dmg if effective_dmg > 0 else 0)
        else:
            damage_instance = damage_instance[0]
            if damage_type == "Stechen":
                effectivedmg.append(
                    0 if damage_instance <= armor else math.ceil(damage_instance / 2)
                )
            elif damage_type == "Schlagen":
                effective_dmg = damage_instance - int(armor / 2)
                effectivedmg.append(effective_dmg if effective_dmg > 0 else 0)
            elif damage_type == "Schneiden":
                effective_dmg = damage_instance - armor
                effectivedmg.append(
                    effective_dmg + ceil(effective_dmg / 5) * 3
                    if effective_dmg > 0
                    else 0
                )
            else:
                effective_dmg = damage_instance - armor
                effectivedmg.append(effective_dmg if effective_dmg > 0 else 0)

    for i, damage_instance in enumerate(effectivedmg):
        total_damage += damage_instance * specific_modifiers[i]
    return total_damage


def rawload(page) -> str:
    try:
        with pathlib.Path.expanduser(pathlib.Path(f"~/wiki/{page}.md")).open() as f:
            return f.read()
    except Exception as e:
        r = requests.get(f"https://nossinet.cc/wiki/{page}/raw")
        logging.exception(f"loaded {page}.md via web, because", e)
        return r.content.decode()


def chances(
    selector: tuple[int, ...],
    modifier=0,
    number_of_quantiles=None,
    mode=0,
    interactive=False,
):
    selector = tuple(sorted(x for x in selector if 0 < int(x) < 6))
    if not selector:
        raise DescriptiveError("No Selectors!")
    modifier = int(modifier)
    occurrences = fastdata(selector, modifier)
    if number_of_quantiles is None:
        return ascii_graph(occurrences, mode)
    else:
        total = sum(occurrences.values())
        vals = [occurrences[x] for x in sorted(occurrences.keys())]
        if not mode:
            fy = [x / total for x in vals]
        elif mode > 0:
            fy = [sum(vals[: i + 1]) / total for i in range(len(vals))]
        else:  # elif mode < 0:
            fy = [(total - sum(vals[:i])) / total for i in range(len(vals))]

        plt.figure()
        plt.bar(
            range(1, len(occurrences.values()) + 1),
            fy,
            facecolor="green",
            alpha=0.75,
            linewidth=1,
        )
        buf = io.BytesIO()
        if max(occurrences.keys()) < 31:
            plt.xticks(list(range(1, max(occurrences.keys()) + 1)))
        plt.ylim(ymin=0.0)
        plt.xlim(xmin=0.0)
        plt.title(
            ", ".join(str(x) for x in selector)
            + "@5"
            + (("R" + str(modifier)) if modifier else "")
        )
        plt.ylabel("%")
        plt.savefig(buf, format="png", bbox_inches="tight", pad_inches=0)
        if interactive:
            plt.show()

        plt.close()
        buf.seek(0)
        return buf


def count_sorted_rolls(num_dice, num_sides):
    counts = {}
    for roll in combinations_with_replacement(range(1, num_sides + 1), num_dice):
        c = Counter(roll)
        result = factorial(num_dice)
        for count in c.values():
            result //= factorial(count)
        counts[roll] = result
    return counts


def count_lowest_rolls(counts, subselection):
    new_counts = {}
    k = -subselection
    for roll, count in counts.items():
        sorted_roll = tuple(sorted(sorted(roll, reverse=k < 0)[: abs(k)]))
        if sorted_roll not in new_counts:
            new_counts[sorted_roll] = 0
        new_counts[sorted_roll] += count
    return new_counts


# takes about half a second
basesets = {i: count_sorted_rolls(i, 10) for i in range(5, 11)}
freq_dicts = {
    i: count_lowest_rolls(basesets[5 + abs(i)], 5 if i > 0 else -5)
    for i in range(-5, 6)
}
