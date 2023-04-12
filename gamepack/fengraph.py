import ast
import io
import json
import logging
import math
import pathlib
import sqlite3
from _md5 import md5
from math import ceil
from typing import Dict, List, Union, Tuple

import matplotlib.pyplot as plt
import requests

from gamepack.Armor import Armor
from gamepack.Dice import DescriptiveError
from gamepack.data import get_str, set_str, handle
from gamepack.fasthelpers import ascii_graph
from gamepack.generate_dmgmods import generate

log = logging.Logger("fengraph")


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
        occ = {k: 0 for k in range(1, 10 * len(selector) + 1)}
        for roll, frequency in dataset(mod).items():
            k = sum(roll[s - 1] for s in selector if 0 < s < 6)
            occ[int(k)] += int(frequency)
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


def dataset(modifier: int) -> Dict[Tuple[int, ...], int]:
    with open(handle("roll_frequencies_" + str(modifier) + ".csv")) as f:
        result = {}
        for line in f.readlines():
            line = line.strip().split(",")
            result[tuple(int(x) for x in line[:-1])] = int(line[-1])
        return result


def chances(selector, modifier=0, number_of_quantiles=None, mode=0, interactive=False):
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

        plt.figure()
        plt.bar(
            range(1, len(occurrences.values()) + 1),
            fy,
            facecolor="green",
            alpha=0.75,
            linewidth=1,
        )
        yield "finalizing graph"
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
        yield "sending data..."
        plt.savefig(buf, format="png", bbox_inches="tight", pad_inches=0)
        if interactive:
            plt.show()

        plt.close()
        buf.seek(0)
        yield buf


if __name__ == "__main__":
    supply_graphdata()
