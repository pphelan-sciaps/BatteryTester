# standard library
from dataclasses import dataclass

# external packages
from bitstring import BitArray

# internal
from . import I2C

class TCA9555(object):
	"""Abstraction of TCA9555 I2C gpio expander used on IF board.
	
	:param address: I2C address of IC on IF board, defaults to 0x27
	:type address: int, optional
	:param i2c: Instance of :class:`TestBoxIF.I2C for accessing I2C
	bus of test board IF, defaults to None
	:type i2c: class:`TestBoxIF.I2C, optional
	"""

	# constants
	VALID_ADDRESSES = range(32, 40)
	REG_WIDTH = 8

	def __init__(self, address: int = 0x27, i2c: I2C = None):
		super(TCA9555, self).__init__()

		if address in self.VALID_ADDRESSES:
			self._address = address
		else:
			self._address = self.VALID_ADDRESSES[-1]
		self._i2c = i2c;
		self._io_ports = [RegisterMap(),RegisterMap()]

	@property
	def address(self):
		return self._address

	@address.setter
	def address(self, new_address):
		if new_address in self.VALID_ADDRESSES:
			self._address = new_address
		else:
			raise ConfigError

	def read_input_port_bit(self, port: int, bit: int) -> int:
		if _i2c is not None:	# write to hardware
			pass
		else:				# offline testing
			try:
				input_bit = self._io_ports[port].input[bit] = 1
			except IndexError as e:
				raise e
				input_bit = None

			return input_bit

	def read_input_port_word(self, port: int) -> BitArray:
		if _i2c is not None:	# write to hardware
			pass
		else:				# offline testing
			try:
				input_bit = self._io_ports[port].input[bit] = 1
			except IndexError as e:
				raise e
				input_bit = None

			return input_bit	


	def set_output_port_bit(self, port: int, bit: int) -> None:
		try:
			idx = self.REG_WIDTH - 1 - bit
			self._io_ports[port].output_port.set(True,idx)
		except IndexError as e:
			raise e
			return

		print(self._io_ports[0].output_port)
		print(self._io_ports[1].output_port)

		if self._i2c is not None:	# write to hardware
			pass

	def clear_output_port_bit(self, port: int, bit: int) -> None:
		try:
			idx = self.REG_WIDTH - 1 - bit
			self._io_ports[port].output_port.set(False,idx)
		except IndexError as e:
			raise e
			return

		if self._i2c is not None:	# write to hardware
			pass

	def write_output_port_word(self, port: int, word: str) -> None:
		try:
			self._io_ports[port].output_port = BitArray(word)
			print(self._io_ports[0].output_port)
			print(self._io_ports[1].output_port)
		except IndexError as e:
			raise e
			return
		except TypeError as e:
			raise e
			return
		except ValueError as e:
			raise e
			return
		except KeyError as e:
			raise e
			return

		if self._i2c is not None:	# write to hardware
			pass
			

	def set_config_bit(self, port: int, bit: int) -> None:
		try:
			idx = self.REG_WIDTH - 1 - bit
			self._io_ports[port].config.set(True,idx)
		except IndexError as e:
			raise e
			return

		print(self._io_ports[0].config)
		print(self._io_ports[1].config)

		if self._i2c is not None:	# write to hardware
			pass

	def clear_config_bit(self, port: int, bit: int) -> None:
		try:
			idx = self.REG_WIDTH - 1 - bit
			self._io_ports[port].config.set(False,idx)
		except IndexError as e:
			raise e
			return

		if self._i2c is not None:	# write to hardware
			pass

	def write_config_word(self, port: int, word: str) -> None:
		try:
			self._io_ports[port].config = BitArray(word)
			print(self._io_ports[0].config)
			print(self._io_ports[1].config)
		except IndexError as e:
			raise e
			return
		except TypeError as e:
			raise e
			return
		except ValueError as e:
			raise e
			return
		except KeyError as e:
			raise e
			return

		if self._i2c is not None:	# write to hardware
			pass		

# helper classes

class ConfigError(Exception):
	pass

class RegisterMap(object):
	"""docstring for RegisterMap"""

	def __init__(self):
		self.input_port: [int] 	= BitArray('0x00')
		self.output_port: [int]	= BitArray('0xff')
		self.polarity: [int]	= BitArray('0x00')
		self.config: [int]		= BitArray('0xff')
