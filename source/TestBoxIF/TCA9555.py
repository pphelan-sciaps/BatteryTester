# -*- coding: utf-8 -*-
"""
This module contains a class modeling the TCA9555 I2C GPIO IC. It also
contains 

"""

# standard library
from dataclasses import dataclass
from cmd import Cmd

# external packages
from bitstring import BitArray
import ft4222   # accessed through I2C, only used here to get device list
#import click

# internal
from . import I2C

class TCA9555(object):
    '''Abstraction of TCA9555 I2C gpio expander used on IF board.
    
    :param address: I2C address of IC on IF board, defaults to 0x27
    :type  address: int, optional
    :param i2c: Instance of :class:`TestBoxIF.I2C` for accessing I2C
        bus of test board IF, defaults to None
    :type  i2c: class:`TestBoxIF.I2C`, optional
    :param io_ports: IC register set for each port
    :type  io_ports: class:`.RegisterMap`

    :attr address: I2C address of IC on IF board
    :type address: int, optional
    '''

    # constants
    VALID_ADDRESSES = range(32, 40)
    REG_WIDTH = 8

    INPUT_CMD   = 0x0
    OUTPUT_CMD  = 0x2
    CONFIG_CMD  = 0x6

    def __init__(self, address: int = 0x27, i2c: I2C = None):
        '''Create new TCA9555 with given I2C address and I2C device'''
        super(TCA9555, self).__init__()

        if address in self.VALID_ADDRESSES:
            self._address = address
        else:
            self._address = self.VALID_ADDRESSES[-1]
        self._i2c = i2c;
        self._io_ports = [RegisterMap(),RegisterMap()]
        self.hw_init()

    # API
    @property
    def address(self):
        return self._address

    @address.setter
    def address(self, new_address):
        if new_address in self.VALID_ADDRESSES:
            self._address = new_address
        else:
            raise ConfigError('')

    def hw_init(self) -> None:
        '''Set hardware registers to default values'''
        for port_num, io_port in enumerate(self._io_ports):
            self.write_output_port_word(
                port=port_num,
                word=io_port.output_port.uint)
            self.write_config_word(
                port=port_num,
                word=io_port.config.uint)

    def read_input_port_bit(self, port: int, bit: int) -> bool:
        '''Read the value of a pin on an input port

        :param port: io port number
        :type  port: int
        :param bit: bit number to read
        :type  bit: int

        :return input_bit: input pin value
        :rtype  input_bit: bool
        '''
        if self._i2c is not None:    # write to hardware
            pass
        else:               # offline testing
            try:
                input_bit = self._io_ports[port].input[bit] = 1
            except IndexError as e:
                raise e
                input_bit = None

            return input_bit

    def read_input_port_word(self, port: int) -> BitArray:
        '''Read the value of the input register on an input port

        :param port: io port number
        :type  port: int

        :return input_bit: input register value
        :rtype  input_bit: class.`BitArray`
        '''
        if self._i2c is not None:    # write to hardware
            pass
        else:               # offline testing
            try:
                input_bit = self._io_ports[port].input[bit] = 1
            except IndexError as e:
                raise e
                input_bit = None

            return input_bit    


    def set_output_port_bit(self, port: int, bit: int) -> None:
        '''Set the value of a pin on an output port high

        :param port: io port number
        :type  port: int
        :param bit: bit number to set
        :type  bit: int
        '''
        try:
            idx = self.REG_WIDTH - 1 - bit
            self._io_ports[port].output_port.set(True,idx)
        except IndexError as e:
            raise e
            return

        if self._i2c is not None:   # write to hardware
            addr 
            self._i2c.write()

    def clear_output_port_bit(self, port: int, bit: int) -> None:
        try:
            idx = self.REG_WIDTH - 1 - bit
            self._io_ports[port].output_port.set(False,idx)
        except IndexError as e:
            raise e
            return

        if self._i2c is not None:   # write to hardware
            pass

    def write_output_port_word(self, port: int, word: int) -> None:
        print(word)
        print(f'{word:02x}')
        try:
            self._io_ports[port].output_port = BitArray(hex=f'{word:02x}')
        except IndexError as e:
            raise e
            print('invalid port number')
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

        if self._i2c is not None:   # write to hardware
            addr = self._address
            cmd  = self.OUTPUT_CMD + port
            word = self._io_ports[port].output_port.uint
            data = bytearray((cmd,word))
            stat = self._i2c.write(addr,data)
            print(stat)
        else:
            print('running in offline mode')


    def set_config_bit(self, port: int, bit: int) -> None:
        try:
            idx = self.REG_WIDTH - 1 - bit
            self._io_ports[port].config.set(True,idx)
        except IndexError as e:
            raise e
            return

        print(self._io_ports[0].config)
        print(self._io_ports[1].config)

        if self._i2c is not None:   # write to hardware
            pass

    def clear_config_bit(self, port: int, bit: int) -> None:
        try:
            idx = self.REG_WIDTH - 1 - bit
            self._io_ports[port].config.set(False,idx)
        except IndexError as e:
            raise e
            return

        if self._i2c is not None:   # write to hardware
            pass

    def write_config_word(self, port: int, word: int) -> None:
        try:
            self._io_ports[port].config = BitArray(hex=f'{word:02x}')
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

        if self._i2c is not None:   # write to hardware
            addr = self._address
            cmd  = self.CONFIG_CMD + port
            word = self._io_ports[port].config.uint
            data = bytearray((cmd,word))
            stat = self._i2c.write(addr,data)
            print(stat)
        else:
            print('running in offline mode')

