# standard library
from enum import Enum
from cmd import Cmd

# external packages
from bitstring import BitArray
import ft4222
from ft4222 import FT4222

class I2CRegisterMap(object):
    """docstring for I2CRegisterMap"""
    def __init__(self, arg):
        super(I2CRegisterMap, self).__init__()
        self.arg = arg
        
class Register(object):
    """docstring for I2CRegister"""
    def __init__(
        self,
        address:    int,
        read_write: str,
        num_bytes:  int,
        default:    str):

        super(Register, self).__init__()
        self._address       = address
        self._read_write    = read_write
        self._num_bytes     = num_bytes
        self._value         = BitArray(default,8*num_bytes)

    # API
    @property
    def address(self):
        return self._address

    @property
    def read_write(self):
        return self._read_write
    
    @property
    def num_bytes(self):
        return self._num_bytes

    @property
    def value(self) -> str:
        return self._value.hex

    @value.setter
    def value(self, new_val: str):
        self._value = BitArray(new_val,8*self._num_bytes)

    def __setitem__(self, bit: int, value: bool):
        idx  = 8*self._num_bytes - 1 - bit
        self._value.set(value,idx)

    def __getitem__(self, bit: int):
        idx  = 8*self._num_bytes - 1 - bit
        return bool(self._value[idx])



class RegType(str,Enum):
    READ        = 'r'
    WRITE       = 'w'
    READWRITE   = 'rw'

    def __str__(self) -> str:
        return str.__str__(self)
        
class I2C(object):

    def __init__(self, ic: FT4222, speed_kbps: int = 100):
        self._ic = ic
        self.hw_init(speed_kbps)

    def __repr__(self):
        return 'I2C object'

    def hw_init(self, speed_kbps: int):
        self._ic.i2cMaster_Init(100)    # speed in kbps

    def write(self, addr: int, data: bytearray):
        print((addr,data))
        return self._ic.i2cMaster_Write(addr, data)

class I2CError(Exception):
    pass

class DemoApp(Cmd):
    # shell settings
    intro = '\nI2C demo app.  Type help or ? to list commands.\n'
    prompt = '(I2C) '

    # commands
    def do_list_device_locations(self,args):
        '''
        Display list of connected FT4222
        '''
        num_devices = ft4222.createDeviceInfoList()
        devices = [ft4222.getDeviceInfoDetail(i) for i in range(num_devices)
        if ft4222.getDeviceInfoDetail(i).get('serial') == b'A']
        device_locations = [device.get('location') for device in devices]

        print(device_locations)

    def do_open_connection(self,args):
        '''
        Create new FT4222 device connected to device at given location
        '''
        args_list = args.split()
        location = int(args_list[0],0)
        ft4222_ic = ft4222.openByLocation(location)
        self.i2c = I2C(ft4222_ic)

    def do_i2c_write(self,args):
        args_list = args.split()
        addr = int(args_list[0],0)
        data = bytearray([int(arg,0) for arg in args_list[1:]])
        print((addr,data))
        
        print(self.i2c.write(addr,data))

    # helper methods
    def __init__(self):
        super(DemoApp, self).__init__()
        self.i2c = None

# cli app for testing
if __name__  == '__main__':
    d = DemoApp().cmdloop()