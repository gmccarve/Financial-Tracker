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

from Utility import Utility, SaveFiles, Windows, Tables
from Dashboard import Dashboard, DataFrameProcessor
from Accounts import Accounts
from Statistics import Statistics
from Investments import Investments


class FinanceTracker(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Personal Finance Tracker")
        self.resizable(True, True)
        
        self.protocol("WM_DELETE_WINDOW", self.closeWindow)
        
        self.current_frame = None  # Keep track of the current section
        
        # Initialize empty DataFrames
        self.income_data    = pd.DataFrame()
        self.expenses_data  = pd.DataFrame()
        self.starting_data  = pd.DataFrame()
        
        self.initMenuBar()
        self.bindShortcuts()
        
        self.showDashboard()
        
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
        
        edit_menu = tk.Menu(menubar, tearoff=0)
        #edit_menu.add_command(label="Edit Initial Values", command=self.editInitialValues, accelerator="Ctrl+E")
        #edit_menu.add_command(label="Reload Data", command=self.reloadData, accelerator="Ctrl+R")
        #edit_menu.add_command(label="Update Data", command=self.updateData, accelerator="Ctrl+U")
        menubar.add_cascade(label="Edit", menu=edit_menu)
        
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Dashboard (Main View)", command=self.showDashboard, accelerator="F1")
        view_menu.add_command(label="Accounts (Balance View)", command=self.showAccounts, accelerator="F2")
        view_menu.add_command(label="Income & Savings", command=self.showSavings, accelerator="F3")
        view_menu.add_command(label="Expenses & Spending", command=self.showSpending, accelerator="F4")
        view_menu.add_command(label="Investments", command=self.showInvestments, accelerator="F5")
        menubar.add_cascade(label="View", menu=view_menu)
        
        #TODO Accounts menu
        #TODO Tools menu
        #TODO Manage menu
        #TODO Help menu
        #TODO Reports menu
        #TODO Remove edit menu and put on dashboard as buttons
        
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
        
        self.bind("<F1>", lambda event: self.showDashboard())
        self.bind("<F2>", lambda event: self.showAccounts())
        self.bind("<F3>", lambda event: self.showSavings())
        self.bind("<F4>", lambda event: self.showSpending())
        self.bind("<F5>", lambda event: self.showInvestments())
        #self.bind("<F6>", lambda event: self.showDashboard())
        #self.bind("<F7>", lambda event: self.showDashboard())
        #self.bind("<F8>", lambda event: self.showDashboard())
        #self.bind("<F9>", lambda event: self.showDashboard())
        #self.bind("<F10>", lambda event: self.showDashboard())
        #self.bind("<F11>", lambda event: self.showDashboard())
        #self.bind("<F12>", lambda event: self.showDashboard())
        
        self.bind("<Escape>",    lambda event: self.closeWindow())
        
        return        
    
    def startFresh(self, on_start=False):
        """Reset the app to a fresh state without prior data"""
        self.data_files         = []    # To store selected files
        self.number_of_files    = 0     # Number of files read-in
        self.sort_orders        = {}    # Track sorting order for each column
        
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
             
        return
      
    def closeWindow(self):
        """Prompt user to save before exiting."""
        #TODO UNDO
        #TODO Doc string
        #if not self.income_data.empty or not self.expenses_data.empty:
        #    if messagebox.askyesno("Save State", "Would you like to save the financial data before exiting?"):
        #        self.saveState()
        self.destroy()
        
    def clearWindow(self):
        """Removes the current frame and replaces it with a new one."""
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = None  # Reset the reference
        
    def saveState(self):
        SaveFiles.saveState(self.last_saved_file, self.income_data, self.expenses_data, self.starting_data)
        
    def saveStateAs(self):
        SaveFiles.saveStateAs(self.income_data, self.expenses_data, self.starting_data)
        
    def showDashboard(self) -> None:
        """
        Displays the main dashboard with income and expense tables.

        It loads fresh copies of the stored income and expenses data.
        """
        self.clearWindow()
        self.current_frame = Dashboard(self)
        self.current_frame.pack(fill='both', expand=True)
        
    def showAccounts(self) -> None:
        """
        Displays the Accounts dashboard with monthly account breakdowns.

        It loads data stored income and expenses data from the main dashboard.
        """
        self.clearWindow()
        self.current_frame = Accounts(self)
        self.current_frame.pack(fill='both', expand=True)
        
    def showSpending(self, event=None) -> None:
        """
        Displays the Spending dashboard.

        It loads data stored income and expenses data from the main dashboard..
        """
        self.clearWindow()
        self.current_frame = Statistics(self, stat_type='Spending')
        self.current_frame.pack(fill='both', expand=True)
       
    def showSavings(self, event=None) -> None:
       """
        Displays the Savings dashboard.

        It loads data stored income and expenses data from the main dashboard.
        """
       self.clearWindow()
       self.current_frame = Statistics(self, stat_type='Savings')
       self.current_frame.pack(fill='both', expand=True)
       
    def showInvestments(self) -> None:
        """
         Displays the Savings dashboard.

         It loads data stored income and expenses data from the main dashboard.
         """
        self.clearWindow()
        self.current_frame = Investments(self)
        self.current_frame.pack(fill='both', expand=True)
        
        
if __name__ == "__main__":
    app = FinanceTracker()
    app.mainloop()
    
    
    
class Dashboard2(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        
        self.master = master  # Reference to the FinanceTracker (Main Window)
        self.last_saved_file = os.path.join(os.path.dirname(__file__), "lastSavedFile.txt")
        
        # Define preset column widths
        self.column_widths = {
                            "Index": 70,
                            "Date": 120,
                            "Description": 500,
                            "Amount": 110,
                            "Account": 150,
                            "Category": 150}
        
        # To hide or show the index column
        self.hide_index = True
        
        self.createWidgets()  # Initialize UI elements
        self.loadAndProcessData()  # Check, load, and display data
        
        self.populateTable(tree=self.expenses_tree, df=self.master.expenses_data, df_name='exp')
        
    def createWidgets(self) -> None:
        """Creates and places widgets in the dashboard."""
    
        # Set up the main frame for all widgets
        self.frame = tk.Frame(self)
        
        # Make sure the parent frame's column is expandable
        self.frame.grid_columnconfigure(0, weight=1)
        
        # Expenses Label
        self.expenses_label = ttk.Label(self.frame, text="EXPENSES", font=(StyleConfig.FONT_FAMILY, StyleConfig.HEADING_FONT_SIZE, "bold"))
        self.expenses_label.grid(row=0, column=0, sticky="n", pady=2)
        
        # Expenses Table
        self.expenses_tree, expenses_frame = self.setupTable(frame_row=1)
        expenses_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=10) 
    
        # Income Label
        self.income_label = ttk.Label(self.frame, text="INCOME", font=(StyleConfig.FONT_FAMILY, StyleConfig.HEADING_FONT_SIZE, "bold"))
        self.income_label.grid(row=2, column=0, sticky="n", pady=2)
        
        # Income Table
        self.income_tree, income_frame = self.setupTable(frame_row=3)
        income_frame.grid(row=3, column=0, sticky='nsew', padx=10, pady=10)
    
        # Make the main frame appear inside the main window
        self.frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        
        # Bind the function to window resizing
        self.bind("<Configure>", self.updateTableSizes)
    
    def loadAndProcessData(self) -> None:
        self

    def setupTable(self, frame_row: int) -> Tuple[ttk.Treeview, ttk.Frame]:
        """Sets up a ttk Treeview table with scrollbars and returns both the table and its frame."""
    
        # Create a frame for the table
        tree_frame = ttk.Frame(self.frame, padding=5)
        
        # Create the Treeview widget
        tree = ttk.Treeview(tree_frame, 
                            show='headings', 
                            selectmode='browse',
                            height=10)
        
        # Ensure frame expands properly
        self.frame.grid_rowconfigure(frame_row, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        
        # Create Scrollbars
        y_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=y_scrollbar.set)
        
        # Set configuration on screen with grid
        y_scrollbar.grid(row=0, column=1, sticky='ns')
        tree.grid(row=0, column=0, sticky='nsew')
        
        # Make sure frame columns and rows expand with the window
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)
        
        style = ttk.Style()
        Tables.tableStyle(style)
        
        return tree, tree_frame
        
    def populateTable(self, tree:ttk.Treeview, df:pd.DataFrame, df_name:'str') -> None:
        """ Populate the ttk.Treeview object"""
        
        if self.hide_index:
            self.column_widths['Index'] = 0
            
        columns = df.columns
        
        # Define column headings
        for col in columns:
            tree.heading(col, text=col, command=lambda c=col: Tables.sortTableByColumn(tree, c, False))
            width = self.column_widths.get(col, 120)
            tree.column(col, anchor=tk.W if col != "Amount" else tk.E, width=width, stretch=tk.NO)
            
        # Populate Treeview with data
        for i, row in df.iterrows():
            values = list(row)
            values[3] = f"${values[3]/100:.2f}"  # Format amount as currency
            tree.insert('', tk.END, values=values)
            
        # Get category list
        cat_list, cat_file = Utility.getCategoryTypes(df_name)
            
            
        
    def updateTableSizes(self, event):
        """Dynamically adjust the table sizes for both income and expense tables."""

        new_width = self.winfo_width()
        new_height = self.winfo_height()
        
        total_fixed_width = sum(column_widths.values())
        scale_factor = new_width / total_fixed_width * 0.98
        
        try:
        
            # Adjust column width dynamically based on window width
            if event is None or new_width != self.all_data_window_width:
                self.all_data_window_width = new_width            
                for tree in [self.expenses_data_tree, self.income_data_tree]:
                    if tree:
                        for col in tree["columns"]:
                            width = int(column_widths.get(col, 120) * scale_factor )
                            tree.column(col, width=width)
        
            # Adjust row count dynamically based on window height
            if event is None or new_height != self.all_data_window_height:
                self.all_data_window_height = new_height
                min_rows = 5
                max_rows = 25
                row_height = 35
                new_row_count = int(max(min_rows, min(max_rows, new_height // row_height)) // 2)
        
                for tree in [self.expenses_data_tree, self.income_data_tree]:
                    if tree:
                        tree.config(height=new_row_count)
        except:
            pass
        
        self.update_idletasks()
     
    def displayIncExpTables(self, inc, exp):
        """Display total expenses and income data.""" 
        
        def showTable(df, df_name):
            """Display a table for the given dataframe in the main window with an editable 'Category' column."""

                
            
            def on_cell_double_click(event):
                """Open a small pop-up window to select a category, positioned next to the clicked cell."""
                item_id = tree.identify_row(event.y)  # Get clicked row
                col_id = tree.identify_column(event.x)  # Get clicked column
            
                if not item_id or col_id != f"#{columns.index('Category')+1}":  # Ensure it's the 'Category' column
                    return
            
                # 
                row_index = tree.get_children().index(item_id)
                row_values = tree.item(item_id, "values") 
                df_index = int(row_values[0])
                
                current_value = df.at[df_index, "Category"] 
            
                # Get cell coordinates
                x, y, width, height = tree.bbox(item_id, columns.index("Category"))
            
                # Get root window coordinates
                root_x = tree.winfo_rootx()  # X position of Treeview relative to screen
                root_y = tree.winfo_rooty()  # Y position of Treeview relative to screen
                
                # Assign base values
                base_x = 210
                base_y = 80
            
                # Compute absolute position for the popup window (to the left of the clicked cell)
                popup_x = root_x + x - base_x  # Offset by 210px to position it to the left
                popup_y = root_y + y - 40   # Offset by 40px to position it up
            
                # Create popup window
                popup = tk.Toplevel()
                popup.title("Select Category")
                popup.geometry(f"{base_x}x{base_y}+{popup_x}+{popup_y}")  # Position popup at calculated location
            
                category_var = tk.StringVar()
                dropdown = ttk.Combobox(popup, textvariable=category_var, values=cat_list, state="readonly")
                dropdown.pack(pady=10)
                dropdown.current(cat_list.index(current_value)) if current_value in cat_list else dropdown.current(0)
            
                def saveSelection():
                    """Save selected category and close popup."""
                    new_category = category_var.get()
                    df.at[df_index, "Category"] = new_category
                    values = [df.at[df_index, col] for col in columns]
                    values[3] = f"${values[3]/100:.2f}"  # Format amount as currency
                    tree.item(tree.get_children()[row_index], values=values)
                    
                    if df_name == 'inc':
                        self.income_data.at[df_index, "Category"] = new_category
                    elif df_name == 'exp':
                        self.expenses_data.at[df_index, "Category"] = new_category

                    if self.current_sort == 'Category':
                        #TODO Figure out some way to change self.current_sort from Tables.sortTableByColumn()
                        Tables.sortTableByColumn(tree, 'Category', False)
                    
                    popup.destroy()
                    
                def exitWindow(event=None):
                    popup.destroy()
                
                # Bind Enter and Escape keys
                popup.bind("<Return>", saveSelection) 
                popup.bind("<Escape>", exitWindow)
            
                # Add Save Button
                save_button = tk.Button(popup, text="Save", command=saveSelection)
                save_button.pack(pady=5)
                
                dropdown.focus_set()
            
                popup.mainloop()
            
            # Bind the function to window resizing
            self.bind("<Configure>", updateTableSizes)
            
            # Bind double-click event
            tree.bind("<Double-Button-1>", on_cell_double_click)
            
            # Bind right-click event to show column menu
            tree.bind("<Button-3>", lambda event: self.showColumnMenu(event, tree, df, df_name))
            
            updateTableSizes(event=None)
            
            return
        
        if self.current_window == 'All Data':
            return
            
        self.clearMainFrame()
        
        self.all_data_window_height = 650
        
        if self.hide_index:
            self.all_data_window_width = 1073
        else:
            self.all_data_window_width = 1133
            
        self.geometry(f"{self.all_data_window_width}x{self.all_data_window_height}")
        
        # Make sure the parent frame's column is expandable
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Set up both trees for size updating
        self.expenses_data_tree = None
        self.income_data_tree = None

        # Populate the expenses tree/table
        expenses_label = ttk.Label(self.main_frame, text="EXPENSES", font=(self.font_type, self.font_size+2, "bold"))
        expenses_label.grid(row=0, column=0, sticky="n", pady=2)
        showTable(exp.copy(), 'exp')
        
        # Populate the income tree/table
        expenses_label = ttk.Label(self.main_frame, text="INCOME", font=(self.font_type, self.font_size+2, "bold"))
        expenses_label.grid(row=2, column=0, sticky="n", pady=2)
        showTable(inc.copy(), 'inc')
        
        self.current_window = 'All Data'
    
    def redisplayDataFrameTable(self) -> None:
        """
        Reevaluates and redisplays the DataFrames after changes to the viewing filters.
    
        This function:
            - Clears the main frame before updating the view.
            - Applies date range and amount range filters.
            - Filters data based on selected accounts and category values.
            - Resets index and redisplays the filtered tables.
    
        Parameters:
            None
    
        Returns:
            None
        """
        
        self.clearMainFrame()
        
        inc_data_copy = self.income_data.copy()
        exp_data_copy = self.expenses_data.copy()

        # Apply filtering based on defined ranges
        for r, ranges in enumerate([False, self.new_date_range, False, self.new_amount_range]):
            if ranges:
                col = inc_data_copy.columns[r] 
            
                if r != 3:
                    inc_data_copy = inc_data_copy[inc_data_copy[col].between(ranges[0], ranges[1])]
                    exp_data_copy = exp_data_copy[exp_data_copy[col].between(ranges[0], ranges[1])]
                else:
                    # Amount is stored in cents, so adjust the range
                    inc_data_copy = inc_data_copy[inc_data_copy[col].between(ranges[0][0]*100, ranges[0][1]*100)]
                    exp_data_copy = exp_data_copy[exp_data_copy[col].between(ranges[1][0]*100, ranges[1][1]*100)]
                
        # Apply filtering for selected accounts and categories
        for v, values in enumerate([self.new_accounts, [self.new_inc_categories, self.new_exp_categories]]):
            if values:
                col = inc_data_copy.columns[r+v+1]
                if v == 0:
                    # Filter by accounts
                    inc_data_copy = inc_data_copy[inc_data_copy[col].isin(values)]
                    exp_data_copy = exp_data_copy[exp_data_copy[col].isin(values)]
                else:
                    # Filter by categories (income and expense separately)
                   inc_data_copy = inc_data_copy[inc_data_copy[col].isin(values[0])]
                   exp_data_copy = exp_data_copy[exp_data_copy[col].isin(values[1])]
                   
        # Reset index after filtering
        inc_data_copy = inc_data_copy.reset_index(drop=True) 
        exp_data_copy = exp_data_copy.reset_index(drop=True) 
        
        # Display the filtered data
        self.displayIncExpTables(inc_data_copy, exp_data_copy)     
    
    def showColumnMenu(self, event, table, df, df_name):
        """Show a menu when right-clicking a table heading."""
        
        #TODO DocStrings
        
        def showLastMonth(delta=0):
            """Only show data for the last 30/60/90/180/365 days"""
                
            if delta > 0:
                self.new_date_range[0] = self.date_range[1] - timedelta(delta)
                self.new_date_range[1] = self.date_range[1]

                self.current_window = ''
                self.redisplayDataFrameTable()  # Refresh display
            
            return
        
        def showCalendar(df):
            """Open a calendar window to select a date range."""      
            
            def convertStrToDate(x):
                """Convert a date in str format to a date format"""
                x = x.split("-")
                return date(int(x[0]), int(x[1]), int(x[2]))
            
            top = tk.Toplevel(self)
            top.title("Select Date Range")
            
            start_label = ttk.Label(top, text="Select Start Date:", font=self.my_font)
            start_label.pack(pady=5)
            
            Windows.openRelativeWindow(top, main_width=self.winfo_x(), main_height=self.winfo_y(), width=235, height=500)
            
            start_cal = Calendar(top, 
                                 selectmode="day", 
                                 year=self.date_range[1].year, 
                                 month=self.date_range[1].month-1 if self.date_range[1].month-1 < 12 else 12, 
                                 day=self.date_range[1].day,
                                 date_pattern = 'Y-mm-dd',
                                 )
            
            start_cal.pack(pady=5)
            
            end_label = ttk.Label(top, text="Select End Date:", font=self.my_font)
            end_label.pack(pady=5)
            
            end_cal = Calendar(top, 
                               selectmode="day", 
                               year=self.date_range[1].year, 
                               month=self.date_range[1].month, 
                               day=self.date_range[1].day, 
                               date_pattern = 'Y-mm-dd',
                               )
            
            end_cal.pack(pady=5)
            
            def confirmSelection(event=None):
                """Filter data based on selected dates and refresh the table display."""
                start_date  = convertStrToDate(start_cal.get_date())
                end_date    = convertStrToDate(end_cal.get_date())
                
                evaluate = False
                
                if start_date != self.new_date_range[0]:
                    self.new_date_range[0] = start_date
                    evaluate = True
                if end_date != self.new_date_range[1]:
                    self.new_date_range[1] = end_date
                    evaluate = True
                
                if evaluate:
                    self.current_window = ''
                    self.redisplayDataFrameTable()  # Refresh display
                
                top.destroy()
                
            def exitWindow(event=None):
                top.destroy()
                        
            confirm_button = ttk.Button(top, text="Confirm", command=confirmSelection)
            confirm_button.pack(pady=10)
            
            # Bind Enter and Escape keys
            top.bind("<Return>", confirmSelection) 
            top.bind("<Escape>", exitWindow)
            
            start_cal.focus_set()
            
            return
        
        def showAmountFilter(df, df_name=None):
            """Open a modern window to filter data based on the 'Amount' column."""
            
            if df_name == 'inc':
                min_amount, max_amount = self.amount_range[0]
            else:
                min_amount, max_amount = self.amount_range[1]
        
            # Create the modern-styled Toplevel window
            top = tk.Toplevel(self)
            top.title("Select Amount Range")
            Windows.openRelativeWindow(top, main_width=self.winfo_x(), main_height=self.winfo_y(), width=290, height=200)
            top.resizable(False, False)
            top.configure(bg="#f8f9fa")  # Light modern background
        
            # Frame to hold the content
            container = ttk.Frame(top, padding=15)
            container.pack(expand=True, fill=tk.BOTH)
        
            # Title Label
            title_label = ttk.Label(container, text="Enter Amount Range", font=(self.my_font.cget('family'), self.my_font.cget('size') + 1, "bold"))
            title_label.pack(pady=(5, 10))
        
            # Create a sub-frame for label/entry alignment
            input_frame = ttk.Frame(container)
            input_frame.pack(pady=5, fill="x")
        
            # Min Value Entry
            min_label = ttk.Label(input_frame, text="Minimum Amount:", font=(self.font_type, self.font_size))
            min_label.grid(row=0, column=0, padx=(0, 10), sticky="e")
            min_entry = ttk.Entry(input_frame, width=14, font=(self.font_type, self.font_size))
            min_entry.insert(0, f"${min_amount:.2f}")  # Pre-fill with min amount
            min_entry.grid(row=0, column=1, padx=(0, 10), sticky="w")
        
            # Max Value Entry
            max_label = ttk.Label(input_frame, text="Maximum Amount:", font=(self.font_type, self.font_size))
            max_label.grid(row=1, column=0, padx=(0, 10), sticky="e")
            max_entry = ttk.Entry(input_frame, width=14, font=(self.font_type, self.font_size))
            max_entry.insert(0, f"${max_amount:.2f}")  # Pre-fill with max amount
            max_entry.grid(row=1, column=1, padx=(0, 10), sticky="w")
        
            # Function to confirm and save values
            def confirmSelection(event=None):
                """Filter data based on manually entered amount range and refresh the table display."""
                try:
                    
                    min_val = float(min_entry.get().split("$")[-1])
                    max_val = float(max_entry.get().split("$")[-1])
        
                    if df_name == 'inc':
                        self.new_amount_range[0][0] = min_val
                        self.new_amount_range[0][1] = max_val
                    else:
                        self.new_amount_range[1][0] = min_val
                        self.new_amount_range[1][1] = max_val
        
                    self.current_window = ''
                    self.redisplayDataFrameTable()  # Refresh display
                    top.destroy()
        
                except ValueError:
                    messagebox.showwarning("Invalid Input", "Please enter valid numeric values.")
        
            def exitWindow(event=None):
                top.destroy()
        
            # Button Frame
            button_frame = ttk.Frame(container)
            button_frame.pack(fill="x", pady=(10, 5))
        
            # Confirm Button
            confirm_button = ttk.Button(button_frame, text="Confirm", command=confirmSelection, style="Accent.TButton")
            confirm_button.pack(pady=5, ipadx=10)  # Centered button
        
            # Bind Enter and Escape keys
            top.bind("<Return>", confirmSelection) 
            top.bind("<Escape>", exitWindow)
        
            # Apply modern styling to button
            style = ttk.Style()
            style.configure("Accent.TButton", font=(self.font_type, self.font_size, "bold"), padding=6)
        
            top.focus_set()
            
            return
        
        def showTextFilter(df, type_of_filter=None, df_name=None):
            """Open a modern, scrollable checkbox menu to filter a column."""
            
            if type_of_filter == 'acc':
                selection = "Account"
                unique_vals = sorted(set(self.income_data[selection].unique()) | set(self.expenses_data[selection].unique()))
            elif type_of_filter == 'cat':
                selection = "Category"
                unique_vals, cat_file = self.getCategoryTypes(df_name)
        
            # Create modern-styled Toplevel window
            top = tk.Toplevel(self)
            top.title(f"Filter by {selection}")
        
            # **Determine proper window height dynamically**
            num_items = len(unique_vals)
            min_height = 200  # Minimum height
            item_height = 28   # Estimated height per checkbox
            dynamic_height = num_items * item_height + 80  # Account for title & buttons
            max_height = 420  # Maximum height before scrolling is needed
        
            window_height = min(max_height, max(min_height, dynamic_height))  # Auto-adjust height
            window_width = 300
            Windows.openRelativeWindow(top, main_width=self.winfo_x(), main_height=self.winfo_y(), width=window_width, height=window_height)
            top.resizable(False, False)
            top.configure(bg="#f8f9fa")  # Light modern background
            top.attributes('-topmost', True)  # Keep on top while main window is active
        
            # Function to release 'topmost' when main window loses focus
            def on_focus_out(event=None):
                """Remove 'always on top' if the main app loses focus."""
                top.attributes('-topmost', True)
        
            top.bind("<FocusOut>", on_focus_out)  # Remove always-on-top when clicked away
        
            # **Main Container (Expands to Avoid Button Overlap)**
            container = ttk.Frame(top, padding=12)
            container.pack(expand=True, fill=tk.BOTH)
        
            # Title Label
            title_label = ttk.Label(container, text=f"Select {selection} to Display", font=(self.font_type, self.font_size + 1, "bold"))
            title_label.pack(pady=(5, 10))
        
            # **Scrollable frame for checkboxes (Fills Available Space)**
            list_frame = ttk.Frame(container)
            list_frame.pack(expand=True, fill="both", padx=5, pady=(0, 5))
        
            canvas = tk.Canvas(list_frame, bg="#f8f9fa", highlightthickness=0)  # Remove extra border
            scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        
            # Frame inside canvas for checkboxes
            checkbox_frame = ttk.Frame(canvas)
        
            # Ensure the checkbox frame resizes dynamically
            checkbox_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
            canvas.create_window((0, 0), window=checkbox_frame, anchor="nw", width=270)  # Ensure full width
        
            canvas.configure(yscrollcommand=scrollbar.set)
        
            # **Conditionally Show Scrollbar Only When Needed**
            if num_items > 9:  # Show scrollbar if there are more than 8 items
                canvas.pack(side="left", fill="both", expand=True, padx=(5, 0))
                scrollbar.pack(side="right", fill="y")
            else:  # No scrollbar needed, ensure frame expands
                canvas.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=(0, 5))
                list_frame.pack_propagate(False)  # Prevent shrinking
        
            # Enable mouse scrolling
            def on_mouse_wheel(event):
                """Enable mouse scrolling inside the frame."""
                canvas.yview_scroll(-1 * (event.delta // 60), "units")  # Windows scroll
        
            def on_scroll(event):
                """Enable scrolling for Linux/Mac."""
                if event.num == 4:
                    canvas.yview_scroll(-1, "units")  # Scroll up
                elif event.num == 5:
                    canvas.yview_scroll(1, "units")  # Scroll down
        
            # Bind scrolling
            canvas.bind("<Enter>", lambda _: canvas.bind_all("<MouseWheel>", on_mouse_wheel))
            canvas.bind("<Leave>", lambda _: canvas.unbind_all("<MouseWheel>"))
            canvas.bind("<Button-4>", on_scroll)  # Mac/Linux
            canvas.bind("<Button-5>", on_scroll)
        
            # Display checkboxes for each account/category
            checkbox_widgets = {}
            for acc in unique_vals:
                var = tk.BooleanVar(value=True)
                checkbox_widgets[acc] = var
                cb = ttk.Checkbutton(checkbox_frame, text=acc, variable=var, style="TCheckbutton")
                cb.pack(anchor="w", padx=5, pady=2, fill="x")  # Ensures proper alignment
        
            # Adjust canvas height dynamically
            checkbox_frame.update_idletasks()  # Update to get correct dimensions
            frame_height = checkbox_frame.winfo_reqheight()  # Get actual height
            canvas.configure(scrollregion=(0, 0, window_width, frame_height))  # Adjust scroll area
        
            # Ensure Confirm Button Always Appears
            button_frame = ttk.Frame(container)
            button_frame.pack(fill="x", padx=5, pady=(5, 10))  # Keep at the bottom
        
            # Function to confirm selection
            def confirmSelection(event=None):
                """Update dataframe display based on selected items."""
                selected = [acc for acc, var in checkbox_widgets.items() if var.get()]
        
                if selected:
                    if type_of_filter == 'acc':
                        self.new_accounts = selected
                    elif type_of_filter == 'cat':
                        if df_name == 'inc':
                            self.new_inc_categories = selected
                        else:
                            self.new_exp_categories = selected
                    self.current_window = ''
                    self.redisplayDataFrameTable()  # Refresh display
                else:
                    messagebox.showwarning("Invalid Selection", "At least one option must be selected.")
        
                top.destroy()
        
            def exitWindow(event=None):
                top.destroy()
        
            # Confirm Button (Now properly aligned & styled)
            confirm_button = ttk.Button(button_frame, text="Confirm", command=confirmSelection, style="Accent.TButton")
            confirm_button.pack(ipadx=10, fill="x")  # Properly aligned & spaced
        
            # Bind Enter & Escape keys
            top.bind("<Return>", confirmSelection)
            top.bind("<Escape>", exitWindow)
        
            # Apply modern button styling
            style = ttk.Style()
            style.configure("Accent.TButton", font=(self.font_type, self.font_size, "bold"), padding=6)
            style.configure("TCheckbutton", font=(self.font_type, self.font_size))
        
            top.focus_set()
        
        def addCategoryToFile(df_name):
            """Open a window to fully edit the category list (add, remove, or update categories)."""
            
            # Retrieve category list and category file path
            cat_list, cat_file = Utility.getCategoryTypes(df_name)
        
            # Create a popup window
            top = tk.Toplevel(self)
            top.title("Edit Categories")
            Windows.openRelativeWindow(top, main_width=self.winfo_x(), main_height=self.winfo_y(), width=400, height=400)
            top.resizable(False, False)
            top.configure(bg="#f8f9fa")  # Light background
            top.attributes('-topmost', True)  # Keep window on top
        
            # Title Label
            title_label = ttk.Label(
                top, text="Manage Categories", font=(self.font_type, self.font_size + 1, "bold")
            )
            title_label.pack(pady=(10, 5))
        
            # **Scrollable Listbox Frame**
            listbox_frame = ttk.Frame(top)
            listbox_frame.pack(pady=(5, 10), padx=10, fill="both", expand=True)
        
            listbox_scroll = ttk.Scrollbar(listbox_frame, orient="vertical")
            category_listbox = tk.Listbox(
                listbox_frame, selectmode=tk.SINGLE, width=40, height=10, yscrollcommand=listbox_scroll.set, font=(self.font_type, self.font_size)
            )
            listbox_scroll.config(command=category_listbox.yview)
        
            category_listbox.pack(side="left", fill="both", expand=True)
            listbox_scroll.pack(side="right", fill="y")
        
            # Populate listbox with categories
            for category in cat_list:
                category_listbox.insert(tk.END, category)
        
            # **Category Input Section**
            entry_frame = ttk.Frame(top)
            entry_frame.pack(pady=5, padx=10, fill="x")
        
            category_entry = ttk.Entry(entry_frame, font=(self.font_type, self.font_size))
            category_entry.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
            def addCategory():
                """Add a new category to the listbox and update the file."""
                new_category = category_entry.get().strip()
        
                if not new_category:
                    messagebox.showwarning("Invalid Input", "Category cannot be empty.", parent=top)
                    return
        
                if new_category in cat_list:
                    messagebox.showinfo("Duplicate Category", "This category already exists.", parent=top)
                    return
        
                # Add to listbox and update internal list
                category_listbox.insert(tk.END, new_category)
                cat_list.append(new_category)
                category_entry.delete(0, tk.END)
        
            def removeCategory():
                """Remove the selected category from the listbox and update the file."""
                selected_index = category_listbox.curselection()
                if not selected_index:
                    messagebox.showwarning("No Selection", "Please select a category to remove.", parent=top)
                    return
        
                selected_category = category_listbox.get(selected_index)
        
                # Confirm before removing
                if messagebox.askyesno("Confirm Delete", f"Remove category '{selected_category}'?", parent=top):
                    category_listbox.delete(selected_index)
                    cat_list.remove(selected_category)
        
            def saveCategories(event=None):
                """Save the modified category list back to the file."""
                try:
                    with open(cat_file, "w") as f:
                        for category in cat_list:
                            f.write(category + "\n")
        
                    self.current_window = ''
                    self.displayIncExpTables(self.income_data.copy(), self.expenses_data.copy())
                    messagebox.showinfo("Success", "Category list updated successfully!", parent=top)
                    top.destroy()
        
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to update file.\n{e}", parent=top)
                    
            def exitWindow(event=None):
                top.destroy()
        
            # **Buttons for Managing Categories**
            button_frame = ttk.Frame(top)
            button_frame.pack(pady=10, padx=10, fill="x")
        
            add_button = ttk.Button(button_frame, text="Add", command=addCategory, style="Accent.TButton")
            add_button.pack(side="left", expand=True, fill="x", padx=5)
        
            remove_button = ttk.Button(button_frame, text="Remove", command=removeCategory, style="Accent.TButton")
            remove_button.pack(side="left", expand=True, fill="x", padx=5)
        
            save_button = ttk.Button(button_frame, text="Save & Close", command=saveCategories, style="Accent.TButton")
            save_button.pack(side="left", expand=True, fill="x", padx=5)
        
            # Bind Enter key to add category
            category_entry.bind("<Return>", addCategory)
            top.bind("<Escape>", exitWindow)
        
            # Apply modern button styling
            style = ttk.Style()
            style.configure("Accent.TButton", font=(self.font_type, self.font_size, "bold"), padding=6)
        
            # Focus on the entry field
            category_entry.focus_set()
            
            return
        
        def hideIndexColumn():
            """ Hide the index column """
            if not self.hide_index:
                self.hide_index = True
            else:
                self.hide_index = False
            self.current_window = ''
            self.redisplayDataFrameTable()  # Refresh display
        
        def deleteDFItem(index, df_name, parent):
            """
            The function:
                -Deletes a row from a DataFrame based on index
                -Reindexes the DataFrame
                -Ensures the 'index' column is the first column
                -Re-displays dataframe
         
            Parameters:.
            df_index (int): The index of the row to delete.
            df_name (str): The name of the dataframe to modify
         
            Returns:
            None
            """
            
            if df_name == 'inc':
                df = parent.income_data
            else:
                df = parent.expenses_data
                
            df = df.drop(index=index, errors="ignore")  # Avoids errors if index is not found

            # Reset index and create a new 'index' column
            df = df.drop(columns=["Index"])
            df = df.reset_index(drop=True)
            df.insert(0, "Index", df.index)  # Ensure 'index' is the first column
            
            if df_name == 'inc':
                parent.income_data = df
            else:
                parent.expenses_data = df

            parent.current_window = ''
            parent.redisplayDataFrameTable()  # Refresh display
                
        def modifyDFItem(index, df_name, parent):
            """
            Opens a new Tkinter window allowing modification of a row in a DataFrame.
        
            Parameters:
            - index (int): The index of the row to modify.
            - df_name (str): The name of the dataframe ('inc' for income, 'exp' for expenses).
            - parent (tk.Tk): Reference to the main application window.
        
            Returns:
            None
            """
            
            if df_name == 'inc':
                df = parent.income_data
            else:
                df = parent.expenses_data
                
            # Ensure index exists
            if index not in df.index:
                messagebox.showwarning("Warning", f"Index {index} not found.")
                return  
            
            # Create a new window
            edit_window = tk.Toplevel(parent)
            edit_window.title("Modify DataFrame Item")
            edit_window.geometry("300x300")
        
            # Retrieve row values
            row_data = df.loc[index]
        
            # Dictionary to store entry widgets
            entry_widgets = {}
        
            # Create labels and entry fields
            for i, (col_name, value) in enumerate(row_data.items()):
                tk.Label(edit_window, text=col_name, font=(parent.font_type, parent.font_size, "bold"), anchor="w").grid(row=i, column=0, padx=10, pady=5, sticky="w")
                
                # Create entry fields for editing
                entry = tk.Entry(edit_window)
                entry.insert(0, str(value))
                entry.grid(row=i, column=1, padx=10, pady=5)
                
                # Store reference to entry widget
                entry_widgets[col_name] = entry
        
            # Save Button Function
            def saveChanges():
                """Saves modifications to the DataFrame with proper type casting and refreshes the table."""
                
                for col_name, entry in entry_widgets.items():
                    value = entry.get()  # Get user input as a string
                    
                    # Ensure the correct type before updating
                    if col_name == "Index":  # First column: Integer
                        value = int(value) if value.isdigit() else df[col_name].dtype.type(df[col_name].iloc[0])
                    elif col_name == "Date":  # Second column: DateTime
                        try:
                            value = pd.to_datetime(value).date()
                        except ValueError:
                            value = df[col_name].dtype.type(df[col_name].iloc[0])  # Default to existing dtype if invalid
                    elif col_name in ["Amount"]:  # Fourth column: Integer
                        value = int(value) if value.isdigit() else df[col_name].dtype.type(df[col_name].iloc[0])
                    elif col_name in ["Category", "Description", "Account"]:  # String Columns
                        value = str(value)
            
                    df.at[index, col_name] = value  # Update DataFrame with correctly cast value
                    
                parent.convertToDatetime(df)
            
                # Refresh DataFrame in the main app
                if df_name == 'inc':
                    parent.income_data = df
                else:
                    parent.expenses_data = df
            
                self.current_window  = ''
                parent.redisplayDataFrameTable()  # Refresh displayed table
                edit_window.destroy()  # Close the edit window
        
            # Save Button
            save_button = tk.Button(edit_window, text="Save", command=saveChanges)
            save_button.grid(row=len(row_data), column=0, columnspan=2, pady=10)
        
            edit_window.mainloop()
            
            return
                
        col_id = table.identify_column(event.x)
        col_name = table.heading(col_id, "text")
        
        menu = tk.Menu(self, tearoff=0)
        
        # Get the clicked column
        region = table.identify("region", event.x, event.y)

        # Activate only if the click is on the column header
        if region == "cell":
            item_id = table.identify_row(event.y)
            row_values = table.item(item_id, "values")
            df_index = int(row_values[0])
            menu.add_command(label="Delete Transaction", command=lambda: deleteDFItem(df_index, df_name, self))
            menu.add_command(label="Modify Transaction", command=lambda: modifyDFItem(df_index, df_name, self))
            
        else:
            if col_name != 'Index':
                menu.add_command(label=f"Sort {col_name} Ascending", command=lambda: Tables.sortTableByColumn(table, col_name, True))
                menu.add_command(label=f"Sort {col_name} Descending", command=lambda: Tables.sortTableByColumn(table, col_name, False))
            
            if col_name == 'Index':
                """Sort and high index column"""
                if not self.hide_index:
                    menu.add_command(label="Hide Index Column", command=lambda: hideIndexColumn()) 
            
            if col_name == 'Date':
                """Calendar of date window initially starting and ending where the date is"""
                menu.add_separator()
                menu.add_command(label="Choose date window", command=lambda: showCalendar(df.copy))
                menu.add_separator()
                menu.add_command(label="Show last 30 days", command=lambda: showLastMonth(delta=30))
                menu.add_command(label="Show last 60 days", command=lambda: showLastMonth(delta=60))
                menu.add_command(label="Show last 90 days", command=lambda: showLastMonth(delta=90))
                menu.add_command(label="Show last 180 days", command=lambda: showLastMonth(delta=180))
                menu.add_command(label="Show last 365 days", command=lambda: showLastMonth(delta=365))
                menu.add_separator()
                if self.hide_index:
                    menu.add_command(label="Show Index Column", command=lambda: hideIndexColumn()) 
                
            elif col_name == 'Description':
                self
            elif col_name == 'Amount':
                """Cutoff window slider"""
                menu.add_separator()
                menu.add_command(label="Choose Amount window", command=lambda: showAmountFilter(df.copy, df_name))
            elif col_name == 'Account':
                """Dropdown menu to only show certain values"""
                menu.add_separator()
                menu.add_command(label="Choose Accounts", command=lambda: showTextFilter(df.copy, type_of_filter='acc', df_name=df_name))
                self
            elif col_name == 'Category':
                menu.add_separator()
                menu.add_command(label="Choose Categories", command=lambda: showTextFilter(df.copy, type_of_filter='cat', df_name=df_name))
                menu.add_command(label="Add New Categories", command=lambda: addCategoryToFile(df_name=df_name))
                """Dropdown menu to only show certain values"""
                self
            
        menu.post(event.x_root, event.y_root)    
    
    def editInitialValues(self) -> None:
        """
        Opens a secondary window to edit initial account balances.
    
        This function:
        - Loads initial account balances into an editable table.
        - Allows users to modify values and save changes.
        - Updates `self.starting_data` upon saving.
        - Handles incorrect user inputs gracefully.
        - Closes the window upon pressing 'Escape' or clicking 'Save'.
        """
    
        # Ensure data is loaded before opening the editor
        if self.starting_data is None or self.starting_data.empty:
            messagebox.showwarning("Warning", "No data loaded! Load files first.")
            return
    
        # Create the edit window
        top = tk.Toplevel(self)
        top.title("Edit Initial Account Balances")
        top.resizable(False, False)
        top.configure(bg="#f4f4f4")  # Light background
    
        # Title Label
        title_label = ttk.Label(top, text="Edit Initial Account Balances", font=(self.font_type, self.font_size+2, "bold"))
        title_label.pack(pady=10)
    
        # Create a frame to hold the table
        frame = ttk.Frame(top)
        frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
    
        # Create a canvas for scrolling
        canvas = tk.Canvas(frame, bg="#f4f4f4")
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    
        # Scrollable frame inside the canvas
        scroll_frame = ttk.Frame(canvas)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    
        # Embed scrollable frame inside canvas
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
    
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
        # Dictionary to store entry widgets for later retrieval
        entry_widgets = {}
        
        # Insert data from dataframe
        for i, account in enumerate(self.accounts):
            initial_balance = self.starting_data[account].values[0] / 100  # Convert cents to dollars
            
            # Account Name Label
            ttk.Label(scroll_frame, text=account, font=(self.font_type, self.font_size)).grid(
                row=i + 1, column=0, padx=10, pady=5, sticky="w"
            )
    
            # Entry Field for Balance
            entry = ttk.Entry(scroll_frame, width=15, font=(self.font_type, self.font_size - 2))
            entry.insert(0, f"{initial_balance:.2f}")
            entry.grid(row=i + 1, column=1, padx=10, pady=5, sticky="w")
    
            entry_widgets[account] = entry
    
        # Function to save changes
        def saveChanges(event=None):
            """
            Saves updated initial values to `self.starting_data` and closes the window.
    
            - Converts entered values from dollars to cents (integer storage).
            - Ensures all values are valid numbers.
            - Displays an error message if invalid input is found.
            - Refreshes the Monthly Breakdown if currently displayed.
            """
            for account, entry in entry_widgets.items():
                new_value = entry.get().strip()
    
                try:
                    # Convert dollars to cents (ensuring integer storage)
                    new_value = int(round(float(new_value), 2) * 100)
                    self.starting_data[account] = new_value
                except ValueError:
                    messagebox.showerror("Error", f"Invalid value for {account}. Please enter a valid number.")
                    return  # Prevents saving if there's an invalid entry
    
            messagebox.showinfo("Success", "Initial balances updated successfully.")
            top.destroy()
    
            # Refresh Monthly Breakdown if currently displayed
            if self.current_window == 'Monthly Breakdown':
                self.showMonthlyBreakdown()
    
        # Function to close the window
        def exitWindow(event=None):
            """Closes the edit window without saving changes."""
            top.destroy()

        # Set window size dynamically based on number of accounts
        window_width = 320
        window_height = (len(self.accounts) + 1) * 45  # Dynamic height
        top.geometry(f"{window_width}x{window_height}")
        
        # Bind hotkeys
        top.bind("<Escape>", exitWindow)
        top.bind("<Return>", saveChanges)
        
        # Bottom Frame for Buttons
        button_frame = ttk.Frame(top)
        button_frame.pack(side="bottom", pady=10)
    
        # Save Button
        save_button = ttk.Button(button_frame, text="Save Changes", command=saveChanges, style="Accent.TButton")
        save_button.pack()
    
        # Apply modern styling
        style = ttk.Style()
        style.configure(
            "Accent.TButton",
            font=(self.font_type, self.font_size - 1, "bold"),
            padding=5,)
        
        return
    
     
    
    
    
    
    
    