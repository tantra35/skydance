import pytest

from skydance.protocol import *


@pytest.fixture(name="state")
def state_fixture():
    return State()


def test_state_frame_number_overflow():
    s = State()
    for _ in range(256):
        s.increment_frame_number()
    assert s.frame_number == bytes([0])


def test_command_bytes(state):
    assert PingCommand(state).raw == bytes.fromhex(
        "55aa5aa57e00800080e18000000100790000007e"
    )


def test_ping(state):
    assert PingCommand(state).body == bytes.fromhex("800080e18000000100790000")


@pytest.mark.parametrize(
    "zone",
    [256, -1, 99999999999, "foo", None],
)
def test_zone_invalid(zone):
    with pytest.raises(expected_exception=ValueError):
        ZoneCommand.validate_zone(zone)


def test_power_on(state):
    assert PowerOnCommand(state, zone=2).body == bytes.fromhex(
        "800080e180000002000a010001"
    )


def test_power_on_higher_zone_number(state):
    assert PowerOnCommand(state, zone=15).body == bytes.fromhex(
        "800080e180000000400a010001"
    )


def test_power_off(state):
    assert PowerOffCommand(state, zone=2).body == bytes.fromhex(
        "800080e180000002000a010000"
    )


def test_master_power_on(state):
    assert MasterPowerOnCommand(state).body == bytes.fromhex(
        "800080e18000000fff0b0300030001"
    )


def test_master_power_off(state):
    assert MasterPowerOffCommand(state).body == bytes.fromhex(
        "800080e18000000fff0b0300000000"
    )


def test_brightness_min(state):
    assert BrightnessCommand(state, zone=2, brightness=1).body == bytes.fromhex(
        "800080e180000002000702000001"
    )


def test_brightness_max(state):
    assert BrightnessCommand(state, zone=2, brightness=255).body == bytes.fromhex(
        "800080e1800000020007020000ff"
    )


@pytest.mark.parametrize(
    "brightness",
    [0, 256, -1, 99999999999, "foo", None],  # level 0 is invalid!
)
def test_brightness_invalid(brightness):
    with pytest.raises(expected_exception=ValueError):
        BrightnessCommand.validate_brightness(brightness)


def test_temperature_min(state):
    assert TemperatureCommand(state, zone=2, temperature=0).body == bytes.fromhex(
        "800080e180000002000d02000000"
    )


def test_temperature_max(state):
    assert TemperatureCommand(state, zone=2, temperature=255).body == bytes.fromhex(
        "800080e180000002000d020000ff"
    )


@pytest.mark.parametrize(
    "temperature",
    [256, -1, 99999999999, "foo", None],
)
def test_temperature_invalid(temperature):
    with pytest.raises(expected_exception=ValueError):
        TemperatureCommand.validate_temperature(temperature)


def test_rgbw_individuals_components(state):
    assert RGBWCommand(
        state, zone=2, red=255, green=0, blue=0, white=0
    ).body == bytes.fromhex("800080e18000000200010700ff000000000000")
    assert RGBWCommand(
        state, zone=2, red=0, green=255, blue=0, white=0
    ).body == bytes.fromhex("800080e1800000020001070000ff0000000000")
    assert RGBWCommand(
        state, zone=2, red=0, green=0, blue=255, white=0
    ).body == bytes.fromhex("800080e180000002000107000000ff00000000")
    assert RGBWCommand(
        state, zone=2, red=0, green=0, blue=0, white=255
    ).body == bytes.fromhex("800080e18000000200010700000000ff000000")


def test_rgbw_mixed(state):
    assert RGBWCommand(
        state, zone=2, red=255, green=128, blue=64, white=1
    ).body == bytes.fromhex("800080e18000000200010700ff804001000000")


def test_rgbw_all_zero(state):
    with pytest.raises(expected_exception=ValueError):
        RGBWCommand(state, zone=2, red=0, green=0, blue=0, white=0)


def test_rgbw_min(state):
    assert RGBWCommand(
        state, zone=2, red=0, green=1, blue=0, white=0
    ).body == bytes.fromhex("800080e1800000020001070000010000000000")


