# standard library
from collections import namedtuple
import curses
import curses.textpad

# external packages

# internal packages
from source.UI.BatShell import BatShell

# constants
ColorPair = namedtuple('ColorPair', ['idx', 'fg', 'bg'])
color_pairs = {
    'BY' : ColorPair(1, curses.COLOR_BLACK, curses.COLOR_YELLOW),
    'BW' : ColorPair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
}

Command = namedtuple('Command', ['key_str', 'key_int', 'description'])
commands = [
    # Command('h', ord('h'), 'elp'),
    Command('e', ord('e'), 'xit'),
    Command('o', ord('o'), 'pen box'),
    Command('c', ord('c'), 'lose box'),
    Command('t', ord('t'), 'est'),
    Command('q', ord('q'), 'uickcharge'),
    Command('d', ord('d'), 'emo'),
    Command('s', ord('s'), 'top'),
    # Command('i', ord('i'), 'mport'),
    # Command('[p]', curses.KEY_STAB, 'command prompt'),
    # Command('[b]', ord('b'), 'exit prompt')
]

PROMPT_STR_DEFAULT = '(BatShell) '

class TUI():
    def __init__(self):
        self.shell = BatShell()
        self.boxes = []

        self.box_id = 'N/A'
        self.test_status = 'N/A'
        self.test_time = 'N/A'

        self.prompt_str = PROMPT_STR_DEFAULT

        self.gas_gauge_stats = {
            'bat_voltage_mV'    : 'xxxxx',
            'bat_current_mA'    : 'xxxxx',
            'bat_charge_mAh'    : 'xxxxx',
            'bat_charge_level'  : 'xxx.x'
        }

        self.ref_stats = {
            'ref_voltage_mV'    : 'xxxxx',
            'ref_current_mA'    : 'xxxxx',
            'ref_charge_mAh'    : ' N/A ',
            'ref_charge_level'  : ' N/A '
        }

        curses.wrapper(self.curses_main)

    # main loop
    def curses_main(self,stdscr):
        # init elements
        self.stdscr = stdscr
        self.title_win  = curses.newwin( 4, 40,  0, 0)
        self.conn_win   = curses.newwin( 2, 40,  4, 0)
        self.box_win    = curses.newwin(10, 40,  6, 0)
        self.cmd_win    = curses.newwin( 3, 80, 16, 0)
        # self.prompt_pad = curses.newpad( 1, 200)
        # self.prompt_pad.refresh(0,0, 19,0, 19,79)
        self.prompt_win = curses.newwin( 1, 80, 19, 0)

        # self.cmd_tb = curses.textpad.Textbox(self.entry_win, insert_mode=True)

        # init colors
        for pair in color_pairs.values():
            curses.init_pair(*pair)

        # setup
        curses.cbreak()
        curses.noecho()
        curses.curs_set(0)
        self.stdscr.nodelay(True)

        self.draw_scr()

        quit = False
        # main loop
        while self.command():
            # step through test state machines
            self.shell.onecmd('step')
            
            # update ui
            self.update_conns()
            self.update_stats()
            self.draw_prompt_win()

            curses.napms(100)


    # helper methods
    def command(self):
        key_int = self.stdscr.getch()
        if key_int != -1:
            curses.beep()

        shell_str = ''
        if key_int == ord('e'):     # exit
            return False

        elif key_int == ord('o'):   # open box
            box_idx = self.get_prompt('enter box index: ')
            self.shell.onecmd(f'open {box_idx}')

            box_id = self.shell.onecmd('box_id')
            self.prompt_str = PROMPT_STR_DEFAULT + f'box {box_id} opened'

        elif key_int == ord('c'):   # close box
            if self.shell.onecmd('test_state') != 'sIDLE':
                self.prompt_str = PROMPT_STR_DEFAULT + 'test must be stopped before closing box'
            else:
                box_id = self.shell.onecmd('box_id')
                self.shell.onecmd('close')
                self.prompt_str = PROMPT_STR_DEFAULT + f'box {box_id} closed'
        
        elif key_int == ord('q'):   # quickcharge
            charge_level_str = self.get_prompt('charge level: ')
            try:
                charge_level = int(charge_level_str)
                if charge_level < 0 or charge_level > 100:
                    raise ValueError
                else:
                    self.shell.onecmd(f'quickcharge {charge_level}')
                    self.prompt_str = PROMPT_STR_DEFAULT + f'quickcharge set to {charge_level}%'
            except ValueError:
                self.prompt_str = PROMPT_STR_DEFAULT + f'value must be number between 0-100%'
            except Exception as e:
                raise e
        
        elif key_int == ord('d'):   # demo cycle
            self.shell.onecmd('start_test -s')
            self.prompt_str = PROMPT_STR_DEFAULT + f'running demo'

        elif key_int == ord('t'):   # demo cycle
            self.shell.onecmd('start_test')
            self.prompt_str = PROMPT_STR_DEFAULT + f'running demo'
        
        elif key_int == ord('s'):   # stop test
            if self.shell.onecmd('test_state') != 'sIDLE':
                prompt_in = self.get_prompt("enter 'y' to stop test: ")

                if prompt_in.lower().strip() == 'y':
                    self.shell.onecmd('stop')
                    self.prompt_str = PROMPT_STR_DEFAULT + f'test stopped'

        # elif key_int == ord('i'):   # import result
        #     fname = self.get_prompt("enter result file name: ")
        # elif key_int == ord('p'):   # command prompt
        #     self.get_prompt()

        return True

    def get_prompt(self, prompt=''):
        self.stdscr.refresh()
        # update prompt window
        self.prompt_str = PROMPT_STR_DEFAULT + prompt
        self.draw_prompt_win()

        # create textbox and window
        x = len(self.prompt_str)
        y = 19
        
        textbox_win = curses.newwin(1, 80-x, 19, x)
        color_attr = curses.color_pair(color_pairs['BW'].idx)
        textbox_win.bkgd(' ', color_attr)
        textbox_win.attrset(color_attr)
        textbox = curses.textpad.Textbox(textbox_win)
        textbox_win.refresh()

        curses.curs_set(1)
        command_str = textbox.edit()
        curses.curs_set(0)  

        del textbox
        del textbox_win

        return command_str


    def update_conns(self):
        self.boxes = self.shell.onecmd('list_boxes')
        self.draw_conn_win()


    def update_stats(self):
        box_id = self.shell.onecmd('box_id')
        self.box_id = box_id if box_id else 'N/A'

        test_state = self.shell.onecmd('test_state')
        self.test_status = test_state if test_state else 'N/A'

        test_time = self.shell.onecmd('test_time')
        self.test_time = test_time if test_time else 'N/A'

        if self.shell.onecmd('test_done') and test_state == 'sIDLE':
            self.prompt_str = PROMPT_STR_DEFAULT + 'done'

        stats = self.shell.onecmd('read_gas_gauge')
        if stats:
            self.gas_gauge_stats ={
                'bat_voltage_mV'   : f'{stats["bat_voltage_mV"]:5.0f}',
                'bat_current_mA'   : f'{stats["bat_current_mA"]:5.0f}',
                'bat_charge_mAh'   : f'{stats["bat_charge_mAh"]:5.0f}',
                'bat_charge_level' : f'{stats["bat_charge_level"]:5.1f}'
            }
        else:
            self.gas_gauge_stats = {
                'bat_voltage_mV'    : 'xxxxx',
                'bat_current_mA'    : 'xxxxx',
                'bat_charge_mAh'    : 'xxxxx',
                'bat_charge_level'  : 'xxx.x'
            }
        
        self.draw_stat_win()

    # drawing methods
    def draw_scr(self):
        self.stdscr.erase()
        self.draw_title_win()
        self.draw_conn_win()
        self.draw_stat_win()
        self.draw_cmd_win()
        self.draw_prompt_win()
        self.stdscr.refresh()

    def draw_title_win(self):
        self.stdscr.refresh()
        self.title_win.erase()
        self.title_win.refresh()
        win_str =  '-------------------\n'
        win_str += '---BatShell V1.0---\n'
        win_str += '-------------------\n'
        self.title_win.addstr(0,0,win_str)
        self.title_win.refresh()

    def draw_conn_win(self):
        self.stdscr.refresh()
        self.conn_win.erase()
        self.conn_win.addstr(0,0,f'Available boxes: {self.boxes}\n')
        self.conn_win.refresh()

    def draw_stat_win(self):
        self.stdscr.refresh()
        self.box_win.erase()
        win_str =  f'Connected Box: {self.box_id}\n'
        win_str += f'Test Status: {self.test_status}\n'
        win_str += f'Test Time: {self.test_time}\n\n'
        win_str += f'Measurement     Gas Gauge Reference:\n'
        win_str += f'Capacity (mAh) |  '
        win_str += f'{self.gas_gauge_stats["bat_charge_mAh"]}  |  '
        win_str += f'{self.ref_stats["ref_charge_mAh"]}\n'
        win_str += f'Capacity (%)   |  '
        win_str += f'{self.gas_gauge_stats["bat_charge_level"]}  |  '
        win_str += f'{self.ref_stats["ref_charge_level"]}\n'
        win_str += f'Voltage (mV)   |  '
        win_str += f'{self.gas_gauge_stats["bat_voltage_mV"]}  |  '
        win_str += f'{self.ref_stats["ref_voltage_mV"]}\n'
        win_str += f'Current (mA)   |  '
        win_str += f'{self.gas_gauge_stats["bat_current_mA"]}  |  '
        win_str += f'{self.ref_stats["ref_current_mA"]}\n'
        self.box_win.addstr(0,0,win_str)
        self.box_win.refresh()

    def draw_cmd_win(self):
        self.stdscr.refresh()
        self.cmd_win.erase()
        color_attr = curses.color_pair(color_pairs['BY'].idx)
        self.cmd_win.bkgd(' ', color_attr)
        self.cmd_win.attrset(color_attr)
        self.cmd_win.addstr(0,0,'commands:\n')

        first = True
        for command in commands:
            # space between elements
            if first:
                first = False
            else:
                self.cmd_win.addstr('   ')


            self.cmd_win.addstr(command.key_str, curses.A_UNDERLINE)
            self.cmd_win.addstr(command.description)

        self.cmd_win.refresh()

    def draw_prompt_win(self):
        
        self.stdscr.refresh()
        self.prompt_win.erase()

        color_attr = curses.color_pair(color_pairs['BW'].idx)
        self.prompt_win.addstr(0,0,self.prompt_str)
        self.prompt_win.bkgd(' ', color_attr)
        self.prompt_win.refresh()

        # self.entry_win.erase()
        
        # self.entry_win.bkgd(' ', color_attr)
        # self.entry_win.attrset(color_attr)
        # # self.pad_win.mvderwin(0,len(self.prompt_str))
        # self.entry_win.refresh()

        # self.shell_subwin.refresh()

tui = None

# cli app for testing
if __name__ == '__main__':
    tui = TUI()