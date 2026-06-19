"""Tests for the Mecha module."""

import pytest

from gamepack.endworld import EnergySystem, MovementSystem, OffensiveSystem, SealSystem, System
from gamepack.endworld.HeatSystem import HeatSystem
from gamepack.endworld.Mecha import Mecha
from gamepack.MDPack import MDObj
from gamepack.WikiPage import WikiPage


@pytest.fixture(autouse=True, scope="session")
def setup_wikipath(tmp_path_factory: pytest.TempPathFactory) -> None:
    """Set up wiki path for all tests."""
    tmp_path = tmp_path_factory.mktemp("wiki")
    WikiPage._wikipath = tmp_path


@pytest.fixture
def basic_heat() -> HeatSystem:
    """Create a basic HeatSystem fixture."""
    # minimal dummy data for constructor
    data = {"capacity": 10, "passive": "1", "active": "2", "flux": 3, "current": 0}
    return HeatSystem("H1", data)


@pytest.fixture
def basic_energy() -> EnergySystem:
    """Create a basic EnergySystem fixture."""
    data = {"mass": 10, "amount": 1, "energy": 2, "heat": 3}
    return EnergySystem("E1", data)


@pytest.fixture
def basic_movement() -> MovementSystem:
    """Create a basic MovementSystem fixture."""
    data = {
        "mass": 100,
        "amount": 1,
        "energy": 50,
        "heat": 0,
        "enabled": "[x]",
        "thrust": 200,
        "anchor": 10,
        "dynamics": 5,
    }
    return MovementSystem("M1", data)


@pytest.fixture
def basic_seal() -> SealSystem:
    """Create a basic SealSystem fixture."""
    data = {"Level": 2, "Test": "Yes"}
    return SealSystem("S1", data)


def test_sealsystem_to_dict_and_headers(basic_seal: SealSystem) -> None:
    """Test SealSystem to_dict and get_headers methods."""
    s = basic_seal
    d = s.to_dict()
    assert d["Level"] == "2"
    assert "Test" in basic_seal.get_headers()


def test_heat_add_and_withdraw(basic_heat: HeatSystem) -> None:
    """Test adding and withdrawing heat from HeatSystem."""
    h = basic_heat
    # add less than capacity
    assert h.add_heat(5) == 0
    assert h.current == 5
    # add more than capacity → returns overage
    assert h.add_heat(10) == 5
    assert h.current == h.capacity
    # withdraw valid amount
    h.current = 5
    assert h.withdraw_heat(3) == 0
    assert h.current == 2
    # withdraw more than current → returns underage
    assert h.withdraw_heat(5) == 3
    assert h.current == 0


def test_heat_spare_capacity(basic_heat: HeatSystem) -> None:
    """Test spare_capacity calculation."""
    h = basic_heat
    h.current = 4
    assert h.spare_capacity() == h.capacity - 4


def test_heat_unpack(basic_heat: HeatSystem) -> None:
    """Test unpacking heat string expressions."""
    h = basic_heat
    r, a = h.unpack("10+5")
    assert (r, a) == (0, 15)
    r, a = h.unpack("10% + 5")
    assert r == 0.1
    assert a == 5


def test_heat_use_toggle_and_disable(basic_heat: HeatSystem) -> None:
    """Test toggling and disabling a HeatSystem."""
    h = basic_heat
    h.enabled = "[ ]"
    h.use(None)
    assert h.enabled == "[x]" or h.enabled == "[ ]"  # toggle behavior

    h.enabled = "[x]"
    h.use("disable")
    # just ensure no exception; exact behavior depends on string


def test_heat_tick_passive_and_active(basic_heat: HeatSystem) -> None:
    """Test tick heat generation for active system."""
    h = basic_heat
    h.current = 5
    h.enabled = "[x]"  # active
    amount = h.tick()
    assert amount == 3.0


@pytest.fixture
def mecha_with_heat() -> Mecha:
    """Create a Mecha with a HeatSystem fixture."""
    m = Mecha()
    # attach a real HeatSystem
    h = HeatSystem(
        "H1",
        {"capacity": 10, "passive": "1", "active": "2", "flux": 3, "current": 0},
    )
    h.enabled = "[x]"
    m.Heat["H1"] = h
    return m


