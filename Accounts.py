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

from Utility import Utility

class Accounts(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        
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
            text = Utility.formatMonthYear(month, year)
            top.title(f"{text} Account Breakdown")
        
            # Create a Treeview for displaying breakdown data
            tree = ttk.Treeview(top, columns=["Account", "Start Balance", "Total Income", "Total Expenses", 
                                  "Net Cash Flow", "Ending Balance", "Savings Rate (%)"], 
                    show="headings", selectmode="none")
            
            # Apply standard formatting for table
            style = ttk.Style()
            Tables.tableStyle(style)
        
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
                    ax.plot([date, date], [old_value, new_amount], linestyle=(0, (5, 2, 1, 2)), color=color)
                    
                    # Horizontal step (date change)
                    if date != old_date and i < len(all_dates):
                        ax.plot([old_date, date], [old_value, old_value], linestyle=(0, (5, 2, 1, 2)), color='purple')
                        
                    ax.scatter(date, new_amount, color=color, marker='o', s=50, zorder=4)
                    
                    
                    step_dates.append(all_dates[i])
                    step_balances.append(balances[i])  # Balance after transaction
                    step_values.append({"Date": date, 
                                        "Description": description,
                                        "Category": category, 
                                        "Amount": value, 
                                        "Balance": new_amount})
                                    
                # End with the ending balance after the last transaction
                ax.plot([date, ending_date], [ending_balance, ending_balance], linestyle=(0, (5, 2, 1, 2)), color='purple')
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
            
            def resetView(event=None):
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
            toolbar.home = resetView
            
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
            Windows.openRelativeWindow(top, main_width=self.winfo_x(), main_height=self.winfo_y(), width=window_width, height=window_height)
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
                Tables.tableStyle(style)
            
                # Define column widths dynamically (ensures consistency)
                default_column_width = 140  # Default width
                last_n_width = 140  # Wider width for last `n` months
                column_widths = {month: (last_n_width if i >= len(months_list) - self.number_of_months_displayed else default_column_width)
                                 for i, month in enumerate(months_list)}
            
                # Apply column order and update headers
                tree["columns"] = months_list
                for col in months_list:
                    tree.heading(col, text=Utility.formatMonthLastDayYear(col[0], col[1]), anchor=tk.CENTER, command=lambda c=col: showMonthBreakdown(c))
                    tree.column(col, width=column_widths[col], anchor=tk.E, stretch=tk.NO)
            
                # Clear previous table content
                Tables.clearTable(tree)
            
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
                Windows.openRelativeWindow(top, main_width=self.winfo_x(), main_height=self.winfo_y(), width=350, height=200)
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
        self.all_months = Utility.generateMonthYearList(self.new_date_range[0], self.new_date_range[1])
        self.number_of_months_displayed = min(len(self.all_months),12)
        
        # Get initial balances
        initial_balances = self.starting_data.copy()
        
        # Load initial balances from a file
        account_summary = monthlyBalances()
        
        # Display the datatable
        displayAccountSummary(account_summary.copy(), initial_balances.copy())
        
        self.current_window = 'Monthly Breakdown'
        
        return