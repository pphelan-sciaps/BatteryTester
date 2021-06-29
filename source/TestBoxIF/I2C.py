# standard library
from __future__ import annotations
import logging
from enum import Enum
from cmd import Cmd
import traceback

# external packages
from bitstring import BitArray
import ft4222
from ft4222 import FT4222
from ft4222 import I2CMaster
from ft4222.I2CMaster import Flag
from ft4222.I2CMaster import ControllerStatus as I2CStat

# internal packages for command line tool
# from .ConnectionManager import ConnectionManager

class RegisterMap(object):
    """docstring for I2CRegisterMap"""
    def __init__(
        self,
        i2c: I2C = None,
        address: int = 0,
        registers: list[Register] = []):

        self._i2c = i2c
        self._address = address
        self._registers = {reg.address:reg for reg in registers}

    # def __getitem__(self, key: str):
    #     return self._registers.get(key, None)

    # def __setitem__(self, key: str, reg: int):
    #     reg = self._registers.get(key, None)
    #     if self._i2c:

    #         if reg:
    #             addr = self._address
    #             data = bytearray((int(key,0),value))
    #             num_bytes = reg.num_bytes
    #             self._i2c.write(addr,data,num_bytes)
    #     else:   # offline testing
    #         print('no i2c object')

    def __repr__(self):
        for reg in self._registers:
            print(reg)

    def write_reg(
        self,
        reg_addr: int,
        value: int=None,
        retries: int=0
    ):

        reg = self._registers.get(reg_addr, None)
        if not reg:
            raise I2CError('invalid register address')
            
        elif reg.read_write == 'r':
            raise I2CError('register is read only')
            

        if value is not None:
            reg.value = value

        if self._i2c:
            addr = self._address
            reg_value = reg.value
            # print(reg_addr,reg_value)
            data = bytearray((reg_addr,reg_value))

            self._i2c.write(addr,data,retries)

    def write_bit(
        self,
        reg_addr: int,
        bit_num: int,
        value: int,
        retries: int=0
    ):

        reg = self._registers.get(reg_addr, None)
        if not reg:
            raise I2CError('invalid register address')
            
        elif reg.read_write == 'r':
            raise I2CError('register is read only')
            

        reg.set_bit(bit_num,value)
        self.write_reg(reg_addr,None,retries)

    def write_all(self):
        if self._i2c:
            for reg_addr, reg in self._registers.items():
                if reg.read_write == 'rw':
                    self.write_reg(reg_addr)

    def read_reg(
        self,
        reg_addr: int,
        transaction=True,
        retries: int=0
    ) -> int:

        reg = self._registers.get(reg_addr, None)
        if not reg:
            raise I2CError('invalid register address')
            return

        if self._i2c and transaction:
            # transaction
            addr = self._address
            data = reg_addr
            word = self._i2c.read(addr,data,reg.num_bytes,retries)

            reg.value = int.from_bytes(word,'big')


        return reg.value

    def read_bit(
        self,
        reg_addr: int,
        bit_num,
        transaction=True,
        retries: int=0
    ):
        reg = self._registers.get(reg_addr, None)
        if not reg:
            raise I2CError('invalid register address')
            return

        if transaction:
            self.read_reg(reg_addr,retries=retries)
        return reg.get_bit(bit_num)

                     


    # def write_all(self):
    #     for reg
        
class Register(object):
    """docstring for I2CRegister"""
    def __init__(
        self,
        address:    int,
        read_write: str,
        num_bytes:  int,
        default:    int):

        self._address       = address
        self._read_write    = read_write
        self._num_bytes     = num_bytes
        self._value         = default

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
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, value: int):
        self._value = value

    @property
    def value_hex(self) -> str:
        return ('0x'+self._value.hex)   

    def set_bit(self, bit_num: int, value: int) -> int:
        word = self.value
        mask = 2 ** bit_num
        if value:
            word |= mask
        else:
            word &= ~mask
        self._value = word

        return word

    def get_bit(self, bit_num) -> bool:
        word = self.value
        mask = 2 ** bit_num
        return bool(word & mask)
    

    ## TODO indexing
    # def __setitem__(self, bit, value):
    #     if isinstance(bit, int):
    #         idx  = self.bit_to_index(bit)
    #         self._value.set(value,idx)
    #     elif isinstance(bit, slice):
    #         start = self.bit_to_index(bit.stop)
    #         stop  = self.bit_to_index(bit.start)
    #         self._value[start:stop] = value
    #     else:
    #         raise TypeError

    # def __getitem__(self, bit):
    #     if isinstance(bit, int):
    #         idx  = self.bit_to_index(bit)
    #         self._value.set(value,idx)
    #     elif isinstance(bit, slice):
    #         start = self.bit_to_index(bit.stop)
    #         stop  = self.bit_to_index(bit.start)
    #         self._value[start:stop] = value
    #     else:
    #         raise TypeError

    #     return bool(self._value[idx])

    def __repr__(self):
        return (f'Addr: {hex(self._address)} RW: {self._read_write} Value: {hex(self._value)})')
        pass

    # # helper methods
    # def bit_to_index(self, bit: int):
    #     return 8 * self._num_bytes - 1 - bit


class RegType(str,Enum):
    READ        = 'r'
    WRITE       = 'w'
    READWRITE   = 'rw'

    def __str__(self) -> str:
        return str.__str__(self)

