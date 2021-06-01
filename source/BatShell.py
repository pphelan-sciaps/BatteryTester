# standard library
from cmd import Cmd
import asyncio

# external packages

# internal packages
from source import TestBoxIF
from source.BatTest.TestManager import TestManager

from source.TestBoxIF.GPIO import GPIOError

class BatShell(Cmd):
    # shell settingsa
    intro = '\nBatMan demo pp.  Type help of ? to list commands.\n'
    prompt = '(BatShell )'

    def do_EOF(self,args):
        print('exiting')
        return True

    # commands
    def do_list_boxes(self,args):
        print('Box USB locations:')
        print(self._test_man.device_locations)

    def do_open(self,args):
        args_list = args.split()
        location_idx = int(args_list[0],0)
        self._test_man.open_connection(location_idx)
        self._box = self._test_man.bat_test(0)._if_board

    def do_start_test(self,args):
        self._test_man.bat_test(0).start_test()

    def do_stop_test(self,args):
        self._test_man.bat_test(0).stop()

    def do_process(self,args):
        self._test_man.bat_test(0).process()

    # test running

    # GPIO
    def do_battery_present(self,args):
        if self._box:
            print(f'Battery present? {self._box.battery_present}')

    def do_charge_enable(self,args):
        if self._box:
            try:
                self._box.gas_gauge.control_init()
                self._box.gpio.charge_enable = 1
                self._box.gpio.led_run_enable = 1
            except GPIOError as e:
                print(e)

    def do_charge_disable(self,args):
        if self._box:
            try:
                self._box.gpio.charge_enable = 0
                self._box.gpio.led_run_enable = 0
            except GPIOError as e:
                print(e)

    def do_charge_status(self,args):
        if self._box:
            print(f'Battery charging? {self._box.gpio.charge_enable}')

    def do_discharge_enable(self,args):
        if self._box:
            try:
                self._box.gas_gauge.control_init()
                self._box.gpio.discharge_enable = 1
                self._box.gpio.led_run_enable = 1
            except GPIOError as e:
                print(e)

    def do_discharge_disable(self,args):
        if self._box:
            try: 
                self._box.gpio.discharge_enable = 0
                self._box.gpio.led_run_enable = 0
            except GPIOError as e:
                print(e)

    def do_discharge_status(self,args):
        if self._box:
            print(f'Battery discharging? {self._box.gpio.discharge_enable}')

    def do_led_run_enable(self,args):
        if self._box:
            self._box.gpio.led_run_enable = 1

    def do_led_run_disable(self,args):
        if self._box:
            self._box.gpio.led_run_enable = 0

    def do_led_done_enable(self,args):
        if self._box:
            self._box.gpio.led_done_enable = 1

    def do_led_done_disable(self,args):
        if self._box:
            self._box.gpio.led_done_enable = 0

    def do_led_error_enable(self,args):
        if self._box:
            self._box.gpio.led_error_enable = 1

    def do_led_error_disable(self,args):
        if self._box:
            self._box.gpio.led_error_enable = 0

    def do_led_all_enable(self,args):
        if self._box:
            self._box.gpio.led_run_enable   = 1
            self._box.gpio.led_done_enable  = 1
            self._box.gpio.led_error_enable = 1

    def do_led_all_disable(self,args):
        if self._box:
            self._box.gpio.led_run_enable   = 0
            self._box.gpio.led_done_enable  = 0
            self._box.gpio.led_error_enable = 0

    def do_read_input_word(self,args):
        args_list = args.split()
        port = int(args_list[0],0)
        if self._box:
            print(f'{hex(self._box.gpio._reg_map.read_input_port_word(port))}')

    def do_read_output_word(self,args):
        args_list = args.split()
        port = int(args_list[0],0)
        if self._box:
            print(f'{hex(self._box.gpio._reg_map.read_output_port_word(port))}')


    # gas gauge
    def do_read_gas_gauge_status(self,args):
        if self._box:
            print(self._box.gas_gauge.status_reg)

    def do_read_gas_gauge_config(self,args):
        if self._box:
            print(self._box.gas_gauge.config_reg)

    def do_write_gas_gauge_config(self,args):
        if self._box:
            args_list = args.split()
            word = int(args_list[0],0)
            self._box.gas_gauge.config_reg = word

    def do_read_gas_gauge(self,args):
        if self._box:
            if self._box.battery_present:
                gas_gauge_data = self._box.gas_gauge.get_all()
                if None in gas_gauge_data.values():
                    print('unable to communicate with battery')
                else:
                    print(f'{gas_gauge_data["timestamp"]}')
                    print(f'charge: {gas_gauge_data["charge_mAh"]:.0f} mAh ' \
                        f'({gas_gauge_data["charge_level"]:.1f}%)')
                    print(f'voltage: {self._box.gas_gauge.voltage_mV:.0f} mV')
                    print(f'current: {self._box.gas_gauge.current_mA:.0f} mA')
            else:
                print('battery not present')

    def do_exit(self,args):
        return True

    # DMMs

    # helper methods
    def __init__(self):
        super(BatShell, self).__init__()
        self._test_man = TestManager()
        self._box = None

    def cmdloop(self, intro=None):
        print(self.intro)
        while True:
            try:
                super(BatShell, self).cmdloop(intro="")
                break
            except KeyboardInterrupt:
                print("^C")
                self.onecmd('stop_test')

# cli app for testing
if __name__ == '__main__':
    BatShell().cmdloop()
