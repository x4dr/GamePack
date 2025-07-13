__author__ = "maric"

from itertools import product
from typing import Type, Callable, Iterable

from gamepack.MDPack import MDObj, MDTable


class System:
    headers = ["Energy", "Mass", "Amount"]

    registry: dict[str, Type["System"]] = {}

    @classmethod
    def register(cls, name: str) -> Callable[[Type["System"]], Type["System"]]:
        cls.registry.setdefault("Energy", System)
        cls.registry.setdefault("Offensive", System)
        cls.registry.setdefault("Defensive", System)
        cls.registry.setdefault("Support", System)

        def wrapper(subclass: Type["System"]) -> Type["System"]:
            cls.registry[name] = subclass
            return subclass

        return wrapper

    @classmethod
    def create(cls, type_name, name, data):
        subclass = cls.registry.get(type_name)
        if not subclass:
            instance = cls(name, data)
            instance.errors.append(f"Unknown system type: {type_name}")
            return instance
        return subclass(name, data)

    def __init__(self, name, data):
        self._data = {k.lower(): v for k, v in data.items()}
        self.name: str = name
        self.errors = []
        self.mass: float = self.number(self.extract("mass"))
        self.amount: float = self.number(self.extract("amount"))
        self.energy: float = self.number(self.extract("energy"))
        self.heat = self.number(self.extract("heat", "0", False))

    def extract(self, key, default: str = "", req=True):
        if key in self._data:
            return self._data[key]
        else:
            if req:
                self.errors.append(f"{self.name}: {key} not found in {self._data}.")
            return default

    def number(self, inp: str, default=0):
        try:
            inp = str(inp).strip()
            if inp.endswith("%"):
                return float(inp[:-1]) / 100
            else:
                return float(inp)
        except ValueError:
            self.errors.append(f'"{inp}" is not a valid number')
            return default

    @property
    def total_mass(self):
        return self.mass * self.amount

    def to_dict(self) -> dict:
        return {
            **{k.title(): v for k, v in self._data.items()},
            "Mass": self.mass,
            "Amount": self.amount,
            "Energy": self.energy,
        }

    def get_headers(self):
        bonusheaders = []
        for h in self._data.keys():
            if h.title() not in self.headers:
                bonusheaders.append(h.title())
        return self.headers + bonusheaders

    @classmethod
    def as_table(cls, systems:Iterable["System"])->MDTable:
        rows = []
        headers = []

        for system in systems:
            row = [system.name]
            d = system.to_dict()
            if headers:
                assert headers == system.get_headers()
            else:
                headers = system.get_headers()
            for h in headers:
                row.append(d.get(h, ""))
            rows.append(row)

        return MDTable(rows, [""] + headers)


@System.register("Movement")
class MovementSystem(System):
    headers = ["Energy", "Heat", "Thrust", "Anchor", "Dynamics", "Mass", "Amount"]

    def __init__(self, name, data):
        super().__init__(name, data)
        self.thrust = self.number(self.extract("thrust"))
        self.anchor = self.number(self.extract("anchor"))
        self.dynamics = self.number(self.extract("dynamics"))

    def speeds(self, mech_total_mass):
        speed = 0
        friction = self.anchor * mech_total_mass / 100
        accel = self.thrust / mech_total_mass
        speeds = []
        for i in range(10000):
            speed += accel
            speed -= friction
            air = speed * speed / (10 * self.dynamics)
            speed -= air
            if speed <= 0:
                speed = 0
            speeds.append(speed)
        return speeds

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            "Thrust": self.thrust,
            "Anchor": self.anchor,
            "Dynamics": self.dynamics,
        }


@System.register("Seal")
class SealSystem(System):
    headers = ["Level"]

    def __init__(self, name, data):
        defaults = {"mass": 0, "amount": 1, "energy": 0}
        super().__init__(name, {**defaults, **data})
        self.level = self.number(self.extract("level"))

    def to_dict(self) -> dict:
        return {"Level": self.level}

    def get_headers(self):
        bonusheaders = []
        for h in self._data.keys():
            if h.title() not in self.headers + super().headers:
                # don't want the base headers
                bonusheaders.append(h.title())
        return self.headers + bonusheaders


@System.register("Energy")
class EnergySystem(System):
    headers = ["Energy", "Mass", "Amount", "Enabled"]
    enablers = ["x", "t", "y", "1"]

    def __init__(self, name, data):
        super().__init__(name, data)
        self.enabled = self.extract("enabled")

    def provide(self) -> float:
        if any(x in self.enabled for x in self.enablers):
            return self.energy * self.amount
        return 0


@System.register("Heat")
class HeatSystem(System):
    headers = ["Capacity", "Passive", "Active", "Flux", "Current"]

    def __init__(self, name, data):
        super().__init__(name, data)
        self.capacity = self.number(self.extract("capacity"))
        self.passive = self.extract("passive")
        self.active = self.extract("active")
        self.flux = self.number(self.extract("flux"))
        self.current = self.number(self.extract("current"))

    def accept(self, heat):
        if self.current + heat <= self.capacity:
            self.current += heat
            return True
        return False

    def cool(self, powered=False):
        def unpack(inp: str):
            r, a = 0, 0
            for part in inp.split("+"):
                if part := part.strip():
                    if part.endswith("%"):
                        r += self.number(part)
                    else:
                        a += self.number(part)
            return r, a

        relative, absolute = unpack(self.passive)
        if powered:
            active_r, active_a = unpack(self.active)
            relative += active_r
            absolute += active_a
        self.current -= self.current * relative
        self.current -= absolute
        self.current = int(max(self.current, 0))  # round down and clamp to 0

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            "Capacity": self.capacity,
            "Passive": self.passive,
            "Active": self.active,
            "Flux": self.flux,
            "Current": self.current,
        }


class Mecha:
    def __init__(self):
        self.description = {}
        self.errors = []
        self.speeds_at_seconds = list(range(16)) + [20, 30, 50, 100]
        self._totalmass = 0
        self.Movement: dict[str, MovementSystem] = {}
        self.Energy: dict[str, EnergySystem] = {}
        self.Heat: dict[str, System] = {}
        self.Offensive: dict[str, System] = {}
        self.Defensive: dict[str, System] = {}
        self.Support: dict[str, System] = {}
        self.Seal: dict[str, System] = {}
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
        self.description, error = mdobj.children.get("Description", MDObj.empty()).confine_to_tables()
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
