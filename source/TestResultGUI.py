# GUI for test result
# system utilities
import sys
import traceback
import configparser

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

# package modules
from PackageLogger import get_logger
from TestResult import TestResult

# consts
HUGE_FONT  = ("Verdana",24)
LARGE_FONT = ("Verdana",16)
NORM_FONT  = ("Helvetica",12)
SMALL_FONT = ("Helvetica",10)
LOGGER_NAME = "TestResultGUI"

def draw_gui():
    # build window
    window = tk.Tk()
    window.title("Battery Pass/Fail Test")
    window.rowconfigure(0, minsize=320, weight=1)
    window.columnconfigure(0, minsize=480, weight=1)

    # build frame
    frm = tk.Frame(window)

    # row 0
    title_lbl = tk.Label(
        frm,
        text="Battery Pass/Fail Check",
        font=LARGE_FONT)
    title_lbl.grid(
        row=0,
        column=0,
        padx=4,
        pady=4,
        sticky="NE")

    # row 1
    view_result_btn = ttk.Button(
        frm,
        text="Load Results File",
        command = lambda: check_result_cllbck())
    view_result_btn.grid(
        row=1,
        column=0,
        padx=4,
        pady=4)

    # row 2
    result_lbl = ttk.Label(
        frm,
        text="No test result loaded",
        font=NORM_FONT)
    result_lbl.grid(
        row=2,
        column=0,
        padx=4,
        pady=4)

    frm.grid(row=0,column=0)

    return window

def get_config():
    # logger

    # test limits
    config = configparser.ConfigParser()
    config.read('BatteryTest.ini')

    # logger
    logger_name = 'BatteryTest'

# callback
def check_result_cllbck():

    fname = filedialog.askopenfilename(
        filetypes=(
            ("log files","*.log"),
            ("text files","*.txt"),
            ("All files","*.*")),
        title="Select battery log file")


    # # build file names
    # fname = sys.argv[1]
    # fname_in = fname
    # fname_out = os.path.splitext(fname)[0] + '.csv'

    # # build test results from file
    # test = TestResult(fname=fname_in, logger_name=logger_name)

    # # export test results to csv
    # test.TestResult_to_csv(fname_out)

    # # compare with test limits
    # errors = 0


if __name__ == '__main__':
    # main logger
    logger = get_logger(LOGGER_NAME)

    # build gui
    window = draw_gui()

    # get configuration


    # run app
    window.mainloop()