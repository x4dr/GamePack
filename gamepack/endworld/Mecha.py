from itertools import product
from typing import Dict, List, Optional, Any, Union, Tuple, Iterable, Callable

from gamepack.BaseCharacter import BaseCharacter
from gamepack.MDPack import MDObj
from .EnergySystem import EnergySystem
from .HeatSystem import HeatSystem
from .MovementSystem import MovementSystem
from .SealSystem import SealSystem
from .System import System


class Mecha(BaseCharacter):
    description: Dict[str, Any]
    speeds_at_seconds: List[int]
    _totalmass: float
    Movement: Dict[str, MovementSystem]
    Energy: Dict[str, EnergySystem]
    Heat: Dict[str, HeatSystem]
    Offensive: Dict[str, System]
    Defensive: Dict[str, System]
    Support: Dict[str, System]
    Seal: Dict[str, SealSystem]
    Sectors: Dict[str, Dict[str, Any]]
    _categories: List[str]
    heatflux: float
    loadouts: Dict[str, List[Union[System, str]]]

    def __init__(self):
        super().__init__()
        self.description: Dict[str, Any] = {}
        self.speeds_at_seconds = list(range(16)) + [20, 30, 50, 100]
        self._totalmass = 0.0
        self.Movement: Dict[str, MovementSystem] = {}
        self.Energy: Dict[str, EnergySystem] = {}
        self.Heat: Dict[str, HeatSystem] = {}
        self.Offensive: Dict[str, System] = {}
        self.Defensive: Dict[str, System] = {}
        self.Support: Dict[str, System] = {}
        self.Seal: Dict[str, SealSystem] = {}
        self.Sectors: Dict[str, Dict[str, Any]] = {}

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
        self.pending_heat = 0.0
        self.fluxpool = 0.0
        self.flux_used = 0.0
        self._turn = 0
        self.loadouts: Dict[str, List[Union[System, str]]] = {}

        self._current_speed = 0.0
        self._target_speed = 0.0
        self._fluxpool = 0.0
        self._pending_heat = 0.0

    @staticmethod
    def load_system_data(name: str, category: str) -> Dict[str, Any]:
        """Load base system data from the wiki library."""
        from gamepack.WikiPage import WikiPage

        # Try to find the system in wiki/systems/<category>/<name>.md
        page_name = f"systems/{category.lower()}/{name}"
        page = WikiPage.load_locate(page_name)
        if page:
            mdobj = page.md()
            tables, _ = mdobj.confine_to_tables(True)
            # Return the first table found as a dict
            for k, v in tables.items():
                if isinstance(v, dict):
                    return v
        return {}

    @classmethod
    def from_mdobj(
        cls, mdobj: MDObj, flash_func: Optional[Callable[[str], None]] = None
    ) -> "Mecha":
        instance = cls()

        def flash(err: str):
            if flash_func:
                flash_func(err)
            instance.errors.append(err)

        if mdobj.plaintext.strip():
            flash("Loose Text: " + mdobj.plaintext)

        for t in mdobj.tables:
            if t:
                flash("Loose Table:" + t.to_md())

        desc_node = mdobj.children.get("Description", MDObj.empty())
        details, errors = desc_node.confine_to_tables()

        # Remove ephemeral fields from description to keep MD clean
        ephemeral = {
            "Turn",
            "Current Speed",
            "Target Speed",
            "Flux Pool",
            "Pending Heat",
        }
        instance.description = {k: v for k, v in details.items() if k not in ephemeral}

        for e in errors:
            flash(e)

        # Restore state from description
        # (Ephemeral state is now handled by the replay engine)

        systems_node = mdobj.children.get("Systems", MDObj.empty())

        for key in instance._categories:
            sys_node: MDObj = systems_node.children.get(key, MDObj.empty())
            tables, errs = sys_node.confine_to_tables(True)

            for e in errs:
                flash(e)

            for k, v in tables.items():
                if isinstance(v, dict):
                    # Load base data and apply overrides
                    base_data = instance.load_system_data(k, key)
                    final_data = base_data.copy()
                    final_data.update(v)

                    if key == "Movement":
                        instance.Movement[k] = MovementSystem(k, final_data)
                    elif key == "Energy":
                        instance.Energy[k] = EnergySystem(k, final_data)
                    elif key == "Heat":
                        instance.Heat[k] = HeatSystem(k, final_data)
                    elif key == "Seal":
                        instance.Seal[k] = SealSystem(k, final_data)
                    elif key == "Offensive":
                        instance.Offensive[k] = System(k, final_data)
                    elif key == "Defensive":
                        instance.Defensive[k] = System(k, final_data)
                    elif key == "Support":
                        instance.Support[k] = System(k, final_data)

        sectors_node: MDObj = mdobj.children.get("Sectors", MDObj.empty())
        sectors, errs = sectors_node.confine_to_tables(True)
        for e in errs:
            flash(e)
        for k, v in sectors.items():
            if isinstance(v, dict):
                instance.Sectors[k] = v

        loadouts_node: MDObj = mdobj.children.get("Loadouts", MDObj.empty())
        for loadout_name, loadout_node in loadouts_node.children.items():
            instance.loadouts[loadout_name.title()] = instance.process_loadout(
                loadout_node.plaintext
            )
        if "Default" not in instance.loadouts:
            default_loadout: List[Union[System, str]] = []
            default_loadout.extend(list(instance.Energy.values()))
            default_loadout.extend(list(instance.Movement.values()))
            default_loadout.extend(list(instance.Heat.values()))
            default_loadout.extend(list(instance.Defensive.values()))
            default_loadout.extend(list(instance.Offensive.values()))
            default_loadout.extend(list(instance.Support.values()))
            instance.loadouts["Default"] = default_loadout

        return instance

    @property
    def total_mass(self) -> float:
        mass_sum = 0.0
        for m in self.Movement.values():
            mass_sum += m.total_mass
        for e in self.Energy.values():
            mass_sum += e.total_mass
        for h in self.Heat.values():
            mass_sum += h.total_mass
        for o in self.Offensive.values():
            mass_sum += o.total_mass
        for d in self.Defensive.values():
            mass_sum += d.total_mass
        for s in self.Support.values():
            mass_sum += s.total_mass
        for sl in self.Seal.values():
            mass_sum += sl.total_mass
        return mass_sum

    @property
    def systems(self) -> Dict[str, Dict[str, System]]:
        return {
            "Movement": self.Movement,  # type: ignore
            "Energy": self.Energy,  # type: ignore
            "Heat": self.Heat,  # type: ignore
            "Offensive": self.Offensive,
            "Defensive": self.Defensive,
            "Support": self.Support,
            "Seal": self.Seal,  # type: ignore
        }

    def get_system(self, name: str) -> Optional[System]:
        if name in self.Movement:
            return self.Movement[name]
        if name in self.Energy:
            return self.Energy[name]
        if name in self.Heat:
            return self.Heat[name]
        if name in self.Offensive:
            return self.Offensive[name]
        if name in self.Defensive:
            return self.Defensive[name]
        if name in self.Support:
            return self.Support[name]
        if name in self.Seal:
            return self.Seal[name]
        return None

    def speeds(self) -> Dict[str, Any]:
        result = {}
        for mname, msys in self.Movement.items():
            if msys.is_active():
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

    def to_mdobj(self) -> MDObj:
        def flash(err: str):
            self.errors.append(err)

        # Update description with current state

        description = MDObj(
            "",
            flash=flash,
            header="Description",
        )
        for k, v in self.description.items():
            description.add_child(MDObj(str(v), flash=flash, header=k))

        systems = self.systems_mdobj().with_header("Systems")

        sectors = MDObj.empty().with_header("Sectors")
        if self.Sectors:
            from gamepack.MDPack import MDTable

            rows = []
            headers = ["Damage", "Malfunctions"]
            for name, data in self.Sectors.items():
                rows.append(
                    [
                        name,
                        str(data.get("Damage", 0)),
                        str(data.get("Malfunctions", "")),
                    ]
                )
            sectors.tables.append(MDTable(rows, [""] + headers))

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
        mdo.add_child(sectors)
        mdo.add_child(loadouts)
        return mdo

    def systems_mdobj(self) -> MDObj:
        systems_mdo = MDObj.empty()
        cat_data: List[Tuple[str, Iterable[System], type[System]]] = [
            ("Movement", self.Movement.values(), MovementSystem),
            ("Energy", self.Energy.values(), EnergySystem),
            ("Heat", self.Heat.values(), HeatSystem),
            ("Offensive", self.Offensive.values(), System),
            ("Defensive", self.Defensive.values(), System),
            ("Support", self.Support.values(), System),
            ("Seal", self.Seal.values(), SealSystem),
        ]
        for key, vals, cls in cat_data:
            # Clear 'Enabled' status for persistence if it's considered ephemeral
            # We clone the objects to avoid side effects on the live mecha
            # Actually, System.to_dict() is used by cls.as_table
            # I'll just override the Enabled value in the resulting table rows
            table = cls.as_table(vals)
            try:
                enabled_idx = table.headers.index("Enabled")
                for row in table.rows:
                    row[enabled_idx] = "[ ]"
            except (ValueError, IndexError):
                pass

            systems_mdo.add_child(MDObj("", tables=[table], header=key))
        return systems_mdo

    def process_loadout(self, plaintext: str) -> List[Union[System, str]]:
        available_systems: Dict[str, System] = {}
        available_systems.update(self.Movement)
        available_systems.update(self.Energy)
        available_systems.update(self.Heat)
        available_systems.update(self.Offensive)
        available_systems.update(self.Defensive)
        available_systems.update(self.Support)
        available_systems.update(self.Seal)

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
                result.append(f"[{current_budget:g}]")
                used = 0.0
                try:
                    current_budget = next(budget_iter)
                except StopIteration:
                    pass
            result.append(item)
            used += cost
        result.append(f"[{current_budget:g}]")
        return result

    def fluxmax(self) -> float:
        flux = 0.0
        for h in self.Heat.values():
            if h.is_active():
                flux += h.flux
        return flux

    def add_heat(self, amt: float) -> float:
        for sys in self.Heat.values():
            if sys.is_active():
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

    def energy_demand(self) -> float:
        """Total energy cost of all systems that are active or booting."""
        total = 0.0
        for cat in self._categories:
            for sys in self.get_syscat(cat).values():
                # Heat systems only cost energy when active (booting is passive/free)
                if sys.systype == "heat":
                    if sys.is_active():
                        total += sys.energy * sys.amount
                elif sys.systype in ["movement", "generic", "seal"]:
                    if sys.is_active() or sys.is_booting():
                        total += sys.energy * sys.amount
        return total

    def energy_allocation(
        self, loadout: Optional[str] = None
    ) -> Tuple[List[System], int]:
        budget = self.energy_budget()

        if not self.loadouts:
            all_systems: List[Union[System, str]] = []
            all_systems.extend(self.Energy.values())
            all_systems.extend(self.Movement.values())
            all_systems.extend(self.Heat.values())
            all_systems.extend(self.Offensive.values())
            all_systems.extend(self.Defensive.values())
            all_systems.extend(self.Support.values())
            all_systems.extend(self.Seal.values())
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
            x
            for x in loadout_items
            if isinstance(x, System)
            and x.is_active()
            and not isinstance(x, EnergySystem)
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

        if name == "Movement":
            return self.Movement  # type: ignore
        if name == "Energy":
            return self.Energy  # type: ignore
        if name == "Heat":
            return self.Heat  # type: ignore
        if name == "Offensive":
            return self.Offensive
        if name == "Defensive":
            return self.Defensive
        if name == "Support":
            return self.Support
        if name == "Seal":
            return self.Seal  # type: ignore
        return {}

    def fluxpool_max(self) -> float:
        """Sum of flux of all heat systems (including passive and active)."""
        return sum(h.flux for h in self.Heat.values())

    def assign_heat(self, name: str, amount: float) -> Tuple[float, str]:
        """Assign heat from fluxpool to a specific heat system. Returns (taken, log_msg)."""
        if name not in self.Heat:
            return 0.0, ""

        sys = self.Heat[name]
        # Heat systems can be assigned heat even if inactive (e.g. Sinks)

        # available_flux is only used when moving heat TO a system?
        # Actually the user says "at no point and in no ordering can the flux pool go over its maximum or under 0"
        # and "the sliders can move however they want and that all happens clientside in js"
        # The server just records the delta.

        # If amount > 0, we are moving heat from pool to system.
        if amount > 0:
            can_take = min(amount, self.fluxpool, sys.spare_capacity())
            if can_take <= 0:
                return 0.0, "No capacity or flux remaining in pool"
            sys.add_heat(can_take)
            self.fluxpool -= can_take
            return can_take, f"Assigned {can_take:g} heat from fluxpool to {name}"
        elif amount < 0:
            # Transfer back to pool
            can_give = min(abs(amount), sys.current)
            if can_give <= 0:
                return 0.0, "System is empty"
            sys.current -= can_give
            self.fluxpool += can_give
            return -can_give, f"Assigned {can_give:g} heat from {name} to fluxpool"
        return 0.0, ""

    def use_system(self, systemtype: str, name: str, parameter: Optional[Any]) -> float:
        syscat = self.get_syscat(systemtype.capitalize())
        sys = syscat.get(name)
        if not sys:
            return 0.0
        heat = sys.use(parameter)
        self.fluxpool += heat
        return heat

    def flux_baseload(self) -> float:
        """Calculate the baseload heat generated by all active systems."""
        added = 0.0
        for cat in self._categories:
            for sys in self.get_syscat(cat).values():
                if sys.is_active():
                    # Sum all heat values for the system
                    added += sum(sys.heats.values()) * sys.amount
        return added

    @property
    def turn(self) -> int:
        return self._turn

    @turn.setter
    def turn(self, value: int):
        self._turn = value

    @property
    def current_speed(self) -> float:
        return self._current_speed

    @current_speed.setter
    def current_speed(self, value: float):
        self._current_speed = value

    @property
    def target_speed(self) -> float:
        return self._target_speed

    @target_speed.setter
    def target_speed(self, value: float):
        self._target_speed = value

    @property
    def fluxpool(self) -> float:
        return self._fluxpool

    @fluxpool.setter
    def fluxpool(self, value: float):
        self._fluxpool = value

    @property
    def pending_heat(self) -> float:
        return self._pending_heat

    @pending_heat.setter
    def pending_heat(self, value: float):
        self._pending_heat = value

    def apply_event(self, event: Dict[str, Any]):
        """Apply a single delta event to the mecha state."""
        etype = event.get("type")
        if etype == "SYSTEM_TOGGLE":
            sys = self.get_system(event["name"])
            if sys:
                sys.enabled = "[x]" if event["state"] == "active" else "[ ]"
        elif etype == "LOADOUT_APPLY":
            self.apply_loadout(event["name"])
        elif etype == "HEAT_ASSIGNMENT":
            self.assign_heat(event["name"], event["amount"])
        elif etype == "SPEED_TARGET":
            self.target_speed = float(event["value"])
        elif etype == "MANUAL_HEAT":
            self.pending_heat = float(event["value"])
        elif etype == "BOOT_ROLL":
            sys = self.get_system(event["name"])
            if sys:
                sys.boot_roll = int(event["value"])
        elif etype == "MOVEMENT":
            if "value" in event:
                self.current_speed = float(event["value"])
        elif etype == "HEAT_GEN":
            if "value" in event:
                self.fluxpool += float(event["value"])
        elif etype == "HEAT_DISSIPATION":
            # Dissipation from storage systems
            if "values" in event:
                for name, amt in event["values"].items():
                    sys = self.Heat.get(name)
                    if sys:
                        sys.withdraw_heat(amt)
        elif etype == "TURN_COMMIT":
            self.turn = int(event["turn"])

    def apply_loadout(self, loadout_name: str):
        """Enable systems in the loadout, disable others."""
        if loadout_name not in self.loadouts:
            return

        # Reset all systems to disabled
        for cat in self._categories:
            for sys in self.get_syscat(cat).values():
                sys.enabled = "[ ]"

        # Enable those in the loadout
        loadout_items = self.loadouts[loadout_name]
        for item in loadout_items:
            if isinstance(item, System):
                item.enabled = "[x]"
                item.boot_progress = item.activation_rounds

    def replay(self, events: List[Dict[str, Any]], turn_limit: Optional[int] = None):
        """Reconstitute state from a list of events."""
        print(f"DEBUG: Replaying {len(events)} events, turn_limit={turn_limit}")
        # Reset ephemeral state to base before replay

        self._turn = 0
        self._current_speed = 0.0
        self._target_speed = 0.0
        self._fluxpool = 0.0
        self._flux_used = 0.0
        self._pending_heat = 0.0
        for cat in self._categories:
            for sys in self.get_syscat(cat).values():
                sys.reset_ephemeral()
                sys.enabled = "[ ]"  # Default to everything off if it's ephemeral

        for event in events:
            if turn_limit is not None and event.get("type") == "TURN_COMMIT":
                if event.get("turn", 0) > turn_limit:
                    break
            self.apply_event(event)

    def next_turn(self) -> Dict[str, Any]:
        """Process the transition to the next turn."""
        print(
            f"DEBUG: next_turn() START, current turn {self.turn}, current pool {self.fluxpool}"
        )
        self.turn += 1

        self.flux_used = 0.0
        events = []
        overheated = False

        # 1. Movement Transition (5 seconds = 50 steps of 0.1s)
        old_speed = self.current_speed
        target = self.target_speed
        new_speed = old_speed

        active_move = [m for m in self.Movement.values() if m.is_active()]
        if active_move:
            # Use the first active movement system for transition
            ms = active_move[0]
            full_curve = ms.speeds(self.total_mass, initial_speed=old_speed)
            if target > old_speed:
                # Accelerating
                new_speed = full_curve[min(5, len(full_curve) - 1)]
                if new_speed > target:
                    new_speed = target
            elif target < old_speed:
                # Decelerating (simplified: drop speed towards target)
                # In the future, use braking force/anchor
                new_speed = (
                    old_speed - (old_speed - target) * 0.5
                )  # Placeholder: 50% drop per turn
                if new_speed < target:
                    new_speed = target
        else:
            # No active movement: decelerate rapidly
            new_speed = old_speed * 0.5
            if new_speed < 0.1:
                new_speed = 0.0

        self.current_speed = new_speed
        events.append(
            {
                "type": "MOVEMENT",
                "value": new_speed,
                "message": f"Speed: {old_speed:g} -> {new_speed:g} km/h (Target: {target:g})",
            }
        )

        # 2. Heat & Energy
        # Add pending heat before ticking
        if self.pending_heat != 0:
            self.fluxpool += self.pending_heat
            events.append(
                {
                    "type": "HEAT_GEN",
                    "value": self.pending_heat,
                    "message": f"Manual heat adjustment: {self.pending_heat:g}",
                }
            )

        # Add baseload heat from all active systems
        # This fills the fluxpool for the turn we just finished
        baseload = self.flux_baseload()
        if baseload > 0:
            self.fluxpool += baseload
            events.append(
                {
                    "type": "HEAT_GEN",
                    "value": baseload,
                    "message": f"Generated {baseload:g} baseload heat.",
                }
            )

        # Check for unassigned heat penalties before ticking
        print(
            f"DEBUG: Checking overheat: pool={self.fluxpool}, max={self.fluxpool_max()}"
        )
        if self.fluxpool > self.fluxpool_max():
            overheated = True
            overage = self.fluxpool - self.fluxpool_max()
            events.append(
                {
                    "type": "PENALTY",
                    "message": f"Unassigned heat overage: {overage:g}! Damage/Shutdown imminent.",
                }
            )
            # Find the first power generator for damage suggestion
            target_gen = None
            if self.Energy:
                # MD usually follows iteration order of the dict if parsed correctly
                target_gen = list(self.Energy.keys())[0]

            events.append(
                {"type": "OVERHEAT", "target": target_gen, "overage": overage}
            )

        # Heat systems dissipate heat from their storage
        thermals = self.tick_heat()
        dissipated = sum(thermals.values())
        events.append(
            {
                "type": "HEAT_DISSIPATION",
                "values": thermals,
                "message": f"Dissipated {dissipated:g} heat from storage.",
            }
        )

        # Process system booting
        booted = []
        for cat in self._categories:
            for sys in self.get_syscat(cat).values():
                if sys.is_booting():
                    # If it needs a roll and we are at the last round of booting, block progress
                    if (
                        sys.needs_roll()
                        and sys.boot_progress >= sys.activation_rounds - 1
                    ):
                        events.append(
                            {
                                "type": "SYSTEM",
                                "message": f"{sys.name} waiting for activation roll.",
                            }
                        )
                        continue

                    # Advance progress
                    progress_gain = 1
                    if sys.boot_roll is not None and sys.breakpoints:
                        # For every breakpoint reached, potentially gain extra progress
                        if any(sys.boot_roll >= bp for bp in sys.breakpoints):
                            progress_gain += 1

                    sys.boot_progress += progress_gain
                    if sys.boot_progress >= sys.activation_rounds:
                        booted.append(sys.name)
                        sys.boot_progress = sys.activation_rounds  # Cap it
                        events.append(
                            {"type": "SYSTEM", "message": f"{sys.name} online."}
                        )

        # Reset per-turn flux tracking
        self.heatflux = 0.0
        self.pending_heat = 0.0
        for h in self.Heat.values():
            h.flux_used = 0.0

        return {
            "turn": self.turn,
            "thermals": thermals,
            "new_flux": self.fluxpool,
            "booted_systems": booted,
            "events": events,
            "overheated": overheated,
        }

    def projected_flux(self) -> float:
        """Calculate the projected heat flux for the next turn."""
        flux = 0.0
        for cat in self._categories:
            for sys in self.get_syscat(cat).values():
                # System will be active if it's already active OR if it's booting and will finish
                will_be_active = sys.is_active()
                if sys.is_booting():
                    # Simplified logic: if it doesn't need a roll or has one, it will advance
                    if (
                        not sys.needs_roll()
                        or sys.boot_progress < sys.activation_rounds - 1
                    ):
                        if sys.boot_progress + 1 >= sys.activation_rounds:
                            will_be_active = True

                if will_be_active:
                    flux += sum(sys.heats.values()) * sys.amount

        # Add manual pending heat
        flux += self.pending_heat
        return flux

    def projected_energy(self) -> float:
        """Calculate the projected energy budget for the next turn."""
        # This is more complex because energy allocation depends on loadouts
        # For now, let's just return the current budget as a placeholder
        return self.energy_budget()

    # Dashboard Helpers
    def current_top_speed(self) -> float:
        data = self.speeds()
        max_s = 0.0
        for sys_data in data.values():
            if sys_data["topspeed"] > max_s:
                max_s = sys_data["topspeed"]
        return max_s

    def current_flux(self) -> float:
        """current flux"""
        return self.heatflux

    def energy_output(self) -> float:
        return self.energy_budget()
