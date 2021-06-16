# standard library
import curses
import curses.textpad
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
    prompt = '(BatShell ) '

    def do_EOF(self,args):
        print('exiting')
        return True

    # commands
    def do_list_boxes(self,args) -> list:
        # print('Box USB locations:')
        # locs = self._test_man.device_locations
        locs = self._test_man.device_locations
        names = self._test_man.device_names

        # print(locs)
        # print(names)
        return locs,names


    def do_open(self,args):
        idx = None
        name = None

        args_list = args.split()
        location_str = args_list[0]

        opened = self._test_man.open_connection(location_str)
        if opened:
            self._box = self._test_man.bat_test(0)._if_board
        return opened
        # self.onecmd('read_gas_gauge')

    def do_close(self,args):
        if self._box:
            self._test_man.close_connection()
            self._box = None

    def do_box_id(self,args):
        if self._box:
            return self._box.usb_id

    def do_start_test(self,args):
        args_list = args.split()
        if '-s' in args_list:
            charge_setpoint = 10
            short_test = True
        else:
            charge_setpoint = 35
            short_test = False

        if self._box:
            self._test_man.bat_test(0).start_test(charge_setpoint, short_test)
    
    def do_resume_test(self,args):
        if self._box:
            self._test_man.bat_test(0).resume_test()

    def do_quickcharge(self,args):
        args_list = args.split()
        try:
            charge_setpoint = int(args_list[0],0)
            self._test_man.bat_test(0).start_quickcharge(charge_setpoint)
        except ValueError:
            print('Invalid charge setpoint')
        except:
            pass

    def do_stop(self,args):
        if self._box:
            self._test_man.bat_test(0).stop()

    def do_import_test(self,args):
        pass

    def do_step(self,args):
        if self._test_man:
            self._test_man.step()

    # test running
    def do_test_state(self,args):
        if self._box:
            return self._test_man.bat_test(0).state_name

    def do_test_time(self,args):
        if self._box:
            return self._test_man.bat_test(0).test_time

    def do_test_pass(self,args):
        if self._box:
            return self._test_man.bat_test(0).test_pass

    def do_test_done(self,args):
        if self._box:
            return self._test_man.bat_test(0).done

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
            print(hex(self._box.gas_gauge.status_reg))
        else:
            print('no box connected')

    def do_read_gas_gauge_config(self,args):
        if self._box:
            config_reg = self._box.gas_gauge.config_reg
            # print(f'{hex(config_reg)} tui- {bin(config_reg)}')
            return config_reg
        else:
            pass
            # print('no box connected')


    def do_write_gas_gauge_config(self,args):
        if self._box:
            args_list = args.split()
            word = int(args_list[0],0)
            self._box.gas_gauge.config_reg = word

    def do_read_gas_gauge(self,args):
        if self._box:
            if self._box.battery_present:
                return self._box.gas_gauge.get_all()


                # gas_gauge_data = self._box.gas_gauge.get_all()
                # if None in gas_gauge_data.values():
                #     print('unable to communicate with battery')
                # else:
                #     print(f'{gas_gauge_data["timestamp"]}')
                #     print(f'charge: {gas_gauge_data["charge_mAh"]:.0f} mAh ' \
                #         f'({gas_gauge_data["charge_level"]:.1f}%)')
                #     print(f'voltage: {self._box.gas_gauge.voltage_mV:.0f} mV')
                #     print(f'current: {self._box.gas_gauge.current_mA:.0f} mA')
            else:
                pass
                # print('battery not present')
                

    def do_exit(self,args):
        return True

    # DMMs

    # helper methods
    def __init__(self, standalone = False):
        super(BatShell, self).__init__()
        self._test_man = TestManager(standalone)
        self._box = None
        self._test_log = None

    def cmdloop(self, intro=None):
        print(self.intro)
        while True:
            try:
                super(BatShell, self).cmdloop(intro="")
                break
            except KeyboardInterrupt:
                print("^C")
                self.onecmd('stop_test')

    def postcmd(self, stop, line):
        return line.lower() == 'exit'


# cli app for testing
if __name__ == '__main__':

    shell = BatShell(standalone = True).cmdloop()
