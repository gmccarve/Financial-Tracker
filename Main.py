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
from Dashboard import Dashboard
from StyleConfig import StyleConfig

pd.set_option('display.max_columns', None)
#pd.set_option('display.max_rows', None)
pd.set_option('display.float_format','{:.2f}'.format)

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
        
        self.save_file_loc = os.path.join(os.path.dirname(__file__), "lastSavedFile.txt")
        self.save_file = self.readSaveFile()
        
        self.user_settings_file = os.path.join(os.path.dirname(__file__), "user_settings.pkl")
        
        self.current_frame = Dashboard(self)
        self.current_frame.grid(row=0, column=0, sticky="nsew")
        
        return

    def initMenuBar(self):
        """Initialize the menu bar with dropdown menus."""
        menubar = tk.Menu(self)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open", command=lambda: self.current_frame.openData(), accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=lambda: self.current_frame.saveData(), accelerator="Ctrl+S")
        file_menu.add_command(label="Save as", command=lambda: self.current_frame.saveDataAs(), accelerator="Ctrl+Shift+S")
        file_menu.add_command(label="New", command=lambda event: self.current_frame.clearTable(), accelerator="Ctrl+N")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.closeWindow, accelerator="Esc")
        menubar.add_cascade(label="File", menu=file_menu)
        
        accounts_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Accounts", menu=accounts_menu)
        
        reports_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Reports", menu=reports_menu)
        
        tools_menu = tk.Menu(menubar, tearoff=0)
        #tools_menu.add_command(label="Train Classifier", command=lambda: self.current_frame.trainClassifier(), accelerator="Ctrl+T")
        menubar.add_cascade(label="Tools", menu=tools_menu)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.config(menu=menubar)
    
    def bindShortcuts(self):
        """Bind keyboard shortcuts to functions."""
        self.bind("<Control-a>", lambda event: self.current_frame.selectAllRows())
        #self.bind("<Control-b>")
        #self.bind("<Control-c>")
        #self.bind("<Control-d>")
        #self.bind("<Control-e>")
        self.bind("<Control-f>", lambda event: self.current_frame.openSearch())
        #self.bind("<Control-g>")
        #self.bind("<Control-h>")
        #self.bind("<Control-i>")
        #self.bind("<Control-j>")
        #self.bind("<Control-k>")
        #self.bind("<Control-l>")
        #self.bind("<Control-m>",)
        self.bind("<Control-n>", lambda event: self.current_frame.clearTable())
        self.bind("<Control-o>", lambda event: self.current_frame.openData())
        #self.bind("<Control-p>")
        #self.bind("<Control-q>")
        #self.bind("<Control-r>")
        self.bind("<Control-s>", lambda event: self.current_frame.saveData())
        self.bind("<Control-S>", lambda event: self.current_frame.saveDataAs())
        self.bind("<Control-t>", lambda event: self.current_frame.trainClassifier())
        #self.bind("<Control-u>", lambda event: self.updateData())
        #self.bind("<Control-v>")
        self.bind("<Control-w>", lambda event: self.closeWindow())
        #self.bind("<Control-x>")
        #self.bind("<Control-y>")
        #self.bind("<Control-z>")
        
        self.bind("<Escape>",    lambda event: self.closeWindow())

        # Bind Delete key to deleteTransaction only if a row is selected
        self.bind("<Delete>", lambda event: self.current_frame.deleteTransaction())
        
        return        
      
    def closeWindow(self):
        """Prompt user to save before exiting."""
        #TODO UNDO
        #TODO Doc string
        #if not self.income_data.empty or not self.expenses_data.empty:
        #    if messagebox.askyesno("Save State", "Would you like to save the financial data before exiting?"):
        #        self.saveState()
        self.destroy()
        
    def readSaveFile(self):
        try:
            with open(self.save_file_loc, 'r') as f:
                save_file = f.readlines()
            return save_file[0]
        except:
            return ''
    
    def changeSaveFile(self):
        with open(self.save_file_loc, 'w') as f:
            f.write(self.save_file)
        return
        
        
if __name__ == "__main__":
    app = FinanceTracker()
    app.mainloop()