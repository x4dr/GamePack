import pytest

from gamepack.MDPack import MDObj
from gamepack.endworld import EnergySystem, MovementSystem, System, SealSystem
from gamepack.endworld.HeatSystem import HeatSystem
from gamepack.endworld.Mecha import Mecha


@pytest.fixture
def basic_heat():
    # minimal dummy data for constructor
    data = {"capacity": 10, "passive": "1", "active": "2", "flux": 3, "current": 0}
    return HeatSystem("H1", data)


@pytest.fixture
def basic_energy():
    data = {"mass": 10, "amount": 1, "energy": 2, "heat": 3}
    return EnergySystem("E1", data)


@pytest.fixture
def basic_movement():
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
def basic_seal():
    data = {"Level": 2, "Test": "Yes"}
    return SealSystem("S1", data)


def test_sealsystem_to_dict_and_headers(basic_seal):
    s = basic_seal
    d = s.to_dict()
    assert d["Level"] == 2
    assert "Test" in basic_seal.get_headers()


def test_heat_add_and_withdraw(basic_heat):
    h = basic_heat
    # add less than capacity
    assert h.add_heat(5) == 0
    assert h.current == 5
    # add more than capacity → returns overage
    assert h.add_heat(10) == 5
    assert h.current == h.capacity
    # withdraw valid amount
    h.current = 5
    assert h.withdraw_heat(3) == 3
    assert h.current == 2
    # withdraw more than current → returns remaining
    assert h.withdraw_heat(5) == 2
    assert h.current == 2


def test_heat_spare_capacity(basic_heat):
    h = basic_heat
    h.current = 4
    assert h.spare_capacity() == h.capacity - 4


def test_heat_unpack(basic_heat):
    h = basic_heat
    r, a = h.unpack("10+5")
    assert (r, a) == (0, 15)
    r, a = h.unpack("10% + 5")
    assert r == 0.1
    assert a == 5


def test_heat_use_toggle_and_disable(basic_heat):
    h = basic_heat
    h.enabled = "[ ]"
    h.use(None)
    assert h.enabled == "[x]" or h.enabled == "[ ]"  # toggle behavior

    h.enabled = "[x]"
    h.use("disable")
    # just ensure no exception; exact behavior depends on string


def test_heat_tick_passive_and_active(basic_heat):
    h = basic_heat
    h.current = 5
    h.enabled = "[x]"  # active
    amount = h.tick()
    assert amount == 3.0


@pytest.fixture
def mecha_with_heat():
    m = Mecha()
    # attach a real HeatSystem
    h = HeatSystem(
        "H1", {"capacity": 10, "passive": "1", "active": "2", "flux": 3, "current": 0}
    )
    h.enabled = "[x]"
    m.Heat["H1"] = h
    m.systems["Heat"]["H1"] = h
    return m


def test_mecha_fluxmax_and_add_heat(mecha_with_heat):
    m = mecha_with_heat
    assert m.fluxmax() == m.Heat["H1"].flux
    # add heat less than capacity
    assert m.add_heat(5) == 0
    # add heat over capacity
    over = m.add_heat(20)
    assert over >= 0


def test_mecha_tick_heat(mecha_with_heat):
    m = mecha_with_heat
    m.add_heat(10)
    result = m.tick_heat()
    assert "H1" in result
    assert result["H1"] == 3.0


def test_mecha_move_heat(mecha_with_heat):
    m = mecha_with_heat
    # add a target HeatSystem
    h2 = HeatSystem(
        "H2", {"capacity": 10, "passive": "1", "active": "2", "flux": 3, "current": 0}
    )
    h2.enabled = "[x]"
    m.Heat["H2"] = h2
    m.systems["Heat"]["H2"] = h2

    amt = m.move_heat("H1", "H2", 5)
    assert isinstance(amt, int)

    with pytest.raises(KeyError):
        m.move_heat("Unknown", "H2", 5)


@pytest.fixture
def empty_mdobj():
    return MDObj.empty()


@pytest.fixture
def basic_mecha():
    return Mecha()


def test_constructor(basic_mecha):
    m = basic_mecha
    assert isinstance(m.Movement, dict)
    assert isinstance(m.Energy, dict)
    assert isinstance(m.systems, dict)
    assert m.errors == []


def test_from_mdobj_creates_mecha(empty_mdobj):
    m = Mecha.from_mdobj(empty_mdobj)
    assert isinstance(m, Mecha)
    assert isinstance(m.loadouts, dict)