# helper classes

class ConfigError(Exception):
    pass

class RegisterMap(object):
    """docstring for RegisterMap"""

    def __init__(self):
        self.input_port    = BitArray('0x00',8)
        self.output_port   = BitArray('0xff',8)
        self.polarity      = BitArray('0x00',8)
        self.config        = BitArray('0xff',8)

class DemoApp(Cmd):
    # shell settings
    intro = 'TCA9555 demo app.  Type help or ? to list commands.\n'
    prompt = '(TCA9555) '

    # commands
    def do_show_connections(self,args):
        '''
        Display list of connected FT4222
        '''
        num_devices = ft4222.createDeviceInfoList()
        devices = [ft4222.getDeviceInfoDetail(i) for i in range(num_devices)
        if ft4222.getDeviceInfoDetail(i).get('serial') == b'A']
        self.device_locations = [device.get('location') for device in devices]

        print(self.device_locations)

    def do_open_connection(self,args):
        '''
        Create new FT4222 device connected to device at given location
        '''

        if not self.device_locations:
            self.do_show_connections('')

        args_list = args.split()
        location_idx = int(args_list[0],0)
        try:
            location = self.device_locations[location_idx]
        except IndexError:
            print('Invalid location')
            return

        ft4222_ic = ft4222.openByLocation(location)
        i2c = I2C(ft4222_ic)
        self.tca9555 = TCA9555(i2c=i2c)

    def do_reset_ports(self,args):
        self.tca9555.hw_init()

    def do_read_input_port_bit(self,args):
        pass

    def do_read_input_port_word(self,args):
        pass

    def do_set_output_port_bit(self, args):
        pass

    def do_clear_output_port_bit(self, args):
        pass

    def do_write_output_word(self, args):
        args_list = args.split()
        port = int(args_list[0],0)
        word = int(args_list[1],0)

        self.tca9555.write_output_port_word(port,word)

    def do_set_config_bit(self, args):
        pass

    def do_clear_config_bit(self, args):
        pass

    def do_write_config_word(self, args):
        try:
            args_list = args.split()
            port = int(args_list[0],0)
            word = int(args_list[1],0)
        except IndexError:
            print('invalid command format')
            return

        self.tca9555.write_config_word(port,word)

    # helper methods
    def __init__(self):
        super(DemoApp, self).__init__()
        self.tca9555 = None
        self.device_locations = []

    def line_to_dict(self, line):
        return tuple(map(int, args.split()))


# cli app for testing
if __name__  == '__main__':
    # create new DUT

    # cli setup
    DemoApp().cmdloop()
            