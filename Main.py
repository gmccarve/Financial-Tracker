import os
import pandas as pd
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import Calendar
from datetime import date
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.text import OffsetFrom
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import seaborn as sns
import calendar
from datetime import datetime, timedelta

from typing import List, Tuple, Union

#from Utility import Utility, SaveFiles, Windows, Tables
from Dashboard import Dashboard
#from Accounts import Accounts
#from Statistics import Statistics
#from Investments import Investments

#pd.set_option('display.max_columns', None)
#pd.set_option('display.max_rows', None)
#pd.set_option('display.float_format','{:.2f}'.format)

class FinanceTracker(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Personal Finance Tracker")
        self.resizable(True, True)
        self.state('zoomed')
        
        self.protocol("WM_DELETE_WINDOW", self.closeWindow)
        
        self.focus_set()
        
        self.initMenuBar()
        self.bindShortcuts()
        
        self.current_frame = Dashboard(self)
        self.current_frame.pack(fill='both', expand=True)
        
        self.all_data = pd.DataFrame()
        
        return

    def initMenuBar(self):
        """Initialize the menu bar with dropdown menus."""
        menubar = tk.Menu(self)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        #file_menu.add_command(label="Open", command=self.selectFilesAndFolders, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.saveState, accelerator="Ctrl+S")
        file_menu.add_command(label="Save as", command=self.saveStateAs, accelerator="Ctrl+Shift+S")
        #file_menu.add_command(label="New", command=self.startFresh, accelerator="Ctrl+N")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.closeWindow, accelerator="Esc")
        menubar.add_cascade(label="File", menu=file_menu)
        
        accounts_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Accounts", menu=accounts_menu)
        
        reports_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Reports", menu=reports_menu)
        
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)

        
        self.config(menu=menubar)
    
    def bindShortcuts(self):
        """Bind keyboard shortcuts to functions."""
        #self.bind("<Control-a>")
        #self.bind("<Control-b>")
        #self.bind("<Control-c>",)
        #self.bind("<Control-d>")
        #self.bind("<Control-e>", lambda event: self.editInitialValues())
        #self.bind("<Control-f>",)
        #self.bind("<Control-g>",)
        #self.bind("<Control-h>",)
        #self.bind("<Control-i>")
        #self.bind("<Control-j>",)
        #self.bind("<Control-k>",)
        #self.bind("<Control-l>")
        #self.bind("<Control-m>",)
        #self.bind("<Control-n>", lambda event: self.startFresh())
        #self.bind("<Control-o>", lambda event: self.selectFilesAndFolders())
        #self.bind("<Control-p>",)
        #self.bind("<Control-q>",)
        #self.bind("<Control-r>", lambda event: self.reloadData())
        self.bind("<Control-s>", lambda event: self.saveState())
        self.bind("<Control-S>", lambda event: self.saveStateAs())
        #self.bind("<Control-t>",)
        #self.bind("<Control-u>", lambda event: self.updateData())
        #self.bind("<Control-v>",)
        self.bind("<Control-w>", lambda event: self.closeWindow())
        #self.bind("<Control-x>",)
        #self.bind("<Control-y>",)
        #self.bind("<Control-z>",)
        
        self.bind("<Escape>",    lambda event: self.closeWindow())
        
        return        
      
    def closeWindow(self):
        """Prompt user to save before exiting."""
        #TODO UNDO
        #TODO Doc string
        #if not self.income_data.empty or not self.expenses_data.empty:
        #    if messagebox.askyesno("Save State", "Would you like to save the financial data before exiting?"):
        #        self.saveState()
        self.destroy()
        
    def saveState(self):
        SaveFiles.saveState(self.last_saved_file, self.income_data, self.expenses_data, self.starting_data)
        
    def saveStateAs(self):
        SaveFiles.saveStateAs(self.income_data, self.expenses_data, self.starting_data)
        
        
if __name__ == "__main__":
    app = FinanceTracker()
    app.mainloop()