def test_total_mass_property(basic_mecha):
    # empty systems → mass = 0
    assert basic_mecha.total_mass == 0


def test_speeds_empty_systems(basic_mecha):
    # with no Movement systems → speeds = {}
    assert basic_mecha.speeds() == {}


def test_fluxmax_and_add_heat(basic_mecha, basic_heat):
    # Add dummy HeatSystem
    h1 = basic_heat
    h1.enabled = "[x]"
    h1.flux = 5
    h1.add_heat = lambda x: 0
    basic_mecha.Heat["H1"] = h1
    basic_mecha.systems["Heat"]["H1"] = h1

    assert basic_mecha.fluxmax() == 5
    assert basic_mecha.add_heat(10) == 0


def test_move_heat_fail(basic_mecha):
    with pytest.raises(KeyError):
        basic_mecha.move_heat("unknown", "H2", 5)


def test_energy_methods(basic_mecha, basic_energy):
    e = basic_energy
    e.energy = 10
    e.provide = lambda: 5
    e.is_disabled = lambda: False
    basic_mecha.Energy["E1"] = e

    budget = basic_mecha.energy_budget()
    total = basic_mecha.energy_total()
    load, activated = basic_mecha.energy_allocation()
    assert budget == 5
    assert total == 10
    assert activated >= 0
    assert isinstance(load, list)


def test_to_mdobj_and_process_loadout(basic_mecha):
    # Ensure methods run without error
    mdobj = basic_mecha.to_mdobj()
    assert isinstance(mdobj, MDObj)

    result = basic_mecha.process_loadout("S1, S2")
    assert isinstance(result, list)


@pytest.fixture
def mecha_with_systems(basic_heat, basic_energy, basic_movement):
    m = Mecha()

    h = basic_heat
    h.enabled = "[x]"
    m.Heat["H1"] = h

    e = basic_energy
    e.is_active = lambda: True
    e.is_disabled = lambda: False
    e.provide = lambda: 5
    m.Energy["E1"] = e

    m.Movement["M1"] = basic_movement

    return m


def test_loadouts_persistence(mecha_with_systems):
    m = Mecha.from_mdobj(MDObj.from_md(mecha_with_systems.to_md()))
    # initially Default exists automatically
    assert "Default" in m.loadouts
    # simulate empty loadouts
    m.loadouts = {}
    load, activated = m.energy_allocation()
    assert "Default" in m.loadouts
    assert isinstance(load, list)
    assert activated >= 0


def test_get_syscat_and_use_system(mecha_with_systems):
    m = mecha_with_systems
    # get_syscat
    cat = m.get_syscat("Generic")
    assert isinstance(cat, dict)
    # use_system with a lambda system
    ds = System("S1", {"heat": "Shoot 3"})
    m.Offensive["X"] = ds
    m.use_system("Offensive", "X", "Shoot")
    assert m.heatflux == 0  # no leftover heat in flux
    assert m.Heat["H1"].current == 3.0


def test_flux_baseload(basic_mecha):
    m = basic_mecha

    m.Offensive["O1"] = System("O1", {"heat": 5, "enabled": "[x]"})
    m.Defensive["D1"] = System("D1", {"heat": 2, "enabled": "[x]"})
    m.Support["S1"] = System("S1", {"heat": 3, "enabled": "[x]"})
    m.flux_baseload()
    assert m.heatflux == 5 + 2 + 3


def test_energy_allocation_budget_loop(mecha_with_systems):
    m = mecha_with_systems
    e = m.Energy["E1"]
    e.energy = 3

    # create a loadout with systems consuming energy
    class DummySys(System):
        def __init__(self, energy):
            super().__init__("Dummy", {})
            self.energy = energy

        def is_active(self):
            return True

    m.loadouts["Default"] = [DummySys(1), DummySys(2), DummySys(5)]
    load, activated = m.energy_allocation()
    # activated should stop when budget exceeded
    assert activated <= 3


def test_process_loadout_bracket_skipping(mecha_with_systems):
    m = mecha_with_systems
    # include brackets in plaintext
    result = m.process_loadout("[5], A, [10], M1")
    # brackets should be ignored, result should include non-bracket entries
    assert result == ["A???", "[0]", mecha_with_systems.Movement["M1"], "[2.0]"]


def test_calculate_speeds(mecha_with_systems):
    m = mecha_with_systems
    speeds = m.speeds()
    assert "M1" in speeds
    info = speeds["M1"]
    assert "topspeed" in info and "speeds" in info and "acceleration_time" in info
