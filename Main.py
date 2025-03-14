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
import pickle


from typing import List, Tuple, Union

#from Utility import Utility, Windows, Tables
from NewDashboard import Dashboard
from StyleConfig import StyleConfig

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.float_format','{:.2f}'.format)

class FinanceTracker(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Personal Finance Tracker")
        self.resizable(True, True)
        self.state('zoomed')
        
        self.protocol("WM_DELETE_WINDOW", self.close_window)
        
        self.focus_set()
        
        self.initMenuBar()
        self.bindShortcuts()
        
        self.current_frame = Dashboard(self)
        self.current_frame.grid(row=0, column=0, sticky="nsew")
        
        return

    def initMenuBar(self):
        """Initialize the menu bar with dropdown menus."""
        menubar = tk.Menu(self)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open", command=lambda: self.current_frame.open_data(), accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=lambda: self.current_frame.save_data(), accelerator="Ctrl+S")
        file_menu.add_command(label="Save as", command=lambda: self.current_frame.save_data_as(), accelerator="Ctrl+Shift+S")
        file_menu.add_command(label="New", command=lambda: self.current_frame.clear_table(), accelerator="Ctrl+N")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.close_window, accelerator="Esc")
        menubar.add_cascade(label="File", menu=file_menu)
        
        accounts_menu = tk.Menu(menubar, tearoff=0)
        accounts_menu.add_command(label="Add Banking Account", command=lambda: self.current_frame.add_banking_account())
        accounts_menu.add_command(label="Add Investment Account", command=lambda: self.current_frame.add_investment_account())
        menubar.add_cascade(label="Accounts", menu=accounts_menu)
        
        reports_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Reports", menu=reports_menu)
        
        tools_menu = tk.Menu(menubar, tearoff=0)
        #tools_menu.add_command(label="Train Classifier", command=lambda: self.current_frame.train_classifier(), accelerator="Ctrl+T")
        menubar.add_cascade(label="Tools", menu=tools_menu)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.config(menu=menubar)
    
    def bindShortcuts(self):
        """Bind keyboard shortcuts to functions."""
        self.bind("<Control-a>", lambda event: self.current_frame.select_all_rows())
        #self.bind("<Control-b>")
        #self.bind("<Control-c>")
        #self.bind("<Control-d>")
        self.bind("<Control-e>", lambda event: self.current_frame.export_data())
        self.bind("<Control-f>", lambda event: self.current_frame.open_search())
        #self.bind("<Control-g>")
        #self.bind("<Control-h>")
        #self.bind("<Control-i>")
        #self.bind("<Control-j>")
        #self.bind("<Control-k>")
        #self.bind("<Control-l>")
        #self.bind("<Control-m>",)
        self.bind("<Control-n>", lambda event: self.current_frame.clear_table())
        self.bind("<Control-o>", lambda event: self.current_frame.open_data())
        #self.bind("<Control-p>")
        #self.bind("<Control-q>")
        #self.bind("<Control-r>")
        self.bind("<Control-s>", lambda event: self.current_frame.save_data())
        self.bind("<Control-S>", lambda event: self.current_frame.save_data_as())
        #self.bind("<Control-t>", lambda event: self.current_frame.train_classifier())
        #self.bind("<Control-u>", lambda event: self.updateData())
        #self.bind("<Control-v>")
        self.bind("<Control-w>", lambda event: self.current_frame.close_window())
        #self.bind("<Control-x>")
        #self.bind("<Control-y>")
        #self.bind("<Control-z>")
        
        self.bind("<Escape>",    lambda event: self.close_window())

        # Bind Delete key to deleteTransaction only if a row is selected
        self.bind("<Delete>", lambda event: self.current_frame.delete_entry())
        
        return
    
    def close_window(self):
        """Prompt user to save before exiting."""
        #TODO UNDO
        #TODO Doc string
        #if not self.income_data.empty or not self.expenses_data.empty:
        #    if messagebox.askyesno("Save State", "Would you like to save the financial data before exiting?"):
        #        self.save_state()
        self.destroy()
        
        
if __name__ == "__main__":
    app = FinanceTracker()
    app.mainloop()