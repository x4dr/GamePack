from itertools import product
from typing import Dict, List, Optional, Any, Union, Tuple, Iterable

from gamepack.MDPack import MDObj
from gamepack.endworld.HeatSystem import HeatSystem
from gamepack.endworld.EnergySystem import EnergySystem
from gamepack.endworld.MovementSystem import MovementSystem
from gamepack.endworld.SealSystem import SealSystem
from gamepack.endworld.System import System


class Mecha:
    def __init__(self):
        self.description: Dict[str, Any] = {}
        self.errors: List[str] = []
        self.speeds_at_seconds = list(range(16)) + [20, 30, 50, 100]
        self._totalmass = 0.0
        self.Movement: Dict[str, MovementSystem] = {}
        self.Energy: Dict[str, EnergySystem] = {}
        self.Heat: Dict[str, HeatSystem] = {}
        self.Offensive: Dict[str, System] = {}
        self.Defensive: Dict[str, System] = {}
        self.Support: Dict[str, System] = {}
        self.Seal: Dict[str, SealSystem] = {}

        # Helper for iteration
        self._categories: List[str] = [
            "Movement",
            "Energy",
            "Heat",
            "Offensive",
            "Defensive",
            "Support",
            "Seal",
        ]

        self.heatflux = 0.0
        self.loadouts: Dict[str, List[Union[System, str]]] = {}

    def get_systems_by_category(self, category: str) -> Dict[str, Any]:
        if category == "Movement":
            return self.Movement
        if category == "Energy":
            return self.Energy
        if category == "Heat":
            return self.Heat
        if category == "Offensive":
            return self.Offensive
        if category == "Defensive":
            return self.Defensive
        if category == "Support":
            return self.Support
        if category == "Seal":
            return self.Seal
        return {}

    @classmethod
    def from_mdobj(cls, mdobj: MDObj) -> "Mecha":
        instance = cls()

        def flash(err: str):
            instance.errors.append(err)

        if mdobj.plaintext.strip():
            flash("Loose Text: " + mdobj.plaintext)

        for t in mdobj.tables:
            if t:
                flash("Loose Table:" + t.to_md())

        desc_node = mdobj.children.get("Description", MDObj.empty())
        details, errors = desc_node.confine_to_tables()
        instance.description = details
        for e in errors:
            flash(e)

        systems_node = mdobj.children.get("Systems", MDObj.empty())
        for key in instance._categories:
            sys_node: MDObj = systems_node.children.get(key, MDObj.empty())
            tables, errs = sys_node.confine_to_tables(True)
            for e in errs:
                flash(e)

            target_dict = instance.get_systems_by_category(key)
            for k, v in tables.items():
                if isinstance(v, dict):
                    target_dict[k] = System.create(key, k, v)

        loadouts_node: MDObj = mdobj.children.get("Loadouts", MDObj.empty())
        for loadout_name, loadout_node in loadouts_node.children.items():
            instance.loadouts[loadout_name.title()] = instance.process_loadout(
                loadout_node.plaintext
            )
        if "Default" not in instance.loadouts:
            default_loadout: List[Union[System, str]] = []
            default_loadout.extend(instance.Movement.values())
            default_loadout.extend(instance.Heat.values())
            default_loadout.extend(instance.Defensive.values())
            default_loadout.extend(instance.Offensive.values())
            default_loadout.extend(instance.Support.values())
            instance.loadouts["Default"] = default_loadout

        return instance

    @property
    def total_mass(self) -> float:
        mass_sum = 0.0
        for key in self._categories:
            for s in self.get_systems_by_category(key).values():
                if isinstance(s, System):
                    mass_sum += s.total_mass
        return mass_sum

    def get_system(self, name: str) -> Optional[System]:
        for key in self._categories:
            cat = self.get_systems_by_category(key)
            if name in cat:
                return cat[name]
        return None

    def speeds(self) -> Dict[str, Any]:
        result = {}
        for mname, msys in self.Movement.items():
            if not msys.is_active():
                continue
            speeds_list = msys.speeds(self.total_mass)
            final = speeds_list[-1]
            s = {str(x): speeds_list[x] for x in range(min(121, len(speeds_list)))}

            result[mname] = {
                "speeds": s,
                "topspeed": final,
                "acceleration_time": len(speeds_list),
                "g": (speeds_list[1] if len(speeds_list) > 1 else 0.0) / 9.81,
            }
        return result

    def to_md(self) -> str:
        return self.to_mdobj().to_md()

    def to_mdobj(self) -> MDObj:
        def flash(err: str):
            self.errors.append(err)

        description = MDObj(
            "",
            flash=flash,
            header="Description",
        )
        for k, v in self.description.items():
            description.add_child(MDObj(str(v), flash=flash, header=k))

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
        systems_mdo = MDObj.empty()
        for key in self._categories:
            sys_dict = self.get_systems_by_category(key)
            if key in System.registry:
                table = System.registry[key].as_table(sys_dict.values())
                systems_mdo.add_child(MDObj("", tables=[table], header=key))
        return systems_mdo

    def process_loadout(self, plaintext: str) -> List[Union[System, str]]:
        available_systems: Dict[str, System] = {}
        for key in self._categories:
            if key == "Energy":
                continue
            available_systems.update(self.get_systems_by_category(key))

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

        prio: List[Tuple[Union[System, str], float]] = []
        for candidate in plaintext.split(","):
            candidate = candidate.strip()
            if not candidate:
                continue
            if candidate.startswith("[") and candidate.endswith("]"):
                continue
            if candidate not in available_systems:
                candidate_q = candidate + "?" * max(
                    0, 3 - len(candidate) + len(candidate.rstrip("?"))
                )
                prio.append((candidate_q, 0.0))
            else:
                sys = available_systems[candidate]
                prio.append((sys, sys.energy))

        budgets_list = sorted(list(budgets))

        result: List[Union[System, str]] = []
        budget_iter = iter(budgets_list)
        try:
            current_budget = next(budget_iter)
        except StopIteration:
            current_budget = 0.0

        used = 0.0

        for item, cost in prio:
            if used + cost > current_budget:
                result.append(f"[{current_budget}]")
                used = 0.0
                try:
                    current_budget = next(budget_iter)
                except StopIteration:
                    pass
            result.append(item)
            used += cost
        result.append(f"[{current_budget}]")
        return result

    def fluxmax(self) -> float:
        flux = 0.0
        for h in self.Heat.values():
            if h.is_active():
                flux += h.flux
        return flux

    def add_heat(self, amt: float) -> float:
        systems = list(self.Heat.values())
        for sys in systems:
            if not sys.is_active():
                continue
            amt = sys.add_heat(amt)
            if amt == 0:
                break
        return amt

    def tick_heat(self) -> Dict[str, float]:
        thermals = {}
        for h in self.Heat.values():
            thermals[h.name] = h.tick()
        return thermals

    def move_heat(self, source_name: str, target_name: str, amount: float) -> float:
        if source_name in self.Heat and target_name in self.Heat:
            source = self.Heat[source_name]
            target = self.Heat[target_name]
            amount_withdrawn = source.withdraw_heat(amount)
            overage = target.add_heat(amount_withdrawn)
            final_overage = self.add_heat(overage)
            return final_overage
        raise KeyError(
            f"Transfer from {source_name} to {target_name} failed: Unknown System"
        )

    def energy_budget(self) -> float:
        budget = 0.0
        for e in self.Energy.values():
            budget += e.provide()
        return budget

    def energy_total(self) -> float:
        total = 0.0
        for e in self.Energy.values():
            total += 0.0 if e.is_disabled() else e.energy
        return total

    def energy_allocation(
        self, loadout: Optional[str] = None
    ) -> Tuple[List[System], int]:
        budget = self.energy_budget()

        if not self.loadouts:
            all_systems: List[Union[System, str]] = []
            for key in self._categories:
                for s in self.get_systems_by_category(key).values():
                    if isinstance(s, System):
                        all_systems.append(s)
            all_systems.sort(key=lambda s: s.name if isinstance(s, System) else str(s))
            self.loadouts["Default"] = all_systems

        if loadout is None:
            loadout_key = str(self.description.get("Loadout", ""))
            if loadout_key not in self.loadouts:
                loadout = list(self.loadouts.keys())[0] if self.loadouts else "Default"
            else:
                loadout = loadout_key

        activated = 0
        loadout_items = self.loadouts.get(loadout, [])
        loadout_systems = [
            x for x in loadout_items if isinstance(x, System) and x.is_active()
        ]

        for s in loadout_systems:
            budget -= s.energy
            if budget < 0:
                break
            activated += 1

        return loadout_systems, activated

    def get_syscat(self, name: str) -> Dict[str, System]:
        if name == "Generic":
            res: Dict[str, System] = {}
            res.update(self.Offensive)
            res.update(self.Defensive)
            res.update(self.Support)
            return res

        return self.get_systems_by_category(name)

    def use_system(self, systemtype: str, name: str, parameter: Optional[Any]):
        syscat = self.get_syscat(systemtype.capitalize())
        sys = syscat.get(name)
        if not sys:
            return
        heat = sys.use(parameter)
        self.heatflux += self.add_heat(heat)

    def flux_baseload(self):
        for key in self._categories:
            for sys in self.get_systems_by_category(key).values():
                if isinstance(sys, System) and sys.is_active():
                    self.heatflux += sys.heats.get("heat0", 0.0)

    # Dashboard Helpers
    def current_top_speed(self) -> float:
        data = self.speeds()
        max_s = 0.0
        for sys_data in data.values():
            if sys_data["topspeed"] > max_s:
                max_s = sys_data["topspeed"]
        return max_s

    def current_flux(self) -> float:
        return self.heatflux

    def energy_output(self) -> float:
        return self.energy_budget()
