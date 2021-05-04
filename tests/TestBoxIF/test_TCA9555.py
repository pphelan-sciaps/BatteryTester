# unit tests for TCA9555

# TCA9555

# RegisterMap
import pytest

from source.TestBoxIF import TCA9555
from source.TestBoxIF import ConfigError

# fixtures
@pytest.fixture
def default_TCA9555():
	return TCA9555()

# address
def test_addr_default():
	tca9555 = TCA9555()
	assert tca9555.address == 0x27

def test_addr_init_valid():
	address = 0x20
	tca9555 = TCA9555(address = address)
	assert tca9555.address == address

def test_addr_init_invalid():
	address = 0x50
	tca9555 = TCA9555(address = address)
	assert tca9555.address == 0x27

def test_addr_change_valid():
	tca9555 = TCA9555()
	tca9555.address = 0x20
	assert tca9555.address == 0x20

def test_addr_change_inivalid():
	tca9555 = TCA9555()
	with pytest.raises(ConfigError):
		tca9555.address = 0x50

# output port
def test_output_port_0_default():
	tca9555 = TCA9555()
	assert tca9555._io_ports[0].output_port.uint == int('0xff',0)

def test_output_port_1_default():
	tca9555 = TCA9555()
	assert tca9555._io_ports[1].output_port.uint == int('0xff',0)

def test_output_port_0_write_word():
	tca9555 = TCA9555()
	tca9555.write_output_port_word(0,'0xa5')
	assert tca9555._io_ports[0].output_port.uint == int('0xa5',0)
	assert tca9555._io_ports[1].output_port.uint == int('0xff',0)

def test_output_port_1_write_word():
	tca9555 = TCA9555()
	tca9555.write_output_port_word(1,'0x5a')
	assert tca9555._io_ports[0].output_port.uint == int('0xff',0)
	assert tca9555._io_ports[1].output_port.uint == int('0x5a',0)

def test_output_port_write_word_index_error():
	tca9555 = TCA9555()
	with pytest.raises(IndexError):
		tca9555.write_output_port_word(2,'0x00')

def test_output_port_0_set_bit():
	tca9555 = TCA9555()
	tca9555.write_output_port_word(0,'0x00')
	tca9555.write_output_port_word(1,'0x00')
	tca9555.set_output_port_bit(port=0,bit=7)
	assert tca9555._io_ports[0].output_port.uint == int('0x80',0)
	assert tca9555._io_ports[1].output_port.uint == int('0x00',0)

def test_output_port_1_set_bit():
	tca9555 = TCA9555()
	tca9555.write_output_port_word(0,'0x00')
	tca9555.write_output_port_word(1,'0x00')
	tca9555.set_output_port_bit(port=1,bit=3)
	assert tca9555._io_ports[0].output_port.uint == int('0x00',0)
	assert tca9555._io_ports[1].output_port.uint == int('0x08',0)

def test_output_port_0_clear_bit():
	tca9555 = TCA9555()
	tca9555.clear_output_port_bit(port=0,bit=7)
	assert tca9555._io_ports[0].output_port.uint == int('0x7F',0)
	assert tca9555._io_ports[1].output_port.uint == int('0xFF',0)

def test_output_port_1_clear_bit():
	tca9555 = TCA9555()
	tca9555.clear_output_port_bit(port=1,bit=3)
	print(tca9555._io_ports)
	assert tca9555._io_ports[0].output_port.uint == int('0xFF',0)
	assert tca9555._io_ports[1].output_port.uint == int('0xF7',0)

# config port
def test_config_0_default():
	tca9555 = TCA9555()
	assert tca9555._io_ports[0].config.uint == int('0xff',0)

def test_config_1_default():
	tca9555 = TCA9555()
	assert tca9555._io_ports[1].config.uint == int('0xff',0)

def test_config_0_write_word():
	tca9555 = TCA9555()
	tca9555.write_config_word(0,'0xa5')
	assert tca9555._io_ports[0].config.uint == int('0xa5',0)
	assert tca9555._io_ports[1].config.uint == int('0xff',0)

def test_config_1_write_word():
	tca9555 = TCA9555()
	tca9555.write_config_word(1,'0x5a')
	assert tca9555._io_ports[0].config.uint == int('0xff',0)
	assert tca9555._io_ports[1].config.uint == int('0x5a',0)

def test_config_write_word_index_error():
	tca9555 = TCA9555()
	with pytest.raises(IndexError):
		tca9555.write_config_word(2,'0x00')

def test_config_0_set_bit():
	tca9555 = TCA9555()
	tca9555.write_config_word(0,'0x00')
	tca9555.write_config_word(1,'0x00')
	tca9555.set_config_bit(port=0,bit=7)
	assert tca9555._io_ports[0].config.uint == int('0x80',0)
	assert tca9555._io_ports[1].config.uint == int('0x00',0)

def test_config_1_set_bit():
	tca9555 = TCA9555()
	tca9555.write_config_word(0,'0x00')
	tca9555.write_config_word(1,'0x00')
	tca9555.set_config_bit(port=1,bit=3)
	assert tca9555._io_ports[0].config.uint == int('0x00',0)
	assert tca9555._io_ports[1].config.uint == int('0x08',0)

def test_config_0_clear_bit():
	tca9555 = TCA9555()
	tca9555.clear_config_bit(port=0,bit=7)
	assert tca9555._io_ports[0].config.uint == int('0x7F',0)
	assert tca9555._io_ports[1].config.uint == int('0xFF',0)

def test_config_1_clear_bit():
	tca9555 = TCA9555()
	tca9555.clear_config_bit(port=1,bit=3)
	print(tca9555._io_ports)
	assert tca9555._io_ports[0].config.uint == int('0xFF',0)
	assert tca9555._io_ports[1].config.uint == int('0xF7',0)


# def test_output_port_write_word_index_error():
# 	pass

# def test_output_port_0_bit_set():
# 	tca9555 = TCA9555()
# 	tca9555.set_output_port_bit(port=0, bit=7)
# 	print(tca9555.__io_ports)
# 	assert tca9555._io_ports[0].output_port.hex == '80'
# 	assert tca9555._io_ports[1].output_port.hex == 'ff'