def test_rgbw_max(state):
    assert RGBWCommand(
        state, zone=2, red=255, green=255, blue=255, white=255
    ).body == bytes.fromhex("800080e18000000200010700ffffffff000000")


@pytest.mark.parametrize(
    "component",
    [256, -1, 99999999999, "foo", None],
)
def test_rgbw_invalid(component):
    with pytest.raises(expected_exception=ValueError):
        RGBWCommand.validate_component(component, hint="foo")


def test_get_number_of_zones(state):
    assert GetNumberOfZonesCommand(state).body == bytes.fromhex(
        "800080e18000000100790000"
    )


number_of_zones_params = {
    "55aa5aa57e00800080e18026510100f910008182838485868788898a8b8c8d8e8f90007e": 16,
    "55aa5aa57e00800080e18026510100f9100081828384858687880000000000000000007e": 8,
    "55aa5aa57e00800080e18026510100f9100000000000000000000000000000000000007e": 0,
}


@pytest.mark.parametrize(
    "response, num",
    [(bytes.fromhex(res), num) for res, num in number_of_zones_params.items()],
)
def test_get_number_of_zones_response(response, num):
    assert GetNumberOfZonesResponse(response).number == num


@pytest.mark.parametrize(
    "zone",
    range(1, 17),
)
def test_get_zone_name(state, zone: int):
    res = GetZoneInfoCommand(state, zone=zone).body
    zone_encoded = 2 ** (zone - 1)
    expected = bytes().join(
        (
            bytes.fromhex("80 00 80 e1 80 00 00"),
            struct.pack("<H", zone_encoded),
            bytes.fromhex("78 00 00"),
        )
    )
    assert res == expected


@pytest.mark.parametrize(
    "zone",
    [17, 256, 0, -1, 99999999999, "foo", None],
)
def test_get_zone_name_invalid(zone: int):
    with pytest.raises(expected_exception=ValueError):
        GetZoneInfoCommand.validate_zone(zone)


@pytest.mark.parametrize(
    "variant",
    [
        bytes.fromhex(
            "55aa5aa57e00800080e18026514000f8100051005a6f6e65205247422b4343540000007e"
        ),
        bytes.fromhex(
            "55aa5aa57e00800080e18026514000f8100051005a6f6e65205247422b4343542000007e"
        ),
        bytes.fromhex(
            "55aa5aa57e00800080e18026514000f8100051005a6f6e65205247422b4343542020007e"
        ),
    ],
)
def test_get_zone_info_response_strip(variant):
    zone_info = GetZoneInfoResponse(variant)
    assert zone_info.name == "Zone RGB+CCT"


def test_get_zone_info_response_utf_8():
    raw = bytes.fromhex(
        "55aa5aa57e02800080e18026510200f8100021004b75636879c58820746f70000000007e"
    )
    zone_info = GetZoneInfoResponse(raw)
    assert zone_info.name == "Kuchyň top"


zone_info_params = {
    "55aa5aa57e568000805dc126518000f8100001005a6f6e6520537769746368000000007e": ZoneType.Switch,
    "55aa5aa57e05800080e18026511000f8100011005a6f6e652044696d6d6572000000007e": ZoneType.Dimmer,
    "55aa5aa57e528000805dc126510800f8100021005a6f6e6520434354000000000000007e": ZoneType.CCT,
    "55aa5aa57e538000805dc126511000f8100031005a6f6e6520524742000000000000007e": ZoneType.RGB,
    "55aa5aa57e548000805dc126512000f8100041005a6f6e6520524742570000000000007e": ZoneType.RGBW,
    "55aa5aa57e00800080e18026514000f8100051005a6f6e65205247422b4343540000007e": ZoneType.RGBCCT,
}


@pytest.mark.parametrize(
    "raw, expected_type",
    [(bytes.fromhex(raw), zt) for raw, zt in zone_info_params.items()],
)
def test_get_zone_info_response_types(raw, expected_type):
    zone_info = GetZoneInfoResponse(raw)
    assert zone_info.type == expected_type
