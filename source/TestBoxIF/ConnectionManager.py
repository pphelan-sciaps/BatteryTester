# standard library
from cmd import Cmd
from enum import Enum

# external packages
import ft4222

# internal packages
from source.TestBoxIF.I2C import I2C

# Box name mapping
box_names = {
    '01A' : 'A',
    '01B' : 'Box01AA',
    '02A' : 'Box02AA',
    '02B' : 'Box02BA',
    '03A' : 'Box03AA',
    '03B' : 'Box03BA',
    '04A' : 'Box04AA',
    '04B' : 'Box04BA',
    '05A' : 'Box05AA',
    '05B' : 'Box05BA'
}

box_names_inv = {v: k for k, v in box_names.items()}

class ConnectionManager(object):
    """docstring for ConnectionManager"""
    def __init__(self):
        self._devices = []
        self._device_locations = []
    
    @property
    def test_box_ids(self):
        return self._test_box_ids

    @property
    def available_box_ids(self) -> int:
        pass

    @property
    def devices(self) -> dict:
        devices = []
        all_devices = [ft4222.getDeviceInfoDetail(i,False) \
            for i in range(ft4222.createDeviceInfoList())]
        for device in all_devices:
            serial = device.get('serial',None)
            port = chr(serial[-1])

            if port == 'A':
                devices.append(device)

        self._devices = devices
        return self._devices


    @property
    def device_locations(self) -> int:
        self._device_locations = [device['location'] \
            for device in self.devices]
        return self._device_locations

    @property
    def device_names(self) -> int:
        self._device_locations = [box_names_inv[device['serial'].decode()] \
            for device in self.devices]
        return self._device_locations


    def open_connection(self, location_str: None) -> I2C:
        try:
            if location_str.isnumeric():
                idx = int(location_str)
                location = self.device_locations[idx]
                box_name = self.device_names[idx]
                ft4222_ic = ft4222.openByLocation(location)
            else:
                serial = box_names[location_str].encode()
                box_name = location_str
                
                ft4222_ic = ft4222.openBySerial(serial)
            return I2C(ft4222_ic,box_name)
        except KeyError:
            print('invalid box name')
        except IndexError as e:
            print(f'Invalid device location index')
        except ft4222.FT2XXDeviceError as e:
            print(f'Unable to open device {location_str}')

class DemoApp(Cmd):
    """docstring for DemoApp"""
    # shell settings
    intro = 'ConnectionManager demo app.  Type help or ? to list commands.\n'
    prompt = '(ConMan) '

    # commands
    def do_get_device_locations(self,args):
        print(self.conn_man.device_locations)

    def do_open_idx(self,args):
        args_list = args.split()
        idx = int(args_list[0],0)


    # helper methods
    def __init__(self):
        super(DemoApp, self).__init__()
        self.conn_man = ConnectionManager()     

# cli app for testing
if __name__ == '__main__':
    DemoApp.cmdloop()
            