import kernelci.lava
import pytest


def test_get_device_type_by_name_1():
    assert kernelci.lava.get_device_type_by_name("some_board", []) is None


def test_get_device_type_by_name_2():
    assert kernelci.lava.get_device_type_by_name("some_board", [], []) is None


@pytest.fixture
def device_types():
    device_types = [
        {"busy": 1, "idle": 0, "name": "x15", "offline": 0},
        {"busy": 1, "idle": 0, "name": "beaglebone-black", "offline": 0},
    ]
    return device_types


@pytest.fixture
def aliases():
    aliases = [{"name": "am57xx-beagle-x15", "device_type": "x15"}]
    return aliases


def test_get_device_type_by_name_3(device_types, aliases):
    assert (
        kernelci.lava.get_device_type_by_name("some_board", device_types,
                                              aliases) is None
    )


def test_get_device_type_by_name_4(device_types, aliases):
    assert (
        kernelci.lava.get_device_type_by_name("x15", device_types, aliases)
        == device_types[0]
    )


def test_get_device_type_by_name_5(device_types, aliases):
    assert (
        kernelci.lava.get_device_type_by_name(
            "am57xx-beagle-x15", device_types, aliases
        )
        == device_types[0]
    )


def test_get_device_type_by_name_6(device_types, aliases):
    assert (
        kernelci.lava.get_device_type_by_name("beaglebone-black", device_types)
        == device_types[1]
    )