class I2C(object):
    FLAG_REPEATED_START = 3
    FLAG_STOP = 4

    def __init__(self, ic: FT4222, name: str = None, speed_kbps: int = 100):
        self.logger = logging.getLogger('batman.TestBoxIF.I2C.I2C')

        self._ic = ic
        self._name = name
        self.hw_init(speed_kbps)

        self.logger.info('I2C init')

    def __del__(self):
        if self._ic:
            self._ic.close()

    def __repr__(self):
        return 'I2C object'

    def hw_init(self, speed_kbps: int):
        stat = self._ic.i2cMaster_Init(100)    # speed in kbps
        self.logger.info('i2c hw init')

    def write(
        self,
        addr: int,
        data: bytearray,
        retries: int=0):
        # print(f'write - addr: {addr} data: {data}')
        # traceback.print_stack()

        while retries >= 0:
            # print(f'{hex(addr)} - {data}')
            try:
                retries -= 1
                self.logger.debug(f'write - addr: {hex(addr)}\tdata: {data}')
                self._ic.i2cMaster_Write(addr, data)

                # wait until not busy
                while True:
                    stat = self.i2c_status
                    if not (stat & (I2CStat.BUSY | I2CStat.BUS_BUSY)):
                        break

                # stat = self.i2c_status
                
                if stat == I2CStat.IDLE:  # ok
                    return True
                elif stat in (I2CStat.ADDRESS_NACK, I2CStat.DATA_NACK):
                    raise I2CNoDeviceError
                else:
                    raise I2CWriteError(stat)

            except I2CError as e:
                if retries < 0:
                    raise e
            except ft4222.FT4222DeviceError as e:
                raise e
                break
            except Exception as e:
                self.logger.exception(e)


    def read(
        self,
        addr: int,
        data: int,
        num_bytes: int,
        retries: int=0
    ) -> bytearray:
        while retries >= 0:
            try:
                retries -= 1
                # address pointer write
                wr_flags = Flag.START
                self.logger.debug(f'write ptr - addr: {hex(addr)}\treg: {data}')
                self._ic.i2cMaster_WriteEx(addr, wr_flags, data)

                # wait until not busy
                while True:
                    stat = self.i2c_status
                    if not (stat & I2CStat.BUSY):
                        break
                
                if stat == I2CStat.BUS_BUSY:  # for combined write read
                    pass
                elif stat in (I2CStat.ADDRESS_NACK, I2CStat.DATA_NACK):
                    raise I2CNoDeviceError
                else:
                    raise I2CReadError('write')
                    

                # data read
                rd_flags = Flag.REPEATED_START | Flag.STOP
                data_rd = self._ic.i2cMaster_ReadEx(addr,rd_flags,num_bytes)
                # print(data_rd)
                self.logger.debug(f'read - addr: {hex(addr)}\tdata: {data_rd}')

                data_no_device = b'\x00'
                while self.i2c_status & (I2CStat.BUSY | I2CStat.BUS_BUSY):
                    # print(self.i2c_status)
                    pass
                stat = self.i2c_status

                if stat == I2CStat.IDLE:  # ok
                    return data_rd
                elif ord(data_rd) == 0:
                    raise I2CNoDeviceError
                else:
                    raise I2CReadError('read')

            except I2CError as e:
                if retries < 0:
                    raise e
            except ft4222.FT4222DeviceError as e:
                raise e
                break

    @property
    def i2c_status(self):
        return self._ic.i2cMaster_GetStatus()

    @property
    def name(self):
        return self._name
    

# helper functions
def uint8_to_uint(msb: int = 0, lsb: int = 0):
    return (msb << 8) + lsb

def uint_to_uint8(val: int):
    msb = (val >> 8) & 0xFF
    lsb = (val) & 0xFF
    return (msb, lsb)

# exceptions
class I2CError(Exception):
    pass

class I2CReadError(I2CError):
    pass

class I2CWriteError(I2CError):
    pass

class I2CNoDeviceError(I2CError):
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
        # num_devices = ft4222.createDeviceInfoList()
        # device_locations = [ft4222.getDeviceInfoDetail(i,False).get('location')\
        #     for i in range(num_devices)\
        #     if ft4222.getDeviceInfoDetail(i,False).get('serial') == b'A']
        # self._device_locations = [device for device in devices]
        print(self.conn_man.device_locations)

        
    def do_open_connection(self,args):
        '''
        Create new FT4222 device connected to device at given location
        '''
        args_list = args.split()
        idx = int(args_list[0],0)
        self.i2c = I2C(self.conn_man.open_connection(idx))
        

    def do_i2c_write(self,args):
        args_list = args.split()
        addr = int(args_list[0],0)
        data = bytearray([int(arg,0) for arg in args_list[1:]])
        # print((addr,data))
        
        print(self.i2c.write(addr,data))

    def do_i2c_read(self,args):
        args_list = args.split()
        addr, reg, num_bytes = map(lambda arg: int(arg,0), args_list)
        data = self.i2c.read(addr, reg, num_bytes)
        # print(data)
        # data_bytes = [int.from_bytes(byte,'big') for byte in data]
        

    # helper methods
    def __init__(self):
        super(DemoApp, self).__init__()
        # self.conn_man = ConnectionManager()
        self.i2c = None

# cli app for testing
if __name__  == '__main__':
    d = DemoApp().cmdloop()