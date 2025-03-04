import os
import pandas as pd
import numpy as np
import pickle
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

from Utility import Utility, SaveFiles, Windows, Tables
from DataFrameProcessor import DataFrameProcessor
from Dashboard import Dashboard


class FinanceTracker(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Personal Finance Tracker")
        self.resizable(True, True)
        
        self.protocol("WM_DELETE_WINDOW", self.onClose)
        
        self.current_frame = None  # Keep track of the current section
        
        self.initMenuBar()
        self.bindShortcuts()
        
        self.startFresh(on_start=True)
        self.initUI()
        
        return

    def initMenuBar(self):
        """Initialize the menu bar with dropdown menus."""
        menubar = tk.Menu(self)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open", command=self.selectFilesAndFolders, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.saveState, accelerator="Ctrl+S")
        file_menu.add_command(label="Save as", command=self.saveStateAs, accelerator="Ctrl+Shift+S")
        file_menu.add_command(label="New", command=self.startFresh, accelerator="Ctrl+N")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.onClose, accelerator="Esc")
        menubar.add_cascade(label="File", menu=file_menu)
        
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Edit Initial Values", command=self.editInitialValues, accelerator="Ctrl+E")
        edit_menu.add_command(label="Reload Data", command=self.reloadData, accelerator="Ctrl+R")
        edit_menu.add_command(label="Update Data", command=self.updateData, accelerator="Ctrl+U")
        menubar.add_cascade(label="Edit", menu=edit_menu)
        
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="All Data", command=self.showDashboard, accelerator="Ctrl+D")
        view_menu.add_command(label="Monthly Breakdown", command=self.showMonthlyBreakdown, accelerator="Ctrl+A")
        view_menu.add_command(label="Savings Breakdown", command=self.showSavings, accelerator="Ctrl+B")
        view_menu.add_command(label="Spending Breakdown", command=self.showSpending, accelerator="Ctrl+L")
        view_menu.add_command(label="Investments", command=self.showInvestments, accelerator="Ctrl+I")
        menubar.add_cascade(label="View", menu=view_menu)
        
        self.config(menu=menubar)
    
    def bindShortcuts(self):
        """Bind keyboard shortcuts to functions."""
        self.bind("<Control-a>", lambda event: self.showMonthlyBreakdown())
        self.bind("<Control-b>", lambda event: self.showStatistics(event=event, df_type='inc'))
        #self.bind("<Control-c>",)
        self.bind("<Control-d>", lambda event: self.showDashboard())
        self.bind("<Control-e>", lambda event: self.editInitialValues())
        #self.bind("<Control-f>",)
        #self.bind("<Control-g>",)
        #self.bind("<Control-h>",)
        self.bind("<Control-i>", lambda event: self.showInvestments())
        #self.bind("<Control-j>",)
        #self.bind("<Control-k>",)
        self.bind("<Control-l>", lambda event: self.showStatistics(event=event, df_type='exp'))
        #self.bind("<Control-m>",)
        self.bind("<Control-n>", lambda event: self.startFresh())
        self.bind("<Control-o>", lambda event: self.selectFilesAndFolders())
        #self.bind("<Control-p>",)
        #self.bind("<Control-q>",)
        self.bind("<Control-r>", lambda event: self.reloadData())
        self.bind("<Control-s>", lambda event: self.saveState())
        self.bind("<Control-S>", lambda event: self.saveStateAs())
        #self.bind("<Control-t>",)
        self.bind("<Control-u>", lambda event: self.updateData())
        #self.bind("<Control-v>",)
        self.bind("<Control-w>", lambda event: self.destroy())
        #self.bind("<Control-x>",)
        #self.bind("<Control-y>",)
        #self.bind("<Control-z>",)
        
        self.bind("<Escape>",    lambda event: self.onClose())
        
        return        

    def initUI(self):
        """Initialize the main interface without tabs."""
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(expand=True, fill="both")
        
        #self.main_frame.focus_set()
        
        #self.selectFilesAndFolders(reload=True)
        #self.showMainFrame(start_fresh=False)
        
        #self.showSpending()
        #self.destroy()
        
        return
    
    def startFresh(self, on_start=False):
        """Reset the app to a fresh state without prior data"""
        self.data_files         = []    # To store selected files
        self.number_of_files    = 0     # Number of files read-in
        self.sort_orders        = {}    # Track sorting order for each column
        
        self.income_data    = pd.DataFrame()
        self.expenses_data  = pd.DataFrame()
        self.starting_data  = pd.DataFrame()
        
        self.date_range = [date(2024, 1, 1),    date(2050, 12, 31)]
        self.new_date_range = self.date_range.copy()
        self.amount_range = [[0, 1e8], [0, 1e8]]
        self.new_amount_range = self.amount_range.copy()
        self.accounts = []
        self.new_accounts = self.accounts.copy()
        self.inc_categories = []
        self.exp_categories = []
        self.new_inc_categories = self.inc_categories.copy()
        self.new_exp_categories = self.exp_categories.copy()
        
        self.last_saved_file = os.path.join(os.path.dirname(__file__), "lastSavedFile.txt")
           
        self.switch_monthly_order = True
        
        self.hide_index = True
        
        self.current_window = ''
        self.current_sort = 'Index'
        
        # For formatting consistency
        
        self.my_font = tk.font.Font(size=12, font='calibri')
        self.font_type = 'calibri'
        self.font_size = 12
        
        self.banded_row = ["#e6f2ff", "#ffffff", '#D3D3D3']
        self.background_color = "#dce7f5"
        
        self.backslash = '\n'
        
        #if on_start == False:
        #    self.clearMainFrame()
        #    self.selectFilesAndFolders(reload=False)
             
        return
    
    
        
    
    
    
    
    

if __name__ == "__main__":
    app = FinanceTracker()
    app.mainloop()