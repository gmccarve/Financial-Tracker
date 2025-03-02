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
import calendar
from datetime import datetime, timedelta

from typing import List, Tuple, Union

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.float_format','{:.2f}'.format)

class FinanceTracker(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Personal Finance Tracker")
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
        self.bind("<Control-b>", lambda event: self.showStatistics(event=event, type_of_data='inc'))
        #self.bind("<Control-c>",)
        self.bind("<Control-d>", lambda event: self.showMainFrame())
        self.bind("<Control-e>", lambda event: self.editInitialValues())
        #self.bind("<Control-f>",)
        #self.bind("<Control-g>",)
        #self.bind("<Control-h>",)
        self.bind("<Control-i>", lambda event: self.showInvestments())
        #self.bind("<Control-j>",)
        #self.bind("<Control-k>",)
        self.bind("<Control-l>", lambda event: self.showStatistics(event=event, type_of_data='exp'))
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
        
        self.main_frame.focus_set()
        
        self.selectFilesAndFolders(reload=True)
        self.showMainFrame(start_fresh=False)
        
        self.showSpending()
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
        self.current_sort = ''
        
        # For formatting consistency
        
        self.my_font = tk.font.Font(size=12, font='calibri')
        self.font_type = 'calibri'
        self.font_size = 12
        
        self.banded_row = ["#e6f2ff", "#ffffff", '#D3D3D3']
        self.background_color = "#dce7f5"
        
        self.backslash = '\n'
        
        if on_start == False:
            self.clearMainFrame()
            self.selectFilesAndFolders(reload=False)
             
        return
      
    def onClose(self):
        """Prompt user to save before exiting."""
        #TODO UNDO
        #TODO Doc string
        #if not self.income_data.empty or not self.expenses_data.empty:
        #    if messagebox.askyesno("Save State", "Would you like to save the financial data before exiting?"):
        #        self.saveState()
        self.destroy()
        
    def goodLookingTables(self, style: ttk.Style) -> None:
        """
        Applies a consistent style to Treeview tables.
    
        Parameters:
            style: The ttk.Style object used for configuring table appearance.
        """
        style.configure("Treeview", rowheight=25, font=(self.font_type, self.font_size))  # Set row height and font
        style.configure("Treeview.Heading", font=(self.font_type, self.font_size + 1, "bold"))  # Bold headers
    
    def clearTreeview(self, tree: ttk.Treeview) -> None:
        """
        Clears all items from a Treeview widget.
    
        Parameters:
            tree: The ttk.Treeview widget to be cleared.
        """
        tree.delete(*tree.get_children())
    
    def generateMonthYearList(self, start_date: datetime, end_date: datetime) -> List[Tuple[int, int]]:
        """
        Generates a list of (month, year) tuples between two datetime objects.
    
        Parameters:
            start_date: The starting datetime object.
            end_date: The ending datetime object.
            
        Returns:
            List of tuples in the format (month, year).
        """
        current_date = datetime(start_date.year, start_date.month, 1)
        end_date = datetime(end_date.year, end_date.month, 1)
        
        month_year_list = []
    
        while current_date <= end_date:
            month_year_list.append((current_date.month, current_date.year))
            
            # Move to the next month
            next_month = current_date.month + 1
            next_year = current_date.year + (1 if next_month > 12 else 0)
            current_date = datetime(next_year, 1 if next_month > 12 else next_month, 1)

        return month_year_list
    
    def formatMonthYear(self, month: int, year: int) -> datetime:
        """
        Convert a month and year into the format 'MM 'YY'.
        
        Parameters:
            month (int): The month
            year (int): The year
            
        Returns:
            A (str) in the format "Mon 'YY"
        """
        return datetime(year, month, 1).strftime("%b '%y")
    
    def formatMonthLastDayYear(self, month: int, year: int) -> datetime:
        """
        Convert a month and year into the format 'Mon 'YY'.
        
        Parameters:
            month (int): The month
            year (int): The year
            
        Returns:
            The last day of a month given as a string in the format "MM DD 'YY"
        """
        last_day = (datetime(year, month + 1, 1) - timedelta(days=1)).day
        return datetime(year, month, last_day).strftime("%b %d, '%y")
    
    def showMonthlyBreakdown(self, event=None):
        """Show Accounts section."""
        
        #TODO Fix formatting and docstrings
        
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
        
        def showMonthBreakdown(month_name):
            """Display a breakdown of all account statistics for the selected month, with an interactive plot."""
            
            # Precompute monthly transactions using `groupby`
            def computeMonthlyStats(df):
                """Compute account statistics for the selected month."""
                filtered_df = df[pd.to_datetime(df['Date']).dt.year == year]
                filtered_df = filtered_df[pd.to_datetime(filtered_df["Date"]).dt.month == month]
                return filtered_df
            
            def getStartingBalance(account, month, year):
                """Retrieve the starting balance of an account for a given month.""" 
                if month == self.date_range[0].month and year == self.date_range[0].year:
                    if "TOTAL" in account:
                        keyword = account.replace("TOTAL ", "").title()
                        list_of_keyword_accounts = [col for col in initial_balances.columns if keyword in col]
                        vals = initial_balances[list_of_keyword_accounts].sum().sum()
                        return vals
                    else:
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
            text = self.formatMonthYear(month, year)
            top.title(f"{text} Account Breakdown")
        
            # Create a Treeview for displaying breakdown data
            tree = ttk.Treeview(top, columns=["Account", "Start Balance", "Total Income", "Total Expenses", 
                                  "Net Cash Flow", "Ending Balance", "Savings Rate (%)"], 
                    show="headings", selectmode="none")
            
            # Apply standard formatting for table
            style = ttk.Style()
            self.goodLookingTables(style)
        
            # Column settings
            column_widths = {"Account": 180, 
                             "Start Balance": 150, 
                             "Total Income": 150, 
                             "Total Expenses": 150, 
                             "Net Cash Flow": 150, 
                             "Ending Balance": 150, 
                             "Savings Rate (%)": 150}
            
            # get minimum size of window
            window_width = sum(column_widths.values()) + 20
                        
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
                if "TOTAL" in account:
                    continue
                
                if account != "":
                
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
                    
                    count += 1
                    
                else:
                    tree.insert("", tk.END, values=[""]*7)
        
                # Apply row styles
                tree.tag_configure("oddrow",    background=self.banded_row[0])
                tree.tag_configure("evenrow",   background=self.banded_row[1])
                tree.tag_configure("totalrow", font=(self.font_type, self.font_size, "bold"), background=self.banded_row[2])  # Light blue for totals
   
            """Plot the data for a selected account"""
            
            # Track the account currently being plotted
            self.selected_account = None
            
            # Extract accounts
            account_list = list(account_summary["Account"].dropna().unique())
            account_list = [element for element in account_list if element]
            
            # Create Matplotlib Figure
            fig, ax = plt.subplots(figsize=(7, 3))
            canvas = FigureCanvasTkAgg(fig, master=top)
            plot_widget = canvas.get_tk_widget()
            
            # Add the Matplotlib Toolbar
            toolbar = NavigationToolbar2Tk(canvas, top, pack_toolbar=False)
            toolbar.update()
            
            # Store original y-axis limits before modifying the plot
            original_xlim = ax.get_xlim()
            original_ylim = ax.get_ylim()
            
            def plotAccountBalance(account_name):
                """Plot the account balance over the month with step-like changes."""
                ax.clear()
                
                if account_name not in account_summary["Account"].values:
                    return

                # Filter data for the selected account
                if account_name == '':
                    return
                elif "TOTAL" in account_name:
                    return
                else:
                    account_data = account_summary[account_summary["Account"] == account_name].iloc[:, 1:]
                
                    inc_values = income_totals[income_totals['Account'] == account_name]
                    exp_values = expense_totals[expense_totals['Account'] == account_name]
                    exp_values = exp_values.assign(Amount=exp_values['Amount'] * -1)
                
                all_data = pd.concat([inc_values, exp_values]).sort_values(by=['Date'])
                all_values = all_data['Amount']
                
                # Compute cumulative sum
                cum_values = np.cumsum(all_values.values)
                
                # Calculate starting balance for the month
                starting_balance = (cum_values[-1] - account_data[month_name].tolist()[0]) * -1
                starting_date = datetime(month_name[1], month_name[0], 1)
                
                #update given starting balance
                balances = (cum_values + starting_balance) / 100.  # Convert to dollars
                
                # Get last day of month                
                ending_balance = balances[-1]
                last_day = calendar.monthrange(month_name[1], month_name[0])[1]
                ending_date = datetime(month_name[1], month_name[0], last_day).date()
                
                all_dates = all_data['Date'].tolist()
            
                # Convert data into a step-plot format
                step_dates      = []
                step_balances   = []
                step_values     = [] 
                
                # Start with the initial balance before the first transaction                
                ax.scatter(starting_date, starting_balance / 100., color='black', marker='x', s=50, zorder=3)
                
                step_dates.append(starting_date)
                step_balances.append(starting_balance/100.)  # Balance after transaction
                step_values.append({"Date": starting_date, 
                                    "Description": "Starting Balance", 
                                    "Balance": starting_balance / 100.})
                
                for i in range(len(all_dates)):
                    # Horizontal step (before transaction)
                    date        = all_data.iloc[i]['Date']
                    value       = all_data.iloc[i]['Amount'] / 100.
                    description = all_data.iloc[i]['Description']
                    category    = all_data.iloc[i]['Category']
                    
                    new_amount = balances[i]
                    
                    if value < 0.0:
                        color = 'red'
                    else:
                        color = 'blue'
                        
                    if i == 0:
                        old_value = starting_balance / 100.
                        old_date = starting_date
                    else:
                        old_value = balances[i-1]
                        old_date = all_data.iloc[i-1]['Date']
                    
                    # Vertical step (transaction occurs)
                    ax.plot([date, date], [old_value, new_amount], linestyle='-', color=color)
                    
                    # Horizontal step (date change)
                    if date != old_date and i < len(all_dates):
                        ax.plot([old_date, date], [old_value, old_value], linestyle='-', color='purple')
                        
                    ax.scatter(date, new_amount, color=color, marker='o', s=50, zorder=4)
                    
                    
                    step_dates.append(all_dates[i])
                    step_balances.append(balances[i])  # Balance after transaction
                    step_values.append({"Date": date, 
                                        "Description": description,
                                        "Category": category, 
                                        "Amount": value, 
                                        "Balance": new_amount})
                                    
                # End with the ending balance after the last transaction
                ax.plot([date, ending_date], [ending_balance, ending_balance], linestyle='-', color='purple')
                step_dates.append(ending_date)
                step_balances.append(ending_balance)  # Balance after transaction
                step_values.append({"Date": ending_date, 
                                    "Description": "Final Balance", 
                                    "Balance": ending_balance})
                ax.scatter(ending_date, ending_balance, color='black', marker='x', s=50, zorder=3)
                
                # Step-like plot with horizontal and vertical lines
                line, = ax.plot(step_dates, step_balances, 
                                marker="o", linestyle="-", 
                                label=account_name, 
                                color="blue", 
                                linewidth=0, markersize=0)
            
                # Set x-axis ticks to match transaction dates
                all_dates_with_bounds = [starting_date] + all_dates + [ending_date]
                ax.set_xticks(all_dates_with_bounds)
                ax.set_xticklabels([date.strftime("%d") if date in all_dates else date.strftime("%d") for date in all_dates_with_bounds], 
                   rotation=45)
                
                ax.set_ylabel("Balance ($)")
                ax.set_title(f"{account_name} - Monthly Balance")
                ax.grid(True, linestyle="--", alpha=0.6)  # Add a subtle grid
                
                canvas.draw()
                
                # Create annotation (tooltip)
                annot = ax.annotate("", xy=(0, 0), xytext=(20, 20), textcoords="offset points",
                                    bbox=dict(boxstyle="round, pad=0.3", fc="white", ec="black"),  # Light bg, black border
                                    arrowprops=dict(arrowstyle="->", color="black"),  # Subtle arrow
                                    fontsize=self.font_size-3, color="black", horizontalalignment='left', zorder=10)
                annot.set_visible(False)
                
                def updateAnnot(x, y, trans_data):
                    """Update tooltip position and text."""
                    
                    def wrapText(text, n_cut=40):
                        words = text.split()
                        lines = []
                        current_line = ""
                    
                        for word in words:
                            if len(current_line) + len(word) + 1 > n_cut:
                                lines.append(current_line)
                                current_line = word
                            else:
                                current_line += " " + word if current_line else word
                    
                        lines.append(current_line)  # Append last line
                        return "\n".join(lines)
                    
                    annot.xy = (x, y)
                    
                    new_line = "\n"
                    
                    description_wrapped = wrapText(trans_data['Description'], n_cut=30)
                    
                    try:
                        text = f"Date: {trans_data['Date'].strftime('%Y-%m-%d')}{new_line}" \
                               f"Description: {description_wrapped}{new_line}" \
                               f"Category: {trans_data['Category']}{new_line}" \
                               f"Amount: ${trans_data['Amount']:,.2f}{new_line}" \
                               f"Balance: ${trans_data['Balance']:,.2f}"
                    except:
                        text = f"Date: {trans_data['Date'].strftime('%Y-%m-%d')}{new_line}" \
                               f"Description: {description_wrapped}{new_line}" \
                               f"Balance: ${trans_data['Balance']:,.2f}"
                               
                    annot.set_text(text)
                    
                    # Get plot boundaries
                    xlim = ax.get_xlim()
                    ylim = ax.get_ylim()
                    
                    x = mdates.date2num(x)
                
                    # Compute relative positions (0 to 1 range)
                    x_rel = (x - xlim[0]) / (xlim[1] - xlim[0])
                    y_rel = (y - ylim[0]) / (ylim[1] - ylim[0])
                
                    # Adjust annotation placement
                    ha = "right" if x_rel > 0.66 else "left"   # Flip horizontal alignment
                    va = "top" if y_rel > 0.66 else "bottom"  # Flip vertical alignment
                
                    x_offset = -10 if ha == "right" else 10   # Move left or right
                    y_offset = -15 if va == "top" else 10     # Move up or down
                
                    annot.set_horizontalalignment(ha)
                    annot.set_verticalalignment(va)
                
                    annot.set_bbox(dict(boxstyle="round,pad=0.3", fc="white", ec="black", alpha=1.0))  # Ensure text visibility
                    annot.xytext = (x_offset, y_offset)  # Move annotation based on alignment

                    annot.set_visible(True)
                
                def onHover(event):
                    """Show tooltip when hovering over a data point, treating X and Y distances separately."""
                    if event.inaxes != ax:
                        annot.set_visible(False)
                        canvas.draw_idle()
                        return
                
                    x_cursor, y_cursor = event.xdata, event.ydata
                
                    if x_cursor is None or y_cursor is None:
                        annot.set_visible(False)
                        canvas.draw_idle()
                        return
                
                    # Get y-axis limits for dynamic thresholding
                    y_min, y_max = ax.get_ylim()
                    
                    # Set separate distance thresholds
                    x_threshold = 0.1  # Allow wider X-axis tolerance
                    y_threshold = 0.01 * (y_max - y_min)  # Dynamic Y-axis sensitivity
                
                    # Find closest point
                    min_x_dist = float("inf")
                    min_y_dist = float("inf")
                    closest_index = -1
                
                    for i, (x, y) in enumerate(zip(line.get_xdata(), line.get_ydata())):
                        x_date_num = mdates.date2num(x)  # Convert datetime to numerical format
                        x_dist = abs(x_date_num - x_cursor)  # X-axis distance
                        y_dist = abs(y - y_cursor)  # Y-axis distance
                        
                        if x_dist < x_threshold and y_dist < y_threshold:  # Both must be within range
                            if x_dist < min_x_dist and y_dist < min_y_dist:
                                min_x_dist = x_dist
                                min_y_dist = y_dist
                                closest_index = i
                
                    if closest_index != -1:
                        trans_data = step_values[closest_index]  # Get transaction data
                        updateAnnot(line.get_xdata()[closest_index], line.get_ydata()[closest_index], trans_data)
                        annot.set_visible(True)
                    else:
                        annot.set_visible(False)
                
                    canvas.draw_idle()
                    
                # Connect hover event
                canvas.mpl_connect("motion_notify_event", onHover)
                
                return                
            
            def onAccountSelect(event):
                """Update the plot when an account is clicked in the table."""
                selected_item = tree.focus()
                if selected_item:
                    selected_account = tree.item(selected_item, "values")[0]  # Get selected account name
                    plotAccountBalance(selected_account)
            
            def reset_view(event=None):
                """Resets the plot view to the original limits."""
                ax.set_xlim(original_xlim)  # Restore x-axis limits
                ax.set_ylim(original_ylim)  # Restore y-axis limits
                canvas.draw_idle()  # Redraw the figure
    
            # Bind events
            tree.bind("<ButtonRelease-1>", onAccountSelect)
            
            # Display first account data by default
            if account_list:
                self.selected_account = account_list[0]
                plotAccountBalance(self.selected_account)
        
            # Grid placement of widgets
            tree.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=10, pady=5)
            plot_widget.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=10, pady=5)
            toolbar.grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        
            # Configure column resizing
            top.grid_columnconfigure(0, weight=1)  # Left empty space
            top.grid_columnconfigure(2, weight=1)  # Right empty space
            top.grid_rowconfigure(0, weight=1)  # Table expands
            top.grid_rowconfigure(2, weight=2)  # Plot expand
            
            # Override the Home button's functionality
            toolbar.home = reset_view
            
            def updateTableSizes(event):
                """Dynamically adjust the table sizes for both income and expense tables."""
                new_width = top.winfo_width()
                
                total_fixed_width = sum(column_widths.values())
                scale_factor = new_width / total_fixed_width * 0.95
                
                try:
                
                    # Adjust column width dynamically based on window width
                    if event is None or new_width != self.account_breakdown_window_width:
                        self.account_breakdown_window_width = new_width            
                        for col in tree["columns"]:
                            width = int(column_widths.get(col, 140) * scale_factor)
                            tree.column(col, width=width)
                except:
                    pass
                
                self.update_idletasks()
        
            # Resize window dynamically
            window_height = len(account_summary) * 32 + 250
            self.openRelativeWindow(top, width=window_width, height=window_height)
            top.resizable(True, True)
            self.account_breakdown_window_width = top.winfo_width()            
                        
            # Bind the function to window resizing
            top.bind("<Configure>", updateTableSizes)
            
            updateTableSizes(event=None)
            
            def exitWindow(event=None):
                top.destroy()
                        
            # Bind Escape keys
            tree.bind("<Escape>", exitWindow)
            
            tree.focus_set()
           
            return                
        
        def displayAccountSummary(account_summary, initial_balances):
            """Displays a financial account summary in two separate tables."""
            
            def populateBalanceTree(tree, account_summary, months_list):
                """Clears and repopulates the balance_tree while maintaining formatting."""
                
                if not self.switch_monthly_order:
                    months_list = months_list[-self.number_of_months_displayed:]
                else:
                    months_list = months_list[:self.number_of_months_displayed]
                
                # Apply standard formatting for table
                style = ttk.Style()
                self.goodLookingTables(style)
            
                # Define column widths dynamically (ensures consistency)
                default_column_width = 140  # Default width
                last_n_width = 140  # Wider width for last `n` months
                column_widths = {month: (last_n_width if i >= len(months_list) - self.number_of_months_displayed else default_column_width)
                                 for i, month in enumerate(months_list)}
            
                # Apply column order and update headers
                tree["columns"] = months_list
                for col in months_list:
                    tree.heading(col, text=self.formatMonthLastDayYear(col[0], col[1]), anchor=tk.CENTER, command=lambda c=col: showMonthBreakdown(c))
                    tree.column(col, width=column_widths[col], anchor=tk.E, stretch=tk.NO)
            
                # Clear previous table content
                self.clearTreeview(tree)
            
                # Repopulate the Treeview with formatted data
                tag = 'oddrow'
                for i, row in account_summary.iterrows():
                    formatted_row = [f"${val/100.:,.2f}" if isinstance(val, (int, float)) else val for val in row[1:].tolist()]
                    
                    # Reverse row order if self.switch_monthly_order is enabled
                    if self.switch_monthly_order:
                        formatted_row.reverse()
                        
                    if not self.switch_monthly_order:
                        formatted_row = formatted_row[-self.number_of_months_displayed:]
                    else:
                        formatted_row = formatted_row[:self.number_of_months_displayed]
            
                    # Maintain alternating row colors
                    tag = "oddrow" if tag == "evenrow" else "evenrow"
                    if "TOTAL" in row['Account']:
                        tag = "totalrow"
            
                    # Insert row into the Treeview
                    tree.insert("", tk.END, values=formatted_row, tags=(tag,))
            
                # Reapply row styles
                for t in (tree, account_tree):
                    t.tag_configure("oddrow", background=self.banded_row[0])
                    t.tag_configure("evenrow", background=self.banded_row[1])
                    t.tag_configure("totalrow", font=(self.font_type, self.font_size, "bold"), background=self.banded_row[2])
                    
                return
            
            def reverseOrder(event=None, tree='', months_list=[]):
                """Reverses the column order and updates the balance_tree while preserving formatting."""
                
                # Get the clicked column
                region = tree.identify("region", event.x, event.y)
                
                # Activate only if the click is on the column header
                if region == "heading":
                    self.switch_monthly_order = not self.switch_monthly_order
                    months_list.reverse()
                    populateBalanceTree(tree, account_summary, months_list)
                
            def onMouseWheel(event, tree, account_tree):
                """ Mouse wheel scrolling - improves speed"""
                if event.state & 0x0001:  # Shift key pressed (for horizontal scroll)
                    tree.xview_scroll(int(-1 * (event.delta / 5)), "units")
                else:  # Default vertical scroll
                    account_tree.yview_scroll(int(-1 * (event.delta / 5)), "units")
                    tree.yview_scroll(int(-1 * (event.delta / 5)), "units")
                return
            
            def changeMonthsDisplayed(balance_tree, account_tree, months_list):
                """Modify the number of months displayed using a slider and entry box."""
                
                top = tk.Toplevel(self)
                top.title("Select Number of Months to Display")
                self.openRelativeWindow(top, width=350, height=200)
                top.resizable(False, False)
            
                tk.Label(top, text="Select Number of Months to Display:", font=(self.font_type, self.font_size)).pack(pady=10)
            
                # Slider (Scale) to select number of months
                slider = tk.Scale(top, from_=1, to=len(months_list), orient="horizontal", length=250, 
                                  tickinterval=3, resolution=1)
                slider.set(self.number_of_months_displayed)
                slider.pack()
            
                # Entry Box for direct input
                entry_var = tk.StringVar(value=str(self.number_of_months_displayed))
                entry_box = ttk.Entry(top, textvariable=entry_var, width=5)
                entry_box.pack(pady=5)
            
                def updateMonths():
                    """Update number_of_months_displayed and refresh table."""
                    try:
                        value = int(entry_var.get())  # Get number from entry box
                        if 1 <= value <= len(self.all_months):
                            self.number_of_months_displayed = value
                            populateBalanceTree(balance_tree, account_summary, months_list)  # Refresh the table
                            top.destroy()  # Close window
                        else:
                            #TODO Change to an error message
                            messagebox.showwarning("Warning", f"Invalid range: Must be between 1 and {len(self.all_months)} months")
                    except ValueError:
                        messagebox.showwarning("Warning", "Invalid input: Enter a number")
            
                # Apply Button
                apply_btn = ttk.Button(top, text="Apply", command=updateMonths)
                apply_btn.pack(pady=10)
            
                # Link slider and textbox
                def syncSlider(event):
                    entry_var.set(str(slider.get()))
            
                def syncEntry(event):
                    try:
                        value = int(entry_var.get())
                        if 1 <= value <= len(self.all_months):
                            slider.set(value)
                    except ValueError:
                        pass  # Ignore invalid input
                        
                def exitWindow(event=None):
                    top.destroy()
                            
                # Bind Escape keys
                top.bind("<Escape>", exitWindow)
            
                slider.bind("<Motion>", syncSlider)  # Sync entry box when moving slider
                entry_box.bind("<KeyRelease>", syncEntry)  # Sync slider when typing
                
                entry_box.focus_set()
            
                top.mainloop()
                
                return
            
            def showColumnMenu(event, balance_tree, account_tree, months_list):
                """ Open column menu """
                menu = tk.Menu(self, tearoff=0)
                
                menu.add_command(label="Reverse Order", command=lambda: reverseOrder(balance_tree, months_list))
                menu.add_command(label="Change Displayed Months", command=lambda: changeMonthsDisplayed(balance_tree, account_tree, months_list))
                
                menu.post(event.x_root, event.y_root)
            
            # Clear the main frame before displaying the table
            self.clearMainFrame()
        
            # Create a parent frame for both tables
            table_frame = ttk.Frame(self.main_frame)
            table_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
            # Extract month-year columns
            months = self.all_months.copy()
        
            # Reverse order if switch_monthly_order is enabled
            if self.switch_monthly_order:
                months.reverse()
        
            # Create Treeview for Account column
            account_tree = ttk.Treeview(table_frame, columns=["Account"], show="headings", selectmode="none", height=15)
            account_tree.heading("Account", text="Account", anchor=tk.W)
            account_tree.column("Account", width=160, anchor=tk.W, stretch=tk.NO)
            account_tree.pack(side=tk.LEFT, fill=tk.Y)
            
            account_tree.bind("<Button-1>", lambda event: reverseOrder(event, balance_tree, months))
            account_tree.bind("<Button-3>", lambda event: showColumnMenu(event, balance_tree, account_tree, months))
        
            # Create a frame for the main Treeview and scrollbar
            data_frame = ttk.Frame(table_frame)
            data_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
            # Create horizontal scrollbar
            x_scroll = ttk.Scrollbar(data_frame, orient=tk.HORIZONTAL)
            x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
            # Create main Treeview for balance table
            balance_tree = ttk.Treeview(
                data_frame, 
                columns=months, 
                show="headings", 
                selectmode="none",
                xscrollcommand=x_scroll.set,
                height=15
            )
            
            # Ensure balance_tree is packed BEFORE calling populateBalanceTree
            balance_tree.pack(expand=True, fill=tk.BOTH)  # 👈 Packing must be here
        
            # Link scrollbar
            x_scroll.config(command=balance_tree.xview)
        
            # Populate the account tree
            tag = 'oddrow'
            for account in account_summary.iloc[:, 0]:
                tag = "oddrow" if tag == "evenrow" else "evenrow"
                if "TOTAL" in account:
                    tag = "totalrow"
                account_tree.insert("", tk.END, values=[account], tags=(tag,))
        
            # Populate the balance tree using the helper function
            populateBalanceTree(balance_tree, account_summary, months)
        
            # Bind mouse scrolling events
            account_tree.bind("<MouseWheel>", lambda event: onMouseWheel(event, balance_tree, account_tree))
            balance_tree.bind("<MouseWheel>", lambda event: onMouseWheel(event, balance_tree, account_tree))
        
            # Keep the window size dynamic
            window_height = len(account_summary) * 32
            window_width = max(int(160 + 110 * len(self.all_months) * 1.03), 1200)
            self.geometry(f"{window_width}x{window_height}")
            self.resizable(True, True)
            
            return
        
        if self.current_window == 'Monthly Breakdown':
            return
        
        self.clearMainFrame()
        
        # Define months for table columns
        self.all_months = self.generateMonthYearList(self.new_date_range[0], self.new_date_range[1])
        self.number_of_months_displayed = min(len(self.all_months),12)
        
        # Get initial balances
        initial_balances = self.starting_data.copy()
        
        # Load initial balances from a file
        account_summary = monthlyBalances()
        
        # Display the datatable
        displayAccountSummary(account_summary.copy(), initial_balances.copy())
        
        self.current_window = 'Monthly Breakdown'
        
        return
        
    def showStatistics(self, event=None, type_of_data='inc'):
        """Displays a savings summary in a Treeview table, allowing analysis by category."""
        
        #TODO Fix formatting and docstrings
        
        def displayStatisticsSummary(df, categories, df_type):
            """Displays a financial account summary in two separate tables."""
            
            def showMonthlyCategoryBreakdown(month_name):
                """Display a breakdown of all account statistics for the selected month, with an interactive plot."""
                
                # Precompute monthly transactions using `groupby`
                def computeMonthlyStats(df):
                    """Compute account statistics for the selected month."""
                    filtered_df = df[pd.to_datetime(df['Date']).dt.year == year]
                    filtered_df = filtered_df[pd.to_datetime(filtered_df["Date"]).dt.month == month]
                    return filtered_df
            
                # Determine the index of the selected month
                month, year = month_name[0], month_name[1]
            
                # Create a popup window
                top = tk.Toplevel(self)
                text = self.formatMonthYear(month, year)
                if df_type == 'INCOME':
                    text = text + " Savings"
                else:
                    text = text + " Spending"
                top.title(f"{text} Breakdown")
            
                # Create a Treeview for displaying breakdown data
                category_tree = ttk.Treeview(top, columns=["Category", 
                                                           "Total Spent", 
                                                           "Number of\nTransactions", 
                                                           "Average\nTransaction", 
                                                           "Median\nTransaction", 
                                                           "Largest\nTransaction",
                                                           "Smallest\nTransaction", 
                                                           "Category\nPercentage (%)"], 
                        show="headings", selectmode="none", height=5)
                
                # Apply standard formatting for table
                style = ttk.Style()
                self.goodLookingTables(style)
                style.configure("Treeview.Heading", padding=(5,25), anchor='center', justify='center')
                style.layout("Treeview.Heading", [
                                                    ("Treeheading.cell", {"sticky": "nswe"}),  # Stretches the header cell
                                                    ("Treeheading.border", {"sticky": "nswe"}),  # Ensures full stretch
                                                    ("Treeheading.padding", {"sticky": "nswe"}),  # Applies padding in all directions
                                                    ("Treeheading.label", {"sticky": "nswe"})  # Ensures text is centered in the label
                                                ])
            
                # Column settings
                column_widths = {"Category": 180, 
                                 "Total Spent": 140, 
                                 "Number of Transactions": 140, 
                                 "Average Transaction": 140, 
                                 "Median Transaction": 140, 
                                 "Largest Transaction": 140, 
                                 "Smallest Transaction": 140,
                                 "Category \nPercentage (%)": 140}

                # get minimum size of window
                window_width = sum(column_widths.values()) + 20
                            
                for col in category_tree["columns"]:
                    category_tree.heading(col, text=col, anchor="center")
                    width = column_widths.get(col, 150)
                    category_tree.column(col, width=width, anchor=tk.E if col != "Category" else tk.W, stretch=tk.NO)
            
                # Compute min/max/transaction counts
                if df_type == "INCOME":
                    totals = computeMonthlyStats(self.income_data.copy())
                else:
                    totals = computeMonthlyStats(self.expenses_data.copy())
                
                # Iterate over categories and compute values
                count = 0
                
                tag = 'oddrow'
                
                total_overall = totals['Amount'].sum()
                
                #TODO sort when header is clicked
                #TODO add total at bottom of table
                #TODO add piechart at bottom of window
                #TODO add table next to piechart that shows all transaction for a clicked on category

                for category in categories:
                    
                    # Alternating row colors for readability
                    tag = "oddrow" if tag == "evenrow" else "evenrow"
                    
                    category_data  = totals[totals['Category'] == category]
                    
                    # Get useful breakdown values
                    total = category_data['Amount'].sum()
                    
                    if total == 0.00:
                        num_transactions = 0
                        average_transaction = 0
                        median_transaction = 0
                        largest_transaction = 0
                        smallest_transaction = 0
                        category_percentage = 0
                        
                    else:
                        num_transactions = category_data.shape[0]
                        average_transaction = category_data['Amount'].mean()
                        median_transaction = category_data['Amount'].median()
                        largest_transaction = category_data['Amount'].max()
                        smallest_transaction = category_data['Amount'].min()
                        category_percentage = (total / total_overall) * 100 if total_overall != 0 else 0  # Avoid division by zero
                    
                    # Format and insert data
                    category_tree.insert("", 
                                tk.END, 
                                values=[category, 
                                        f"${total/100.:,.2f}", 
                                        f"{num_transactions}", 
                                        f"${average_transaction/100.:,.2f}", 
                                        f"${median_transaction/100.:,.2f}", 
                                        f"${largest_transaction/100.:,.2f}",
                                        f"${smallest_transaction/100.:,.2f}",
                                        f"{category_percentage:.1f}%"], 
                                tags=(tag,))
                    
                    count += 1
            
                    # Apply row styles
                    category_tree.tag_configure("oddrow",    background=self.banded_row[0])
                    category_tree.tag_configure("evenrow",   background=self.banded_row[1])
                    
       
                """Plot the data for a selected account"""
                
                # Grid placement of widgets
                category_tree.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=10, pady=5)
                #plot_widget.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=10, pady=5)
                #toolbar.grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
            
                # Configure column resizing
                top.grid_columnconfigure(0, weight=1)  # Left empty space
                top.grid_columnconfigure(2, weight=1)  # Right empty space
                top.grid_rowconfigure(0, weight=1)  # Table expands
                top.grid_rowconfigure(2, weight=2)  # Plot expand
                
                # Override the Home button's functionality
            
                # Resize window dynamically
                def updateTableSizes(event):
                    """Dynamically adjust the table sizes for both income and expense tables."""
                    new_width = top.winfo_width()
                    
                    total_fixed_width = sum(column_widths.values())
                    scale_factor = new_width / total_fixed_width * 0.95
                    
                    try:
                    
                        # Adjust column width dynamically based on window width
                        if event is None or new_width != self.account_breakdown_window_width:
                            self.account_breakdown_window_width = new_width            
                            for col in category_tree["columns"]:
                                width = int(column_widths.get(col, 140) * scale_factor)
                                category_tree.column(col, width=width)
                    except:
                        pass
                    
                    self.update_idletasks()
                    
                window_height = len(categories) * 32
                self.openRelativeWindow(top, width=window_width, height=window_height)
                top.resizable(True, True)
                self.account_breakdown_window_width = top.winfo_width()            
                            
                # Bind the function to window resizing
                top.bind("<Configure>", updateTableSizes)
                
                updateTableSizes(event=None)
                
                def exitWindow(event=None):
                    top.destroy()
                            
                # Bind Escape keys
                category_tree.bind("<Escape>", exitWindow)
                
                category_tree.focus_set()
               
                return                
                return
            
            def populateBalanceTree(date_tree, summary_df, months_list, categories):
                """Clears and repopulates the balance_tree while maintaining formatting."""
                
                if not self.switch_monthly_order:
                    months_list = months_list[-self.number_of_months_displayed:]
                else:
                    months_list = months_list[:self.number_of_months_displayed]
                
                # Apply standard formatting for table
                style = ttk.Style()
                self.goodLookingTables(style)
            
                # Define column widths dynamically (ensures consistency)
                default_column_width = 140  # Default width
                last_n_width = 140  # Wider width for last `n` months
                column_widths = {month: (last_n_width if i >= len(months_list) - self.number_of_months_displayed else default_column_width)
                                 for i, month in enumerate(months_list)}
            
                # Apply column order and update headers
                date_tree["columns"] = months_list
                for col in months_list:
                    date_tree.heading(col, text=self.formatMonthLastDayYear(col[0], col[1]), anchor=tk.CENTER, command=lambda c=col: showMonthlyCategoryBreakdown(c))
                    date_tree.column(col, width=column_widths[col], anchor=tk.E, stretch=tk.NO)
            
                # Clear previous table content
                self.clearTreeview(date_tree)

                # Repopulate the Treeview with formatted data
                tag = 'oddrow'
                
                for i, cat in enumerate(categories):
                    if cat in summary_df.columns:
                        row = summary_df[cat].tolist()
                    else:
                        row = [0]*self.number_of_months_displayed
                        
                    formatted_row = [f"${val/100.:,.2f}" if isinstance(val, (int, float)) else val for val in row]

                    # Reverse row order if self.switch_monthly_order is enabled
                    if self.switch_monthly_order:
                        formatted_row.reverse()
                        
                    if not self.switch_monthly_order:
                        formatted_row = formatted_row[-self.number_of_months_displayed:]
                    else:
                        formatted_row = formatted_row[:self.number_of_months_displayed]
            
                    # Maintain alternating row colors
                    tag = "oddrow" if tag == "evenrow" else "evenrow"
            
                    # Insert row into the Treeview
                    date_tree.insert("", tk.END, values=formatted_row, tags=(tag,))
                
                # Reapply row styles
                for t in (date_tree, category_tree):
                    t.tag_configure("oddrow", background=self.banded_row[0])
                    t.tag_configure("evenrow", background=self.banded_row[1])
                    
                return
            
            def reverseOrder(event=None, tree='', months_list=[]):
                """Reverses the column order and updates the balance_tree while preserving formatting."""
                
                col_id = tree.identify_column(event.x)  # Identify which column was clicked
                row_id = tree.identify_row(event.y)     # Identify which row was clicked
            
                # If row_id is empty, then it's a header click
                if not row_id and col_id != "#0":
                
                    # Toggle the switch_monthly_order variable
                    self.switch_monthly_order = not self.switch_monthly_order
                    months_list.reverse()  # Reverse the column order
                    
                    # Call populateBalanceTree to apply changes
                    populateBalanceTree(date_tree, summary_df, months_list, categories)
                
                return
                
            def onMouseWheel(event, tree, account_tree):
                """ Mouse wheel scrolling - improves speed"""
                if event.state & 0x0001:  # Shift key pressed (for horizontal scroll)
                    tree.xview_scroll(int(-1 * (event.delta / 5)), "units")
                else:  # Default vertical scroll
                    account_tree.yview_scroll(int(-1 * (event.delta / 5)), "units")
                    tree.yview_scroll(int(-1 * (event.delta / 5)), "units")
                return
            
            def changeMonthsDisplayed(balance_tree, account_tree, months_list):
                """Modify the number of months displayed using a slider and entry box."""
                
                top = tk.Toplevel(self)
                top.title("Select Number of Months to Display")
                self.openRelativeWindow(top, width=350, height=200)
                top.resizable(False, False)
            
                tk.Label(top, text="Select Number of Months to Display:", font=(self.font_type, self.font_size)).pack(pady=10)
            
                # Slider (Scale) to select number of months
                slider = tk.Scale(top, from_=1, to=len(months_list), orient="horizontal", length=250, 
                                  tickinterval=3, resolution=1)
                slider.set(self.number_of_months_displayed)
                slider.pack()
            
                # Entry Box for direct input
                entry_var = tk.StringVar(value=str(self.number_of_months_displayed))
                entry_box = ttk.Entry(top, textvariable=entry_var, width=5)
                entry_box.pack(pady=5)
            
                def updateMonths():
                    """Update number_of_months_displayed and refresh table."""
                    try:
                        value = int(entry_var.get())  # Get number from entry box
                        if 1 <= value <= len(self.all_months):
                            self.number_of_months_displayed = value
                            populateBalanceTree(date_tree, summary_df, months, categories)  # Refresh the table
                            top.destroy()  # Close window
                        else:
                            #TODO Change to an error message
                            messagebox.showwarning("Warning", f"Invalid range: Must be between 1 and {len(self.all_months)} months")
                    except ValueError:
                        messagebox.showwarning("Warning", "Invalid input: Enter a number")
            
                # Apply Button
                apply_btn = ttk.Button(top, text="Apply", command=updateMonths)
                apply_btn.pack(pady=10)
            
                # Link slider and textbox
                def syncSlider(event):
                    entry_var.set(str(slider.get()))
            
                def syncEntry(event):
                    try:
                        value = int(entry_var.get())
                        if 1 <= value <= len(self.all_months):
                            slider.set(value)
                    except ValueError:
                        pass  # Ignore invalid input
                        
                def exitWindow(event=None):
                    top.destroy()
                            
                # Bind Escape keys
                top.bind("<Escape>", exitWindow)
            
                slider.bind("<Motion>", syncSlider)  # Sync entry box when moving slider
                entry_box.bind("<KeyRelease>", syncEntry)  # Sync slider when typing
                
                entry_box.focus_set()
            
                top.mainloop()
                
                return
            
            def showColumnMenu(event=None, date_tree=ttk.Treeview, category_tree=ttk.Treeview, months_list=[]):
                """ Open column menu """
                menu = tk.Menu(self, tearoff=0)
                
                menu.add_command(label="Reverse Order", command=lambda: reverseOrder(event, date_tree, months_list))
                menu.add_command(label="Change Displayed Months", command=lambda: changeMonthsDisplayed(date_tree, category_tree, months_list))
                
                menu.post(event.x_root, event.y_root)
            
            # Clear the main frame before displaying the table
            self.clearMainFrame()
            
            df_label = ttk.Label(self.main_frame, text=df_type, font=(self.font_type, self.font_size+2, "bold"))
            df_label.pack(expand=False, fill=tk.NONE, padx=10, pady=(5, 2), anchor="center")
        
            # Create a parent frame for both tables
            table_frame = ttk.Frame(self.main_frame)
            table_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
            
            # Extract month-year columns
            months = self.all_months.copy()
            
            # Ensure Date column is in datetime format    
            df["Date"] = pd.to_datetime(df["Date"])
            
            # Set Date as the index
            df.set_index("Date", inplace=True)  
            
            summary_df = (df.groupby([pd.Grouper(freq="ME"), "Category"])["Amount"].sum().unstack(fill_value=0))
            
            # Reverse order if switch_monthly_order is enabled
            if self.switch_monthly_order:
                months.reverse()
        
            # Create Treeview for Account column
            category_tree = ttk.Treeview(table_frame, columns=["Categories"], show="headings", selectmode="none", height=15)
            category_tree.heading("Categories", text="Categories", anchor=tk.W)
            category_tree.column("Categories", width=200, anchor=tk.W, stretch=tk.NO)
            category_tree.pack(side=tk.LEFT, fill=tk.Y)
        
            # Create a frame for the main Treeview and scrollbar
            data_frame = ttk.Frame(table_frame)
            data_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
            # Create horizontal scrollbar
            x_scroll = ttk.Scrollbar(data_frame, orient=tk.HORIZONTAL)
            x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
            # Create main Treeview for balance table
            date_tree = ttk.Treeview(
                data_frame, 
                columns=months, 
                show="headings", 
                selectmode="none",
                xscrollcommand=x_scroll.set,
                height=15
            )
            
            date_tree.pack(expand=True, fill=tk.BOTH)
        
            # Link scrollbar
            x_scroll.config(command=category_tree.xview)
        
            # Populate the date tree
            tag = 'oddrow'
            for cat in categories:
                tag = "oddrow" if tag == "evenrow" else "evenrow"
                category_tree.insert("", tk.END, values=[cat], tags=(tag,))
        
            # Populate the balance tree using the helper function
            populateBalanceTree(date_tree, summary_df, months, categories)
        
            # Bind mouse scrolling events
            date_tree.bind("<MouseWheel>", lambda event: onMouseWheel(event, date_tree, category_tree))
            category_tree.bind("<MouseWheel>", lambda event: onMouseWheel(event, date_tree, category_tree))
            
            category_tree.bind("<Button-1>", lambda event: reverseOrder(event, date_tree, months))
            category_tree.bind("<Button-3>", lambda event: showColumnMenu(event, date_tree, category_tree, months))
        
            # Keep the window size dynamic
            window_height = max(len(categories) * 30, 400)
            window_width = min(int(200 + 110 * len(self.all_months) * 2), 1200)
            self.geometry(f"{window_width}x{window_height}")
            self.resizable(True, True)
            
            return
    
        # Get respective dataframe
        if type_of_data == 'inc':
            if self.current_window == 'Spending':
                return
            df = self.income_data.copy()
            df_type = 'INCOME'
            self.current_window = 'Spending'
            
        else:
            if self.current_window == 'Savings':
                return
            df = self.expenses_data.copy()
            df_type = 'EXPENSES'
            self.current_window = 'Savings'
            
        # Clear the main frame before populating the table
        self.clearMainFrame()
            
        # Get list of categories
        cat_list, _ = self.getCategoryTypes(type_of_data)
        
        # Get list of months
        self.all_months = self.generateMonthYearList(self.new_date_range[0], self.new_date_range[1])
        self.number_of_months_displayed = len(self.all_months)
        
        displayStatisticsSummary(df.copy(), cat_list, df_type)
    
        return
    
    def showSpending(self, event=None) -> None:
       """
        Displays the Spending Breakdown section.

        This method calls `showStatistics` with `type_of_data='exp'` 
        to present an analysis of expenses.
        
        Parameters:
        event (tkinter event, optional): Event trigger (default is None).
        """
       self.showStatistics(type_of_data='exp')
       
    def showSavings(self, event=None) -> None:
       """
        Displays the Savings Breakdown section.

        This method calls `showStatistics` with `type_of_data='inc'` 
        to present an analysis of income.
        
        Parameters:
        event (tkinter event, optional): Event trigger (default is None).
        """
       self.showStatistics(type_of_data='inc')
    
    def showInvestments(self, event=None) -> None:
        """Show Investments section."""
        #TODO
        self.current_window = 'Investments'
        self.clearMainFrame()
        label = ttk.Label(self.main_frame, text="Investments", font=("Arial", 14, "bold"))
        label.pack(pady=20)
        
    def showMainFrame(self, event=None, start_fresh=True) -> None:
        """
        Displays the mainframe with income and expense tables.

        It loads fresh copies of the stored income and expenses data.

        Parameters:
        event (tkinter event, optional): Event trigger (default is None).
        start_fresh (bool, optional): Flag indicating whether to refresh data (default is True).
        """
        self.displayIncExpTables(self.income_data.copy(), self.expenses_data.copy())
    
    def clearMainFrame(self) -> None:
        """
        Clears all widgets from the main frame.

        This method removes all child widgets from `self.main_frame`
        to prepare it for a new view.
        """
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
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
    
    def updateData(self) -> None:
        """
        Updates the financial data based on CSV files.
    
        This method triggers `selectFilesAndFolders` with `update=True`,
        ensuring that the data is refreshed with the latest available files.
        """
        self.selectFilesAndFolders(update=True)

    def selectFilesAndFolders(self, event=None, reload=False, update=False):
        """Open file dialog to select csv or pkl file(s)"""
        
        #TODO Doc strings
        
        def loadCSVFile(file):
            """
            Load financial data from a CSV file and categorize transactions 
            into income and expenses based on account type.
            
            Parameters:
                file (str): Path to the CSV file.
        
            Returns:
                tuple: (income_df, expense_df) - DataFrames for income and expenses.
            """
            file_name = file.split("/")[-1]
        
            def readAFCU(file, file_name):
                """Reads and processes AFCU CSV file."""
                df = pd.read_csv(file).fillna(0)
        
                # Drop rows where all values are zero
                df = df.loc[~(df == 0).all(axis=1)]
        
                # Drop 'No.' column if it exists
                df = df.drop(columns=['No.'], errors='ignore')
        
                # Separate into income and expense
                inc_df = df[df['Debit'] == 0.00].drop(columns=['Debit']).rename(columns={'Credit': 'Amount'})
                exp_df = df[df['Credit'] == 0.00].drop(columns=['Credit']).rename(columns={'Debit': 'Amount'})
        
                # Apply common transformations
                for new_df in [inc_df, exp_df]:
                    new_df['Account'] = file_name.replace(".csv", "")
                    new_df['Category'] = ""
                    new_df['Amount'] = abs(new_df['Amount'])
        
                return inc_df, exp_df
        
            def readPFCU(file, file_name):
                """Reads and processes PFCU CSV file."""
                df = pd.read_csv(file).fillna(0)
        
                # Drop rows where all values are zero
                df = df.loc[~(df == 0).all(axis=1)]
        
                # Select correct date column
                if 'credit' in file_name.lower():
                    df = df.rename(columns={'Posted Date': 'Date'}).drop(columns=['Transaction Date'], errors='ignore')
                else:
                    df = df.rename(columns={'Transaction Date': 'Date'}).drop(columns=['Posted Date'], errors='ignore')
        
                # Drop 'Balance' column
                df = df.drop(columns=['Balance'], errors='ignore')
        
                # Convert money format to float
                df['Amount'] = df['Amount'].replace({'\$': '', ',': '', '\(': '-', '\)': ''}, regex=True).astype(float)
        
                # Reverse sign for credits (since they're recorded as negative)
                if 'credit' in file_name.lower():
                    df['Amount'] *= -1
                    
                df['Account'] = file_name.replace(".csv", "")
                df['Category'] = ""
        
                # Split into income (positive) and expenses (negative)
                inc_df = df[df['Amount'] > 0].copy() 
                exp_df = df[df['Amount'] < 0].copy()
                
                # Split into income (positive) and expenses (negative)
                inc_df['Amount'] = inc_df['Amount'].abs() 
                exp_df['Amount'] = exp_df['Amount'].abs()
        
                return inc_df, exp_df
        
            def readCapitalOne(file, file_name):
                """Reads and processes Capital One CSV file."""
                df = pd.read_csv(file).fillna(0)
        
                # Drop rows where all values are zero
                df = df.loc[~(df == 0).all(axis=1)]
        
                # Drop irrelevant columns
                df = df.drop(columns=['Card No.', 'Posted Date'], errors='ignore')
        
                # Standardize date column
                df = df.rename(columns={'Transaction Date': 'Date'})
        
                # Separate into income and expense
                inc_df = df[df['Debit'] == 0.00].drop(columns=['Debit']).rename(columns={'Credit': 'Amount'})
                exp_df = df[df['Credit'] == 0.00].drop(columns=['Credit']).rename(columns={'Debit': 'Amount'})
        
                # Apply common transformations
                for new_df in [inc_df, exp_df]:
                    new_df['Account'] = file_name.replace(".csv", "")
                    new_df['Category'] = ""
                    new_df['Amount'] = abs(new_df['Amount'])
        
                    # Ensure 'Category' column is in the 4th position
                    category_col = new_df.pop('Category')
                    new_df.insert(4, 'Category', category_col)
        
                return inc_df, exp_df
        
            # Determine which function to use based on the file name
            if file_name.startswith("AFCU"):
                income, expenses = readAFCU(file, file_name)
            elif file_name.startswith("Capital One"):
                income, expenses = readCapitalOne(file, file_name)
            elif file_name.startswith("PFCU"):
                income, expenses = readPFCU(file, file_name)
            else:
                raise ValueError(f"Unsupported file type: {file_name}")
        
            # Convert amounts to cents (integers)
            income["Amount"] = (income["Amount"] * 100).round().astype(int)
            expenses["Amount"] = (expenses["Amount"] * 100).round().astype(int)
        
            return income, expenses                   
        
        def loadPickleFile(file):
            """
            Load financial data from a pickle (.pkl) file.
        
            Parameters:
                file (str): Path to the pickle file.
        
            Returns:
                tuple:
                    pd.DataFrame: Income transactions.
                    pd.DataFrame: Expense transactions.
                    pd.DataFrame: Initial balance data.
            """
            with open(file, "rb") as f:
                yearly_data = pickle.load(f)

            return yearly_data['Income'], yearly_data['Expenses'], yearly_data['Initial']
        
        def loadXLSXFile(file):
            """
            Load financial data from an Excel (.xlsx) file.
        
            This function:
                Reads 'Income', 'Expenses', and 'Starting Balance' sheets, removing unnecessary columns.
        
            Parameters:
                file (str): Path to the Excel file.
        
            Returns:
                tuple:
                    pd.DataFrame: Income transactions.
                    pd.DataFrame: Expense transactions.
                    pd.DataFrame: Initial balance data.
            """
            sheets = ['Income', 'Expenses', 'Starting Balance']
            data = {sheet: pd.read_excel(file, sheet_name=sheet).drop(columns=["Unnamed: 0"], errors='ignore') for sheet in sheets}
        
            return data['Income'], data['Expenses'], data['Starting Balance']
        
        def compareOldAndNewDF(df1, df2):
            """
            Compare two DataFrames and return rows in df1 that are not present in df2.
        
            This function:
                - Removes the 'Category' column from df1 if present.
                - Converts the 'Date' column to a consistent date format.
                - Drops 'Category' and 'Index' columns from df2 if present.
                - Identifies rows unique to df1.
        
            Parameters:
                df1 (pd.DataFrame): First DataFrame (typically the new dataset).
                df2 (pd.DataFrame): Second DataFrame (typically the older dataset for comparison).
        
            Returns:
                pd.DataFrame: Rows from df1 that are not present in df2.
            """
            # Drop 'Category' from df1 if present
            df1 = df1.drop(columns=['Category'], errors='ignore')
        
            # Convert 'Date' column to datetime and retain only the date part
            df1['Date'] = pd.to_datetime(df1['Date'], dayfirst=False, format='mixed').dt.date
        
            # Drop 'Category' and 'Index' from df2 if they exist
            df2 = df2.drop(columns=[col for col in ['Category', 'Index'] if col in df2.columns], errors='ignore')
        
            # Identify rows in df1 that are not present in df2
            return df1.loc[~df1.apply(tuple, axis=1).isin(df2.apply(tuple, axis=1))]
        
        def addNewValuesToDF(df1, df2):
            """
            Combine two DataFrames while preserving category information.
        
            This function:
                - Concatenates df1 and df2.
                - Drops the 'Index' column if present.
        
            Parameters:
                df1 (pd.DataFrame): First DataFrame.
                df2 (pd.DataFrame): Second DataFrame.
        
            Returns:
                pd.DataFrame: Merged DataFrame with all unique rows.
            """
            merged_df = pd.concat([df1, df2], ignore_index=True).drop(columns=['Index'], errors='ignore')
            
            return merged_df               
        
        # Reading in an updated csv file to add only new info and not lose old category information
        if update and not self.income_data.empty and not self.expenses_data.empty:
            filetypes = [("CSV Files", "*.csv")]
            
            data_files = filedialog.askopenfilenames(title="Select Files", filetypes=filetypes)
            
            if len(data_files) != 0:
                for data_file in data_files:
                    inc, exp = loadCSVFile(data_file)
                    
                    new_inc = compareOldAndNewDF(inc, self.income_data.copy())
                    new_exp = compareOldAndNewDF(exp, self.expenses_data.copy())
                    
                    if not new_inc.empty:
                        self.income_data = addNewValuesToDF(self.income_data.copy(), new_inc)
                    if not new_exp.empty:
                        self.expenses_data = addNewValuesToDF(self.expenses_data.copy(), new_exp)
                    
                self.current_window = ''
                self.setupDataFrames()
                    
            return
        
        # Function to reload the last save file
        if reload:
            try:
                with open(self.last_saved_file, 'r') as f:
                    data_files = f.readlines()
                if os.path.exists(data_files[0]):   
                    self.income_data    = pd.DataFrame()
                    self.expenses_data  = pd.DataFrame()
                else:
                    reload = False
            except:
                reload = False
            
        if not reload:
            filetypes = [("Pickle Files", "*.pkl"), 
                         ("Excel Files", "*.xlsx"), 
                         ("CSV Files", "*.csv")]
            
            filetypes = filetypes[::-1]
                
            data_files = filedialog.askopenfilenames(title="Select Files", filetypes=filetypes)       
        
        if len(data_files) != 0:
            for data_file in data_files:
                if data_file.endswith(".pkl"):
                    inc, exp, self.starting_data = loadPickleFile(data_file)
                elif data_file.endswith(".xlsx"):
                    inc, exp, self.starting_data = loadXLSXFile(data_file)
                else:
                    inc, exp = loadCSVFile(data_file)
                
                self.income_data    = pd.concat([self.income_data, inc], ignore_index=False)
                self.expenses_data  = pd.concat([self.expenses_data, exp], ignore_index=False)
                    
                self.data_files.append(data_file)
                    
            self.setupDataFrames()
               
        else:
            messagebox.showinfo("Error", message = "No File Selected")
            
        return        
    
    def setupDataFrames(self):
        """Format the expenses and income dataframes and also setup initial variables/lists"""
        
        #TODO Docstrings
        
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
        
        def findMismatchedCategories(df, df_type):
            """Add an asterisk to categories not found in the categories list"""
            cat_list, _ = self.getCategoryTypes(df_type)
            df['Category'] = df['Category'].astype(str).apply(lambda x: f"*{x}" if x.strip() not in map(str.strip, map(str, cat_list)) else x)
            return df
        
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
        self.income_data    = removeEmptyAmounts(self.income_data)
        self.expenses_data  = removeEmptyAmounts(self.expenses_data)
        
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
        
        # Determine list of categories:
        self.inc_categories, _ = self.getCategoryTypes(name='inc')
        self.exp_categories, _ = self.getCategoryTypes(name='exp')
        
        self.new_inc_categories = self.inc_categories.copy()
        self.new_exp_categories = self.exp_categories.copy()        
        
        # Fill in empty entries in the Category column 
        self.income_data["Category"]    = self.income_data["Category"].replace(["", None, np.nan], "Not Assigned")
        self.expenses_data["Category"]  = self.expenses_data["Category"].replace(["", None, np.nan], "Not Assigned")
        
        # Find category values that dont' match the category lists
        self.income_data    = findMismatchedCategories(self.income_data, df_type='inc')
        self.expenses_data  = findMismatchedCategories(self.expenses_data, df_type='exp')
        
        # Generate the dataframe of starting balances
        for account in self.accounts:
            if account not in self.starting_data.columns:
                self.starting_data[account] = [0]
            
        # Display the dataframes        
        self.displayIncExpTables(self.income_data.copy(), self.expenses_data.copy())  
        
        return    
    
    def reloadData(self) -> None:
        """
        Reloads financial data by triggering the file selection function.
    
        This function clears the current window and reloads data files.
    
        Retuns:
            None
        """
        self.current_window = ''
        self.selectFilesAndFolders(reload=True)
    
    def saveState(self) -> None:
        """
        Saves financial data based on the last saved file format.
    
        - If the last saved file is a `.pkl`, saves as a Pickle file.
        - If the last saved file is a `.xlsx`, saves as an Excel file.
        - If the last saved file is in CSV format (5 lines), saves as CSV.
        - If no valid file is found, prompts the user.
        
        Retuns:
            None
        """ 
        
        try:
            with open(self.last_saved_file, 'r') as ff:
                file_lines = ff.readlines()
    
            if len(file_lines) == 1:
                file_name = file_lines[0].strip()
                if file_name.endswith(".pkl"):
                    self.saveToPickleFile(file_name)
                elif file_name.endswith(".xlsx"):
                    self.saveToXLSX(file_name)
            elif len(file_lines) == 5:
                self.saveToCSV(file_lines)
            else:
                messagebox.showinfo("Message", "No data to save")
        except FileNotFoundError:
            messagebox.showinfo("Message", "No previously saved file found.")
        
    def saveStateAs(self) -> None:
        """
        Saves financial data with user-specified file format.
    
        Prompts the user to select a save location and file format (`.xlsx`, `.pkl`, `.csv`).
        
        Retuns:
            None
        """
        filetypes = [
            ("Excel Files", "*.xlsx"),
            ("Pickle Files", "*.pkl"),
            ("CSV Files", "*.csv"),
        ]
        
        file_name = filedialog.asksaveasfilename(
            title="Select Files",
            filetypes=filetypes,
            defaultextension=".xlsx"
        )
    
        if file_name:
            self.sendToSaveFile(file_name)
    
    def sendToSaveFile(self, file_name: str) -> None:
        """
        Saves data to a file, choosing the correct format.
    
        Parameters:
            file_name: The file path where data should be saved.
        
        Retuns:
            None
        """
        if file_name.endswith(".pkl"):
            self.saveToPickleFile(file_name)
        elif file_name.endswith(".xlsx"):
            self.saveToXLSX(file_name)
        elif file_name.endswith(".csv"):
            self.saveToCSV(file_name)
    
    def saveToXLSX(self, file_name: str) -> None:
        """
        Saves financial data to an Excel (.xlsx) file.
    
        Parameters:
            file_name: The file path for saving.
        
        Retuns:
            None
        """
        data_frames = [self.income_data, self.expenses_data, self.starting_data]
        sheet_names = ['Income', 'Expenses', 'Starting Balance']
    
        try:
            with pd.ExcelWriter(file_name) as writer:
                for df, sheet_name in zip(data_frames, sheet_names):
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
    
            messagebox.showinfo("File Saved", f"Data successfully saved to \n{file_name}")
            self.updateLastSavedFile(file_name)
    
        except Exception as e:
            messagebox.showinfo("File Not Saved", f"Error - Data not saved to \n{file_name}\n\n{str(e)}")
    
    def saveToCSV(self, file_name: Union[str, List[str]]) -> None:
        """
        Saves financial data to CSV files.
    
        If the provided file name is a list (legacy behavior), extracts the directory and base name from the first item.
    
        Parameters:
            file_name: The file path or list of file paths.
        
        Returns:
            None
        """
        
        try:
            if type(file_name) == str:
                dir_base = "/".join(file_name.split("/")[:-1])
                file_base = file_name.split("/")[-1].split(".")[0]
            else:
                dir_base = "/".join(file_name[0].split("/")[:-1])
                file_base = file_name[0].split("/")[-1].split("_")[0]
            
            list_dfs = [self.income_data, self.expenses_data, self.starting_data]
            type_names = ['Income', 'Expenses', 'Starting Balance']
            file_names = []
            
            try:
                for idx, df in enumerate(list_dfs):
                    file_path = os.path.join(dir_base, file_base + "_" + type_names[idx] + ".csv")
                    df.to_csv(file_path, index=False)
                    file_names.append(file_path)
                    
                all_file_names = "\n\n".join(file_names)
                messagebox.showinfo("Files Saved", f"Data successfully saved to \n\n{all_file_names}")
                
                self.updateLastSavedFile(all_file_names)
                
            except:
                messagebox.showinfo("File Not Saved", f"Error - Data not saved to \n{file_name}")     
    
        except Exception as e:
            messagebox.showinfo("File Not Saved", f"Error - Data not saved to \n{file_name}\n\n{str(e)}")
        
    def saveToPickleFile(self, file_name: str) -> None:
        """
        Saves financial data to a Pickle (.pkl) file.
    
        Parameters:
            file_name: The file path for saving.
        
        Returns:
            None
        """
        yearly_data = {
            'Income': self.income_data,
            'Expenses': self.expenses_data,
            'Initial': self.starting_data,
        }
    
        try:
            with open(file_name, "wb") as f:
                pickle.dump(yearly_data, f)
    
            messagebox.showinfo("File Saved", f"Data successfully saved to \n{file_name}")
            self.updateLastSavedFile(file_name)
    
        except Exception as e:
            messagebox.showinfo("File Not Saved", f"Error - Data not saved to \n{file_name}\n\n{str(e)}")

    def updateLastSavedFile(self, file_name):
        """
        Updates the record of the last saved file.
    
        Parameters:
            file_name: The file path that was last successfully saved.
        
        Results:
            None
        """
        try:
            with open(self.last_saved_file, "w") as f:
                f.write(file_name)
        except Exception as e:
            messagebox.showinfo("Error", f"Could not update last saved file: \n\n{str(e)}")        

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
            frame.grid(row=row, column=0, sticky='nsew', pady=2)
            
            # Ensure frame expands properly
            self.main_frame.grid_rowconfigure(row, weight=1)
            self.main_frame.grid_columnconfigure(0, weight=1)
        
            columns = list(df.columns)
            tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
            
            if df_name == 'inc':
                self.income_data_tree = tree
            else:
                self.expenses_data_tree = tree
            
            self.clearTreeview(tree)
            
            # Create Scrollbars
            y_scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=y_scrollbar.set)
            
            # Set configuration on screen with grid
            y_scrollbar.grid(row=0, column=1, sticky='ns')
            tree.grid(row=0, column=0, sticky='nsew')
            
            # Make sure frame columns and rows expand with the window
            frame.grid_columnconfigure(0, weight=1)
            frame.grid_rowconfigure(0, weight=1)
        
            # Define preset column widths
            column_widths = {
                "Index": 70,
                "Date": 120,
                "Description": 500,
                "Amount": 110,
                "Account": 150,
                "Category": 150
            }
            
            if self.hide_index:
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

            # Get category list
            cat_list, cat_file = self.getCategoryTypes(df_name)    
            
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
                        self.sortIncExpTable(tree, 'Category', df, False)
                    
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
                
            def updateTableSizes(event):
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
        
        # Populate teh income tree/table
        expenses_label = ttk.Label(self.main_frame, text="INCOME", font=(self.font_type, self.font_size+2, "bold"))
        expenses_label.grid(row=2, column=0, sticky="n", pady=2)
        showTable(inc.copy(), 'inc')
        
        self.current_window = 'All Data'
        
        return 

    def getCategoryTypes(self, name: str) -> Tuple[List[str], str]:
        """
        Retrieves category types from the appropriate file.
    
        Parameters:
            name (str): If 'inc', loads income categories; otherwise, loads spending categories.
    
        Returns:
            Tuple[List[str], str]: A sorted list of category names and the full path to the category file.
        """
        file_name = "IncomeCategories.txt" if name == 'inc' else "SpendingCategories.txt"
        cat_file = os.path.join(os.path.dirname(__file__), file_name)
        
        with open(cat_file) as ff:
            categories = [cat.strip() for cat in ff.readlines()]  # Strip newline characters

        return sorted(categories), cat_file     
   
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
    
    def openRelativeWindow(self, new_window, width: int, height: int) -> None:
        """
        Positions the new window relative to the main application window.
    
        This ensures that the new window appears slightly offset from the main window.
    
        Parameters:
            new_window: The new Tkinter window to be positioned.
            width (int): The width of the new window.
            height (int): The height of the new window.
    
        Returns:
            None
        """
        # Get the main window's position
        main_x = self.winfo_x()
        main_y = self.winfo_y()
    
        # Position new window slightly offset from the main window
        new_x = main_x + 50
        new_y = main_y + 50
    
        new_window.geometry(f"{width}x{height}+{new_x}+{new_y}")  # Format: "WIDTHxHEIGHT+X+Y"
    
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
        
        col_id = table.identify_column(event.x)
        col_name = table.heading(col_id, "text")
        
        menu = tk.Menu(self, tearoff=0)
        
        if col_name != 'Index':
            menu.add_command(label=f"Sort {col_name} Ascending", command=lambda: self.sortIncExpTable(table, col_name, df, True))
            menu.add_command(label=f"Sort {col_name} Descending", command=lambda: self.sortIncExpTable(table, col_name, df, False))
        
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

    def sortIncExpTable(self,  table: tk.Widget, column_name: str, df: pd.DataFrame, sort_direction: Union[int, bool]) -> None:
        """
        Sorts the income/expense table by a selected column, reversing order on each click.
    
        - If the column was previously sorted, clicking again reverses the order.
        - If sorting for the first time, it determines the initial order based on current data.
        - Applies sorting based on primary column and fallback order on 'Date', 'Amount', 'Account', 'Category'.
        - Updates the table display after sorting.
        - Applies alternating row colors for readability.
    
        Parameters:
            table (tk.Widget): The Treeview table to update after sorting.
            column_name (str): The column to sort by.
            df (pd.DataFrame): The DataFrame containing the table data.
            sort_direction (Union[int, bool]): Sorting order (0 for auto-detect, True for ascending, False for descending).
    
        Returns:
        None
        """
        
        # Prevent redundant sorting
        if self.current_sort == column_name and sort_direction != self.sort_orders.get(column_name, True):
            return
        
        # Determine initial sorting direction if unspecified (0)
        #TODO FIX SORT
        if type(sort_direction) == int:
            last_sort = self.sort_orders.get(column_name, None)
            
            if last_sort is None:
                sort_direction = True
            else:
                sort_direction = not self.sort_orders[column_name]
        
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
            
        self.current_sort = column_name
            
        return

if __name__ == "__main__":
    app = FinanceTracker()
    app.mainloop()