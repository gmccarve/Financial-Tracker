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

class Statistics(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        
    def showStatistics(self, event=None, df_type='inc'):
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

                def treeviewSortColumn(tv, col, reverse):
                    """Sorts a Treeview column properly, handling currency values and reapplying row colors."""

                    def convertValue(val):
                        """Converts currency values ($XXX.XX) to float for sorting."""
                        try:
                            return float(val.replace("$", "").replace(",", "").replace("%", ""))  # Remove $ and convert to float
                        except ValueError:
                            return val  # Return as-is if not convertible (handles text columns)
                
                    # Get values and sort correctly
                    l = [(convertValue(tv.set(k, col)), k) for k in tv.get_children('')]
                    l.sort(reverse=reverse)
                
                    # Rearrange items in sorted order
                    for index, (val, k) in enumerate(l):
                        tv.move(k, '', index)
                
                    # Reapply banded row styling
                    applyBandedRows(tv)
                
                    # Reverse sort next time
                    tv.heading(col, command=lambda: treeviewSortColumn(tv, col, not reverse))
                    
                def applyBandedRows(tv):
                    """Recolors Treeview rows to maintain alternating row stripes after sorting."""
                    for index, row in enumerate(tv.get_children('')):
                        tag = "evenrow" if index % 2 == 0 else "oddrow"
                        tv.item(row, tags=(tag,))
                
                    # Define colors for tags
                    tv.tag_configure("evenrow", background=self.banded_row[0])
                    tv.tag_configure("oddrow", background=self.banded_row[1])                  
                    
                # Determine the index of the selected month
                month, year = month_name[0], month_name[1]
            
                # Create a popup window
                top = tk.Toplevel(self)
                try:
                    top.state("zoomed")
                except:
                    top.attributes("-zoomed", True)
                text = Utility.formatMonthYear(month, year)
                
                if df_type == 'INCOME':
                    text = text + " Savings"
                else:
                    text = text + " Spending"
                top.title(f"{text} Breakdown")
                
                columns =  ["Category", 
                            "Total Spent", 
                            "Number of\nTransactions", 
                            "Largest\nTransaction",
                            "Smallest\nTransaction", 
                            "Category\nPercentage (%)"]
            
                # Create a Treeview for displaying breakdown data
                category_tree = ttk.Treeview(top, columns=columns, show="headings", selectmode="none", height=5)
                
                # Apply standard formatting for table
                style = ttk.Style()
                Tables.tableStyle(style)
            
                # Column settings
                small_width, large_width = 140, 180
                column_widths = {}
                for col in columns:
                    if col == "Category":
                        column_widths[col] = large_width
                    else:
                        column_widths[col] = small_width

                # get minimum size of window
                window_width = (sum(column_widths.values()) + 20)
                            
                for col in category_tree["columns"]:
                    category_tree.heading(col, text=col, anchor="center", command=lambda c=col: treeviewSortColumn(category_tree, c, False))
                    width = column_widths.get(col, small_width)
                    category_tree.column(col, width=width, anchor=tk.E if col != "Category" else tk.W, stretch=tk.NO)
            
                # Compute min/max/transaction counts
                if df_type == "inc":
                    totals = computeMonthlyStats(self.income_data.copy())
                else:
                    totals = computeMonthlyStats(self.expenses_data.copy())
                    
                # Total value for month
                total_overall = totals['Amount'].sum()
                
                #TODO add table next to piechart that shows all transaction for a clicked on category

                for category in categories:
                    
                    category_data  = totals[totals['Category'] == category]
                    
                    # Get useful breakdown values
                    total = category_data['Amount'].sum()
                    
                    if total == 0.00:
                        num_transactions = 0
                        largest_transaction = 0
                        smallest_transaction = 0
                        category_percentage = 0
                        
                    else:
                        num_transactions = category_data.shape[0]
                        largest_transaction = category_data['Amount'].max()
                        smallest_transaction = category_data['Amount'].min()
                        category_percentage = (total / total_overall) * 100 if total_overall != 0 else 0  # Avoid division by zero
                    
                    # Format and insert data
                    category_tree.insert("", 
                                tk.END, 
                                values=[category, 
                                        f"${total/100.:,.2f}", 
                                        f"{num_transactions}", 
                                        f"${largest_transaction/100.:,.2f}",
                                        f"${smallest_transaction/100.:,.2f}",
                                        f"{category_percentage:.1f}%"])
                    
                applyBandedRows(category_tree)
       
                """Plot the data for a selected account"""  
                
                # Dropdown menu for information breakdown
                plot_types = [
                                "Category Breakdown Pie Chart",
                                "Spending Over Time (Line Chart)",
                                "Bar Chart: Most Expensive Categories",
                                "Boxplot: Transaction Variability",
                                "Heatmap: Spending by Day of the Week"
                            ]
                selected_chart = tk.StringVar(value=plot_types[0])
                chart_dropdown = ttk.Combobox(top, textvariable=selected_chart, values=plot_types, state="readonly")
                
                # Create Matplotlib Figure
                fig, ax = plt.subplots(figsize=(4, 4))
                canvas = FigureCanvasTkAgg(fig, master=top)
                plot_widget = canvas.get_tk_widget()
                
                # Add the Matplotlib Toolbar
                toolbar = NavigationToolbar2Tk(canvas, top, pack_toolbar=False)
                toolbar.update()
                
                # Store original y-axis limits before modifying the plot
                original_xlim = ax.get_xlim()
                original_ylim = ax.get_ylim()
                
                def plotPieChart():
                    """Category Breakdown Pie Chart"""
                    
                    def onPieClick(event):
                        """Detects clicks on pie chart sections and updates the breakdown table."""
                        for wedge in ax.patches:
                            if wedge.contains_point((event.x, event.y)):  # Check if a slice was clicked
                                category = wedge.get_gid()  # Get the category name
                                if category:
                                    updateSubCategoryBreakdown(category)
                                    return
                                
                    ax.clear()
                
                    # Compute category totals
                    category_totals = totals.groupby("Category")["Amount"].sum()
                    
                    # Exclude specific categories
                    exclude_categories = ["Credit Card Payment", "Work", "Car Payment", "CC Payment"]
                    category_totals = category_totals[~category_totals.index.isin(exclude_categories)]
                    category_totals = category_totals[~category_totals.index.str.contains("Transfer", case=False, na=False)]

                    # Sort categories from highest to lowest spending
                    category_totals = category_totals.sort_values(ascending=False)
                
                    # Calculate percentage values
                    total_spent = category_totals.sum()
                    percentages = (category_totals / total_spent) * 100
                
                    # Filter out categories with 0% contribution
                    category_totals = category_totals[percentages > 0]
                    percentages = percentages[percentages > 0]
                
                    # Define colors
                    colors = plt.cm.Paired.colors[:len(category_totals)]  # Use a color palette
                
                    # Define how many categories get direct labels
                    num_labeled_categories = 10  # Adjust this number if needed
                
                    # Create label texts (only for top categories)
                    labels = [f"{cat}" if i < num_labeled_categories else "" 
                              for i, (cat, pct) in enumerate(zip(category_totals.index, percentages))]
                    
                    # Move the pie chart to the left using `ax.set_position()`
                    #ax.set_position([0.05, 0.1, 0.4, 0.8])  # [Left, Bottom, Width, Height]
                
                    # Plot the pie chart
                    wedges, texts, autotexts = ax.pie(
                        category_totals, labels=labels, autopct=lambda p: f"{p:.1f}%" if p > 2 else "",
                        startangle=90, colors=colors, wedgeprops={'edgecolor': 'black'},
                        pctdistance=0.85
                    )
                    
                    # Store category names in wedges for click detection
                    for wedge, category in zip(wedges, category_totals.index):
                        wedge.set_gid(category)  # Assign category name as ID
                
                    # Connect the click event to the function
                    canvas.mpl_connect("button_press_event", onPieClick)
                    
                    # Improve text readability
                    for text in autotexts:
                        text.set_fontsize(10)
                        text.set_color("black")
                
                    # Ensure the chart is a circle (not an ellipse)
                    ax.set_title("Spending Breakdown by Category", fontsize=12, fontweight="bold")
                    ax.axis("equal")  
                
                    # Update the canvas
                    canvas.draw()
                
                def plotExpensiveCategories():
                    """Bar Chart: Most Expensive Categories."""
                    ax.clear()
                    category_totals = df.groupby("Category")["Amount"].sum().sort_values(ascending=False)
                    ax.bar(category_totals.index, category_totals.values, color="red")
                    ax.set_title("Most Expensive Categories")
                    ax.set_xlabel("Category")
                    ax.set_ylabel("Total Spending ($)")
                    plt.xticks(rotation=45)
                    canvas.draw()
                
                def plotBoxplot():
                    """Boxplot: Transaction Variability."""
                    ax.clear()
                    sns.boxplot(x="Category", y="Amount", data=totals, ax=ax)
                    ax.set_title("Transaction Variability by Category")
                    ax.set_xlabel("Category")
                    ax.set_ylabel("Amount ($)")
                    plt.xticks(rotation=45)
                    canvas.draw()
                
                def plotHeatmap():
                    """Heatmap: Spending by Day of the Week."""
                    ax.clear()
                    df["Day of Week"] = df["Date"].dt.day_name()
                    heatmap_data = df.groupby("Day of Week")["Amount"].sum().reindex(
                        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                    )
                    sns.heatmap(pd.DataFrame(heatmap_data), annot=True, cmap="coolwarm", ax=ax, fmt=".0f")
                    ax.set_title("Spending by Day of the Week")
                    canvas.draw()
                
                # Function to Update the Chart Based on Selection
                def updateChart(event=None):
                    """Update the displayed chart based on ComboBox selection."""
                    chart_type = selected_chart.get()
                
                    if chart_type == "Category Breakdown Pie Chart":
                        plotPieChart()
                    elif chart_type == "Bar Chart: Most Expensive Categories":
                        plotExpensiveCategories()
                    elif chart_type == "Boxplot: Transaction Variability":
                        plotBoxplot()
                    elif chart_type == "Heatmap: Spending by Day of the Week":
                        plotHeatmap()
                
                # Bind ComboBox to the Update Function
                chart_dropdown.bind("<<ComboboxSelected>>", updateChart)
                
                def resetView(event=None):
                    """Resets the plot view to the original limits."""
                    ax.set_xlim(original_xlim)  # Restore x-axis limits
                    ax.set_ylim(original_ylim)  # Restore y-axis limits
                    canvas.draw_idle()  # Redraw the figure
        
                def sortBreakdownTable(event=None, column=""):
                    return
                
                # Create a Label for the breakdown table title
                breakdown_title = tk.Label(top, text="Category Breakdown", font=(self.font_type, self.font_size+2, "bold"), anchor="center")
                
                # Ensure correct column names
                breakdown_columns = [str(col) for col in totals.columns]
                
                breakdown_tree = ttk.Treeview(top, columns=breakdown_columns, show="headings", selectmode="none", height=5)
                
                # Define preset column widths
                breakdown_columns_widths = {
                    "Index":0,
                    "Date": 150,
                    "Description": 500,
                    "Amount": 110,
                    "Account": 150,
                    "Category": 0
                }
                
                # Apply styling
                style = ttk.Style()
                Tables.tableStyle(style)
                
                # Configure column headings
                for col in breakdown_columns:
                    if col in breakdown_tree["columns"]:  # Ensure column is valid
                        breakdown_tree.heading(col, text=col, anchor="center", command= lambda event: sortBreakdownTable(event, col))
                        width = breakdown_columns_widths.get(col, 100)
                        breakdown_tree.column(col, width=width, anchor=tk.W, stretch=tk.NO)
                applyBandedRows(breakdown_tree)

                def updateSubCategoryBreakdown(category=category):
                    """Updates breakdown_tree to show transactions for the selected category."""
    
                    # Update the title with the selected category
                    breakdown_title.config(text=f"Transactions for {category}")
    
                    # Clear existing rows in the Treeview
                    for item in breakdown_tree.get_children():
                        breakdown_tree.delete(item)
                
                    # Filter DataFrame for the selected category
                    filtered_df = totals[totals["Category"] == category]
                
                    # Populate breakdown_tree with the filtered transactions
                    for _, row in filtered_df.iterrows():
                        values = list(row)
                        values[3] = f"${values[3]/100:.2f}"  # Format amount as currency
                        breakdown_tree.insert("", "end", values=values)
                        applyBandedRows(breakdown_tree)
                        
                def onCategorySelect(event):
                    """Handles category selection and updates transaction breakdown."""
                    # Get selected row(s) in category_tree
                    selected_item = category_tree.focus()
                
                    if selected_item:  # Ensure something was selected
                        # Extract the category from the first column of the selected row
                        category = category_tree.item(selected_item, "values")[0]
                
                        # Call function to update breakdown_tree with this category's transactions
                        updateSubCategoryBreakdown(category)
                
                def resetView(event=None):
                    """Resets the plot view to the original limits."""
                    ax.set_xlim(original_xlim)  # Restore x-axis limits
                    ax.set_ylim(original_ylim)  # Restore y-axis limits
                    canvas.draw_idle()  # Redraw the figure
                    
                def applyBandedRows(tv):
                    """Recolors Treeview rows to maintain alternating row stripes after sorting."""
                    for index, row in enumerate(tv.get_children('')):
                        tag = "evenrow" if index % 2 == 0 else "oddrow"
                        tv.item(row, tags=(tag,))
                        
                # Bind the function to category selection event
                category_tree.bind("<ButtonRelease-1>", lambda event: onCategorySelect(event))
                updateSubCategoryBreakdown(categories[0])

                # Place category_tree at the top (full width)
                category_tree.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=10, pady=5)
                
                # Place chart dropdown and toolbar above the chart, each taking half of plot_widget's width
                chart_dropdown.grid(row=1, column=0, columnspan=1, sticky="ew", padx=10, pady=5)
                toolbar.grid(row=1, column=1, columnspan=1, sticky="ew", padx=5, pady=5)
                
                # Place title above breakdown table
                breakdown_title.grid(row=1, column=2, columnspan=2, sticky="ew", padx=5, pady=5)  
                
                # Place the chart and breakdown table side by side
                plot_widget.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)
                breakdown_tree.grid(row=2, column=2, rowspan=2, columnspan=2, sticky="nsew", padx=5, pady=5)
                
                # Configure column and row resizing
                top.grid_columnconfigure(0, weight=1)  # Plot widget (left)
                top.grid_columnconfigure(1, weight=1)  # Keeps plot balanced with toolbar
                top.grid_columnconfigure(2, weight=1)  # Breakdown table (right)
                top.grid_columnconfigure(3, weight=1)  # Ensures full-width balance
                
                top.grid_rowconfigure(0, weight=1)  # Category tree (top)
                top.grid_rowconfigure(1, weight=0)  # Dropdown & toolbar (small space)
                top.grid_rowconfigure(2, weight=4)  # Chart and table share space
                top.grid_rowconfigure(3, weight=0)  # Ensures no excessive spacing below
                
                # Override the Home button's functionality
                toolbar.home = resetView
            
                # Resize window dynamically
                def updateTableSizes(event):
                    """Dynamically adjust the table sizes for both income and expense tables."""
                    new_width = top.winfo_width()
                    new_height = top.winfo_height()
                    
                    total_fixed_width = sum(column_widths.values())
                    scale_factor = new_width / total_fixed_width * 0.98
                    
                    try:
                    
                        # Adjust column width dynamically based on window width
                        if event is None or new_width != self.statistics_window_width:
                            self.statistics_window_width = new_width            
                            for col in category_tree["columns"]:
                                width = int(column_widths.get(col, 140) * scale_factor)
                                category_tree.column(col, width=width)
                                
                        # Adjust row count dynamically based on window height
                        if event is None or new_height != self.statistics_window_height:
                            self.statistics_window_height = new_height
                            min_rows = 5
                            max_rows = 10
                            row_height = 35
                            new_row_count = max(min_rows, min(max_rows, new_height // row_height))
                    
                            category_tree.config(height=new_row_count)
                    except:
                        pass
                    
                    self.update_idletasks()
                    
                top.resizable(True, True)
                self.statistics_window_width = top.winfo_width()            
                            
                # Bind the function to window resizing
                top.bind("<Configure>", updateTableSizes)
                
                updateTableSizes(event=None)
                
                def exitWindow(event=None):
                    top.destroy()
                            
                # Bind Escape key
                top.bind("<Escape>", exitWindow)
                
                category_tree.focus_set()
                plotPieChart()
                               
                return
            
            def populateBalanceTree(date_tree, summary_df, months_list, categories):
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
                date_tree["columns"] = months_list
                for col in months_list:
                    date_tree.heading(col, text=Utility.formatMonthLastDayYear(col[0], col[1]), anchor=tk.CENTER, command=lambda c=col: showMonthlyCategoryBreakdown(c))
                    date_tree.column(col, width=column_widths[col], anchor=tk.E, stretch=tk.NO)
            
                # Clear previous table content
                Tables.clearTable(date_tree)

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
            
            if df_type == 'inc':
                text = "SAVINGS"
            else:
                text = "EXPENSES"
            df_label = ttk.Label(self.main_frame, text=text, font=(self.font_type, self.font_size+2, "bold"))
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
        if df_type == 'inc':
            if self.current_window == 'Spending':
                return
            df = self.income_data.copy()
            self.current_window = 'Spending'
            
        else:
            if self.current_window == 'Savings':
                return
            df = self.expenses_data.copy()
            self.current_window = 'Savings'
            
        # Clear the main frame before populating the table
        self.clearMainFrame()
            
        # Get list of categories
        cat_list, _ = Utility.getCategoryTypes(df_type)
        
        # Get list of months
        self.all_months = Utility.generateMonthYearList(self.new_date_range[0], self.new_date_range[1])
        self.number_of_months_displayed = len(self.all_months)
        
        displayStatisticsSummary(df.copy(), cat_list, df_type)
    
        return