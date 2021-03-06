import ast
import io
import json
import logging
import math
import pathlib
import sqlite3
import time
from _md5 import md5
from math import ceil
from typing import Dict, List, Union

import numpy
import requests

from gamepack.Armor import Armor
from gamepack.Dice import DescriptiveError
from gamepack.DiceParser import DiceParser
from gamepack.data import get_str, set_str, handle
from gamepack.generate_dmgmods import generate, tuplecombos

log = logging.Logger("fengraph")

try:
    from scipy.integrate import quad
    from scipy.interpolate import interp1d
    from scipy.optimize import fsolve
except ImportError:

    def notfound(*args, **kwargs):
        raise Exception("Scipy is not installed!", [args, kwargs])

    quad = notfound
    interp1d = notfound
    fsolve = notfound


# noinspection PyDefaultArgument
def dicecache_db(cache=[]) -> sqlite3.Connection:
    """db connection singleton"""

    if cache:
        return cache[0]
    dbpath = handle("dicecache")
    cache.append(sqlite3.connect(dbpath))
    cache[0].cursor().executescript(
        "create table if not exists results (sel TEXT, mod INT, res TEXT);"
    )
    cache[0].commit()

    return cache[0]


def fastdata(selector: tuple[int], mod: int):
    if mod not in range(-5, 6):
        return
    db = dicecache_db()
    res = db.execute(
        "SELECT res FROM results WHERE sel = ? AND mod = ?", [str(selector), mod]
    ).fetchone()
    if res:
        return {int(k): int(v) for k, v in json.loads(res[0]).items()}
    for mod in range(-5, 6):
        df = dataset(mod)
        occ = {k: 0 for k in range(1, 10 * len(selector) + 1)}
        for row, series in df.iterrows():
            k, v = select_modified(selector, series)
            occ[int(k)] += int(v)
        db.execute(
            "INSERT INTO results VALUES (?,?,?)",
            [str(selector), int(mod), json.dumps(occ)],
        )
    db.commit()
    return fastdata(selector, mod)


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


