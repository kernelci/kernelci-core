import kernelci.lab.lava as lava
import pytest


def test_get_device_type_by_name_1():
    assert lava.get_device_type_by_name("some_board", []) is None


def test_get_device_type_by_name_2():
    assert lava.get_device_type_by_name("some_board", [], []) is None


@pytest.fixture
def device_types():
    return ["x15", "beaglebone-black"]


@pytest.fixture
def aliases():
    aliases = [{"name": "am57xx-beagle-x15", "device_type": "x15"}]
    return aliases


def test_get_device_type_by_name_3(device_types, aliases):
    assert (
        lava.get_device_type_by_name("some_board", device_types,
                                              aliases) is None
    )


def test_get_device_type_by_name_4(device_types, aliases):
    assert (
        lava.get_device_type_by_name("x15", device_types, aliases)
        == device_types[0]
    )


def test_get_device_type_by_name_5(device_types, aliases):
    assert (
        lava.get_device_type_by_name(
            "am57xx-beagle-x15", device_types, aliases
        )
        == device_types[0]
    )


def test_get_device_type_by_name_6(device_types, aliases):
    assert (
        lava.get_device_type_by_name("beaglebone-black", device_types)
        == device_types[1]
    )
