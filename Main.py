import os
import pandas as pd
import numpy as np
import pickle
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import Calendar
from datetime import date
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import calendar
from datetime import datetime, timedelta

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.float_format','{:.2f}'.format)

class FinanceTracker(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Personal Finance Tracker")
        self.geometry("1200x900")
        self.resizable(True, True)
        
        self.protocol("WM_DELETE_WINDOW", self.onClose)
        
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
        file_menu.add_command(label="Reload", command=lambda event: self.selectFilesAndFolders(reload=True), accelerator="Ctrl+R")
        file_menu.add_command(label="New", command=lambda event: self.startFresh(), accelerator="Ctrl+N")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.onClose, accelerator="Esc")
        menubar.add_cascade(label="File", menu=file_menu)
        
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Edit Initial Values", command=self.editInitialValues, accelerator="Ctrl+E")
        edit_menu.add_command(label="Redo", accelerator="Ctrl+Y")
        menubar.add_cascade(label="Edit", menu=edit_menu)
        
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="All Data", command=self.showMainFrame, accelerator="Ctrl+D")
        view_menu.add_command(label="Monthly Breakdown", command=self.showMonthlyBreakdown, accelerator="Ctrl+A")
        view_menu.add_command(label="Savings Breakdown", command=self.showSavings, accelerator="Ctrl+B")
        view_menu.add_command(label="Spending Breakdown", command=self.showSpending, accelerator="Ctrl+L")
        view_menu.add_command(label="Investments", command=self.showInvestments, accelerator="Ctrl+I")
        menubar.add_cascade(label="View", menu=view_menu)
        
        self.config(menu=menubar)
    
    def bindShortcuts(self):
        """Bind keyboard shortcuts to functions."""
        self.bind("<Control-a>", lambda event: self.showMonthlyBreakdown())
        self.bind("<Control-b>", lambda event: self.showSavings())
        #self.bind("<Control-c>",)
        self.bind("<Control-d>", lambda event: self.showMainFrame())
        self.bind("<Control-e>", lambda event: self.editInitialValues())
        #self.bind("<Control-f>",)
        #self.bind("<Control-g>",)
        #self.bind("<Control-h>",)
        self.bind("<Control-i>", lambda event: self.showInvestments())
        #self.bind("<Control-j>",)
        #self.bind("<Control-k>",)
        self.bind("<Control-l>", lambda event: self.showSpending())
        #self.bind("<Control-m>",)
        self.bind("<Control-n>", lambda event: self.startFresh())
        self.bind("<Control-o>", lambda event: self.selectFilesAndFolders())
        #self.bind("<Control-p>",)
        #self.bind("<Control-q>",)
        self.bind("<Control-r>", lambda event: self.selectFilesAndFolders(reload=True))
        self.bind("<Control-s>", lambda event: self.saveState())
        self.bind("<Control-S>", lambda event: self.saveStateAs())
        #self.bind("<Control-t>",)
        #self.bind("<Control-u>",)
        #self.bind("<Control-v>",)
        #self.bind("<Control-w>",)
        #self.bind("<Control-x>",)
        #self.bind("<Control-y>",)
        #self.bind("<Control-z>",)
        
        self.bind("<Escape>",    lambda event: self.onClose())
        
        return        

    def initUI(self):
        """Initialize the main interface without tabs."""
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(expand=True, fill="both")
        
        self.main_frame.focus_set()
        
        self.showMainFrame(start_fresh=False)
        self.selectFilesAndFolders(reload=True)
        
        self.showMonthlyBreakdown()
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
        self.categories = []
        self.new_categories = self.categories.copy()
        
        self.last_saved_file = os.path.join(os.path.dirname(__file__), "lastSavedFile.txt")
           
        self.switch_monthly_order = True
        
        self.drop_index = True
        
        # For formatting consistency
        
        self.my_font = tk.font.Font(size=12, font='calibri')
        self.font_type = 'calibri'
        self.font_size = 12
        
        self.banded_row = ["#f5f5f5", "#ffffff"]
        
        if on_start == False:
            self.clearMainFrame()
            self.selectFilesAndFolders(reload=False)
             
        return
      
    def onClose(self):
        """Prompt user to save before exiting."""
        #TODO UNDO
        #if not self.income_data.empty or not self.expenses_data.empty:
        #    if messagebox.askyesno("Save State", "Would you like to save the financial data before exiting?"):
        #        self.saveState()
        self.destroy()
        
    def goodLookingTables(self, table_tree):
        """Make any table look good from treeview"""
        table_tree.configure("Treeview", rowheight=25, font=(self.font_type, self.font_size))  # Set row height and font
        table_tree.configure("Treeview.Heading", font=(self.font_type, self.font_size+1, "bold"))  # Bold headers
        table_tree.map("Treeview", background=[("selected", "#cce5ff"), ("active", "#3A70C2")])  # Highlight selected row
        
        return
    
    def clearTreeview(self, tree):
        """Removes all items from a Treeview."""
        tree.delete(*tree.get_children())
        
    def showMonthlyBreakdown(self, event=None):
        """Show Accounts section."""
        
        def generateMonthYearList(start_date: datetime, end_date: datetime):
            """
            Generate a list of (month, year) tuples between two datetime objects.
            
            :param start_date: The starting datetime object
            :param end_date: The ending datetime object
            :return: List of tuples in the format (month, year)
            """
            current_date = datetime(start_date.year, start_date.month, 1)
            end_date = datetime(end_date.year, end_date.month, 1)
            
            month_year_list = []
        
            while current_date <= end_date:
                month_year_list.append((current_date.month, current_date.year))
                # Move to the next month
                if current_date.month == 12:
                    current_date = datetime(current_date.year + 1, 1, 1)
                else:
                    current_date = datetime(current_date.year, current_date.month + 1, 1)
        
            return month_year_list
        
        def formatMonthYear(month, year):
            """
            Convert a month and year into the format 'Mon 'YY'.
            
            :param month: The month as an integer (1-12)
            :param year: The year as an integer
            :return: A string in the format 'Mon 'YY'
            """
            return datetime(year, month, 1).strftime("%b '%y")
            
        def monthlyBalances():
            
            def computeMonthlyTotals(df):
                """Compute total amounts per account per month using groupby & Grouper."""
                df = df.copy()  # Avoid modifying the original DataFrame
                df["Date"] = pd.to_datetime(df["Date"])  # Ensure Date column is in datetime format
                df.set_index("Date", inplace=True)  # Set Date as the index
                val = (df.groupby([pd.Grouper(freq="ME"), "Account"])["Amount"].sum().unstack(fill_value=0))
                return val

            inc, exp = self.income_data.copy(), self.expenses_data.copy()
        
            # Get unique account names and group them by type
            all_accounts = sorted(set(inc["Account"].unique()) | set(exp["Account"].unique()))
        
            account_types = {
                "CHECKING": [],
                "SAVINGS": [],
                "CREDIT": [],
                "LOAN": [], 
                "RETIREMENT": [],
            }
        
            for account in all_accounts:
                for acc, key in account_types.items():
                    if acc in account.upper():
                        account_types[acc].append(account)
                        break
        
            income_monthly_totals = computeMonthlyTotals(inc)
            expenses_monthly_totals = computeMonthlyTotals(exp)

            # Prepare Account Summary Table
            account_summary = pd.DataFrame(columns=["Account"] + self.all_months)
            
            # Networth list by month
            networth = np.zeros((len(self.all_months)))

            for acc_type, accounts in account_types.items():
                for account in accounts:
                    
                    initial_value = initial_balances[account].tolist()[0]
                                              
                    # Compute cumulative end-of-month balance
                    balance_series = initial_value + (
                        income_monthly_totals.get(account, 0) - expenses_monthly_totals.get(account, 0)
                    ).cumsum()
            
                    # Fill missing months with initial balance
                    monthly_balances = balance_series.tolist()
                    row = [account] + monthly_balances
                    account_summary.loc[len(account_summary)] = row
                    
                    networth += np.asarray(monthly_balances)
                    
                # Add a totals row for each account type
                if len(accounts) > 0:
                    totals_row = ["TOTAL " + acc_type] + list(account_summary.iloc[-len(accounts):].drop(columns=["Account"]).sum(axis=0))
                    account_summary.loc[len(account_summary)] = totals_row
                else:
                    totals_row = ["TOTAL " + acc_type] + [0 for _ in range(len(self.all_months))]
                    account_summary.loc[len(account_summary)] = totals_row
            
                # Add a break row (empty)
                account_summary.loc[len(account_summary)] = [""] + ["" for _ in range(len(self.all_months))]
            
            account_summary.loc[len(account_summary)] = ["TOTAL NETWORTH"] + networth.tolist()

            return account_summary
        
        def displayAccountSummary(account_summary, initial_balances, months):
            """Display financial data """
            
            def changeMonthsDisplayed():
                """Modify the number of months displayed using a slider and entry box."""
                top = tk.Toplevel(self)
                top.title("Select Number of Months to Display")
                self.openRelativeWindow(top, width=350, height=200)
                top.resizable(False, False)
            
                tk.Label(top, text="Select Months to Display:", font=(self.font_type, self.font_size)).pack(pady=10)
            
                # Slider (Scale) to select number of months
                slider = tk.Scale(top, from_=3, to=len(self.all_months), orient="horizontal", length=250, 
                                  tickinterval=3, resolution=1)
                slider.set(number_of_months_displayed)
                slider.pack()
            
                # Entry Box for direct input
                entry_var = tk.StringVar(value=str(number_of_months_displayed))
                entry_box = ttk.Entry(top, textvariable=entry_var, width=5)
                entry_box.pack(pady=5)
            
                def updateMonths():
                    """Update number_of_months_displayed and refresh table."""
                    try:
                        value = int(entry_var.get())  # Get number from entry box
                        if 3 <= value <= len(self.all_months):
                            displayed_months = self.all_months[-value:]  # Show the last `n` months
                            addToTreeView(tree, account_tree, account_summary, displayed_months)  # Refresh the table
                            top.destroy()  # Close window
                        else:
                            #TODO Change to an error message
                            print("Invalid range: Must be between 3 and 24 months")
                    except ValueError:
                        print("Invalid input: Enter a number")
            
                # Apply Button
                apply_btn = ttk.Button(top, text="Apply", command=updateMonths)
                apply_btn.pack(pady=10)
            
                # Link slider and textbox
                def syncSlider(event):
                    entry_var.set(str(slider.get()))
            
                def syncEntry(event):
                    try:
                        value = int(entry_var.get())
                        if 3 <= value <= len(self.all_months):
                            slider.set(value)
                    except ValueError:
                        pass  # Ignore invalid input
            
                slider.bind("<Motion>", syncSlider)  # Sync entry box when moving slider
                entry_box.bind("<KeyRelease>", syncEntry)  # Sync slider when typing
            
                top.mainloop()
                
                return
            
            def showColumnMenu(event, table):
                
                menu = tk.Menu(self, tearoff=0)
                
                menu.add_command(label="Reverse Order", command=lambda: switchOrder(event))
                menu.add_command(label="Change Displayed Months", command=lambda: changeMonthsDisplayed())
                
                menu.post(event.x_root, event.y_root)
                
            def switchOrder(event):
                """Toggle month order and refresh the table without reloading the UI."""
                self.switch_monthly_order = not self.switch_monthly_order  # Toggle order                    
                addToTreeView(tree, account_tree, account_summary, displayed_months)  
                return
                
            def on_mouse_wheel(event):
                """ Mouse wheel scrolling - improves speed"""
                if event.state & 0x0001:  # Shift key pressed (for horizontal scroll)
                    tree.xview_scroll(int(-1 * (event.delta / 10)), "units")
                else:  # Default vertical scroll
                    account_tree.yview_scroll(int(-1 * (event.delta / 60)), "units")
                    tree.yview_scroll(int(-1 * (event.delta / 20)), "units")
                return                
            
            def showMonthBreakdown(month_name):
                """Display a breakdown of all account statistics for the selected month."""
                
                # Precompute monthly transactions using `groupby`
                def computeMonthlyStats(df):
                    """Compute account statistics for the selected month."""
                    filtered_df = df[pd.to_datetime(df['Date']).dt.year == year]
                    filtered_df = filtered_df[pd.to_datetime(filtered_df["Date"]).dt.month == month]
                    return filtered_df
                
                def getStartingBalance(account, month, year):
                    """Retrieve the starting balance of an account for a given month.""" 
                    if month == self.date_range[0].month and year == self.date_range[0].year:
                        return initial_balances[account].tolist()[0]
                    else:
                        if month == 1:
                            m, y = 12, year-1
                        else:
                            m, y = month-1, year
                            
                        return account_summary.loc[account_summary["Account"] == account][(m, y)].tolist()[0]
            
                # Determine the index of the selected month
                month, year = month_name[0], month_name[1]
            
                # Create a popup window
                top = tk.Toplevel(self)
                text = formatMonthYear(month, year)
                top.title(f"{text} Account Breakdown")
            
                # Create a Treeview for displaying breakdown data
                tree = ttk.Treeview(top, columns=["Account", "Start Balance", "Total Income", "Total Expenses", 
                                      "Net Cash Flow", "Ending Balance", "Savings Rate (%)"], 
                        show="headings", selectmode="none")
                
                # Apply standard formatting for table
                style = ttk.Style()
                self.goodLookingTables(style)
            
                # Column settings
                column_widths = {"Account": 180, "Start Balance": 150, "Total Income": 150, "Total Expenses": 150, 
                     "Net Cash Flow": 150, "Ending Balance": 150, "Savings Rate (%)": 150}
                
                # get minimum size of window
                window_width = 10
                for k, v in column_widths.items():
                    window_width += v
                            
                for col in tree["columns"]:
                    tree.heading(col, text=col, anchor=tk.CENTER)
                    width = column_widths.get(col, 150)
                    tree.column(col, width=width, anchor=tk.E if col != "Account" else tk.W, stretch=tk.NO)
            
                # Compute min/max/transaction counts
                income_totals       = computeMonthlyStats(self.income_data.copy())
                expense_totals     = computeMonthlyStats(self.expenses_data.copy())
            
                # Iterate over accounts and compute values
                count = 0
                
                tag = 'oddrow'
                
                for account in account_summary["Account"]:
                    
                    # Alternating row colors for readability
                    tag = "oddrow" if tag == "evenrow" else "evenrow"
                    
                    if account != "" and "TOTAL" not in account:
                    
                        inc_values = income_totals[income_totals['Account'] == account]
                        exp_values = expense_totals[expense_totals['Account'] == account]
                        
                        # Get total and net values
                        total_inc = inc_values['Amount'].sum()
                        total_exp = exp_values['Amount'].sum()
                        net_cash_flow = total_inc - total_exp
                        
                        # Get starting and ending balances
                        start_balance = getStartingBalance(account, month, year)
                        end_balance   = start_balance + net_cash_flow
    
                        # Get savings rate
                        savings_rate = (net_cash_flow / start_balance * 100) if total_inc != 0 and start_balance != 0 else "N/A"                        
                        
                        # Format and insert data
                        tree.insert("", 
                                    tk.END, 
                                    values=[account, 
                                            f"${start_balance/100.:,.2f}", 
                                            f"${total_inc/100.:,.2f}", 
                                            f"${total_exp/100.:,.2f}", 
                                            f"${net_cash_flow/100.:,.2f}", 
                                            f"${end_balance/100.:,.2f}", 
                                            f"{savings_rate:.2f}%" if savings_rate != "N/A" else "N/A"], 
                                    tags=(tag,))
                        
                    elif "TOTAL" in account and "OTHER" not in account and "RETIREMENT" not in account:
                        tree.insert("", tk.END, values=[""]*7)
                    else:
                        continue
                    
                    count += 1
            
                    # Apply row styles
                    tree.tag_configure("oddrow",    background=self.banded_row[0])  # Light gray
                    tree.tag_configure("evenrow",   background=self.banded_row[1])  # White
                    
                window_height = count * 30
                
                self.openRelativeWindow(top, width=window_width, height=window_height)
                top.resizable(False, False)
                    
                tree.pack(expand=True, fill=tk.BOTH)
                
                def exitWindow(event=None):
                    top.destroy()
                            
                # Bind Escape keys
                tree.bind("<Escape>", exitWindow)
                
                tree.focus_set()
               
                return                
            
            def addToTreeView(tree, account_tree, account_summary, months):
                
                # Clear the Treeview contents but keep UI intact
                self.clearTreeview(tree)  
                self.clearTreeview(account_tree)
                
                if self.switch_monthly_order:
                    months_ = months[::-1]
                else:
                    months_ = months
                    
                tree["columns"] = months_
                
                # Reapply column headings
                for col in months_:
                    text = formatMonthYear(col[0], col[1])  # Format 'Mon 'YY'
                    tree.heading(col, text=text, anchor=tk.CENTER, command=lambda c=col: showMonthBreakdown(c))
                    tree.column(col, width=column_widths.get(col, 100), anchor=tk.E, stretch=tk.NO)  # Adjust width
                    
                tag = 'oddrow'
            
                num_months = len(months_)
            
                # Repopulate Treeview with new month order
                for i, row in account_summary.iterrows():
                    """
                    tmp_row = row.tolist()
                    tmp_row = tmp_row[1:]
                    tmp_row = tmp_row[-num_months:]
                    if self.switch_monthly_order:
                        tmp_row = tmp_row[::-1]
                    formatted_row = [f"${val/100.:,.2f}" if isinstance(val, (int, float)) else val for val in tmp_row]
                    
                    #TODO FIX THIS SHITTTTT
                    
                    # Alternating row colors
                    tag = "oddrow" if tag == "evenrow" else "evenrow"
                    if "TOTAL" in row['Account']:
                        tag = "totalrow"
                    # Insert into both Treeviews
                    account_tree.insert("", tk.END, values=[row["Account"]], tags=(tag,))
                    tree.insert("", tk.END, values=formatted_row, tags=(tag,))
                    """
                    
                return i
            
            # Determine number of months to display
            number_of_months_displayed = min(12, len(months))
            displayed_months = months[-number_of_months_displayed:]
            
            # Create the Treeview Table
            table_frame = ttk.Frame(self.main_frame)
            table_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
            # Define column widths
            window_width = 160
            column_widths = {"Account": 160}  # Wider for account names
            for month in displayed_months:
                column_widths[month] = 110  # Increase width for readability
                window_width += 110
    
            # Create a separate Treeview for the Account column
            account_tree = ttk.Treeview(table_frame, columns=["Account"], show="headings", selectmode="none", height=15)
            account_tree.heading("Account", text="Account", anchor=tk.W)
            account_tree.column("Account", width=160, anchor=tk.W, stretch=tk.NO)
            account_tree.pack(side=tk.LEFT, fill=tk.Y)
                        
            # Bind right-click event to show column menu
            account_tree.bind("<Button-1>", lambda event: switchOrder(event))
            account_tree.bind("<Button-3>", lambda event: showColumnMenu(event, account_tree))
    
            # Create a frame for the main Treeview and scrollbar
            data_frame = ttk.Frame(table_frame)
            data_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
            # Scrollbar for horizontal scrolling
            x_scroll = ttk.Scrollbar(data_frame, orient=tk.HORIZONTAL)
            x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
    
            # Main Treeview (for months)
            tree = ttk.Treeview(
                data_frame, 
                columns=displayed_months, 
                show="headings", 
                selectmode="none", 
                xscrollcommand=x_scroll.set,
                height=15
            )
    
            # Link scrollbar
            x_scroll.config(command=tree.xview)
            
            # Apply standard formatting for table
            style = ttk.Style()
            self.goodLookingTables(style)
    
            i = addToTreeView(tree, account_tree, account_summary, displayed_months)
    
            # Apply row styles
            for t in (tree, account_tree):
                tree.tag_configure("oddrow", background=self.banded_row[0])
                tree.tag_configure("evenrow", background=self.banded_row[1])
                t.tag_configure("totalrow", font=(self.font_type, self.font_size, "bold"), background="#e6f2ff")  # Light blue for totals
    
            tree.pack(expand=True, fill=tk.BOTH)
    
            # Bind mouse scrolling events
            tree.bind("<MouseWheel>", on_mouse_wheel)
            account_tree.bind("<MouseWheel>", on_mouse_wheel)
    
            # Keep the window size dynamic
            window_height = i * 32
            window_width = min(int(window_width * 1.03), 1200)
            self.geometry(f"{window_width}x{window_height}")
            self.resizable(True, False)
            
            return
        
        self.clearMainFrame()
        
        # Define months for table columns
        self.all_months = generateMonthYearList(self.new_date_range[0], self.new_date_range[1])
        
        # Get initial balances
        initial_balances = self.starting_data.copy()
        
        # Load initial balances from a file
        account_summary = monthlyBalances()
        
        # Display the datatable
        displayAccountSummary(account_summary, initial_balances, self.all_months)
        
        return
        
    def showSavings(self, event=None):
        """Show Spending Breakdown section."""
        self.clearMainFrame()
        label = ttk.Label(self.main_frame, text="Savings Breakdown", font=("Arial", 14, "bold"))
        label.pack(pady=20)
    
    def showSpending(self, event=None):
        """Show Spending Breakdown section."""
        self.clearMainFrame()
        label = ttk.Label(self.main_frame, text="Spending Breakdown", font=("Arial", 14, "bold"))
        label.pack(pady=20)
    
    def showInvestments(self, event=None):
        """Show Investments section."""
        self.clearMainFrame()
        label = ttk.Label(self.main_frame, text="Investments", font=("Arial", 14, "bold"))
        label.pack(pady=20)
        
    def showMainFrame(self, event=None, start_fresh=True):
        """Show the mainframe of the program"""
        self.clearMainFrame()
        if start_fresh:
            self.displayIncExpTables(self.income_data.copy(), self.expenses_data.copy())
        return
    
    def clearMainFrame(self):
        """Clear the main frame for a new view."""
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        return
    
    def editInitialValues(self):
        """Open a secondary window to edit initial values for accounts."""
    
        # Ensure data is loaded
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
        scroll_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
    
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
    
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
        # Dictionary to store entry widgets for later retrieval
        entry_widgets = {}
        
        # Insert data from dataframe
        for i, account in enumerate(self.accounts):
            initial_balance = self.starting_data[account].values[0]
            
            # Account Name Label
            ttk.Label(scroll_frame, text=account, font=(self.font_type, self.font_size)).grid(
                row=i + 1, column=0, padx=10, pady=5, sticky="w"
            )
    
            # Entry Field for Balance
            entry = ttk.Entry(scroll_frame, width=15, font=(self.font_type, self.font_size - 2))
            entry.insert(0, f"{initial_balance/100:.2f}")
            entry.grid(row=i + 1, column=1, padx=10, pady=5, sticky="w")
    
            entry_widgets[account] = entry
    
        # Function to save changes
        def saveChanges(event=None):
            """Save edited initial values to the dataframe."""
            for account, entry in entry_widgets.items():
                new_value = entry.get()
    
                try:
                    new_value = int(round(float(new_value),2) * 100)
                    self.starting_data[account] = new_value
                except Exception:
                    messagebox.showerror("Error", f"Invalid value for {account}. Please enter a number.")
    
            messagebox.showinfo("Success", "Initial balances updated successfully.")
            top.destroy()
            
            self.showMonthlyBreakdown()
            
        def exitWindow(event=None):
            top.destroy()
            
        window_width = 320
        window_height = (len(self.accounts)+1) * 45
        geom = str(window_width) + "x" + str(window_height)
        top.geometry(geom)
        
        top.bind("<Escape>", exitWindow)
        top.bind("<Return>", saveChanges)
        
        # Save Button (Now at Bottom)
        button_frame = ttk.Frame(top)
        button_frame.pack(side="bottom", pady=10)
    
        save_button = ttk.Button(button_frame, text="Save Changes", command=saveChanges, style="Accent.TButton")
        save_button.pack()
    
        # Apply modern styling
        style = ttk.Style()
        style.configure(
            "Accent.TButton",
            font=(self.font_type, self.font_size - 1, "bold"),
            padding=5,)
        
        return

    def selectFilesAndFolders(self, reload=False, update=False):
        """Open file dialog to select csv or pkl file(s)"""
        
        def loadCSVFile(file):
            """Load financial data from csv file(s)."""
            
            headers = ['Date', 'Description', 'Amount', 'Account', 'Category']
                
            file_name = file.split("/")[-1]
        
            try:
                df = pd.read_csv(file).fillna(0)
                
                expenses = {header: [] for header in headers}
                income = {header: [] for header in headers}
                
                for i in range(df.shape[0]):
                
                    #Differentiate between the different sources of information
                    if file_name.startswith("AFCU"):
                
                        date        = df['Date'][i]
                        description = df['Description'][i]
                        credit      = df['Credit'][i]
                        debit       = df['Debit'][i]
                        
                    elif file_name.startswith("Capital"):
                        
                        date        = df['Transaction Date'][i]
                        description = df['Description'][i]
                        credit      = df['Credit'][i]
                        debit       = df['Debit'][i]
                    
                    elif file_name.startswith("PFCU"):
                        
                        if 'credit' in file_name.lower():
                            date      = df['Posted Date'][i]
                        else:
                            date    = df['Transaction Date'][i]

                        description = df['Description'][i]
                        amount      = df['Amount'][i]
                        
                        for j in ["$", ",", ")"]:
                            amount = amount.replace(j,"")
                        amount = float(amount.replace("(","-"))
                        
                        if amount > 0.0:
                            credit = amount
                            debit = 0.0
                        else:
                            credit = 0.0
                            debit = amount
                            
                        if file_name.endswith("Credit.csv"):
                            old_credit = credit
                            old_debit = debit
                            
                            debit = old_credit
                            credit = old_debit
                        
                    if debit == 0.0:
                        income['Date'].append(date)
                        income['Description'].append(description)
                        income['Amount'].append(abs(float(credit)))
                        income['Account'].append(file_name.replace(".csv",""))
                        income['Category'].append('')
                            
                    else:
                        expenses['Date'].append(date)
                        expenses['Description'].append(description)
                        expenses['Amount'].append(abs(float(debit)))
                        expenses['Account'].append(file_name.replace(".csv",""))
                        expenses['Category'].append('')
                    
                expenses = pd.DataFrame(expenses)
                income   = pd.DataFrame(income)
                
                # Change all amounts to cents for float handling
                expenses['Amount']  = (expenses["Amount"] * 100).round().astype(int)
                income['Amount']    = (income["Amount"] * 100).round().astype(int)
        
                return expenses, income
                    
            except Exception as e:
                messagebox.showinfo(message = f"CSV file {file} not read. \n\n Error {e}")
                return '', ''
               
        def loadPickleFile(file):
            """Load financial data from a pickle file."""
            with open(file, "rb") as f:
                yearly_data = pickle.load(f)
            return yearly_data['Expenses'], yearly_data['Income'], yearly_data['Initial']
        
        #TODO add way to read in old csv files with new information but w/o category information and combine with already existing data
        
        if reload:
            try:
                with open(self.last_saved_file, 'r') as f:
                    data_files = f.readlines()
                if os.path.exists(data_files[0]):   
                    self.clearMainFrame()
                    self.income_data    = pd.DataFrame()
                    self.expenses_data  = pd.DataFrame()
                else:
                    reload = False
            except:
                reload = False
            
        if not reload:
            filetypes = [("Pickle Files", "*.pkl"),
                             ("CSV Files", "*.csv")]
            
            filetypes = filetypes[::-1]
                
            data_files = filedialog.askopenfilenames(title="Select Files", filetypes=filetypes)
            #data_files = ['C:/Users/Admin/OneDrive/Desktop/Documents/Budget/TEST/PFCU Savings.csv']           
        
        if len(data_files) != 0:
            for data_file in data_files:
                if data_file.endswith(".pkl"):
                    exp, inc, self.starting_data = loadPickleFile(data_file)
                    #exp, inc = loadPickleFile(data_file)
                else:
                    exp, inc = loadCSVFile(data_file)
                
                self.income_data    = pd.concat([self.income_data, inc], ignore_index=False)
                self.expenses_data  = pd.concat([self.expenses_data, exp], ignore_index=False)
                    
                self.data_files.append(data_file)
                    
            self.setupDataFrames()
               
        else:
            messagebox.showinfo("Error", message = "No File Selected")
            
        return        
    
    def setupDataFrames(self):
        """Format the expenses and income dataframes and also setup initial variables/lists"""
        
        def getDataFrameIndex(df):
            """Add/correct index column of dataframe"""
            if 'Index' not in df:
                df.insert(0, 'Index', df.index)
            else:
                df = df.drop('Index', axis=1)
                df.insert(0, 'Index', df.index)
            return df
        
        def convertToDatetime(df):
            """Convert date formate in dataframes."""
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=False, format='mixed').dt.date
            return df
        
        def sortDataFrame(df):
            """Sort Dataframe by given set of columns"""
            df = df.sort_values(by=['Date', 'Amount', 'Account', 'Category'], ascending=True, inplace=False).reset_index(drop=True) 
            return df
        
        def getStartEndDates(df):
            """Calculate the earliest and latest dates of the income and expenses dataframe"""  
            return df['Date'].min(), df['Date'].max()
        
        def removeEmptyAmounts(df):
            """Remove all rows with 0.00 in the amounts column"""
            return df[df['Amount'] != 0].reset_index(drop=True)
        
        def getMinMaxVals(df):
            """Calculate the minimum and maximum values of a dataframe"""
            return df['Amount'].min(), df['Amount'].max()
        
        # Check if either of the dataframes are empty for error handling later
        exp_empty, inc_empty = False, False
        
        if self.expenses_data.empty:
            exp_empty = True
        if self.income_data.empty:
            inc_empty = True
        
        # Format dataframe 'Date' columns 
        self.income_data    = convertToDatetime(self.income_data)
        self.expenses_data  = convertToDatetime(self.expenses_data) 
 
        # Sort dateframes
        self.income_data    = sortDataFrame(self.income_data)
        self.expenses_data  = sortDataFrame(self.expenses_data)
        
        # Format dataframe 'Index' columns
        self.income_data    = getDataFrameIndex(self.income_data)
        self.expenses_data  = getDataFrameIndex(self.expenses_data)
        
        # Calculate earliest and latest date of dataframes for table display
        income_start_date, income_end_date      = getStartEndDates(self.income_data)
        expenses_start_date, expenses_end_date  = getStartEndDates(self.expenses_data)
        
        if exp_empty:
            self.date_range[0] = income_start_date
            self.date_range[1] = income_end_date
        elif inc_empty:
            self.date_range[0] = expenses_start_date
            self.date_range[1] = expenses_end_date
        else:
            self.date_range[0]  = min(income_start_date, expenses_start_date)
            self.date_range[1]  = max(income_end_date, expenses_end_date)
        
        self.new_date_range = self.date_range.copy() 
        
        # Remove entries with 0.00 in amount column
        self.income_data = removeEmptyAmounts(self.income_data)
        self.expenses_data = removeEmptyAmounts(self.expenses_data)
        
        # Calculate minimum and maximum amounts for dataframes for table display
        income_min, income_max      = getMinMaxVals(self.income_data)
        expenses_min, expenses_max  = getMinMaxVals(self.expenses_data)
        
        self.amount_range[0][0] = income_min / 100.
        self.amount_range[0][1] = income_max / 100.
        
        self.amount_range[1][0] = expenses_min / 100.
        self.amount_range[1][1] = expenses_max / 100.
        
        self.new_amount_range = self.amount_range.copy()
        
        # Determine a list of accounts
        self.accounts = list([self.income_data['Account'].tolist(), self.expenses_data['Account'].tolist()])
        self.accounts = sorted(list(set([x for xs in self.accounts for x in xs])))
        
        self.new_accounts = self.accounts.copy()
        
        # Fill in empty entries in the Category column 
        self.income_data["Category"] = self.income_data["Category"].replace(["", None, np.nan], "Not Assigned")
        self.expenses_data["Category"] = self.expenses_data["Category"].replace(["", None, np.nan], "Not Assigned")
        
        # Generate the dataframe of starting balances
        if self.starting_data.empty:
            for account in self.accounts:
                self.starting_data[account] = [0]
            
        # Display the dataframes        
        self.displayIncExpTables(self.income_data.copy(), self.expenses_data.copy())  
        
        return    
    
    def saveState(self):
        """Save function."""
        if len(self.data_files) > 0:
            if len(self.data_files) == 1 and self.data_files[0].endswith(".pkl"):
                self.saveToPickleFile(self.data_files[0])
            else:
                self.saveStateAs()
        else:
            messagebox.showinfo("Message", "No data to save")  
            
        return
        
    def saveStateAs(self):
        """Save as function."""
        filetypes = [("Pickle Files", "*.pkl")]
        
        pickle_file = filedialog.asksaveasfilename(title="Select Files", filetypes=filetypes, defaultextension=".pkl")
        
        self.saveToPickleFile(pickle_file)
        
        return        
        
    def saveToPickleFile(self, pickle_file):
        """Save income and expenses information to pickle file"""
        yearly_data = {'Expenses'   : self.expenses_data, 
                       'Income'     : self.income_data, 
                       'Initial'    : self.starting_data}
        
        pickle_file = os.path.join(pickle_file)
        with open(pickle_file, "wb") as f:
            pickle.dump(yearly_data, f)    
            
        messagebox.showinfo("File Saved", f"Data successfully saved to \n{pickle_file}")
        
        with open(self.last_saved_file, "w") as f:
            f.write(pickle_file)
        
        return

    def displayIncExpTables(self, inc, exp):
        """Display total expenses and income data.""" 
        
        def showTable(df, df_name):
            """Display a table for the given dataframe in the main window with an editable 'Category' column."""
            
            if df_name == 'inc':
                row = 3
            else:
                row = 1

            # Create a frame with padding for aesthetics
            frame = ttk.Frame(self.main_frame, padding=5)
            frame.grid(row=row, column=0, sticky='w', pady=2)
        
            columns = list(df.columns)
            tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
            
            self.clearTreeview(tree)
            
            # Create Scrollbars
            y_scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=y_scrollbar.set)
            y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            tree.pack(expand=True, fill=tk.BOTH)
        
            # Define preset column widths
            column_widths = {
                "Index": 70,
                "Date": 120,
                "Description": 450,
                "Amount": 110,
                "Account": 150,
                "Category": 150
            }
            
            if self.drop_index:
                column_widths['Index'] = 0
            
            style = ttk.Style()
            self.goodLookingTables(style)
        
            # Define column headings
            for col in columns:
                tree.heading(col, text=col, command=lambda c=col: self.sortIncExpTable(tree, c, df, 0))
                width = column_widths.get(col, 120)
                tree.column(col, anchor=tk.W if col != "Amount" else tk.E, width=width, stretch=tk.NO)
        
            # Apply alternating row colors
            tree.tag_configure("oddrow", background=self.banded_row[0])
            tree.tag_configure("evenrow", background=self.banded_row[1])
            tag = 'oddrow'
        
            # Populate Treeview with data
            for i, row in df.iterrows():
                values = list(row)
                values[3] = f"${values[3]/100:.2f}"  # Format amount as currency
                tag = "oddrow" if tag == "evenrow" else "evenrow"
                tree.insert('', tk.END, values=values, tags=(tag,))
        
            tree.pack(expand=True, fill=tk.BOTH)

            # Get category list
            cat_list, cat_file = self.getCategoryTypes(df_name)    
        
            def on_cell_click(event):
                """Open a dropdown menu when clicking on a 'Category' cell."""
                item_id = tree.identify_row(event.y)  # Get clicked row
                col_id = tree.identify_column(event.x)  # Get clicked column
        
                if not item_id or col_id != f"#{columns.index('Category')+1}":  # Ensure it's the 'Category' column
                    return
                
                row_index = int(tree.index(item_id))
                current_value = df.at[row_index, "Category"]
        
                # Retrieve selected row values
                row_values = tree.item(item_id, "values")
                index_value = int(row_values[0])
           
                # Get the current category
                current_value = df.at[row_index, "Category"]
        
                # Get cell coordinates
                x, y, width, height = tree.bbox(item_id, columns.index("Category"))
        
                # Create dropdown menu
                category_var = tk.StringVar(value=current_value)
                dropdown = ttk.Combobox(tree, textvariable=category_var, values=cat_list, state="readonly")
                dropdown.place(x=x, y=y, width=width, height=height)
        
                # Function to update DataFrame on selection
                def onCategorySelected(event):
                    """Update the DataFrame when a category is selected."""
                    new_value = category_var.get()
                    
                    if df_name == 'inc':
                        self.income_data.at[index_value, "Category"] = new_value
                    else:
                        self.expenses_data.at[index_value, "Category"] = new_value
                    
                    df.at[index_value, "Category"] = new_value  # Update the displayed DataFrame
                    
                    values = [df.at[index_value, col] for col in columns]
                    values[3] = f"${values[3]/100:.2f}"  # Format amount as currency
                    
                    tree.item(item_id, values=values)# Update the Treeview
                    dropdown.destroy()  # Remove the dropdown               
        
                dropdown.bind("<<ComboboxSelected>>", onCategorySelected)
                
                dropdown.focus_set()  # Focus on dropdown
        
            # Bind the table click event to open the dropdown
            tree.bind("<Button-1>", on_cell_click)
            
            # Bind right-click event to show column menu
            tree.bind("<Button-3>", lambda event: self.showColumnMenu(event, tree, df, df_name))
            
            return
        
        def showTimeSeriesPlot(inc, exp):      
            """Display a cumulative sum time series plot of amounts for each account in the given dataframe."""
            def clearPlotArea():
                """Clear the right-side plot area before displaying a new plot."""
                if hasattr(self, 'time_series_plot_frame'):
                    self.time_series_plot_frame.destroy()
            
            # Ensure account column is categorized correctly
            accounts = sorted(set(inc["Account"].unique()) | set(exp["Account"].unique()))

            # Create Matplotlib Figure
            fig = Figure(figsize=(6, 4), dpi=100)
            ax = fig.add_subplot(111)
            
            inc_days = inc['Date'].max() - inc['Date'].min()
            exp_days = exp['Date'].max() - exp['Date'].min()
            num_dates = max(inc_days, exp_days).days
            if num_dates > 91:
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
            else:
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
            
            # Iterate over each account to compute and plot net cash flow
            for account in accounts:
                    
                # Filter income and expenses per account
                income_by_date = inc[inc["Account"] == account].groupby("Date")["Amount"].sum() / 100.
                expenses_by_date = exp[exp["Account"] == account].groupby("Date")["Amount"].sum() / 100.
                
                # Error handling incase one of the dataframes is empty
                if income_by_date.empty and expenses_by_date.empty:
                    messagebox.showinfo("Error", message = "No data to display as plot")
                elif income_by_date.empty:
                    all_dates = pd.date_range(start=exp["Date"].min(), end=exp["Date"].max())
                elif expenses_by_date.empty:
                    all_dates = pd.date_range(start=inc["Date"].min(), end=inc["Date"].max())
                else:
                    all_dates = pd.date_range(start=min(inc["Date"].min(), exp["Date"].min()), 
                                              end=max(inc["Date"].max(), exp["Date"].max()))
                    
                income_by_date = income_by_date.reindex(all_dates, fill_value=0)
                expenses_by_date = expenses_by_date.reindex(all_dates, fill_value=0)
            
                # Compute net cash flow (Income - Expenses) and cumulative sumn
                net_cash_flow = (income_by_date - expenses_by_date).cumsum() + self.starting_data[account].values[0] / 100.
            
                # Plot the net income/expense difference
                ax.plot(net_cash_flow.index, net_cash_flow.values, label=account)
            
            ax.axhline(0, color="black", linestyle="--", linewidth=1)  # Reference line at zero
            ax.set_title("Cumulative Income vs. Expenses Difference by Account")
            ax.set_xlabel("Date")
            ax.set_ylabel("Net Cash Flow ($)")
            ax.legend(loc="upper left", fontsize="small")
            ax.grid(True)
            
            # Ensure previous plot is removed before adding a new one
            clearPlotArea()
            
            # Create a dedicated frame for the plot
            self.plot_frame = ttk.Frame(self.main_frame)
            self.plot_frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=10)  # Ensure expansion
            
            # Allow the frame to expand
            self.main_frame.grid_rowconfigure(4, weight=1)  # Allow row 4 to expand
            self.main_frame.grid_columnconfigure(0, weight=1)  # Allow column 0 to expand
            
            # Embed the Matplotlib figure in Tkinter
            canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
            canvas.draw()
            
            # Create a frame for the toolbar (this fixes visibility issues)
            toolbar_frame = ttk.Frame(self.plot_frame)
            toolbar_frame.pack(side="top", fill="x")  # Ensure it's visible at the top
            
            # Add Matplotlib interactive toolbar for zooming, panning, etc.
            toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
            toolbar.update()
            
            # Pack the plot itself
            canvas.get_tk_widget().pack(fill="both", expand=True)
            
            return
        
        self.clearMainFrame()
        if self.drop_index:
            self.geometry("993x950")
        else:
            self.geometry("1063x950")
        
        # Make sure the parent frame's column is expandable
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        expenses_label = ttk.Label(self.main_frame, text="EXPENSES", font=(self.font_type, self.font_size, "bold"))
        expenses_label.grid(row=0, column=0, sticky="n", pady=2)
        showTable(exp.copy(), 'exp')
        
        expenses_label = ttk.Label(self.main_frame, text="INCOME", font=(self.font_type, self.font_size, "bold"))
        expenses_label.grid(row=2, column=0, sticky="n", pady=2)
        showTable(inc.copy(), 'inc')
        
        showTimeSeriesPlot(inc.copy(), exp.copy())
        
        return 

    def getCategoryTypes(self, name=None):
        """get category types from files"""
        if name == 'inc':
            file_name = "IncomeCategories.txt"
        else:
            file_name = "SpendingCategories.txt"
            
        cat_list = []
        
        cat_file = os.path.join(os.path.dirname(__file__), file_name)
        
        with open(cat_file) as ff:
            categories = ff.readlines()
        for cat in categories:
            if cat.endswith("\n"):
                cat_list.append(cat[:-1])
            else:
                cat_list.append(cat)
                
        return sorted(cat_list), cat_file     
   
    def redisplayDataFrameTable(self):
        """Evaluate the Dataframes after changing the viewing windows, min/max, etc."""
        
        self.clearMainFrame()
        
        inc_data_copy = self.income_data.copy()
        exp_data_copy = self.expenses_data.copy()
        
        for r, ranges in enumerate([False, self.new_date_range, False, self.new_amount_range]):
            if ranges:
                col = inc_data_copy.columns[r] 
            
                if r != 3:
                    inc_data_copy = inc_data_copy[inc_data_copy[col].between(ranges[0], ranges[1])]
                    exp_data_copy = exp_data_copy[exp_data_copy[col].between(ranges[0], ranges[1])]
                else:
                    inc_data_copy = inc_data_copy[inc_data_copy[col].between(ranges[0][0]*100, ranges[0][1]*100)]
                    exp_data_copy = exp_data_copy[exp_data_copy[col].between(ranges[1][0]*100, ranges[1][1]*100)]
                
        for v, values in enumerate([self.new_accounts, self.new_categories]):
            if values:
                col = inc_data_copy.columns[r+v+1]
                inc_data_copy = inc_data_copy[inc_data_copy[col].isin(values)]
                exp_data_copy = exp_data_copy[exp_data_copy[col].isin(values)]
                
        inc_data_copy = inc_data_copy.reset_index(drop=True) 
        exp_data_copy = exp_data_copy.reset_index(drop=True) 
        
        self.displayIncExpTables(inc_data_copy, exp_data_copy)
        
        return
    
    def openRelativeWindow(self, new_window, width, height):
        """Ensure that the new window is open relative to the main window"""
        
        # Get the main window's position
        main_x = self.winfo_x()
        main_y = self.winfo_y()
        
        # Set the position relative to the main window (e.g., 50 pixels to the right and down)
        new_x = main_x + 50
        new_y = main_y + 50
    
        new_window.geometry(f"{width}x{height}+{new_x}+{new_y}")  # Format: "WIDTHxHEIGHT+X+Y"
        
        return
    
    def showColumnMenu(self, event, table, df, df_name):
        """Show a menu when right-clicking a table heading."""
        
        def showLastMonth(delta=0):
            """Only show data for the last 30/60/90/180/365 days"""
                
            if delta > 0:
                self.new_date_range[0] = self.date_range[1] - timedelta(delta)
                self.new_date_range[1] = self.date_range[1]

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
            
            self.openRelativeWindow(top, width=235, height=500)
            
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
            self.openRelativeWindow(top, width=290, height=200)
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
            self.openRelativeWindow(top, width=window_width, height=window_height)
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
        
            # **Display checkboxes for each account/category**
            checkbox_widgets = {}
            for acc in unique_vals:
                var = tk.BooleanVar(value=True)
                checkbox_widgets[acc] = var
                cb = ttk.Checkbutton(checkbox_frame, text=acc, variable=var, style="TCheckbutton")
                cb.pack(anchor="w", padx=5, pady=2, fill="x")  # Ensures proper alignment
        
            # **Fix for white space issue**: Adjust canvas height dynamically
            checkbox_frame.update_idletasks()  # Update to get correct dimensions
            frame_height = checkbox_frame.winfo_reqheight()  # Get actual height
            canvas.configure(scrollregion=(0, 0, window_width, frame_height))  # Adjust scroll area
        
            # **Ensure Confirm Button Always Appears**
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
                        self.new_categories = selected
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
            cat_list, cat_file = self.getCategoryTypes(df_name)
        
            # Create a popup window
            top = tk.Toplevel(self)
            top.title("Edit Categories")
            self.openRelativeWindow(top, width=400, height=400)
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
            if not self.drop_index:
                self.drop_index = True
            else:
                self.drop_index = False
            self.redisplayDataFrameTable()  # Refresh display
        
        col_id = table.identify_column(event.x)
        col_name = table.heading(col_id, "text")
        
        menu = tk.Menu(self, tearoff=0)
        
        if col_name != 'Index':
            menu.add_command(label=f"Sort {col_name} Ascending", command=lambda: self.sortIncExpTable(table, col_name, df.copy, True))
            menu.add_command(label=f"Sort {col_name} Descending", command=lambda: self.sortIncExpTable(table, col_name, df.copy, False))
        
        if col_name == 'Index':
            """Sort and high index column"""
            if not self.drop_index:
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
            if self.drop_index:
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

    def sortIncExpTable(self, table, column_name, df, sort_direction):
        """Sort the table by a selected column, reversing order on each click."""
        
        if sort_direction == 0:
            if df[column_name].values.tolist() == sorted(df[column_name].values.tolist()):           
                sort_direction = False
            else:
                sort_direction = True
        
        df.sort_values(by=[column_name, 'Date', 'Amount', 'Account', 'Category'], ascending=sort_direction, inplace=True)
        self.sort_orders[column_name] = not sort_direction  # Toggle order for next sort
        
        for item in table.get_children():
            table.delete(item)
        
        # Apply alternating row colors
        table.tag_configure("oddrow", background=self.banded_row[0])
        table.tag_configure("evenrow", background=self.banded_row[1])
        tag = 'oddrow'

        for i, row in df.iterrows():
            values = list(row)
            values[3] = f"${values[3]/100:.2f}"  # Format amount as currency
            tag = "oddrow" if tag == "evenrow" else "evenrow"
            table.insert('', tk.END, values=values, tags=(tag,))
            
        return

if __name__ == "__main__":
    app = FinanceTracker()
    app.mainloop()