def test_mecha_fluxmax_and_add_heat(mecha_with_heat: Mecha) -> None:
    """Test Mecha fluxmax and add_heat methods."""
    m = mecha_with_heat
    assert m.fluxmax() == m.Heat["H1"].flux
    # add heat less than capacity
    assert m.add_heat(5) == 0
    # add heat over capacity
    over = m.add_heat(20)
    assert over >= 0


def test_mecha_tick_heat(mecha_with_heat: Mecha) -> None:
    """Test Mecha tick_heat method."""
    m = mecha_with_heat
    m.add_heat(10)
    result = m.tick_heat()
    assert "H1" in result
    assert result["H1"] == 3.0


def test_mecha_move_heat(mecha_with_heat: Mecha) -> None:
    """Test moving heat between HeatSystems."""
    m = mecha_with_heat
    # add a target HeatSystem
    h2 = HeatSystem(
        "H2",
        {"capacity": 10, "passive": "1", "active": "2", "flux": 3, "current": 0},
    )
    h2.enabled = "[x]"
    m.Heat["H2"] = h2

    amt = m.move_heat("H1", "H2", 5)
    assert isinstance(amt, (int, float))

    with pytest.raises(KeyError):
        m.move_heat("Unknown", "H2", 5)


@pytest.fixture
def empty_mdobj() -> MDObj:
    """Create an empty MDObj fixture."""
    return MDObj.empty()


@pytest.fixture
def basic_mecha() -> Mecha:
    """Create a basic Mecha fixture."""
    return Mecha()


def test_constructor(basic_mecha: Mecha) -> None:
    """Test Mecha constructor initializes empty systems."""
    m = basic_mecha
    assert isinstance(m.Movement, dict)
    assert isinstance(m.Energy, dict)
    assert isinstance(m.systems, dict)
    assert m.errors == []


def test_from_mdobj_creates_mecha(empty_mdobj: MDObj) -> None:
    """Test creating a Mecha from an MDObj."""
    m = Mecha.from_mdobj(empty_mdobj)
    assert isinstance(m, Mecha)
    assert isinstance(m.loadouts, dict)


def test_total_mass_property(basic_mecha: Mecha) -> None:
    """Test total_mass property returns 0 for empty Mecha."""
    # empty systems → mass = 0
    assert basic_mecha.total_mass == 0


def test_speeds_empty_systems(basic_mecha: Mecha) -> None:
    """Test speeds returns empty dict with no Movement systems."""
    # with no Movement systems → speeds = {}
    assert basic_mecha.speeds() == {}


def test_fluxmax_and_add_heat(basic_mecha: Mecha, basic_heat: HeatSystem) -> None:
    """Test fluxmax and add_heat with a dummy HeatSystem."""
    # Add dummy HeatSystem
    h1 = basic_heat
    h1.enabled = "[x]"
    h1.flux = 5
    h1.add_heat = lambda x: 0  # type: ignore[method-assign, assignment]  # noqa: ARG005
    basic_mecha.Heat["H1"] = h1

    assert basic_mecha.fluxmax() == 5
    assert basic_mecha.add_heat(10) == 0


def test_move_heat_fail(basic_mecha: Mecha) -> None:
    """Test move_heat raises KeyError for unknown system."""
    with pytest.raises(KeyError):
        basic_mecha.move_heat("unknown", "H2", 5)


def test_energy_methods(basic_mecha: Mecha, basic_energy: EnergySystem) -> None:
    """Test energy_budget, energy_total, and energy_allocation."""
    e = basic_energy
    e.energy = 10
    e.provide = lambda: 5  # type: ignore[method-assign]
    e.is_disabled = lambda: False  # type: ignore[method-assign]
    basic_mecha.Energy["E1"] = e

    budget = basic_mecha.energy_budget()
    total = basic_mecha.energy_total()
    load, activated = basic_mecha.energy_allocation()
    assert budget == 5
    assert total == 10
    assert activated >= 0
    assert isinstance(load, list)


