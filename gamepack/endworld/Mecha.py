__author__ = "maric"

from itertools import product

from gamepack.MDPack import MDObj
from gamepack.endworld import SealSystem, HeatSystem
from gamepack.endworld.EnergySystem import EnergySystem
from gamepack.endworld.MovementSystem import MovementSystem
from gamepack.endworld.System import System


class Mecha:
    def __init__(self):
        self.description = {}
        self.errors = []
        self.speeds_at_seconds = list(range(16)) + [20, 30, 50, 100]
        self._totalmass = 0
        self.Movement: dict[str, MovementSystem] = {}
        self.Energy: dict[str, EnergySystem] = {}
        self.Heat: dict[str, HeatSystem] = {}
        self.Offensive: dict[str, System] = {}
        self.Defensive: dict[str, System] = {}
        self.Support: dict[str, System] = {}
        self.Seal: dict[str, SealSystem] = {}
        self.systems: dict[str, dict[str, System]] = {  # for iteration purposes
            "Movement": self.Movement,
            "Energy": self.Energy,
            "Heat": self.Heat,
            "Offensive": self.Offensive,
            "Defensive": self.Defensive,
            "Support": self.Support,
            "Seal": self.Seal,
        }
        self.heatflux = 0
        self.loadouts: dict[str, list[System]] = {}

    @classmethod
    def from_mdobj(cls, mdobj):
        self = cls()

        def flash(err):
            self.errors.append(err)

        # inform about things that should not be there
        if mdobj.plaintext.strip():
            flash("Loose Text: " + mdobj.plaintext)

        for t in mdobj.tables:
            if t:
                flash("Loose Table:" + t.to_md())
        self.description, error = mdobj.children.get(
            "Description", MDObj.empty()
        ).confine_to_tables()
        flash(error)

        systems = mdobj.children.get("Systems", MDObj.empty()).children
        for key in self.systems.keys():
            sys: MDObj = systems.get(key, MDObj.empty())
            tables = sys.confine_to_tables(True)
            self.systems[key].update(
                {k: System.create(key, k, v) for k, v in tables[0].items()}
            )
        loadouts: MDObj = mdobj.children.get("Loadouts", MDObj.empty())
        for loadout_name, loadout_node in loadouts.children.items():
            self.loadouts[loadout_name.title()] = self.process_loadout(
                loadout_node.plaintext
            )
        if "Default" not in self.loadouts:
            self.loadouts["Default"] = (
                list(self.Movement.values())
                + list(self.Heat.values())
                + list(self.Defensive.values())
                + list(self.Offensive.values())
                + list(self.Support.values())
            )
        return self

    @property
    def total_mass(self):
        return sum(
            s.total_mass
            for systemcategory in self.systems.values()
            for s in systemcategory.values()
        )

    def speeds(self):
        result = {}
        for mname, msys in self.Movement.items():
            speeds = msys.speeds(self.total_mass)
            final = speeds[-1]
            threshold = final * 0.9
            for idx, val in enumerate(speeds):
                if val >= threshold:
                    s = {
                        str(x): speeds[x]
                        for x in self.speeds_at_seconds
                        if 0 < x < len(speeds)
                    }
                    result[mname] = {"speeds": s, "topspeed": val, "duration": idx}
                    break
        return result

    def post_process(self, flash):
        pass

    def to_mdobj(self):

        def flash(err):
            self.errors.append(err)

        description = MDObj(
            "",
            flash=flash,
            header="Description",
        )
        for k, v in self.description.items():
            description.add_child(MDObj(v, flash=flash, header=k))

        systems = self.systems_mdobj().with_header("Systems")
        loadouts = MDObj.empty().with_header("Loadouts")
        for loadout_name, prio_list in self.loadouts.items():
            loadouts.add_child(
                MDObj(
                    ", ".join(
                        [x.name if isinstance(x, System) else str(x) for x in prio_list]
                    )
                ).with_header(loadout_name)
            )
        mdo = MDObj("")
        mdo.add_child(description)
        mdo.add_child(systems)
        mdo.add_child(loadouts)
        return mdo

    def systems_mdobj(self) -> MDObj:
        systems = MDObj.empty()
        for system_cat, sys in self.systems.items():
            table = System.registry[system_cat].as_table(sys.values())
            systems.add_child(MDObj("", tables=[table], header=system_cat))
        return systems

    def process_loadout(self, plaintext: str) -> list[System]:
        systems = {
            x_name: x
            for cat_name, category in self.systems.items()
            if cat_name != "Energy"
            for x_name, x in category.items()
        }
        energies = list(self.Energy.values())
        n = len(energies)

        budgets = set()
        for enabled_flags in product([False, True], repeat=n):
            budgets.add(
                sum(
                    e.energy * e.amount
                    for e, flag in zip(energies, enabled_flags)
                    if flag
                )
            )
        prio = []
        for candidate in plaintext.split(","):
            candidate = candidate.strip()
            if candidate.startswith("[") and candidate.endswith("]"):
                continue
            if candidate not in systems.keys():
                candidate += "?" * max(
                    0, 3 - len(candidate) + len(candidate.rstrip("?"))
                )
                prio.append((candidate, 0))
            else:
                prio.append((systems[candidate], systems[candidate].energy))
        budgets = sorted(budgets)

        result = []
        budget_iter = iter(budgets)
        current_budget = next(budget_iter)
        used = 0

        for sys, cost in prio:
            if used + cost > current_budget:
                result.append(f"[{current_budget}]")
                used = 0
                current_budget = next(budget_iter)
            result.append(sys)
            used += cost
        result.append(f"[{current_budget}]")
        return result

    def energy_allocation(self, loadout: str) -> int:
        """
        Calculate how many systems can be activated in the given loadout
        based on available energy and energy priorities.
        Args:
            loadout (str): The name of the loadout

        Returns:
            int: The number of systems successfully activated
        """
        budget = 0
        for e in self.Energy.values():
            energy = e.provide()
            budget += energy

        activated = 0
        for s in self.loadouts[loadout]:
            budget -= s.energy
            if budget < 0:
                break
            activated += 1

        return activated
