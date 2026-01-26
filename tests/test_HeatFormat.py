from gamepack.endworld.System import to_heatformat, System


def test_heatformat_positional():
    # Case 1: Positional heat with decimals and whole numbers
    data = {"heat0": 5.0, "heat1": 3.5, "heat2": 0.0}
    # Should export as "5; 3.5; 0"
    formatted = to_heatformat(data)
    assert formatted == "5; 3.5; 0"

    # Round trip
    sys = System("Test", {"heat": formatted})
    assert sys.heats["heat0"] == 5.0
    assert sys.heats["heat1"] == 3.5
    assert sys.heats["heat2"] == 0.0


def test_heatformat_named():
    # Case 2: Named heat values
    data = {"core": 10.0, "laser": 5.5}
    # Should export as "core 10; laser 5.5"
    formatted = to_heatformat(data)
    assert formatted == "core 10; laser 5.5"

    # Round trip
    sys = System("Test", {"heat": formatted})
    assert sys.heats["core"] == 10.0
    assert sys.heats["laser"] == 5.5


def test_heatformat_mixed():
    # Case 3: Mixed positional and named, with dirty input handling
    input_str = "5; core 10.0; 0.5"
    sys = System("Test", {"heat": input_str})

    assert sys.heats["heat0"] == 5.0
    assert sys.heats["core"] == 10.0
    assert sys.heats["heat2"] == 0.5

    # Export should be clean
    formatted = to_heatformat(sys.heats)
    assert formatted == "5; 0.5; core 10"  # positional sorted first, then named


def test_heatformat_no_decimals():
    # Case 4: Ensure no decimals if they are .0
    data = {"heat0": 1.0, "heat1": 2.0}
    assert to_heatformat(data) == "1; 2"
