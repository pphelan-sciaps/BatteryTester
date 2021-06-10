# standard library
from cmd import Cmd

# external packages
import ft4222

# internal packages

class ConnectionManager(object):
    """docstring for ConnectionManager"""
    def __init__(self):
        self._device_locations = []
    
    @property
    def test_box_ids(self):
        return self._test_box_ids

    @property
    def available_box_ids(self) -> int:
        pass

    @property
    def device_locations(self) -> int:
        num_devices = ft4222.createDeviceInfoList()
        devices = [ft4222.getDeviceInfoDetail(i,False) \
            for i in range(num_devices) \
            if ft4222.getDeviceInfoDetail(i,False).get('serial') == b'A']
        self._device_locations = [device.get('location') for device in devices]
        return self._device_locations


    def open_connection(self, idx: int) -> ft4222.FT4222:
        locations = self.device_locations
        print(locations)
        
        try:
            location = locations[idx]
            ft4222_ic = ft4222.openByLocation(location)
            return ft4222_ic
        except IndexError as e:
            print(f'Invalid device location index')
        except ft4222.FT2XXDeviceError as e:
            print(f'Unable to open device at location {location}')

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
            