def supply_graphdata():
    dmgtypes = ["Hacken", "Stechen", "Schneiden", "Schlagen"]
    weapons = weapondata()
    armormax = 14
    wmd5 = md5(str(weapons).encode("utf-8")).hexdigest()
    damages: Dict[str, Dict[str, List[Dict[str, Dict[str, float]]]]] = {}
    try:
        f = get_str("weaponstuff_internal").splitlines()
        nmd5 = f[0]
        if str(nmd5).strip() == str(wmd5).strip():
            with open("NossiSite/static/graphdata.json") as g:
                if str(wmd5) in g.read(
                    len(str(wmd5) * 2)
                ):  # find hash at the beginning of the json
                    return
            damages = ast.literal_eval("\n".join(f[1:]))
        else:
            logging.debug(
                f"fengraph hashes: {str(nmd5).strip()} != "
                f"{str(wmd5).strip()}, so graphdata will be regenerated"
            )
            damages = {}
    except SyntaxError as e:
        logging.debug(f"syntax error in weaponstuff_internal, regenerating: {e.msg}")
    except FileNotFoundError:
        damages = {}
        # regenerate and write weaponstuff
    maxdmg = 0
    if not damages:

        modifiers = {}
        try:
            lines = get_str("5d10r0vr0_ordered_data")
        except FileNotFoundError:
            generate(0, 0)
            lines = get_str("5d10r0vr0_ordered_data")

        for line in lines.splitlines():
            line = ast.literal_eval(line)
            total = sum(line[1].values())
            zero_excluded_positive = [line[1].get(i, 0) for i in range(1, 21)]
            zepc = zero_excluded_positive[:9] + [sum(zero_excluded_positive[9:])]
            zepc_relative = [x / total for x in zepc]
            modifiers[line[0]] = zepc_relative

        logging.debug("regenerating weapon damage data")
        for stats, modifier in modifiers.items():
            statstring1 = " ".join(str(x) for x in stats[0])
            statstring2 = " ".join(str(x) for x in stats[1])
            damages[statstring1] = damages.get(statstring1, {})
            damages[statstring1][statstring2] = []
            damage = damages[statstring1][statstring2]  # reduce length of calling stuff
            logging.debug(f"damage data: {stats}, {modifier}")
            for i in range(armormax):
                damage.append({})
                for w, wi in weapons.items():
                    damage[-1][w] = {}
                    for d, di in wi.items():
                        damage[-1][w][d] = modify_dmg(modifier, di, d, i)
        logging.debug("writing weaponstuff...")
        set_str("weaponstuff_internal", str(wmd5) + "\n" + str(damages))

    comparison_json: Dict[
        str, Union[List[str], Dict[str, List[List[List[float]]]], float, int]
    ] = {
        "Hash": wmd5,
        "Names": list(weapons.keys()),
        "Types": list(dmgtypes),
    }
    attackerstat: str
    for attackerstat, defender in sorted(damages.items()):
        attackdict = {}
        defenderstat: str
        for defenderstat, damage in defender.items():
            damagematrix = []
            per_armor: Dict[str, Dict[str, float]]
            for per_armor in damage:
                logging.debug(str(per_armor))
                dmg_per_dmgtype: List[List[float]] = [
                    [per_armor[weapon][damagetype] for weapon in list(weapons.keys())]
                    for damagetype in dmgtypes
                ]

                damagematrix.append(dmg_per_dmgtype)
                candidates = max(
                    x
                    for x in [
                        [
                            per_armor[weapon][damagetype]
                            for weapon in comparison_json["Names"]
                        ]
                        for damagetype in dmgtypes
                    ]
                )
                nm = max(candidates)
                logging.debug(f"{nm}, {maxdmg}")
                if nm > maxdmg:
                    logging.debug(f"updating maxdmg to {nm}")
                    maxdmg = nm
            attackdict[defenderstat]: List[List[List[float]]] = damagematrix
        comparison_json[attackerstat] = attackdict
    comparison_json["max"] = math.ceil(maxdmg)
    with open("NossiSite/static/graphdata.json", "w") as f:
        f.write(json.dumps(comparison_json))


def weapondata():
    dmgraw = rawload("weapons")
    weapons = {}
    for dmgsect in dmgraw.split("###"):
        if not dmgsect.strip() or "[TOC]" in dmgsect:
            continue
        weapon = dmgsect[: dmgsect.find("\n")].strip()
        weapons[weapon] = {}
        for dmgline in dmgsect.split("\n"):
            if "Wert" in dmgline or "---" in dmgline or len(dmgline) < 50:
                continue
            if "|" not in dmgline:
                break
            dmgtype = dmgline[dmgline.find("[") + 1 : dmgline.find("]")].strip()
            weapons[weapon][dmgtype] = dmgline[35:]
        if "##" in dmgsect:
            break

    dmgtypes = set()
    for weapon, wi in weapons.items():
        for dt in wi.keys():
            dmgtypes.add(dt)

    for weapon, wi in weapons.items():
        for dt in dmgtypes:
            wi[dt] = [
                [int(y) for y in x.split(";")] if x.strip() else [0]
                for x in wi.get(dt, "|" * 11).split("|")
            ]
    return weapons


def rawload(page) -> str:
    try:
        with pathlib.Path.expanduser(pathlib.Path(f"~/wiki/{page}.md")).open() as f:
            return f.read()
    except Exception as e:
        r = requests.get(f"https://nosferatu.vampir.es/wiki/{page}/raw")
        logging.exception(f"loaded {page}.md via web, because", e)
        return r.content.decode()


def armordata() -> Dict[str, Armor]:
    armraw = rawload("armor")
    armor = {}
    begun = 0
    for armline in armraw.splitlines():
        if begun and "|" not in armline:
            break
        elif "|" not in armline:
            continue
        begun += 1
        if begun > 2:
            a = Armor.from_formatted(armline)
            armor[a.name] = a
    return armor


def dataset(modifier):
    import pandas

    return pandas.read_csv(
        handle("roll_frequencies_" + str(modifier) + ".csv"),
        names=["D1", "D2", "D3", "D4", "D5", "frequency"],
    )