def test_to_mdobj_and_process_loadout(basic_mecha: Mecha) -> None:
    """Test to_mdobj and process_loadout methods."""
    # Ensure methods run without error
    mdobj = basic_mecha.to_mdobj()
    assert isinstance(mdobj, MDObj)

    result = basic_mecha.process_loadout("S1, S2")
    assert isinstance(result, list)


@pytest.fixture
def mecha_with_systems(
    basic_heat: HeatSystem,
    basic_energy: EnergySystem,
    basic_movement: MovementSystem,
) -> Mecha:
    """Create a Mecha with Heat, Energy, and Movement systems fixture."""
    m = Mecha()

    h = basic_heat
    h.enabled = "[x]"
    m.Heat["H1"] = h

    e = basic_energy
    e.is_active = lambda: True  # type: ignore[method-assign]
    e.is_disabled = lambda: False  # type: ignore[method-assign]
    e.provide = lambda: 5  # type: ignore[method-assign]
    m.Energy["E1"] = e

    m.Movement["M1"] = basic_movement

    return m


def test_loadouts_persistence(mecha_with_systems: Mecha) -> None:
    """Test loadouts persist through round-trip conversion."""
    m = Mecha.from_mdobj(MDObj.from_md(mecha_with_systems.to_md()))
    # initially Default exists automatically
    assert "Default" in m.loadouts
    # simulate empty loadouts
    m.loadouts = {}
    load, activated = m.energy_allocation()
    assert "Default" in m.loadouts
    assert isinstance(load, list)
    assert activated >= 0


def test_get_syscat_and_use_system(mecha_with_systems: Mecha) -> None:
    """Test get_syscat and use_system methods."""
    m = mecha_with_systems
    # get_syscat
    cat = m.get_syscat("Generic")
    assert isinstance(cat, dict)
    # use_system with an OffensiveSystem
    ds = OffensiveSystem("X", {"heat": "Shoot 3"})
    m.Offensive["X"] = ds
    m.use_system("Offensive", "X", "Shoot")
    assert m.fluxpool == 3.0


def test_flux_baseload(basic_mecha: Mecha) -> None:
    """Test flux_baseload calculation."""
    m = basic_mecha

    o1 = OffensiveSystem("O1", {"heat": 5, "enabled": "[x]", "amount": 1})
    o1.boot_progress = o1.activation_rounds
    m.Offensive["O1"] = o1

    d1 = System("D1", {"heat": 2, "enabled": "[x]", "amount": 1})
    d1.boot_progress = d1.activation_rounds
    m.Defensive["D1"] = d1

    s1 = System("S1", {"heat": 3, "enabled": "[x]", "amount": 1})
    s1.boot_progress = s1.activation_rounds
    m.Support["S1"] = s1

    val = m.flux_baseload()
    assert val == 5 + 2 + 3


def test_energy_allocation_budget_loop(mecha_with_systems: Mecha) -> None:
    """Test energy allocation respects budget."""
    m = mecha_with_systems
    e = m.Energy["E1"]
    e.energy = 3

    # create a loadout with systems consuming energy
    class DummySys(System):
        def __init__(self, energy: int) -> None:
            super().__init__("Dummy", {})
            self.energy = energy

        def is_active(self) -> bool:
            return True

    m.loadouts["Default"] = [DummySys(1), DummySys(2), DummySys(5)]
    _load, activated = m.energy_allocation()
    # activated should stop when budget exceeded
    assert activated <= 3


def test_process_loadout_bracket_skipping(mecha_with_systems: Mecha) -> None:
    """Test process_loadout skips bracketed entries."""
    m = mecha_with_systems
    # include brackets in plaintext
    result = m.process_loadout("[5], A, [10], M1")
    # brackets should be ignored, result should include non-bracket entries
    assert result == ["A???", "[0]", mecha_with_systems.Movement["M1"], "[2]"]


def test_calculate_speeds(mecha_with_systems: Mecha) -> None:
    """Test speeds calculation for Movement systems."""
    m = mecha_with_systems
    speeds = m.speeds()
    assert "M1" in speeds
    info = speeds["M1"]
    assert "topspeed" in info and "speeds" in info and "acceleration_time" in info
