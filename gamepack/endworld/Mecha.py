"""Mecha module for the Endworld game system.

Defines the Mecha class, a piloted combat chassis with complex subsystem
management including movement, energy, heat, offensive, defensive,
support, and seal systems.
"""

import contextlib
from collections.abc import Mapping
from itertools import product
from typing import TYPE_CHECKING, Any

from gamepack.BaseCharacter import BaseCharacter
from gamepack.MDPack import MDObj

from .EnergySystem import EnergySystem
from .HeatSystem import HeatSystem
from .MovementSystem import MovementSystem
from .OffensiveSystem import OffensiveSystem
from .SealSystem import SealSystem
from .System import System

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable


class Mecha(BaseCharacter):
    """A piloted combat mecha with multiple subsystem categories.

    Manages Movement, Energy, Heat, Offensive, Defensive, Support, and
    Seal systems. Supports loadout-based energy allocation, heat tracking,
    speed calculations, and event-driven state replay.
    """

    description: dict[str, Any]
    speeds_at_seconds: list[int]
    _totalmass: float
    Movement: dict[str, MovementSystem]
    Energy: dict[str, EnergySystem]
    Heat: dict[str, HeatSystem]
    Offensive: dict[str, OffensiveSystem]
    Defensive: dict[str, System]
    Support: dict[str, System]
    Seal: dict[str, SealSystem]
    Sectors: dict[str, dict[str, Any]]
    _categories: list[str]
    loadouts: dict[str, list[System | str]]
    shutoff_counters: dict[str, int]

    def __init__(self) -> None:
        """Initialize an empty Mecha with default system dictionaries."""
        super().__init__()
        self.description: dict[str, Any] = {}
        self.speeds_at_seconds = [*list(range(16)), 20, 30, 50, 100]
        self._totalmass = 0.0
        self.Movement: dict[str, MovementSystem] = {}
        self.Energy: dict[str, EnergySystem] = {}
        self.Heat: dict[str, HeatSystem] = {}
        self.Offensive: dict[str, OffensiveSystem] = {}
        self.Defensive: dict[str, System] = {}
        self.Support: dict[str, System] = {}
        self.Seal: dict[str, SealSystem] = {}
        self.Sectors: dict[str, dict[str, Any]] = {}
        self.shutoff_counters = {}

        self._categories: list[str] = [
            "Movement",
            "Energy",
            "Heat",
            "Offensive",
            "Defensive",
            "Support",
            "Seal",
        ]

        self.pending_heat = 0.0
        self.fluxpool = 0.0
        self._turn = 0
        self.loadouts: dict[str, list[System | str]] = {}

        self._current_speed = 0.0
        self._target_speed = 0.0
        self._fluxpool = 0.0
        self._pending_heat = 0.0

    @staticmethod
    def load_system_data(name: str, category: str) -> dict[str, Any]:
        """Load base system data from the wiki library.

        Searches for the system definition in the wiki under the path
        ``systems/<category>/<name>.md`` and returns the first table
        found as a dictionary.

        Args:
            name: The name of the system to load.
            category: The category folder to search in (e.g. "movement").

        Returns:
            A dictionary of system properties, or an empty dict if not found.

        """
        from gamepack.WikiPage import WikiPage

        # Try to find the system in wiki/systems/<category>/<name>.md
        page_name = f"systems/{category.lower()}/{name}"
        page = WikiPage.load_locate(page_name)
        if page:
            mdobj = page.md()
            tables, _ = mdobj.confine_to_tables(horizontal=True)
            # Return the first table found as a dict
            for _k, v in tables.items():
                if isinstance(v, dict):
                    return v
        return {}

    @classmethod
    def from_mdobj(
        cls,
        mdobj: MDObj,
        flash_func: Callable[[str], None] | None = None,
    ) -> Mecha:
        """Construct a Mecha instance from an MDObj.

        Parses the markdown object to extract description, systems, sectors,
        and loadouts. Systems are loaded from wiki data with overrides applied
        from the markdown tables. A default loadout is generated if none is
        defined.

        Args:
            mdobj: The markdown object to construct the mecha from.
            flash_func: Optional function to call for error messages.

        Returns:
            A new Mecha instance populated with parsed data.

        """
        instance = cls()

        def flash(err: str) -> None:
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
            tables, errs = sys_node.confine_to_tables(horizontal=True)

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
                        instance.Offensive[k] = OffensiveSystem(k, final_data)
                    elif key == "Defensive":
                        instance.Defensive[k] = System(k, final_data)
                    elif key == "Support":
                        instance.Support[k] = System(k, final_data)

        sectors_node: MDObj = mdobj.children.get("Sectors", MDObj.empty())
        sectors, errs = sectors_node.confine_to_tables(horizontal=True)
        for e in errs:
            flash(e)
        for k, v in sectors.items():
            if isinstance(v, dict):
                instance.Sectors[k] = v

        loadouts_node: MDObj = mdobj.children.get("Loadouts", MDObj.empty())
        for loadout_name, loadout_node in loadouts_node.children.items():
            instance.loadouts[loadout_name] = instance.process_loadout(
                loadout_node.plaintext,
            )
        if "Default" not in instance.loadouts:
            default_loadout: list[System | str] = []
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
        """Calculate the total mass of all systems across every category.

        Returns:
            The sum of all system masses as a float.

        """
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
    def systems(self) -> Mapping[str, Mapping[str, System]]:
        """Get all systems organized by category.

        Returns:
            A dictionary mapping category names to their system dictionaries.

        """
        return {
            "Movement": self.Movement,
            "Energy": self.Energy,
            "Heat": self.Heat,
            "Offensive": self.Offensive,
            "Defensive": self.Defensive,
            "Support": self.Support,
            "Seal": self.Seal,
        }

    def get_system(self, name: str) -> System | None:
        """Look up a system by name across all categories.

        Args:
            name: The name of the system to find.

        Returns:
            The matching System instance, or None if not found.

        """
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

    def speeds(self) -> dict[str, Any]:
        """Calculate speed profiles for all active movement systems.

        Returns:
            A dictionary mapping movement system names to their speed
            profiles, including per-second speeds, top speed, acceleration
            time, and G-force.

        """
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
        """Convert the Mecha instance to an MDObj.

        Serializes description, systems, sectors, and loadouts into a
        hierarchical markdown object structure.

        Returns:
            An MDObj representation of the mecha.

        """

        def flash(err: str) -> None:
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
                    ],
                )
            sectors.tables.append(MDTable(rows, ["", *headers]))

        loadouts = MDObj.empty().with_header("Loadouts")
        for loadout_name, prio_list in self.loadouts.items():
            loadouts.add_child(
                MDObj(
                    ", ".join(
                        [x.name if isinstance(x, System) else str(x) for x in prio_list],
                    ),
                ).with_header(loadout_name),
            )
        mdo = MDObj("")
        mdo.add_child(description)
        mdo.add_child(systems)
        mdo.add_child(sectors)
        mdo.add_child(loadouts)
        return mdo

    def systems_mdobj(self) -> MDObj:
        """Generate an MDObj containing all system tables by category.

        Marks all systems as disabled (``[ ]``) for persistence purposes.

        Returns:
            An MDObj with a child node per system category, each
            containing a table of system data.

        """
        systems_mdo = MDObj.empty()
        cat_data: list[tuple[str, Iterable[System], type[System]]] = [
            ("Movement", self.Movement.values(), MovementSystem),
            ("Energy", self.Energy.values(), EnergySystem),
            ("Heat", self.Heat.values(), HeatSystem),
            ("Offensive", self.Offensive.values(), OffensiveSystem),
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
            except ValueError, IndexError:
                pass

            systems_mdo.add_child(MDObj("", tables=[table], header=key))
        return systems_mdo

    def process_loadout(self, plaintext: str) -> list[System | str]:
        """Parse a loadout plaintext string into an ordered system list.

        Splits the plaintext by commas, looks up each candidate in the
        available systems, and budgets energy across possible energy
        configurations.

        Args:
            plaintext: A comma-separated string of system names.

        Returns:
            An ordered list of System instances and budget markers.

        """
        available_systems: dict[str, System] = {}
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
                sum(e.energy * e.amount for e, flag in zip(energies, enabled_flags, strict=False) if flag),
            )

        prio: list[tuple[System | str, float]] = []
        for candidate in plaintext.split(","):
            candidate = candidate.strip()
            if not candidate:
                continue
            if candidate.startswith("[") and candidate.endswith("]"):
                continue
            if candidate not in available_systems:
                candidate_q = candidate + "?" * max(
                    0,
                    3 - len(candidate) + len(candidate.rstrip("?")),
                )
                prio.append((candidate_q, 0.0))
            else:
                sys = available_systems[candidate]
                prio.append((sys, sys.energy))

        budgets_list = sorted(budgets)

        result: list[System | str] = []
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
                with contextlib.suppress(StopIteration):
                    current_budget = next(budget_iter)
            result.append(item)
            used += cost
        result.append(f"[{current_budget:g}]")
        return result

    def fluxmax(self) -> float:
        """Calculate the maximum heat flux capacity from active heat systems.

        Returns:
            The total flux capacity as a float.

        """
        flux = 0.0
        for h in self.Heat.values():
            if h.is_active():
                flux += h.flux
        return flux

    def add_heat(self, amt: float) -> float:
        """Distribute heat across all active heat systems.

        Each active heat system absorbs as much heat as it can before
        passing the remainder to the next.

        Args:
            amt: The amount of heat to distribute.

        Returns:
            The remaining heat that could not be absorbed.

        """
        for sys in self.Heat.values():
            if sys.is_active():
                amt = sys.add_heat(amt)
                if amt == 0:
                    break
        return amt

    def tick_heat(self) -> dict[str, float]:
        """Advance the heat tick for each heat system (dissipation phase).

        Returns:
            A dictionary mapping heat system names to the amount of heat
            dissipated this tick.

        """
        thermals = {}
        for h in self.Heat.values():
            thermals[h.name] = h.tick()
        return thermals

    def move_heat(self, source_name: str, target_name: str, amount: float) -> float:
        """Transfer heat between two heat systems.

        Withdraws heat from the source system and adds it to the target.
        Any excess that the target cannot absorb is distributed globally.

        Args:
            source_name: Name of the source heat system.
            target_name: Name of the target heat system.
            amount: The amount of heat to transfer.

        Returns:
            The amount of heat successfully transferred.

        Raises:
            KeyError: If either system name is unknown.

        """
        if source_name in self.Heat and target_name in self.Heat:
            source = self.Heat[source_name]
            target = self.Heat[target_name]
            amount_withdrawn = source.withdraw_heat(amount)
            overage = target.add_heat(amount_withdrawn)
            return self.add_heat(overage)
        msg = f"Transfer from {source_name} to {target_name} failed: Unknown System"
        raise KeyError(
            msg,
        )

    def energy_budget(self) -> float:
        """Calculate the total energy currently being provided.

        Returns:
            The total available energy budget as a float.

        """
        budget = 0.0
        for e in self.Energy.values():
            budget += e.provide()
        return budget

    def energy_total(self) -> float:
        """Calculate the total energy capacity from all energy systems.

        Returns:
            The sum of energy values from non-disabled systems.

        """
        total = 0.0
        for e in self.Energy.values():
            total += 0.0 if e.is_disabled() else e.energy
        return total

    def energy_demand(self) -> float:
        """Calculate the total energy demand of all active or booting systems.

        Heat systems only cost energy when active; movement, generic, and
        seal systems also cost energy while booting.

        Returns:
            The total energy demand as a float.

        """
        total = 0.0
        for cat in self._categories:
            for sys in self.get_syscat(cat).values():
                # Heat systems only cost energy when active (booting is passive/free)
                if sys.systype == "heat":
                    if sys.is_active():
                        total += sys.energy * sys.amount
                elif sys.systype in ["movement", "generic", "seal"] and (sys.is_active() or sys.is_booting()):
                    total += sys.energy * sys.amount
        return total

    def energy_allocation(self, loadout: str | None = None) -> tuple[list[System], int]:
        """Allocate energy to systems according to a loadout priority list.

        Systems are activated in loadout priority order until the energy
        budget is exhausted.

        Args:
            loadout: Optional name of the loadout to use. If None, uses
                the loadout specified in the mecha description.

        Returns:
            A tuple of (list of activated systems, number of systems activated).

        """
        budget = self.energy_budget()

        if not self.loadouts:
            all_systems: list[System | str] = []
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
                loadout = next(iter(self.loadouts.keys())) if self.loadouts else "Default"
            else:
                loadout = loadout_key

        activated = 0
        loadout_items = self.loadouts.get(loadout, [])
        loadout_systems = [
            x for x in loadout_items if isinstance(x, System) and x.is_active() and not isinstance(x, EnergySystem)
        ]

        active_systems: list[System] = []
        for s in loadout_systems:
            cost = s.energy * s.amount
            if budget - cost < 0:
                break
            budget -= cost
            active_systems.append(s)
            activated += 1

        return active_systems, activated

    def get_syscat(self, name: str) -> Mapping[str, System]:
        """Get all systems in a named category.

        The special category "Generic" combines Offensive, Defensive,
        and Support systems.

        Args:
            name: The category name (e.g. "Movement", "Heat", "Generic").

        Returns:
            A dictionary of systems in the requested category, or an
            empty dict if the category is unknown.

        """
        if name == "Generic":
            res: dict[str, System] = {}
            res.update(self.Offensive)
            res.update(self.Defensive)
            res.update(self.Support)
            return res

        if name == "Movement":
            return self.Movement
        if name == "Energy":
            return self.Energy
        if name == "Heat":
            return self.Heat
        if name == "Offensive":
            return self.Offensive
        if name == "Defensive":
            return self.Defensive
        if name == "Support":
            return self.Support
        if name == "Seal":
            return self.Seal
        return {}

    def fluxpool_max(self) -> float:
        """Sum of flux capacity of all heat systems (passive and active).

        Returns:
            The total flux capacity across all heat systems.

        """
        return sum(h.flux for h in self.Heat.values())

    def assign_heat(self, name: str, amount: float) -> tuple[float, str]:
        """Assign heat between the flux pool and a specific heat system.

        A positive amount moves heat from the pool to the system;
        a negative amount moves heat back to the pool.

        Args:
            name: The name of the target heat system.
            amount: The amount of heat to move (positive = pool to system,
                negative = system to pool).

        Returns:
            A tuple of (actual amount moved, log message string).

        """
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
        if amount < 0:
            # Transfer back to pool
            can_give = min(abs(amount), sys.current)
            if can_give <= 0:
                return 0.0, "System is empty"
            sys.current -= can_give
            self.fluxpool += can_give
            return -can_give, f"Assigned {can_give:g} heat from {name} to fluxpool"
        return 0.0, ""

    def use_system(self, systemtype: str, name: str, parameter: Any | None) -> float:
        """Activate a system and return the generated heat.

        Args:
            systemtype: The category of the system (e.g. "Offensive").
            name: The name of the system to use.
            parameter: Optional parameter to pass to the system's use method.

        Returns:
            The amount of heat generated by using the system.

        """
        syscat = self.get_syscat(systemtype.capitalize())
        sys = syscat.get(name)
        if not sys:
            return 0.0
        heat = sys.use(parameter)
        self.fluxpool += heat
        return heat

    def flux_baseload(self) -> float:
        """Calculate the baseload heat generated by all active systems.

        Returns:
            The total baseload heat across all active systems.

        """
        added = 0.0
        for cat in self._categories:
            for sys in self.get_syscat(cat).values():
                if sys.is_active():
                    # Sum all heat values for the system
                    added += sum(sys.heats.values()) * sys.amount
        return added

    @property
    def turn(self) -> int:
        """Get the current turn number.

        Returns:
            The current turn count.

        """
        return self._turn

    @turn.setter
    def turn(self, value: int) -> None:
        """Set the current turn number.

        Args:
            value: The turn number to set.

        """
        self._turn = value

    @property
    def current_speed(self) -> float:
        """Get the mecha's current speed.

        Returns:
            The current speed in m/s.

        """
        return self._current_speed

    @current_speed.setter
    def current_speed(self, value: float) -> None:
        """Set the mecha's current speed.

        Args:
            value: The speed value in m/s.

        """
        self._current_speed = value

    @property
    def target_speed(self) -> float:
        """Get the mecha's target speed.

        Returns:
            The target speed in m/s.

        """
        return self._target_speed

    @target_speed.setter
    def target_speed(self, value: float) -> None:
        """Set the mecha's target speed.

        Args:
            value: The target speed in m/s.

        """
        self._target_speed = value

    @property
    def fluxpool(self) -> float:
        """Get the current flux pool level (unallocated heat).

        Returns:
            The current flux pool value.

        """
        return self._fluxpool

    @fluxpool.setter
    def fluxpool(self, value: float) -> None:
        """Set the current flux pool level.

        Args:
            value: The flux pool value to set.

        """
        self._fluxpool = value

    @property
    def pending_heat(self) -> float:
        """Get the amount of pending manual heat.

        Returns:
            The pending heat value.

        """
        return self._pending_heat

    @pending_heat.setter
    def pending_heat(self, value: float) -> None:
        """Set the amount of pending manual heat.

        Args:
            value: The pending heat value to set.

        """
        self._pending_heat = value

    def apply_event(self, event: dict[str, Any]) -> None:
        """Apply a single delta event to the mecha state.

        Supports event types: SYSTEM_TOGGLE, LOADOUT_APPLY,
        HEAT_ASSIGNMENT, SPEED_TARGET, MANUAL_HEAT, BOOT_ROLL,
        MOVEMENT, HEAT_GEN, HEAT_DISSIPATION, and TURN_COMMIT.

        Args:
            event: A dictionary with at minimum a "type" key and
                type-specific data keys.

        """
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

    def apply_loadout(self, loadout_name: str) -> None:
        """Enable systems in the loadout and disable all others.

        Resets all systems to disabled, then enables and starts booting
        each system in the specified loadout.

        Args:
            loadout_name: The name of the loadout to apply.

        """
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

    def replay(self, events: list[dict[str, Any]], turn_limit: int | None = None) -> None:
        """Reconstitute mecha state from a list of delta events.

        Resets all ephemeral state (speed, flux, heat, system states) to
        defaults, then applies each event in order up to an optional
        turn limit.

        Args:
            events: A list of event dictionaries to replay.
            turn_limit: Optional maximum turn number to replay.

        """
        print(f"DEBUG: Replaying {len(events)} events, turn_limit={turn_limit}")
        # Reset ephemeral state to base before replay

        self._turn = 0
        self._current_speed = 0.0
        self._target_speed = 0.0
        self._fluxpool = 0.0
        self._pending_heat = 0.0
        for cat in self._categories:
            for sys in self.get_syscat(cat).values():
                sys.reset_ephemeral()
                sys.enabled = "[ ]"  # Default to everything off if it's ephemeral

        for event in events:
            if turn_limit is not None and event.get("type") == "TURN_COMMIT" and event.get("turn", 0) > turn_limit:
                break
            self.apply_event(event)

    def next_turn(self) -> dict[str, Any]:
        """Process the transition to the next turn with Double-Flux and Shutoff logic.

        Handles movement speed changes, double-flux heat transfer (inbound
        from systems to pool, outbound from pool to sinks), global pool
        overheat checking, heat dissipation, and turn state reset.

        Returns:
            A dictionary containing the new turn state including speed,
            flux levels, dissipation data, and any events generated.

        """
        self.turn += 1
        events = []
        overheated = False

        # 1. Movement
        old_speed = self.current_speed
        target = self.target_speed
        new_speed = old_speed
        active_move = [m for m in self.Movement.values() if m.is_active()]
        if active_move:
            ms = active_move[0]
            # Use 5 seconds of movement (Turn length)
            full_curve = ms.speeds(self.total_mass, initial_speed=old_speed)
            if target > old_speed:
                # Accelerate towards target
                new_speed = full_curve[min(5, len(full_curve) - 1)]
                new_speed = min(new_speed, target)
            elif target < old_speed:
                # Decelerate (Braking Force)
                new_speed = old_speed - (old_speed - target) * 0.5
                new_speed = max(new_speed, target)
        else:
            new_speed = old_speed * 0.5
            if new_speed < 0.1:
                new_speed = 0.0
        self.current_speed = new_speed
        events.append({"type": "MOVEMENT", "value": new_speed})

        # 2. Double-Flux Heat Transfer Logic
        total_flux_cap = self.fluxpool_max()

        # Phase A: Inbound (Systems -> Pool)
        remaining_inbound_flux = total_flux_cap

        # Add manual pending heat to pool first (e.g. firing weapons)
        manual_heat = self.pending_heat
        moved_manual = min(manual_heat, remaining_inbound_flux)
        self.fluxpool += moved_manual
        remaining_inbound_flux -= moved_manual
        internal_manual_overheat = manual_heat - moved_manual

        # Update Shutoff Counters and calculate system heat
        for cat in self._categories:
            for sys in self.get_syscat(cat).values():
                gen = 0.0
                if isinstance(sys, EnergySystem):
                    if sys.is_active():
                        gen = sys.generated_heat()
                        self.shutoff_counters[sys.name] = sys.shutoff
                    elif self.shutoff_counters.get(sys.name, 0) > 0:
                        gen = sys.generated_heat()
                        self.shutoff_counters[sys.name] -= 1
                elif sys.is_active():
                    gen = sum(sys.heats.values()) * sys.amount
                    events.append(
                        {
                            "type": "SHUTOFF_DELAY",
                            "message": f"{sys.name} cooling... ({self.shutoff_counters[sys.name]} turns left)",
                        },
                    )

                if gen > 0:
                    can_move = min(gen, remaining_inbound_flux)
                    self.fluxpool += can_move
                    remaining_inbound_flux -= can_move
                    sys.current_heat = gen - can_move
                else:
                    sys.current_heat = 0.0

        events.append(
            {"type": "HEAT_GEN", "value": total_flux_cap - remaining_inbound_flux},
        )

        # Phase B: Outbound (Pool -> Sinks/Vents)
        moved_to_sinks = 0.0
        remaining_outbound_flux = total_flux_cap

        if self.fluxpool > 0:
            for h_sys in self.Heat.values():
                can_take = min(
                    remaining_outbound_flux,
                    h_sys.flux,
                    h_sys.spare_capacity(),
                    self.fluxpool,
                )
                if can_take > 0:
                    h_sys.add_heat(can_take)
                    self.fluxpool -= can_take
                    remaining_outbound_flux -= can_take
                    moved_to_sinks += can_take

        if moved_to_sinks > 0:
            # We don't have a direct HEAT_SINK event that is replayed to update sys.current,
            # but HEAT_ASSIGNMENT can be used if we want to log it?
            # Actually replay() uses HEAT_ASSIGNMENT to update sys.current.
            # But here it's automatic. We should probably log HEAT_ASSIGNMENT for each sink
            # or add a new event type that handles automatic dissipation.
            # For now, Mecha.apply_event handles HEAT_ASSIGNMENT.
            pass

        # 3. Check for Global Pool Overheat (Overflow)
        if self.fluxpool > total_flux_cap:
            overheated = True
            events.append(
                {"type": "POOL_OVERFLOW", "value": self.fluxpool - total_flux_cap},
            )

        # 4. Dissipation (Vents work on their internal heat)
        thermals = self.tick_heat()
        events.append({"type": "HEAT_DISSIPATION", "values": thermals})

        # 5. Reset turn state
        self.pending_heat = 0.0

        return {
            "turn": self.turn,
            "internal_overheat": sum(s.current_heat for cat in self._categories for s in self.get_syscat(cat).values())
            + internal_manual_overheat,
            "moved_to_pool": total_flux_cap - remaining_inbound_flux,
            "moved_to_sinks": moved_to_sinks,
            "dissipated": sum(thermals.values()),
            "pool_status": self.fluxpool,
            "new_flux": self.fluxpool,
            "new_speed": new_speed,
            "events": events,
            "overheated": overheated,
        }

    def projected_flux(self) -> float:
        """Calculate the projected heat flux for the next turn.

        Considers systems that will be active or will finish booting,
        plus any pending manual heat.

        Returns:
            The projected flux as a float.

        """
        flux = 0.0
        for cat in self._categories:
            for sys in self.get_syscat(cat).values():
                # System will be active if it's already active OR if it's booting and will finish
                will_be_active = sys.is_active()
                # Simplified logic: if it doesn't need a roll or has one, it will advance
                if (
                    sys.is_booting()
                    and (not sys.needs_roll() or sys.boot_progress < sys.activation_rounds - 1)
                    and sys.boot_progress + 1 >= sys.activation_rounds
                ):
                    will_be_active = True

                if will_be_active:
                    flux += sum(sys.heats.values()) * sys.amount

        # Add manual pending heat
        flux += self.pending_heat
        return flux

    def projected_energy(self) -> float:
        """Calculate the projected energy budget for the next turn.

        Returns:
            The projected energy budget as a float (currently a placeholder
            returning the current budget).

        """
        # This is more complex because energy allocation depends on loadouts
        # For now, let's just return the current budget as a placeholder
        return self.energy_budget()

    # Dashboard Helpers
    def current_top_speed(self) -> float:
        """Get the highest top speed across all active movement systems.

        Returns:
            The maximum top speed in m/s.

        """
        data = self.speeds()
        max_s = 0.0
        for sys_data in data.values():
            max_s = max(max_s, sys_data["topspeed"])
        return max_s

    def projected_cooling(self) -> float:
        """Calculate the projected total heat dissipation for the next turn.

        Considers both passive and active dissipation from all heat systems.

        Returns:
            The projected cooling capacity as a float.

        """
        total = 0.0
        for h in self.Heat.values():
            sys_diss = 0.0
            if not h.is_disabled():
                rel, abs_val = h.unpack(h.passive)
                sys_diss += abs_val + (rel * h.current)
            if h.is_active() or h.is_booting():
                rel, abs_val = h.unpack(h.active)
                sys_diss += abs_val + (rel * h.current)
            total += min(sys_diss, h.current)
        return total

    def energy_output(self) -> float:
        """Get the current energy output from all energy systems.

        Returns:
            The total energy budget as a float.

        """
        return self.energy_budget()