def select_modified(selector, series):
    return sum(series[s - 1] for s in selector if 0 < s < 6), series[-1]


def helper(f, integratedsum, q, lastquant):
    def internalhelper(x):
        try:
            result = quad(f, lastquant, x, limit=200)
            return result[0] - integratedsum * q
        except Exception:
            logging.debug(f"integration errvals: {q}, {lastquant}, {x}")
            raise

    return internalhelper


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


def montecarlo(roll):
    p = DiceParser()
    occurences = {}
    time0 = time.time()
    while time.time() - time0 < 10:
        r = p.do_roll(roll).result
        occurences[r] = occurences.get(r, 0) + 1
    return f"from {sum(occurences.values())} results:\n {plot(occurences)}"


def versus(part1, part2, mode):
    yield "processing..."
    mod1, mod2 = part1[2], part2[2]
    data = get_str(f"5d10r{mod1}vr{mod2}_ordered_data")
    yield "load complete..."
    stat1 = tuple(sorted([int(x) for x in part1[:2]], reverse=True))
    stat2 = tuple(sorted([int(x) for x in part2[:2]], reverse=True))
    logging.debug("\n".join(str(x) for x in tuplecombos))
    index = tuplecombos.index((stat1, stat2))
    occurences = ast.literal_eval(data.splitlines()[index])
    if occurences[0] != (stat1, stat2):
        raise DescriptiveError(
            f"possible corruption: expected {(stat1,stat2)} found {occurences[0]}"
        )
    yield "data found..."
    occurences = occurences[1]  # only the dict is now relevant
    yield ascii_graph(occurences, mode)


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


def chances(selector, modifier=0, number_of_quantiles=None, mode=0):
    selector = tuple(sorted(int(x) for x in selector if 0 < int(x) < 6))
    if not selector:
        raise DescriptiveError("No Selectors!")
    modifier = int(modifier)
    yield "processing..."
    occurrences = fastdata(selector, modifier)
    yield "generating result..."

    if number_of_quantiles is None:
        yield ascii_graph(occurrences, mode)
    else:
        total = sum(occurrences.values())
        yield "generating graph..."
        vals = [occurrences[x] for x in sorted(occurrences.keys())]
        if not mode:
            fy = [x / total for x in vals]
        elif mode > 0:
            fy = [sum(vals[: i + 1]) / total for i in range(len(vals))]
        else:  # elif mode < 0:
            fy = [(total - sum(vals[:i])) / total for i in range(len(vals))]

        fx = sorted(list(occurrences.keys()))
        f = interp1d(fx, fy, kind=2, bounds_error=False, fill_value=0)
        import matplotlib.pyplot as plt

        plt.figure()
        plt.bar(
            range(1, len(occurrences.values()) + 1),
            fy,
            facecolor="green",
            alpha=0.75,
            linewidth=1,
        )
        linx = numpy.linspace(
            1, max(occurrences.keys()) + 1, max(occurrences.keys()) * 10
        )
        integratedsum = 1
        quantiles = [0]
        if number_of_quantiles:
            yield "calculating integrals"
            tries = 0
            while tries < 3:
                n = -1
                try:
                    n = max(min(int(number_of_quantiles), 100), 0) + 1
                    quantiles = [0]
                    for q in [1 / n for _ in range(n - 1)]:
                        quantiles.append(
                            fsolve(
                                func=helper(f, integratedsum, q, quantiles[-1]),
                                x0=numpy.array([quantiles[-1]] if quantiles[-1] else 1),
                            )
                        )
                    tries += 3
                except Exception as e:
                    logging.exception(f"exception in calculating integrals {n}:", e)
                    raise
        yield "finalizing graph"
        plt.plot(linx, f(linx), "--")
        buf = io.BytesIO()
        for q in quantiles[1:]:
            plt.axvline(q)
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
        yield "sending data..."
        plt.savefig(buf, format="png", bbox_inches="tight", pad_inches=0)
        plt.show()
        plt.close()
        buf.seek(0)
        yield buf


if __name__ == "__main__":
    supply_graphdata()
