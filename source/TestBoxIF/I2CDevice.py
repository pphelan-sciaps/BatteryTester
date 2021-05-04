class I2CDevice(object):
	"""Parent class for modeling ICs with an I2C interface

	"""

	def __init__(self, address: int = 0x27, i2c: I2C = None):
		super(TCA9555, self).__init__()

		self._address = address
		self._i2c = i2c;

 