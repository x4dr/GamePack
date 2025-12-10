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
            if not msys.is_active():
                continue
            speeds = msys.speeds(self.total_mass)
            final = speeds[-1]
            s = {str(x): speeds[x] for x in range(min(121, len(speeds)))}
            # {
            # str(x): speeds[x] for x in self.speeds_at_seconds if 0 < x < len(speeds)
            # }

            result[mname] = {
                "speeds": s,
                "topspeed": final,
                "acceleration_time": len(speeds),
                "g": (speeds[1] if len(speeds) > 1 else 0) / 9.81,
            }
        return result

    def post_process(self, flash):
        pass

    def to_md(self):
        return self.to_mdobj().to_md()

    def to_mdobj(self) -> MDObj:
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
                # Insert budget marker: indicates how much energy has been used up to this point
                # Anything before this marker consumes 'current_budget' energy; helps visualize loadout thresholds
                result.append(f"[{current_budget}]")
                used = 0
                current_budget = next(budget_iter)
            result.append(sys)
            used += cost
        result.append(f"[{current_budget}]")
        return result

    def fluxmax(self):
        flux = 0
        for h in self.Heat.values():
            if h.is_active():
                flux += h.flux
        return flux

    def add_heat(self, amt: int) -> int:
        systems = list(self.Heat.values())
        for i in range(len(systems)):
            sys = systems[i]
            if not sys.is_active():
                continue
            amt = sys.add_heat(amt)  # heat overage is returned
            if amt == 0:
                break
        return amt

    def tick_heat(self):
        thermals = {}
        for h in self.Heat.values():
            thermals[h.name] = h.tick()
        return thermals

    def move_heat(self, source, target, amount):
        if source in self.Heat and target in self.Heat:
            source = self.Heat[source]
            target = self.Heat[target]
            amount = source.withdraw_heat(amount)
            amount = target.add_heat(amount)
            amount = self.add_heat(amount)
            return amount
        raise KeyError(f"Transfer from {source} to {target} failed: Unknown System")

    def energy_budget(self):
        budget = 0
        for e in self.Energy.values():
            energy = e.provide()
            budget += energy
        return budget

    def energy_total(self):
        budget = 0
        for e in self.Energy.values():
            budget += 0 if e.is_disabled() else e.energy
        return budget

    def energy_allocation(self, loadout: str = None) -> (list, int):
        budget = self.energy_budget()

        if not self.loadouts:
            # No loadouts defined → include all systems alphabetically
            all_systems = [
                s
                for cat in self.systems.values()
                for s in cat.values()
                if isinstance(s, System)
            ]
            all_systems.sort(key=lambda s: s.name)  # alphabetical
            self.loadouts["Default"] = all_systems

        if loadout is None:
            loadout = self.description.get("Loadout", list(self.loadouts.keys())[0])

        activated = 0
        load = [
            x
            for x in self.loadouts[loadout]
            if not isinstance(x, str) and x.is_active()
        ]
        for s in load:
            budget -= s.energy
            if budget < 0:
                break
            activated += 1

        return load, activated

    def get_syscat(self, name):
        if name == "Generic":
            return {**self.Offensive, **self.Defensive, **self.Support}
        return self.systems[name]

    def use_system(self, systemtype, name, parameter):
        syscat = self.get_syscat(systemtype.capitalize())
        sys = syscat.get(name, parameter)
        heat = sys.use(parameter)
        if heat is None:
            raise Exception(
                f"System usage failed for {systemtype.capitalize()}: {name}"
            )
        self.heatflux += self.add_heat(heat)

    def flux_baseload(self):
        for syscat in self.systems.values():
            for sys in syscat.values():
                if sys.is_active():
                    self.heatflux += sys.heats.get("heat0", 0)
