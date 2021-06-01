# unit tests for TCA9555

# TCA9555

# RegisterMap
import pytest

from source.TestBoxIF import TCA9555
from source.TestBoxIF.I2C import I2C
from source.TestBoxIF.I2C import Register
from source.TestBoxIF.I2C import RegType

# Fixtures
@pytest.fixture
def default_register():
    return Register(
        address = 0,
        read_write = RegType.READWRITE,
        num_bytes = 1,
        default = '0x00')

def readonly_register():
    return Register(
        address = 0,
        read_write = RegType.READ,
        num_bytes = 1,
        default = '0x00')

# Register
def test_default_addr_init(default_register):
    assert default_register.address == 0

def test_addr_init():
    reg = Register(
        address = 5,
        read_write = RegType.READWRITE,
        num_bytes = 1,
        default = '0x00')

    assert reg.address == 5

def test_default_read_write_init(default_register):
    assert default_register.read_write == RegType.READWRITE

def test_read_write_init():
    reg = Register(
        address = 5,
        read_write = RegType.READWRITE,
        num_bytes = 1,
        default = '0x00')

    assert reg.read_write == RegType.READWRITE

def test_read_init():
    reg = Register(
        address = 5,
        read_write = RegType.READ,
        num_bytes = 1,
        default = '0x00')

    assert reg.read_write == RegType.READ

def test_default_num_bytes_init(default_register):
    assert default_register.num_bytes == 1

def test_num_bytes_init():
    reg = Register(
        address = 5,
        read_write = RegType.READ,
        num_bytes = 2,
        default = '0x00')

    assert reg.num_bytes == 2

def test_default_value_init(default_register):
    assert default_register.value == '0x00'

def test_value_init():
    reg = Register(
        address = 5,
        read_write = RegType.READ,
        num_bytes = 2,
        default = '0xa5')
    assert reg.value == '0xa5'

def test_word_set(default_register):
    reg = default_register
    reg.value = '0xa5'
    assert reg.value == '0xa5'

def test_bit_set(default_register):
    reg = default_register
    reg[3] = True
    assert reg.value == '0x08'

def test_bit_get():
    reg = Register(
        address = 5,
        read_write = RegType.READ,
        num_bytes = 2,
        default = '0x0004')
    assert reg[2]

def test_slice_set(default_register):
    reg = default_register
    reg[2:6] = '0xf'
    assert reg.value == '0x3C'

def test_slice_get(default_register):
    reg = default_register
    reg.value = '0xa5'
    assert reg[2:6] == '0x9'

# RegisterMap
