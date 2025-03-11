import os
import pandas as pd
import numpy as np
import pickle
import importlib
import re
import sys

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, PhotoImage, font
import tkinter.simpledialog as simpledialog
import tkinter.colorchooser as colorchooser
from PIL import Image, ImageTk
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

from Utility import Utility, Tables, Windows, Classifier
from StyleConfig import StyleConfig


class DataFrameProcessor:
    @staticmethod
    def getDataFrameIndex(df: pd.DataFrame) -> pd.DataFrame:
        """
        Ensures that the 'Index' column exists and is correctly set as the first column.

        If the 'Index' column does not exist, it is created from the DataFrame's index.
        If it already exists, it is removed and reinserted as the first column.

        Parameters:
        - df (pd.DataFrame): The input DataFrame.

        Returns:
        - pd.DataFrame: Updated DataFrame with 'Index' as the first column.
        """
        df = df.reset_index(drop=True)  # Reset index to start fresh
        if 'No.' in df.columns:
            df = df.drop(columns=['No.'])
        df.insert(0, 'No.', df.index)
        return df
    @staticmethod 
    def convertCurrency(df: pd.DataFrame) -> pd.DataFrame:
        """
        Converts the 'Payment', 'Deposit', and 'Balance' columns in a DataFrame to cents (int) format

        Parameters:
        - df (pd.DataFrame): The input DataFrame containing a 'Date' column.

        Returns:
        - pd.DataFrame: Updated DataFrame
        """
        for col in ['Payment', 'Deposit', 'Balance']:
            if col in df.columns:
                df[col] = df[col].astype(str)  # Ensure strings for processing
                
                # Remove dollar signs, commas, and handle negative parentheses
                df[col] = df[col].replace({'\\$': '', ',': '', '\\(': '-', '\\)': ''}, regex=True)
                
                # Convert to numeric, replace NaNs with 0, multiply by 100, and round to int
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                df[col] = (df[col] * 100).round().astype(int)

        return df
    @staticmethod 
    def convertToDatetime(df: pd.DataFrame) -> pd.DataFrame:
        """
        Converts the 'Date' column in a DataFrame to datetime format, ensuring proper formatting.

        Parameters:
        - df (pd.DataFrame): The input DataFrame containing a 'Date' column.

        Returns:
        - pd.DataFrame: Updated DataFrame with the 'Date' column converted to datetime format.
        """
        df['Date'] = pd.to_datetime(df['Date'], dayfirst=False, format='mixed').dt.date
        return df
    @staticmethod 
    def sortDataFrame(df: pd.DataFrame) -> pd.DataFrame:
        """
        Sorts a DataFrame in ascending order based on 'Date' column.

        Parameters:
        - df (pd.DataFrame): The input DataFrame.

        Returns:
        - pd.DataFrame: Sorted DataFrame with a reset index.
        """
        df = df.sort_values(by=['Date'], ascending=True, inplace=False).reset_index(drop=True) 
        return df
    @staticmethod 
    def getStartEndDates(df: pd.DataFrame) -> Tuple[pd.Timestamp, pd.Timestamp]:
        """
        Retrieves the earliest and latest dates from the 'Date' column of the DataFrame.

        Parameters:
        - df (pd.DataFrame): The input DataFrame containing a 'Date' column.

        Returns:
        - Tuple[pd.Timestamp, pd.Timestamp]: A tuple containing the earliest and latest dates.
        """
        return df['Date'].min(), df['Date'].max()
    @staticmethod 
    def getMinMaxVals(df: pd.DataFrame) -> Tuple[float, float]:
        """
        Computes the minimum and maximum values of the 'Amount' column in the DataFrame.

        Parameters:
        - df (pd.DataFrame): The input DataFrame containing an 'Amount' column.

        Returns:
        - Tuple[float, float]: A tuple containing (min_value, max_value) from the 'Amount' column.
        """
        return df['Amount'].min(), df['Amount'].max()
    @staticmethod 
    def findMismatchedCategories( df: pd.DataFrame, df_type: str) -> pd.DataFrame:
        """
        Identifies and marks categories that are not found in the predefined category list.

        Categories that are not in the list will be prefixed with an asterisk (*).

        Parameters:
        - df (pd.DataFrame): The input DataFrame containing a 'Category' column.
        - df_type (str): The type of DataFrame ('inc' for income, 'exp' for expenses).

        Returns:
        - pd.DataFrame: Updated DataFrame with mismatched categories marked with an asterisk (*).
        """
        cat_list, _ = Utility.getCategoryTypes(df_type)
        df['Category'] = df['Category'].astype(str).apply(lambda x: f"*{x}" if x.strip() not in map(str.strip, map(str, cat_list)) else x)
        return df
    @staticmethod 
    def accountBalance(df: pd.DataFrame) -> pd.Series:
        """
        Calculate the current balance for each account.
        - Uses the most recent 'Balance' value if available.
        - Falls back to (Deposit - Payment) if Balance is missing or zero.
    
        Parameters:
            df (pd.DataFrame): Transactions dataframe.
    
        Returns:
            pd.Series: A series containing the latest balance for each account.
        """
        if "Account" not in df.columns or ("Balance" not in df.columns and "Payment" not in df.columns and "Deposit" not in df.columns):
            return pd.Series(dtype=float)  # Return empty Series if required columns are missing
    
        # Get the most recent balance for each account (sort by Date if applicable)
        if "Date" in df.columns:
            #df = DataFrameProcessor.convertToDatetime(df)
            df = df.sort_values(by="Date", ascending=True)
    
        latest_balances = df.groupby("Account")["Balance"].last()  # Last balance entry per account
    
        # Compute alternative balance where latest balance is zero
        computed_balances = df.groupby("Account").agg({"Deposit": "sum", "Payment": "sum"})
        computed_balances = abs(computed_balances["Deposit"]) - abs(computed_balances["Payment"])  # Convert to Series
    
        # Use the latest balance unless it's zero, then use computed balance
        final_balances = latest_balances.mask(latest_balances == 0, computed_balances)
    
        return final_balances

class DataManager:
    @staticmethod
    def readCSV(file_path:'str') -> pd.DataFrame:
        """
        Load financial data from a CSV file
        
        Parameters:
            file_path (str): Path to the CSV file.
    
        Returns:
            (pd.DataFrame): DataFrames of transactions
        """
        try:
            df = pd.read_csv(file_path).fillna(0)
            return df
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {e}")
            return pd.DataFrame()        
    @staticmethod 
    def openData() -> List[Tuple[str, pd.DataFrame]]:
        """
        Opens a file dialog for .csv and .pkl files.
        
        Returns:
            (pkl_file, csv_files) tuple:
                pkl_file (str or None) - path to a single .pkl file if found.
                csv_files (List[str])  - list of .csv paths if found (empty if pkl_file is found).
        """
        # Prompt user to pick multiple files
        file_paths = filedialog.askopenfilenames(
            filetypes=[("CSV and PKL files", "*.csv *.pkl")])
        
        if not file_paths:
            return None, []
        
        csv_files = []
        pkl_file = None
        
        # Separate CSVs from PKL
        for path in file_paths:
            ext = os.path.splitext(path)[1].lower()
            
            if ext == ".csv":
                csv_files.append(path)
            elif ext == ".pkl":
                if pkl_file is None:
                    pkl_file = path
                else:
                    messagebox.showwarning("Multiple PKL Files",
                                           "Multiple PKL files selected; only the first will be used.")
            else:
                messagebox.showwarning("Unsupported File", f"Skipping file: {path}")
        
        # If a single PKL was found, return it immediately (ignore any CSV)
        if pkl_file is not None:
            return pkl_file, []
        
        # Otherwise, return the list of CSV files
        return None, csv_files
    @staticmethod     
    def parseNewDF(dashboard: "Dashboard", df:pd.DataFrame, account_name: str) -> pd.DataFrame:
        """
        Parses new data files and assigns correct formatting based on account type.
        - Determines if the file is an investment or banking account.
        - Standardizes column headers.
        - Converts necessary fields.
    
        Parameters:
            df (pd.DataFrame): DataFrame containing the CSV data.
            account (str): Account name derived from the filename.
    
        Returns:
            pd.DataFrame: Formatted DataFrame ready for use.
        """            
        
        # Define keywords to differentiate account types
        investment_keywords = ["TSP", "IRA", "401K", "Investment", "Stocks", "Bonds", "Mutual Funds", "TRS", "Retirement"]
        banking_keywords = ["Checking", "Savings", "Credit", "Loan"]
        
        # Guess account type based on filename
        account_type = "Banking"
        for keyword in investment_keywords:
            if keyword.lower() in account_name.lower():
                account_type = "Investment"
                break
        for keyword in banking_keywords:
            if keyword.lower() in account_name.lower():
                account_type = "Banking"
                break

        # Normalize column headers
        header_mapping = {
            "Transaction ID": "No.",
            "Transaction Date": "Date",
            "Amount": "Payment",
            "Credit": "Deposit",
            "Debit": "Payment",
            "Memo": "Note",
            "Shares": "Shares",  # Investment-specific
            "Ticker": "Ticker",  # Investment-specific
            "Market Value": "MarketValue"  # Investment-specific
        }
        
        # Normalize column headers
        df.columns = [header_mapping.get(col, col) for col in df.columns]
        
        # Check for investment-specific columns and override classification if found
        if any(col in df.columns for col in ["Shares", "Ticker", "Market Value"]):
            account_type = "Investment"
        
        # Ensure required columns exist

        if account_type == 'Banking':
            expected_headers = list(dashboard.banking_column_widths)
        else:
            expected_headers = list(dashboard.investment_column_widths)
            
        for col in expected_headers:
            if col not in df.columns:
                df[col] = ""  # Add missing columns
                
        # Ensure all expected headers exist
        for col in expected_headers:
            if col not in df.columns:
                df[col] = ""  # Fill missing columns with empty values
        
        # Convert data types as necessary
        df = DataFrameProcessor.convertToDatetime(df)
        df = DataFrameProcessor.sortDataFrame(df)
        df = DataFrameProcessor.getDataFrameIndex(df) 
        
        # Convert numeric fields if applicable
        df = DataFrameProcessor.convertCurrency(df)
        
        # Assign account name and type
        df['Account'] = account_name
        df['Account Type'] = account_type
        df['Category'] = ''
        
        # Categorize the account based on Payment, Deposit, and Balance values
        if (
            (df["Payment"] <= 0.00).all() and
            (df["Deposit"] >= 0.00).all() and
            (df["Balance"] == 0.00).all()
        ):
            case = "Type 1"
        elif (
            (df["Payment"] >= 0.00).all() and
            (df["Deposit"] <= 0.00).all() and
            (df["Balance"] == 0.00).all()
        ):
            case = "Type 2"
        elif (
            (df["Payment"] >= 0.00).all() and
            (df["Deposit"] >= 0.00).all() and
            (df["Balance"] == 0.00).all()
        ):
            case = "Type 3"
        elif (
            (df["Payment"] >= -999999.00).all() and 
            (df["Deposit"] == 0.00).all()
        ):
            case = "Type 4"
        else:
            case = "Type 0"
    
        # Select only the relevant columns in the correct order
        df = df[expected_headers]
  
        return df, case    
    @staticmethod     
    def updateData() -> None:
        """
        Updates the financial data based on CSV files.
    
        This method triggers `selectFilesAndFolders` with `update=True`,
        ensuring that the data is refreshed with the latest available files.
        """
        #self.selectFilesAndFolders(update=True)
        #TODO Add functionality
        return
    @staticmethod 
    def compareOldAndNewDF(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
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
    @staticmethod 
    def addNewValuesToDF(df1: pd.DataFrame, df2: pd.DataFrame):
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
    @staticmethod
    def exportData(transaction_data:pd.DataFrame, initial_balances:dict, new_file: str) -> str:
        """Exports all data to Excel."""
        if new_file == '':
            file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                     filetypes=[("Excel Files", "*.xlsx")])
            if not file_path:
                return
        else:
            file_path = new_file
            
        transaction_data = DataFrameProcessor.convertToDatetime(transaction_data)

        initial_balances = pd.DataFrame.from_dict(initial_balances, orient="index", columns=["Initial Date", "Initial Value"]).reset_index().rename(columns={"index": "Account"})
        with pd.ExcelWriter(file_path) as writer:
            transaction_data.to_excel(writer, sheet_name="Transactions", index=False)
            initial_balances.to_excel(writer, sheet_name="Initial Balances", index=False)
            #df3.to_excel(writer, sheet_name="Sheet3", index=False)
    
        messagebox.showinfo("Export Complete", f"Data saved to {file_path}")  
    @staticmethod
    def saveData(transaction_data:pd.DataFrame, initial_balances:dict, account_types: dict, new_file: str) -> None:
        """Exports all data to pickel save file"""
        if new_file == '':
            file_path = filedialog.asksaveasfilename(defaultextension=".pkl",
                                                     filetypes=[("Save Files", "*.pkl")])
            if not file_path:
                return
        else:
            file_path = new_file

        transaction_data = DataFrameProcessor.convertToDatetime(transaction_data)

        with open(file_path, "wb") as f:
            pickle.dump({"Transaction Data": transaction_data, 
                         "Initial Balances": initial_balances, 
                         "Account Types": {key.replace('.csv', ''): value for key, value in account_types.items()}}, 
                         f)
        
        messagebox.showinfo("Save Complete", f"Data saved to {file_path}")  
        
        return file_path
    @staticmethod
    def loadSaveFile(save_file: str):
        """TEST"""
        
        if save_file == '':
            return pd.DataFrame, {}
                
        try:
            with open(save_file, "rb") as f:
                data = pickle.load(f)

            all_data_df = data.get('Transaction Data', pd.DataFrame())
            init_bal_dict = data.get("Initial Balances", {})
            acc_type_dict = data.get("Account Types", {})
    
            return all_data_df, init_bal_dict, acc_type_dict
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {e}")
            return pd.DataFrame(), {}, {}
        
class TransactionManager:            
    @staticmethod     
    def openTransactionWindow(dashboard_actions: "Dashboard", dashboard: "Dashboard", edit=False) -> None:
        #TODO Move to appropriate place/class
        """Opens a transaction window for adding/editing a transaction, pre-filling if data is provided."""
    
        def validateInputs():
            """Checks if inputs match expected types before submission."""
            errors = []
            input_values = {header: entry.get().strip() for header, entry in entry_fields.items()}
    
            if all(value == "" for value in input_values.values()):
                messagebox.showwarning("Warning", "Cannot save an empty transaction.")
                return False
    
            for header, entry in entry_fields.items():
                value = entry.get().strip()
    
                if header in ["Payment", "Deposit", "Balance"]:
                    value = value if value else "0.00"
                    try:
                        float_value = float(value.replace("$", "").replace(",", ""))
                        entry_fields[header].delete(0, tk.END)
                        entry_fields[header].insert(0, f"{float_value:.2f}")
                        entry.config(bg="white")
                    except ValueError:
                        errors.append(f"'{header}' must be a valid number.")
                        entry.config(bg="lightcoral")
    
                elif header == "Date":
                    if not value.strip():
                        value = dashboard.day_one
                    
                    valid_date = False
                    date_formats = ["%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y", "%d %b %Y", "%b %d, %Y"]

                    for fmt in date_formats:
                        try:
                            parsed_date = datetime.strptime(value, fmt).date()
                            entry_fields[header].delete(0, tk.END)
                            entry_fields[header].insert(0, parsed_date.strftime("%Y-%m-%d"))  # Convert to standard format
                            entry.config(bg="white")
                            valid_date = True
                            break
                        except ValueError:
                            continue  # Try next format
                    
                    if not valid_date:
                        errors.append(f"'{header}' must be a valid date (YYYY-MM-DD, MM/DD/YYYY, DD-MM-YYYY, etc.).")
                        entry.config(bg="lightcoral")
    
            if errors:
                messagebox.showerror("Input Error", "\n".join(errors))
                return False
            return True
    
        def submitTransaction(event=None):
            """Parses, validates, and processes the transaction."""
            stored_values = {header: entry.get().strip() for header, entry in entry_fields.items()}
        
            if not validateInputs():
                transaction_window.destroy()
                return stored_values
        
            # Has to be included twice to overcome overrides. IDK. It works.
            stored_values = {header: entry.get().strip() for header, entry in entry_fields.items()}
        
            # Convert stored values to DataFrame
            new_df = pd.DataFrame([stored_values])
            new_df, acc_type = DataManager.parseNewDF(dashboard, new_df, stored_values.get("Account", "Unknown"))
        
            # Ensure proper data type conversion
            for col in ["No.", "Payment", "Deposit", "Balance"]:
                if col in new_df.columns:
                    new_df[col] = pd.to_numeric(new_df[col], errors='coerce').fillna(0).astype(int)  # Convert to int

            if prefill_data:
                # Editing an existing transaction
                selected_items = dashboard_actions.widget_dashboard.tree.selection()
                selected_number = int(dashboard_actions.widget_dashboard.tree.item(selected_items[0], "values")[0])  # Convert to int for index matching
        
                # Find the index of the selected transaction in all_data
                index_to_update = dashboard.all_data[dashboard.all_data["No."] == selected_number].index
        
                if not index_to_update.empty:
                    # Ensure new_df has the same columns as all_data before assignment
                    new_df = new_df[dashboard.all_data.columns]
        
                    # Assign values row-wise
                    for col in dashboard.all_data.columns:
                        dashboard.all_data.loc[index_to_update, col] = new_df.iloc[0][col]
        
                else:
                    messagebox.showerror("Error", "Transaction not found for editing.")
                    return
            else:
                # Adding new transaction
                if dashboard.all_data.empty:
                    dashboard.all_data = new_df
                else:
                    dashboard.all_data = pd.concat([dashboard.all_data, new_df], ignore_index=True)
        
            dashboard.all_data = DataFrameProcessor.getDataFrameIndex(dashboard.all_data)
            dashboard_actions.updateTable(dashboard.all_data)
        
            transaction_window.destroy()
    
        def closeWindow(event=None):
            """Closes the transaction window."""
            transaction_window.destroy()
    
        # Create transaction window
        transaction_window = tk.Toplevel(dashboard)
        transaction_window.title("Edit Transaction" if edit else "Add Transaction")
    
        transaction_window.bind("<Escape>", closeWindow)
        transaction_window.bind("<Return>", submitTransaction)
    
        entry_fields = {}

        if dashboard.table_to_display == 'Banking':
            headers = list(dashboard.banking_column_widths.keys())[1:]
        elif dashboard.table_to_display == 'Investment':
            headers = list(dashboard.investment_column_widths.keys())[1:]
            
        if edit:
           selected_items = dashboard_actions.widget_dashboard.tree.selection()
           if not selected_items:
               messagebox.showwarning("Warning", "No transaction selected for editing.")
               return
       
           selected_values = dashboard_actions.widget_dashboard.tree.item(selected_items, "values")
           headers = [dashboard_actions.widget_dashboard.tree.heading(col)["text"] for col in dashboard_actions.widget_dashboard.tree["columns"]]
        
           prefill_data = dict(zip(headers, selected_values)) 
           
           headers = headers[1:]
           
        else:
            prefill_data = None
    
        # Configure the second column to expand with window resizing
        transaction_window.grid_columnconfigure(1, weight=1)
    
        for idx, column in enumerate(headers):
            tk.Label(transaction_window, text=column, anchor="w").grid(row=idx, column=0, padx=10, pady=5, sticky="w")
    
            entry = tk.Entry(transaction_window)
            entry.grid(row=idx, column=1, padx=10, pady=5, sticky="ew")
    
            if prefill_data and column in prefill_data:
                entry.insert(0, prefill_data[column])
    
            entry_fields[column] = entry
            
        window_width, window_height = 300, (30*(idx+1))+60
        Windows.openRelativeWindow(transaction_window, main_width=dashboard.winfo_x(), main_height=dashboard.winfo_y(), width=window_width, height=window_height)
    
        submit_button = tk.Button(transaction_window, 
                                  text="Submit", 
                                  command=submitTransaction,
                                  bg=StyleConfig.BUTTON_COLOR, 
                                  fg=StyleConfig.TEXT_COLOR, 
                                  relief=StyleConfig.BUTTON_STYLE)
        submit_button.grid(row=len(headers), column=0, columnspan=2, pady=10)
    
        submit_button.focus_set()
    @staticmethod 
    def deleteTransaction(dashboard_actions: "Dashboard", dashboard: "Dashboard") -> None:
        """Deletes the selected transaction(s) from the data table."""
        selected_items = dashboard_actions.widget_dashboard.tree.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "No transactions selected!")
            return
    
        selected_numbers = [dashboard_actions.widget_dashboard.tree.item(item, "values")[0] for item in selected_items]
        selected_numbers = set(map(int, selected_numbers))
    
        indices_to_drop = dashboard.all_data[dashboard.all_data["No."].isin(selected_numbers)].index
    
        confirm = messagebox.askyesno("Confirm Delete", 
                                      f"Are you sure you want to delete {len(indices_to_drop)} transaction(s)?", 
                                      parent=dashboard)
        if confirm is None or not confirm:  # Explicitly check for None
            return  # User canceled or closed the dialog, so exit
    
        dashboard.all_data = dashboard.all_data.drop(indices_to_drop).reset_index(drop=True)
        dashboard.all_data = DataFrameProcessor.getDataFrameIndex(dashboard.all_data)
    
        dashboard_actions.updateTable(dashboard.all_data)
  
class DashboardUI(tk.Frame):
    def __init__(self, parent_dashboard, master=None, *args, **kwargs):
        """
        A Frame-based class that builds the UI portion of the Dashboard.
        
        Parameters:
            parent_dashboard: Reference to the main Dashboard instance 
        """
        super().__init__(master, *args, **kwargs)
        
        self.parent_dashboard = parent_dashboard

        # Keep references to your UI widgets
        self.sidebar = None
        self.toolbar = None
        self.main_content = None
        self.tree = None
        
        # This frame itself also needs geometry management in the parent:
        self.grid(row=0, column=0, sticky="nsew")
        
        # Actions manager for all dashboard/UI actions
        self.actions_manager = DashboardActions(self.parent_dashboard, self)
        
        # Build out the UI
        self.createWidgets()
        
    ########################################################
    # WIDGETS
    ########################################################
    def createWidgets(self):
        """Creates and places all main widgets for the dashboard."""
        
        # Sidebar widget
        self.sidebar = tk.Frame(self, width=350, relief=tk.RIDGE, bg=StyleConfig.BG_COLOR)
        self.sidebar.grid(row=0, column=0, sticky='nsew')
        self.createSidebar()
        
        # Non-Sidebar Widgets
        self.main_content = tk.Frame(self)
        self.main_content.grid(row=0, column=1, sticky='nsew')
        
        # Toolbar widget
        self.createToolbar()
        
        # Treeview widget
        self.createTransactionTable()
        
        # Configure layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Apply UI Style
        self.applyStyleChanges()
        
    ########################################################
    # SIDEBAR
    ########################################################
    def createSidebar(self):
        """Creates the sidebar with accounts, reports, and actions."""
        
        # Accounts Listbox
        self.banking_label = tk.Label(
            self.sidebar, 
            text="Banking Accounts",   
            font=(StyleConfig.FONT_FAMILY, StyleConfig.HEADING_FONT_SIZE, "bold"),
            bg=StyleConfig.BG_COLOR, 
            fg=StyleConfig.TEXT_COLOR
            )
        self.banking_label.pack(anchor='center', pady=5)
    
        # Add a frame to contain the listbox and scrollbar
        self.accounts_listbox_frame = ttk.Frame(self.sidebar)
        self.accounts_listbox_frame.pack(fill="x", padx=5, pady=2)
        
        # Create listbox with a scrollbar
        self.accounts_list = tk.Listbox(self.accounts_listbox_frame, height=6, width=35)
        self.accounts_list.pack(side=tk.LEFT, fill='x', expand=True)
    
        # Add scrollbar for smooth scrolling
        self.accounts_scrollbar = ttk.Scrollbar(self.accounts_listbox_frame, orient=tk.VERTICAL, command=self.accounts_list.yview)
        self.accounts_scrollbar.pack(side=tk.RIGHT, fill='y')
        self.accounts_list.config(yscrollcommand=self.accounts_scrollbar.set)
    
        # Bind smooth scrolling behavior
        self.accounts_list.bind("<MouseWheel>",  self.actions_manager.smoothScroll)
        
        # Bind double-click event to filter transactions
        self.accounts_list.bind("<Double-Button-1>",  self.actions_manager.filterTransactionsByBankingAccount)
        
        
        # Categories Listbox
        self.category_label = tk.Label(
            self.sidebar, 
            text="Categories",
            font=(StyleConfig.FONT_FAMILY, StyleConfig.HEADING_FONT_SIZE, "bold"),
            bg=StyleConfig.BG_COLOR, 
            fg=StyleConfig.TEXT_COLOR
            )
        self.category_label.pack(anchor='center', pady=5)
    
        # Add a frame to contain the listbox and scrollbar
        self.category_listbox_frame = ttk.Frame(self.sidebar)
        self.category_listbox_frame.pack(fill="x", padx=5, pady=2)
        
        # Create listbox with a scrollbar
        self.category_list = tk.Listbox(self.category_listbox_frame, height=6, width=35)
        self.category_list.pack(side=tk.LEFT, fill='x', expand=True)
    
        # Add scrollbar for smooth scrolling
        self.category_scrollbar = ttk.Scrollbar(self.category_listbox_frame, orient=tk.VERTICAL, command=self.category_list.yview)
        self.category_scrollbar.pack(side=tk.RIGHT, fill='y')
        self.category_list.config(yscrollcommand=self.category_scrollbar.set)
    
        # Bind smooth scrolling behavior
        self.category_list.bind("<MouseWheel>",  self.actions_manager.smoothScroll)
        
        # Bind double-click event to filter transactions
        self.category_list.bind("<Double-Button-1>",  self.actions_manager.filterTransactionsByCategory)
        
        
        # Payees Listbox
        self.payee_label = tk.Label(
            self.sidebar, 
            text="Payees",
            font=(StyleConfig.FONT_FAMILY, StyleConfig.HEADING_FONT_SIZE, "bold"),
            bg=StyleConfig.BG_COLOR, 
            fg=StyleConfig.TEXT_COLOR
            )
        self.payee_label.pack(anchor='center', pady=5)
    
        # Add a frame to contain the listbox and scrollbar
        self.payee_listbox_frame = ttk.Frame(self.sidebar)
        self.payee_listbox_frame.pack(fill="x", padx=5, pady=2)
        
        # Create listbox with a scrollbar
        self.payee_list = tk.Listbox(self.payee_listbox_frame, height=6, width=35)
        self.payee_list.pack(side=tk.LEFT, fill='x', expand=True)
    
        # Add scrollbar for smooth scrolling
        self.payee_scrollbar = ttk.Scrollbar(self.payee_listbox_frame, orient=tk.VERTICAL, command=self.payee_list.yview)
        self.payee_scrollbar.pack(side=tk.RIGHT, fill='y')
        self.payee_list.config(yscrollcommand=self.payee_scrollbar.set)
    
        # Bind smooth scrolling behavior
        self.payee_list.bind("<MouseWheel>",  self.actions_manager.smoothScroll)
        
        # Bind double-click event to filter transactions
        self.payee_list.bind("<Double-Button-1>",  self.actions_manager.filterTransactionsByPayee)
        
        
        # Investments Listbox
        self.investment_label = tk.Label(
            self.sidebar, 
            text="Investment Accounts",
            font=(StyleConfig.FONT_FAMILY, StyleConfig.HEADING_FONT_SIZE, "bold"),
            bg=StyleConfig.BG_COLOR, 
            fg=StyleConfig.TEXT_COLOR
            )
        self.investment_label.pack(anchor='center', pady=5)
    
        # Add a frame to contain the listbox and scrollbar
        self.investment_listbox_frame = ttk.Frame(self.sidebar)
        self.investment_listbox_frame.pack(fill="x", padx=5, pady=2)
        
        # Create listbox with a scrollbar
        self.investments_list = tk.Listbox(self.investment_listbox_frame, height=6, width=35)
        self.investments_list.pack(side=tk.LEFT, fill='x', expand=True)
    
        # Add scrollbar for smooth scrolling
        self.investments_scrollbar = ttk.Scrollbar(self.investment_listbox_frame, orient=tk.VERTICAL, command=self.investments_list.yview)
        self.investments_scrollbar.pack(side=tk.RIGHT, fill='y')
        self.investments_list.config(yscrollcommand=self.investments_scrollbar.set)
    
        # Bind smooth scrolling behavior
        self.investments_list.bind("<MouseWheel>",  self.actions_manager.smoothScroll)
        
        # Bind double-click event to filter transactions
        self.investments_list.bind("<Double-Button-1>",  self.actions_manager.filterTransactionsByInvestmentAccount)
            
        
        # Reports Listbox
        self.reports_label = tk.Label(
            self.sidebar, 
            text="Reports",
            font=(StyleConfig.FONT_FAMILY, StyleConfig.HEADING_FONT_SIZE, "bold"),
            bg=StyleConfig.BG_COLOR, 
            fg=StyleConfig.TEXT_COLOR
            )
        self.reports_label.pack(anchor='center', pady=5)
    
        # Add a frame to contain the listbox and scrollbar
        self.reports_listbox_frame = ttk.Frame(self.sidebar)
        self.reports_listbox_frame.pack(fill="x", padx=5, pady=2)
        
        # Create listbox with a scrollbar
        self.reports_list = tk.Listbox(self.reports_listbox_frame, height=6, width=35)
        self.reports_list.pack(side=tk.LEFT, fill='x', expand=True)
    
        # Add scrollbar for smooth scrolling
        self.reports_scrollbar = ttk.Scrollbar(self.reports_listbox_frame, orient=tk.VERTICAL, command=self.reports_list.yview)
        self.reports_scrollbar.pack(side=tk.RIGHT, fill='y')
        self.reports_list.config(yscrollcommand=self.reports_scrollbar.set)
    
        # Bind smooth scrolling behavior
        self.reports_list.bind("<MouseWheel>",  self.actions_manager.smoothScroll)
        
        # Bind double-click event to filter transactions
        self.reports_list.bind("<Double-Button-1>",  self.actions_manager.displayReports)
        
        """
        ttk.Label(self.sidebar, text="Actions", font=(StyleConfig.FONT_FAMILY, StyleConfig.SUB_FONT_SIZE, "bold")).pack(anchor='w', pady=5)
        self.actions_list = tk.Listbox(self.sidebar, height=4, width=45)  # Increased width
        self.actions_list.pack(fill='x', padx=5, pady=2)
        """
        
    ########################################################
    # TOOLBAR
    ########################################################
    def createToolbar(self):
        """Creates a toolbar with basic transaction actions."""
        
        self.toolbar = tk.Frame(self.main_content, relief=tk.RIDGE, bg=StyleConfig.BG_COLOR)
        self.toolbar.grid(row=0, column=0, sticky='nsew')
        
        self.button_image_loc = os.path.join(os.path.dirname(__file__), "Images")
        
        self.buttons = []
        self.separators = []
        self.images = {}
        
        self.button_separators = [3, 6, 8, 9]
        
        self.buttons = []
        button_data = [
            ("Add",         "add.png",      self.actions_manager.addTransaction),
            ("Edit",        "edit.png",     self.actions_manager.editTransaction),
            ("Delete",      "delete.png",   self.actions_manager.deleteTransaction),
            ("Open",        "open.png",     self.actions_manager.openData),
            ("Balances",    "accounts.png", self.actions_manager.trackBankBalances),
            ("Payee",       "payee.png",    self.actions_manager.viewPayees),
            ("Category",    "category.png", self.actions_manager.viewCategories),
            ("Banking",     "banking.png",  lambda: self.actions_manager.filterByAccountType("Banking")),
            ("Stocks",      "stonks.png",   lambda: self.actions_manager.filterByAccountType("Investments")),
            ("Reports",     "budget.png",   self.actions_manager.displayReports),
            ("Export",      "export.png",   self.actions_manager.exportData),
            ("Options",     "options.png",  self.actions_manager.viewOptions),
        ]
        
        btn_size = 50  
        
        for index, (text, icon, command) in enumerate(button_data):
            img_path = os.path.join(self.button_image_loc, icon)
            img = Image.open(img_path)
            img = img.resize((36,36))  # Resize image to 24x24 pixels
            self.images[icon] = ImageTk.PhotoImage(img)
            
            try:
                btn = tk.Button(
                    self.toolbar, 
                    text=text, 
                    image=self.images[icon], 
                    compound=tk.TOP, 
                    command=command, 
                    width=btn_size, 
                    height=btn_size, 
                    bg=StyleConfig.BUTTON_COLOR, 
                    relief=StyleConfig.BUTTON_STYLE
                    )
            except:
                btn = tk.Button(
                    self.toolbar, 
                    text=text, 
                    compound=tk.TOP, 
                    command=command, 
                    width=btn_size, 
                    height=btn_size, 
                    bg=StyleConfig.BUTTON_COLOR, 
                    relief=StyleConfig.BUTTON_STYLE
                    )
                
            btn.pack(side=tk.LEFT, padx=4, pady=2)
            self.buttons.append(btn)
            
            if index in self.button_separators:
                ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
                
        # Search label
        self.search_label = tk.Label(
            self.toolbar, 
            text="Search:", 
            font=(StyleConfig.FONT_FAMILY, StyleConfig.FONT_SIZE),
            bg=StyleConfig.BG_COLOR, 
            fg=StyleConfig.TEXT_COLOR
            )
        self.search_label.pack(side=tk.LEFT, padx=5)
        
        # Search entry
        self.search_entry = tk.Entry(self.toolbar, 
                                     width=30, 
                                     bg=StyleConfig.BUTTON_COLOR, 
                                     )
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind("<Return>", lambda event:  self.actions_manager.searchTransactions())
        
        search_button = tk.Button(self.toolbar, 
                                  text="Go",
                                  command=self.actions_manager.searchTransactions, 
                                  bg=StyleConfig.BUTTON_COLOR, 
                                  relief=StyleConfig.BUTTON_STYLE
                                  )
        search_button.pack(side=tk.LEFT, padx=5)
        self.buttons.append(search_button)
        
        adv_search_button = tk.Button(self.toolbar, 
                                      text="Advanced Search", 
                                      command=self.actions_manager.openAdvancedSearch,
                                      bg=StyleConfig.BUTTON_COLOR, 
                                      relief=StyleConfig.BUTTON_STYLE
                                      )
        adv_search_button.pack(side=tk.LEFT, padx=5)
        self.buttons.append(adv_search_button)
        self.buttons.append(adv_search_button)
        
    ########################################################
    # MAIN TRANSACTION TABLE
    ########################################################
    def createTransactionTable(self):
        """Creates the transaction table with scrolling."""
        
        # Create frame
        self.table_frame = tk.Frame(self.main_content)
        self.table_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
        
        # Adjust layout
        self.table_frame.grid_columnconfigure(0, weight=1)
        self.table_frame.grid_rowconfigure(0, weight=1)
        
        self.tree = ttk.Treeview(self.table_frame, 
                                 show='headings',
                                 yscrollcommand=lambda *args: self.y_scrollbar.set(*args),
                                 height=15)
        self.tree.grid(row=0, column=0, sticky='nsew')
        
        # Attach vertical scrollbar on the right
        self.y_scrollbar = ttk.Scrollbar(self.table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.y_scrollbar.set)
        self.y_scrollbar.grid(row=0, column=1, sticky='ns')
        
        self.main_content.grid_columnconfigure(0, weight=1)
        self.main_content.grid_rowconfigure(1, weight=1)
        
        # Bind double-click to edit cell
        self.tree.bind("<Double-1>",  self.actions_manager.editCell)

    ########################################################
    # UI STYLE
    ########################################################    
    def applyStyleChanges(self):
        """Applies updated style settings dynamically to ttk and standard Tk widgets."""
        
        # Apply background color to main sections
        self.sidebar.config(bg=StyleConfig.BG_COLOR)
        self.toolbar.config(bg=StyleConfig.BG_COLOR)
        self.main_content.config(bg=StyleConfig.BG_COLOR)
        self.table_frame.config(bg=StyleConfig.BG_COLOR)
    
        style = ttk.Style()
    
        # Update Treeview 
        style.configure("Treeview", 
                        rowheight=StyleConfig.ROW_HEIGHT, 
                        font=(StyleConfig.FONT_FAMILY, StyleConfig.FONT_SIZE),
                        background=StyleConfig.BG_COLOR,
                        foreground=StyleConfig.TEXT_COLOR,
                        fieldbackground=StyleConfig.BG_COLOR)
        
        # Update Treeview headers
        style.configure("Treeview.Heading", 
                        font=(StyleConfig.FONT_FAMILY, StyleConfig.HEADING_FONT_SIZE, "bold"),
                        background=StyleConfig.HEADER_COLOR, 
                        foreground='black',
                        fieldbackground=StyleConfig.BG_COLOR,
                        relief="flat")
    
        # Update alternating row colors (banded rows)
        Tables.applyBandedRows(self.tree, colors=[StyleConfig.BAND_COLOR_1, StyleConfig.BAND_COLOR_2])
        
        # Ensure selection highlight matches dark mode
        style.map("Treeview", 
                  background=[("selected", StyleConfig.SELECTION_COLOR)],
                  foreground=[("selected", "#FFFFFF" if StyleConfig.DARK_MODE else "#000000")])
        
        # Update toolbar buttons
        for btn in self.buttons:
            btn.config(bg=StyleConfig.BUTTON_COLOR,
                       fg=StyleConfig.TEXT_COLOR,  
                       relief=StyleConfig.BUTTON_STYLE, 
                       padx=StyleConfig.BUTTON_PADDING, 
                       pady=StyleConfig.BUTTON_PADDING, 
                       font=(StyleConfig.FONT_FAMILY, StyleConfig.BUTTON_FONT_SIZE))
    
        # Update Sidebar Labels
        self.banking_label.config(bg=StyleConfig.BG_COLOR, 
                                  fg=StyleConfig.TEXT_COLOR, 
                                  font=(StyleConfig.FONT_FAMILY, StyleConfig.HEADING_FONT_SIZE, "bold"))
        self.investment_label.config(bg=StyleConfig.BG_COLOR, 
                                     fg=StyleConfig.TEXT_COLOR, 
                                     font=(StyleConfig.FONT_FAMILY, StyleConfig.HEADING_FONT_SIZE, "bold"))
        self.category_label.config(bg=StyleConfig.BG_COLOR, 
                                   fg=StyleConfig.TEXT_COLOR, 
                                   font=(StyleConfig.FONT_FAMILY, StyleConfig.HEADING_FONT_SIZE, "bold"))
        self.payee_label.config(bg=StyleConfig.BG_COLOR, 
                                   fg=StyleConfig.TEXT_COLOR, 
                                   font=(StyleConfig.FONT_FAMILY, StyleConfig.HEADING_FONT_SIZE, "bold"))
        self.reports_label.config(bg=StyleConfig.BG_COLOR, 
                                   fg=StyleConfig.TEXT_COLOR, 
                                   font=(StyleConfig.FONT_FAMILY, StyleConfig.HEADING_FONT_SIZE, "bold"))
    
        # Update Sidebar Account Lists
        self.accounts_list.config(bg=StyleConfig.BG_COLOR, 
                                  fg=StyleConfig.TEXT_COLOR, 
                                  font=(StyleConfig.FONT_FAMILY, StyleConfig.BUTTON_FONT_SIZE))
        self.investments_list.config(bg=StyleConfig.BG_COLOR, 
                                     fg=StyleConfig.TEXT_COLOR, 
                                     font=(StyleConfig.FONT_FAMILY, StyleConfig.BUTTON_FONT_SIZE))
        self.category_list.config(bg=StyleConfig.BG_COLOR, 
                                  fg=StyleConfig.TEXT_COLOR, 
                                  font=(StyleConfig.FONT_FAMILY, StyleConfig.BUTTON_FONT_SIZE))
        self.payee_list.config(bg=StyleConfig.BG_COLOR, 
                                  fg=StyleConfig.TEXT_COLOR, 
                                  font=(StyleConfig.FONT_FAMILY, StyleConfig.BUTTON_FONT_SIZE))
        self.reports_list.config(bg=StyleConfig.BG_COLOR, 
                                  fg=StyleConfig.TEXT_COLOR, 
                                  font=(StyleConfig.FONT_FAMILY, StyleConfig.BUTTON_FONT_SIZE))
    
        # Update Search Label in Toolbar
        self.search_label.config(bg=StyleConfig.BG_COLOR, 
                                 fg=StyleConfig.TEXT_COLOR, 
                                 font=(StyleConfig.FONT_FAMILY, StyleConfig.BUTTON_FONT_SIZE))
        self.search_entry.config(bg=StyleConfig.BG_COLOR, 
                                 fg=StyleConfig.TEXT_COLOR, 
                                 font=(StyleConfig.FONT_FAMILY, StyleConfig.BUTTON_FONT_SIZE))

    
        # Ensure the colors update immediately
        self.update_idletasks()
    
class DashboardActions:
    """
    Handles user-driven actions from the Dashboard. 
    """

    def __init__(self, main_dashboard: "Dashboard", widget_dashboard: "Dashboard") -> None:
        """
        Initializes a DashboardActions object, storing references to the application's data
        (main_dashboard) and the UI layer (widget_dashboard).

        Parameters:
        -----------
        main_dashboard : Dashboard
            The primary controller object that holds all data and logic for the application.
        widget_dashboard : Dashboard
            The Frame-based dashboard instance that manages and displays the UI widgets.
        """
        # Store references to the main (data) dashboard and the widget (UI) dashboard
        self.main_dashboard = main_dashboard
        self.widget_dashboard = widget_dashboard

    def addTransaction(self) -> None:
        """
        Opens a transaction window in 'add' mode.

        This method calls the TransactionManager to display a form for creating a new transaction.
        Once submitted, the new transaction is appended to the main_dashboard's data.
        """
        # Hand off 'self' (the actions manager) and 'main_dashboard' to the TransactionManager
        # with edit=False, meaning we are adding a new transaction rather than editing an existing one.
        TransactionManager.openTransactionWindow(self, self.main_dashboard, edit=False)

    def editTransaction(self) -> None:
        """
        Opens a transaction window in 'edit' mode.

        This method calls the TransactionManager to display a form for modifying the currently
        selected transaction in the Treeview. Once submitted, the changes are saved back to
        the main_dashboard's data.
        """
        # Hand off 'self' (the actions manager) and 'main_dashboard' to the TransactionManager
        # with edit=True, indicating we want to edit a transaction that is currently selected.
        TransactionManager.openTransactionWindow(self, self.main_dashboard, edit=True)

    def deleteTransaction(self) -> None:
        """
        Deletes the currently selected transaction(s) from the data.

        This method calls the TransactionManager to remove the selected transaction(s)
        from the main_dashboard's data, and then refreshes the UI to reflect the changes.
        """
        # Hand off 'self' (the actions manager) and 'main_dashboard' to the TransactionManager
        # for deleting whichever transaction(s) the user has selected in the UI.
        TransactionManager.deleteTransaction(self, self.main_dashboard) 

    def openData(self) -> None:
        """
        Opens one or more data files and merges the results into the main Dashboard's DataFrame.
    
        Steps:
        1. Invokes DataManager.openData() to present a file dialog for CSV or PKL files.
        2. If the user chooses a PKL file, sets the main_dashboard's save_file attribute and calls loadSaveFile().
        3. Otherwise, if CSV files are chosen, reads each CSV, processes it into a DataFrame, and appends it to
           main_dashboard.all_data. 
        4. Updates the UI to reflect newly loaded transactions.
    
        Returns:
        -------
        None
            This function modifies the application's data (main_dashboard.all_data) 
            and refreshes the UI in-place, without returning anything.
        """
        # 1) Prompt user for file(s)
        pkl_file, csv_files = DataManager.openData()
        
        # 2) If user selected a PKL file, handle loading that file
        if pkl_file:
            self.main_dashboard.save_file = pkl_file
            self.loadSaveFile()  # Load and display data from the PKL
            return
        
        # 3) Otherwise, if user selected one or more CSV files, parse and append them
        if csv_files:
            parsed_data = []
            for csv_path in csv_files:
                # Read the CSV into a DataFrame
                df = DataManager.readCSV(csv_path)
                if not df.empty:
                    account_name = os.path.basename(csv_path).split(".")[0]
                    # Convert DataFrame to a standardized format
                    parsed_df, case = DataManager.parseNewDF(self.main_dashboard, df, account_name)
                    parsed_data.append(parsed_df)
                    # Track the 'case' or data pattern for this account
                    self.main_dashboard.account_cases[os.path.basename(csv_path)] = case
                    if account_name not in self.main_dashboard.initial_account_balances:
                        self.main_dashboard.initial_account_balances[account_name] = [self.main_dashboard.day_one, 0.00]
            
            # Merge all newly read CSV data into main_dashboard.all_data
            if parsed_data:
                final_df = pd.concat(parsed_data, ignore_index=True)
                self.main_dashboard.all_data = pd.concat(
                    [self.main_dashboard.all_data, final_df],
                    ignore_index=True
                )
                self.main_dashboard.all_data = DataFrameProcessor.getDataFrameIndex(self.main_dashboard.all_data)
                self.updateTable(self.main_dashboard.all_data)
        else:
            # User cancelled or no valid files selected
            pass

    def exportData(self, event: tk.Event | None = None) -> None:
        """
        Exports transaction data to an Excel file.
    
        Uses the DataManager.exportData method to prompt for an Excel (.xlsx) save location,
        then writes the DataFrame and initial account balances to separate sheets.
    
        Parameters
        ----------
        event : tk.Event | None, optional
            An optional Tkinter event object, allowing this function to be bound to GUI events. 
            Defaults to None.
    
        Returns
        -------
        None
            The exported file is saved to disk, with no return value needed.
        """
        # Pass a copy of the data and balances to ensure we don't accidentally mutate the original.
        DataManager.exportData(
            self.main_dashboard.all_data.copy(),
            self.main_dashboard.initial_account_balances.copy(),
            new_file=''
        )       
        
    def saveData(self, event: tk.Event | None = None) -> None:
        """
        Saves the current data to a .pkl file.
    
        Uses DataManager.saveData to write the main_dashboard's all_data, initial_account_balances,
        and account_cases to a pickle file. Updates the save_file path accordingly and then
        records it to disk via changeSaveFile().
    
        Parameters
        ----------
        event : tk.Event | None, optional
            An optional Tkinter event object, allowing this function to be bound to GUI events. 
            Defaults to None.
    
        Returns
        -------
        None
            The save file is updated on disk, with no return value needed.
        """
        # Use the existing save_file path in main_dashboard.master, or prompt user if empty.
        self.main_dashboard.master.save_file = DataManager.saveData(
            self.main_dashboard.all_data.copy(),
            self.main_dashboard.initial_account_balances.copy(),
            self.main_dashboard.account_cases,
            new_file=self.main_dashboard.master.save_file
        )
        # Write the chosen file path to a tracking file for future reference
        self.main_dashboard.master.changeSaveFile()
    
    def saveDataAs(self, event: tk.Event | None = None) -> None:
        """
        Saves the current data to a new .pkl file, effectively a 'Save As' operation.
    
        Uses DataManager.saveData to open a file dialog for a new save location, writes
        main_dashboard's data and related info to pickle, and updates the application's
        tracking of the save_file path.
    
        Parameters
        ----------
        event : tk.Event | None, optional
            An optional Tkinter event object, allowing this function to be bound to GUI events.
            Defaults to None.
    
        Returns
        -------
        None
            The data is saved to a user-specified file, with no return value.
        """
        # Force user to pick a new file name by passing an empty 'new_file' arg
        self.main_dashboard.master.save_file = DataManager.saveData(
            self.main_dashboard.all_data.copy(),
            self.main_dashboard.initial_account_balances.copy(),
            self.main_dashboard.account_cases,
            new_file=''
        )
        # Update the last saved file record
        self.main_dashboard.master.changeSaveFile()
            
    def loadSaveFile(self, event: tk.Event | None = None) -> None:
        """
        Loads previously saved financial data from a .pkl file into the main Dashboard.
    
        This function:
        1. Uses DataManager.loadSaveFile(...) to load pickled data: transaction DataFrame, 
           initial account balances, and account types.
        2. If data is retrieved successfully, it updates self.main_dashboard.all_data 
           and related dictionaries.
        3. Refreshes the UI table to display the newly loaded data.
    
        Parameters
        ----------
        event : tk.Event | None, optional
            If called from a bound event, the Tkinter event is passed in. Defaults to None.
    
        Returns
        -------
        None
            The main_dashboard's data structures and the UI table are updated in-place.
        """
        all_data_df, init_bal_dict, acc_type_dict = DataManager.loadSaveFile(
            self.main_dashboard.master.save_file
        )

        # Ensure proper assignment
        if isinstance(all_data_df, pd.DataFrame):
            self.main_dashboard.all_data = all_data_df.copy()
        else:
            self.main_dashboard.all_data = pd.DataFrame()  # Fallback to an empty DataFrame
    
        self.main_dashboard.initial_account_balances = init_bal_dict
        self.main_dashboard.account_cases = acc_type_dict
    
        self.updateTable(self.main_dashboard.all_data)
    
    def updateTable(self, df:pd.DataFrame) -> None:
        """
        Clears and repopulates the Treeview widget with rows from the provided DataFrame.
    
        This function:
        1. Clears any existing rows in the Treeview.
        2. Reindexes and parses the DataFrame for date format.
        3. Determines which columns to display based on main_dashboard.table_to_display.
        4. Configures Treeview columns and headings.
        5. Inserts new rows, formatting currency columns as needed.
        6. Applies banded-row styling and updates the UI sidebars (accounts, etc.).
    
        Parameters
        ----------
        df : pd.DataFrame
            A Pandas DataFrame containing transaction data, expected to have a
            "No." column, date fields, and columns for payments, deposits, etc.
    
        Returns
        -------
        None
            The Treeview is updated in-place; no return value.
        """
        # 1) Clear existing data in the Treeview
        for row in self.widget_dashboard.tree.get_children():
            self.widget_dashboard.tree.delete(row)
        
        # 2) Reindex and parse dates
        df = DataFrameProcessor.getDataFrameIndex(df)
        df = DataFrameProcessor.convertToDatetime(df)
        
        # 3) Determine which columns to display
        if self.main_dashboard.table_to_display == 'Banking':
            desired_columns = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
            float_cols = [5, 6, 7]  # Indices that contain monetary data
            column_data = self.main_dashboard.banking_column_widths
        else:
            desired_columns = []
            float_cols = [5, 6, 7]
            column_data = self.main_dashboard.banking_column_widths

        # 4) Configure Treeview columns
        column_names = list(column_data.keys())
        column_names = [column_names[i] for i in desired_columns]
        self.widget_dashboard.tree["columns"] = column_names
        self.widget_dashboard.tree.configure(show='headings')
        
        # Create each heading
        for idx, col_name in enumerate(column_data):
            # Only configure columns in desired_columns (or all if none specified)
            if idx in desired_columns or not desired_columns:
                self.widget_dashboard.tree.heading(
                    col_name, 
                    text=col_name, 
                    anchor=tk.CENTER,
                    command=lambda c=col_name: self.sortTableByColumn(self.widget_dashboard.tree, c, False)
                )
                self.widget_dashboard.tree.column(col_name, width=column_data[col_name], anchor=tk.W)
            
         # 5) Insert new data rows
        for index, row_data in df.iterrows():
            formatted_row = list(row_data)
    
            # Format any float columns as currency
            for idx in float_cols:
                if idx < len(formatted_row):
                    formatted_row[idx] = f"${formatted_row[idx] / 100:.2f}"
                    
            # If the Payee column (index 3) is empty and Description (index 2) contains a candidate payee,
            # update both the formatted row and the underlying dataframe.
            if str(formatted_row[3]).strip() == '':
                description = str(formatted_row[2])
                for candidate in self.main_dashboard.payees:
                    if candidate and candidate.lower() in description.lower():
                        formatted_row[3] = candidate
                        self.main_dashboard.all_data.at[index, "Payee"] = candidate
                        break
                    
            #TODO Use ML to guess payee
                            
            # Keep only the desired columns if specified
            if desired_columns:
                filtered = [formatted_row[i] for i in desired_columns if i < len(formatted_row)]
                formatted_row = filtered
    
            self.widget_dashboard.tree.insert("", tk.END, values=formatted_row)
    
        # 6) Apply banded rows & update sidebars
        Tables.applyBandedRows(
            self.widget_dashboard.tree,
            colors=[StyleConfig.BAND_COLOR_1, StyleConfig.BAND_COLOR_2]
        )
        
        self.updateCategoryToolbox(df)
        self.updatePayeeToolbox(df)        
        self.updateInvestmentAccountsToolbox(df)

        self.updateBankingAccountsToolbox(df)
        self.updateBalancesInDataFrame() 
        self.updateBankingAccountsToolbox(df)
        
    def sortTableByColumn(self, tv: ttk.Treeview, col: str, sort_direction: bool) -> None:
        """
        Sorts the Treeview rows by the given column (either ascending or descending).
    
        Relies on Tables.sortTableByColumn, which handles numeric/currency parsing and re-applies
        banded-row styling after sorting.
    
        Parameters
        ----------
        tv : ttk.Treeview
            The Treeview widget to be sorted.
        col : str
            The column name (as recognized by the Treeview) to sort on.
        sort_direction : bool
            If True, sort descending; if False, sort ascending.
    
        Returns
        -------
        None
            The Treeview items are rearranged in-place to reflect the sorted order.
        """
        Tables.sortTableByColumn(
            tv, col, sort_direction,
            [StyleConfig.BAND_COLOR_1, StyleConfig.BAND_COLOR_2]
        )
            
    def updateBankingAccountsToolbox(self, df: pd.DataFrame) -> None:
        """
        Updates the sidebar listbox with banking accounts and their balances.
        
        This function clears the existing entries in the accounts listbox, then adds a default
        "All Banking Accounts" option followed by each individual account from the current
        account balances. Each balance is formatted (converted from cents to dollars with two decimal places).
        
        Parameters
        ----------
        df : pd.DataFrame
            A DataFrame representing transaction data (not directly used in this function).
        
        Returns
        -------
        None
            Updates the UI in-place.
        """
        # Clear previous entries from the accounts listbox
        self.widget_dashboard.accounts_list.delete(0, tk.END)  # Clear previous entries

        # Insert default "All Banking Accounts" option
        self.widget_dashboard.accounts_list.insert(tk.END, "All Banking Accounts")
     
        # Insert individual banking accounts with their balances formatted as dollars
        for account, balance in self.main_dashboard.current_account_balances.items():    
            self.widget_dashboard.accounts_list.insert(tk.END, f"{account} ${balance / 100:.2f}")  # Format balance
        
    def updateInvestmentAccountsToolbox(self, df: pd.DataFrame) -> None:
        #TODO
        """Updates the sidebar listbox with only investment accounts and their balances."""
        self

        
    def updateCategoryToolbox(self, df: pd.DataFrame) -> None:
        """
        Refreshes the category_list Listbox with all known categories.
    
        This method:
        1. Clears any existing entries from the category_list.
        2. Inserts a special "All Categories" option at the top.
        3. Iterates over self.main_dashboard.categories and inserts each category
           into the category_list.
    
        Parameters
        ----------
        df : pd.DataFrame
            A DataFrame representing the application's data. Although not directly
            used here, it is provided for consistency with other toolbox update methods
            and may be used later if filtering or additional logic is needed.
    
        Returns
        -------
        None
            The category_list Listbox is updated in-place with the available categories.
        """
        # 1) Clear all existing entries in the category list
        self.widget_dashboard.category_list.delete(0, tk.END)
    
        # 2) Add a special "All Categories" option
        self.widget_dashboard.category_list.insert(tk.END, "All Categories")
        
        self.getCategories()
    
        # 3) Insert each category from main_dashboard.categories
        for category in self.main_dashboard.categories:
            self.widget_dashboard.category_list.insert(tk.END, category)
            
    def updatePayeeToolbox(self, df: pd.DataFrame) -> None:
        """
        Refreshes the payee_list Listbox with all known payees.
    
        This method:
        1. Clears any existing entries from the payee_list.
        2. Inserts a special "All Payees" option at the top.
        3. Iterates over self.main_dashboard.payees and inserts each payee
           into the payee_list.
    
        Parameters
        ----------
        df : pd.DataFrame
            A DataFrame representing the application's data. Although not directly
            used here, it is provided for consistency with other toolbox update methods
            and may be used later if filtering or additional logic is needed.
    
        Returns
        -------
        None
            The payee_list Listbox is updated in-place with the available payees.
        """
        # 1) Clear all existing entries in the payee list
        self.widget_dashboard.payee_list.delete(0, tk.END)
    
        # 2) Add a special "All Payess" option
        self.widget_dashboard.payee_list.insert(tk.END, "All Payees")
        
        self.getPayees()
    
        # 3) Insert each payee from main_dashboard.payees
        for payee in self.main_dashboard.payees:
            self.widget_dashboard.payee_list.insert(tk.END, payee)

    def trackBankBalances(self) -> None:
        """
        Opens a Toplevel window to manually review and update the latest balance for each banking account.

        The window displays three columns:
        - Account name (from main_dashboard.all_data)
        - Initial Date (loaded from main_dashboard.initial_account_balances or defaulted)
        - Initial Value (converted from cents to dollars)

        For each banking account:
        1. If the account is not yet in the initial_account_balances DataFrame, a new row is appended
            with a default date (self.main_dashboard.day_one) and a zero balance.
        2. The corresponding row is retrieved to initialize entry widgets for date and balance.
        3. The balance is shown in dollars (dividing the stored cents by 100).

        Inner helper functions:
        - validateInputs() -> bool: Validates the user input for each account.
        - applyChanges() -> None: Updates the initial_account_balances DataFrame with the entered values,
            then calls updateBalancesInDataFrame() and closes the window.
        - closeWindow(event: tk.Event | None = None) -> None: Closes the balance window.

        Returns
        -------
        None
            The UI window is displayed, and when changes are applied, the DataFrame and UI are updated.
        """
    
        if "Account" not in self.main_dashboard.all_data:
            return
    
        balance_window = tk.Toplevel(self.main_dashboard)
        balance_window.title("Track Bank Balances")
    
        # Create header labels
        headers = ["Account", "Date", "Balance"]
        for col, header in enumerate(headers):
            tk.Label(balance_window, 
                     text=header, 
                     font=(StyleConfig.FONT_FAMILY, StyleConfig.HEADING_FONT_SIZE, "bold"),
                     bg=StyleConfig.BG_COLOR, 
                     fg=StyleConfig.TEXT_COLOR
                     ).grid(row=0, column=col, padx=5, pady=5)
    
        # Dictionary to hold references to the entry widgets for each account
        entry_fields = {}
    
         # Get unique banking accounts from all_data
        banking_accounts = self.main_dashboard.all_data["Account"].unique().tolist()
        for row, account in enumerate(banking_accounts, start=1):
            tk.Label(balance_window, 
                     text=account, 
                     bg=StyleConfig.BG_COLOR, 
                     fg=StyleConfig.TEXT_COLOR
                     ).grid(row=row, column=0, padx=5, pady=5, sticky="w")
    
            # If the account is not already in the initial_account_balances DataFrame, append a new row.
            if account not in self.main_dashboard.initial_account_balances["Account"].values:
                new_row = pd.DataFrame({
                    "Account": [account],
                    "Initial Date": [self.main_dashboard.day_one],
                    "Initial Value": [0]
                })
                self.main_dashboard.initial_account_balances = pd.concat(
                    [self.main_dashboard.initial_account_balances, new_row],
                    ignore_index=True
                )
    
            # Retrieve the row for the current account
            account_row = self.main_dashboard.initial_account_balances[
                self.main_dashboard.initial_account_balances["Account"] == account
            ]
            if not account_row.empty:
                initial_date = account_row["Initial Date"].iloc[0]
                initial_value = account_row["Initial Value"].iloc[0]
            else:
                # Fallback defaults if the account is not found.
                initial_date = self.main_dashboard.day_one
                initial_value = 0

            # Date entry widget (shows the initial date)
            date_var = tk.StringVar(value=initial_date)
            date_entry = tk.Entry(balance_window, textvariable=date_var, width=12)
            date_entry.grid(row=row, column=1, padx=5, pady=5)

            # Balance entry widget (converts cents to dollars for display)
            balance_var = tk.StringVar(value=f"{initial_value / 100:.2f}")
            balance_entry = tk.Entry(balance_window, textvariable=balance_var, width=10)
            balance_entry.grid(row=row, column=2, padx=5, pady=5)
    
            # Store the Tk variables for later update
            entry_fields[account] = (date_var, balance_var)
            
        window_width, window_height = 300, (row+1)*31+60
        Windows.openRelativeWindow(balance_window, 
                                   main_width=self.main_dashboard.winfo_x(), 
                                   main_height=self.main_dashboard.winfo_y(), 
                                   width=window_width, 
                                   height=window_height
                                   )
    
        # Button frame
        button_frame = tk.Frame(balance_window, bg=StyleConfig.BG_COLOR)
        button_frame.grid(row=len(banking_accounts) + 1, column=0, columnspan=3, pady=10)
        
        # --- Inner helper functions ---
        def validateInputs() -> bool:
            """
            Validates that each account's date is in a correct format and that the balance is a valid number.

            Returns
            -------
            bool
                True if all inputs are valid; otherwise, False.
            """
            date_formats = ["%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y", "%d %b %Y", "%b %d, %Y"]
            errors = []
    
            for account, (date_var, balance_var) in entry_fields.items():
                date_value = date_var.get().strip()
                balance_value = balance_var.get().strip()

                # Validate Date
                valid_date = False
                for fmt in date_formats:
                    try:
                        parsed_date = datetime.strptime(date_value, fmt).date()
                        date_var.set(parsed_date.strftime("%Y-%m-%d"))  # Normalize format
                        valid_date = True
                        break
                    except ValueError:
                        continue
    
                if not valid_date:
                    errors.append(f"Invalid date format for {account}: {date_value}")
    
                # Validate Balance
                try:
                    balance_value = float(balance_value)
                    balance_var.set(f"{balance_value:.2f}")  # Ensure formatting
                except ValueError:
                    errors.append(f"Invalid balance for {account}: {balance_value}")
    
            if errors:
                messagebox.showerror("Input Error", "\n".join(errors))
                return False
            return True
    
        def applyChanges():
            """
            Saves the entered date and balance for each account into the initial_account_balances DataFrame,
            then propagates balance changes and closes the balance window.
            """
            for account, (date_var, balance_var) in entry_fields.items():
                try:
                    date_value = date_var.get()
                    balance_value = int(float(balance_var.get()) * 100)
                except ValueError:
                    messagebox.showerror("Error", f"Invalid balance input for {account}. Please enter a number.")
                    return

                # Create a mask to find the row for this account
                mask = self.main_dashboard.initial_account_balances["Account"] == account
                if mask.any():
                    # Update existing row
                    self.main_dashboard.initial_account_balances.loc[mask, "Initial Date"] = date_value
                    self.main_dashboard.initial_account_balances.loc[mask, "Initial Value"] = balance_value
                else:
                    # Append a new row if the account doesn't exist
                    new_row = pd.DataFrame({
                        "Account": [account],
                        "Initial Date": [date_value],
                        "Initial Value": [balance_value]
                    })
                    self.main_dashboard.initial_account_balances = pd.concat(
                        [self.main_dashboard.initial_account_balances, new_row],
                        ignore_index=True
                    )

            self.updateBalancesInDataFrame()
            balance_window.destroy()
    
        def closeWindow(event: tk.Event | None = None) -> None:
            """Closes the balance tracking window."""
            balance_window.destroy()
        # --- End inner functions ---
    
        # Buttons
        ok_button = tk.Button(button_frame, 
                              text="OK", 
                              command=applyChanges, 
                              bg=StyleConfig.BUTTON_COLOR, 
                              fg=StyleConfig.TEXT_COLOR, 
                              relief=StyleConfig.BUTTON_STYLE)
        ok_button.grid(row=0, column=0, padx=5, pady=5)
    
        cancel_button = tk.Button(button_frame, 
                                  text="Cancel", 
                                  command=closeWindow, 
                                  bg=StyleConfig.BUTTON_COLOR, 
                                  fg=StyleConfig.TEXT_COLOR, 
                                  relief=StyleConfig.BUTTON_STYLE)
        cancel_button.grid(row=0, column=1, padx=5, pady=5)
    
        # Bind keyboard shortcuts
        balance_window.bind("<Return>", lambda event: applyChanges())
        balance_window.bind("<Escape>", closeWindow)
    
        balance_window.focus_force()
           
    def updateBalancesInDataFrame(self) -> None:
        """
        Propagates balance changes in the transactions DataFrame (master.all_data) based on the
        latest initial account balances stored in initial_account_balances.

        For each account in initial_account_balances:
        - If the "Initial Date" is not equal to self.day_one, the function calculates the
            propagated balance using calculateBalancesPerType and updates current_account_balances.
        - Otherwise, sets the current balance for that account to 0.00.
        Finally, the updated master.all_data DataFrame is displayed by calling updateTable.

        Returns
        -------
        None
            The master.all_data DataFrame is updated in-place and the UI refreshed.
        """
        if self.main_dashboard.all_data.empty:
            return
        
        # Iterate over each row in the initial_account_balances DataFrame.
        for _, row in self.main_dashboard.initial_account_balances.iterrows():
            account     = row["Account"]
            init_date   = row["Initial Date"]
            init_value  = row["Initial Value"]
            if init_date != self.main_dashboard.day_one:
                # Calculate the propagated balance for this account and update current_account_balances.
                self.main_dashboard.all_data, self.main_dashboard.current_account_balances[account] = self.calculateBalancesPerType(
                                                                                self.main_dashboard.all_data.copy(), 
                                                                                account, 
                                                                                init_date, 
                                                                                init_value)

            else:
                self.main_dashboard.current_account_balances[account] = 0.00
        
    def calculateBalancesPerType(self, df: pd.DataFrame, account: str, given_date: str, given_balance: float) -> pd.DataFrame:
        """
        Calculates balances for all transactions in an account based on its type, given a known balance on a specific date.
    
        Parameters:
            df (pd.DataFrame): DataFrame containing transactions.
            account (str): Account name to filter transactions.
            given_date (str): Known date in 'YYYY-MM-DD' format.
            given_balance (float): Known balance on that date.
            account_type (str): The category of the account (Type 1, Type 2, etc.).
    
        Returns:
            pd.DataFrame: Updated DataFrame with recalculated balances.
        """
        
        # Ensure the 'Date' column is in datetime format
        df["Date"] = pd.to_datetime(df["Date"])
    
        # Filter transactions for the specified account
        account_df = df[df["Account"] == account].copy()
    
        # Sort transactions by date to ensure proper balance propagation
        account_df = account_df.sort_values(by="Date")
    
        # Find the index of the transaction that has the given date
        reference_idx = account_df[account_df["Date"] == given_date].index.min()

        # Get account type
        account_type = self.main_dashboard.account_cases[account]
        
        if pd.isna(reference_idx):
    
            # Find the nearest previous transaction
            previous_idx = account_df[account_df["Date"] < given_date].index.max()
            next_idx = account_df[account_df["Date"] > given_date].index.min()
    
            if not pd.isna(previous_idx):
                reference_idx = previous_idx
            elif not pd.isna(next_idx):
                reference_idx = next_idx
            else:
                return df  # Exit if no valid transactions exist
        
        # Set the balance for the known transaction
        account_df.at[reference_idx, "Balance"] = given_balance
    
        # Forward propagate balance for later transactions
        for i in range(reference_idx, reference_idx+len(account_df)):
            if i == reference_idx:
                prev_balance = given_balance
            else:
                prev_balance = account_df.at[i - 1, "Balance"]
            deposit = account_df.at[i, "Deposit"]
            payment = account_df.at[i, "Payment"]
    
            if account_type == "Type 1":
                account_df.at[i, "Balance"] = prev_balance + payment + deposit  # (-) Payments, (+) Deposit, 0.00 Balance
            elif account_type == "Type 2":
                account_df.at[i, "Balance"] = prev_balance - payment - deposit  # (+) Payments, (-) Deposit, 0.00 Balance
            elif account_type == "Type 3":
                account_df.at[i, "Balance"] = prev_balance + deposit - payment  # Normal case
            elif account_type == "Type 4":
                account_df.at[i, "Balance"] = prev_balance + payment  # Deposits are ignored
            else:
                return df 
            
        last_balance = account_df.at[i, 'Balance']
           
        #TODO
        """
        # Backward propagate balance for earlier transactions
        for i in range(reference_idx - 1, -1, -1):
            next_balance = account_df.at[i + 1, "Balance"]
            deposit = account_df.at[i, "Deposit"]
            payment = account_df.at[i, "Payment"]
    
            if account_type == "Type 1":
                account_df.at[i, "Balance"] = next_balance - payment - deposit  # (-) Payments, (+) Deposit, 0.00 Balance
            elif account_type == "Type 2":
                account_df.at[i, "Balance"] = next_balance + payment + deposit  # (+) Payments, (-) Deposit, 0.00 Balance
            elif account_type == "Type 3":
                account_df.at[i, "Balance"] = next_balance - deposit + payment  # Normal case
            elif account_type == "Type 4":
                account_df.at[i, "Balance"] = next_balance - payment  # Deposits are ignored
            else:
                return df
        """
        
        # Merge updated balances back into the original DataFrame
        df.update(account_df)
    
        return df, last_balance

    def viewPayees(self) -> None:
        """
        Opens a Tkinter Toplevel window for managing (add, modify, delete) payees.
    
        The window displays all current payees in a Listbox and provides:
        - 'Add' and 'Modify' functions that use a simpledialog to get input from the user.
        - 'Delete' function with confirmation.
        - An 'Exit' button to close the window.
        - Scrollable Listbox to handle many payees.
    
        Returns
        -------
        None
            The payee management UI is created and run in a child window; nothing is returned.
        """
        # Create a Toplevel window anchored relative to the main dashboard
        payee_window = tk.Toplevel(self.main_dashboard)
        payee_window.title("Manage Payees")
        
        # Set window dimensions and position
        window_height, window_width = 400, 300
        Windows.openRelativeWindow(
            payee_window, 
            main_width=self.main_dashboard.winfo_x(),
            main_height=self.main_dashboard.winfo_y(),
            width=window_width, 
            height=window_height
        )
        
        # Title label
        ttk.Label(
            payee_window, 
            text="Payees",
            font=(StyleConfig.FONT_FAMILY, StyleConfig.HEADING_FONT_SIZE, "bold")
        ).pack(pady=5)
        
        # Frame for the Listbox and scrollbar
        list_frame = ttk.Frame(payee_window)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
        # Create a Listbox to display existing payees
        payee_listbox = tk.Listbox(list_frame, height=15)
        payee_listbox.pack(side=tk.LEFT, fill="both", expand=True)
    
        # Attach a vertical scrollbar to the listbox
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=payee_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        payee_listbox.config(yscrollcommand=scrollbar.set)
        
        def loadPayees() -> None:
            """
            Refreshes the main_dashboard.payees list and reloads them into the listbox.
            """
            self.getPayees()  # Merges file payees with any new ones from the DataFrame
    
            # Clear and repopulate the listbox
            payee_listbox.delete(0, tk.END)
            for payee in self.main_dashboard.payees:
                payee_listbox.insert(tk.END, payee)
    
        def addPayee() -> None:
            """
            Opens a small dialog to input a new payee, then appends it to the list.
            Updates the payee file if successful.
            """
            new_payee = simpledialog.askstring("Add Payee", "Enter new payee:")
            if new_payee and new_payee not in self.main_dashboard.payees:
                self.main_dashboard.payees.append(new_payee)
                payee_listbox.insert(tk.END, new_payee)
                savePayees()
    
        def modifyPayee() -> None:
            """
            Opens a small dialog to rename the currently selected payee.
            """
            selected_index = payee_listbox.curselection()
            if selected_index:
                old_payee = payee_listbox.get(selected_index)
                new_payee = simpledialog.askstring(
                    "Modify Payee",
                    "Enter new name:",
                    initialvalue=old_payee
                )
                if new_payee and new_payee not in self.main_dashboard.payees:
                    self.main_dashboard.payees[selected_index[0]] = new_payee
                    payee_listbox.delete(selected_index)
                    payee_listbox.insert(selected_index, new_payee)
                    savePayees()
    
        def deletePayee() -> None:
            """
            Deletes the currently selected payee after user confirmation.
            Updates the payee file and reloads the listbox view.
            """
            selected_index = payee_listbox.curselection()
            if selected_index:
                confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this payee?")
                if confirm:
                    # Remove item from self.main_dashboard.payees
                    sorted(self.main_dashboard.payees.pop(selected_index[0]))
                    payee_listbox.delete(selected_index)
                    savePayees()
                # Refresh payees in the UI if needed
                self.viewPayees()
    
        def savePayees() -> None:
            """
            Overwrites the payee file with the current contents of main_dashboard.payees.
            """
            with open(self.main_dashboard.payee_file, "w") as f:
                for payee in self.main_dashboard.payees:
                    f.write(payee + "\n")
            self.main_dashboard.payees = sorted(self.main_dashboard.payees)
        
        def closeWindow(event=None) -> None:
            """
            Closes the payee window when called.
            """
            payee_window.destroy()
    
        # Call loadPayees initially to populate the listbox
        loadPayees()
    
        # Frame to hold the Add / Modify / Delete / Exit buttons
        button_frame = tk.Frame(payee_window, bg=StyleConfig.BG_COLOR)
        button_frame.pack(pady=10)
    
        # Button styling from StyleConfig
        button_attributes = {
            "bg": StyleConfig.BUTTON_COLOR,
            "fg": StyleConfig.TEXT_COLOR,
            "font": (StyleConfig.FONT_FAMILY, StyleConfig.BUTTON_FONT_SIZE),
            "relief": StyleConfig.BUTTON_STYLE,
            "padx": StyleConfig.BUTTON_PADDING,
            "pady": StyleConfig.BUTTON_PADDING,
            "width": 10  # Ensure a consistent width for each button
        }
        
       # Create the buttons
        add_button = tk.Button(button_frame, text="Add", command=addPayee, **button_attributes)
        modify_button = tk.Button(button_frame, text="Modify", command=modifyPayee, **button_attributes)
        delete_button = tk.Button(button_frame, text="Delete", command=deletePayee, **button_attributes)
        exit_button = tk.Button(button_frame, text="Exit", command=closeWindow, **button_attributes)
    
        # Lay out buttons: Add, Modify, Delete in the first row, Exit in the second row
        add_button.grid(row=0, column=0, padx=5, pady=5)
        modify_button.grid(row=0, column=1, padx=5, pady=5)
        delete_button.grid(row=0, column=2, padx=5, pady=5)
        exit_button.grid(row=1, column=0, columnspan=3, padx=5, pady=5)
    
        # Bind Escape key to close the window, and give focus to it
        payee_window.bind("<Escape>", lambda event: closeWindow())
        payee_window.focus_force()
        
    def getPayees(self)-> None:
        """
        Loads payees from a text file and merges them with any existing
        payees found in the main_dashboard.all_data DataFrame.
    
        This function:
        1. Reads lines from main_dashboard.payee_file.
        2. Gathers unique 'Payees' entries from the all_data DataFrame (if present).
        3. Combines both sets of payees and sorts them.
        4. Stores the final list of payees in main_dashboard.payees.
    
        Returns
        -------
        None
            The main_dashboard.payees list is updated in-place; nothing is returned.
        """
        # 1) Load payees from file
        with open(self.main_dashboard.payee_file, "r") as f:
            file_payees = [line.strip() for line in f.readlines()]
        
        try:
            # 2) Gather payees from the DataFrame if "Payee" column exists
            if "Payee" in self.main_dashboard.all_data.columns:
                data_payees = set(self.main_dashboard.all_data["Payee"].dropna().unique())
            else:
                data_payees = set()
        except AttributeError:
            # If all_data is missing or not set, fall back to empty
            data_payees = set()
        
        # 3) Merge both sets of payees; 4) sort and store in main_dashboard.payees
        self.main_dashboard.payees = sorted(set(file_payees) | data_payees)   
          
    def getCategories(self) -> None:
        """
        Loads categories from a text file and merges them with any existing
        categories found in the main_dashboard.all_data DataFrame.
    
        This function:
        Reads lines from main_dashboard.category_file.
        Stores the final list of categories in main_dashboard.categories.
    
        Returns
        -------
        None
            The main_dashboard.categories list is updated in-place; nothing is returned.
        """
        with open(self.main_dashboard.category_file, "r") as f:
            file_categories = [line.strip() for line in f.readlines()]
        
        self.main_dashboard.categories = sorted(file_categories)   

    def viewCategories(self) -> None:
        """
        Opens a Tkinter Toplevel window for managing (add, modify, delete) categories.
    
        The window displays all current categories in a Listbox and provides:
        - 'Add' and 'Modify' functions that use a simpledialog to get input from the user.
        - 'Delete' function with confirmation.
        - An 'Exit' button to close the window.
        - Scrollable Listbox to handle many categories.
    
        Returns
        -------
        None
            The category management UI is created and run in a child window; nothing is returned.
        """
        # Create a Toplevel window anchored relative to the main dashboard
        category_window = tk.Toplevel(self.main_dashboard)
        category_window.title("Manage Categories")
        
        # Set window dimensions and position
        window_height, window_width = 400, 300
        Windows.openRelativeWindow(
            category_window, 
            main_width=self.main_dashboard.winfo_x(),
            main_height=self.main_dashboard.winfo_y(),
            width=window_width, 
            height=window_height
        )
        
        # Title label
        ttk.Label(
            category_window, 
            text="Categories",
            font=(StyleConfig.FONT_FAMILY, StyleConfig.HEADING_FONT_SIZE, "bold")
        ).pack(pady=5)
        
        # Frame for the Listbox and scrollbar
        list_frame = ttk.Frame(category_window)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
        # Create a Listbox to display existing categories
        category_listbox = tk.Listbox(list_frame, height=15)
        category_listbox.pack(side=tk.LEFT, fill="both", expand=True)
    
        # Attach a vertical scrollbar to the listbox
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=category_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        category_listbox.config(yscrollcommand=scrollbar.set)
        
        def loadCategories() -> None:
            """
            Refreshes the main_dashboard.categories list and reloads them into the listbox.
            """
            self.getCategories()  # Merges file categories with any new ones from the DataFrame
    
            # Clear and repopulate the listbox
            category_listbox.delete(0, tk.END)
            for category in self.main_dashboard.categories:
                category_listbox.insert(tk.END, category)
    
        def addCategory() -> None:
            """
            Opens a small dialog to input a new category, then appends it to the list.
            Updates the category file if successful.
            """
            new_category = simpledialog.askstring("Add Category", "Enter new category:")
            if new_category and new_category not in self.main_dashboard.categories:
                self.main_dashboard.categories.append(new_category)
                category_listbox.insert(tk.END, new_category)
                saveCategories()
    
        def modifyCategory() -> None:
            """
            Opens a small dialog to rename the currently selected category.
            """
            selected_index = category_listbox.curselection()
            if selected_index:
                old_category = category_listbox.get(selected_index)
                new_category = simpledialog.askstring(
                    "Modify Category",
                    "Enter new name:",
                    initialvalue=old_category
                )
                if new_category and new_category not in self.main_dashboard.categories:
                    self.main_dashboard.categories[selected_index[0]] = new_category
                    category_listbox.delete(selected_index)
                    category_listbox.insert(selected_index, new_category)
                    saveCategories()
    
        def deleteCategory() -> None:
            """
            Deletes the currently selected category after user confirmation.
            Updates the category file and reloads the listbox view.
            """
            selected_index = category_listbox.curselection()
            if selected_index:
                confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this category?")
                if confirm:
                    # Remove item from self.main_dashboard.categories
                    sorted(self.main_dashboard.categories.pop(selected_index[0]))
                    category_listbox.delete(selected_index)
                    saveCategories()
                # Refresh categories in the UI if needed
                self.viewCategories()
    
        def saveCategories() -> None:
            """
            Overwrites the category file with the current contents of main_dashboard.categories.
            """
            with open(self.main_dashboard.category_file, "w") as f:
                for category in self.main_dashboard.categories:
                    f.write(category + "\n")
        
        def closeWindow(event=None) -> None:
            """
            Closes the category window when called.
            """
            category_window.destroy()
    
        # Call loadCategories initially to populate the listbox
        loadCategories()
    
        # Frame to hold the Add / Modify / Delete / Exit buttons
        button_frame = tk.Frame(category_window, bg=StyleConfig.BG_COLOR)
        button_frame.pack(pady=10)
    
        # Button styling from StyleConfig
        button_attributes = {
            "bg": StyleConfig.BUTTON_COLOR,
            "fg": StyleConfig.TEXT_COLOR,
            "font": (StyleConfig.FONT_FAMILY, StyleConfig.BUTTON_FONT_SIZE),
            "relief": StyleConfig.BUTTON_STYLE,
            "padx": StyleConfig.BUTTON_PADDING,
            "pady": StyleConfig.BUTTON_PADDING,
            "width": 10  # Ensure a consistent width for each button
        }
        
       # Create the buttons
        add_button = tk.Button(button_frame, text="Add", command=addCategory, **button_attributes)
        modify_button = tk.Button(button_frame, text="Modify", command=modifyCategory, **button_attributes)
        delete_button = tk.Button(button_frame, text="Delete", command=deleteCategory, **button_attributes)
        exit_button = tk.Button(button_frame, text="Exit", command=closeWindow, **button_attributes)
    
        # Lay out buttons: Add, Modify, Delete in the first row, Exit in the second row
        add_button.grid(row=0, column=0, padx=5, pady=5)
        modify_button.grid(row=0, column=1, padx=5, pady=5)
        delete_button.grid(row=0, column=2, padx=5, pady=5)
        exit_button.grid(row=1, column=0, columnspan=3, padx=5, pady=5)
    
        # Bind Escape key to close the window, and give focus to it
        category_window.bind("<Escape>", lambda event: closeWindow())
        category_window.focus_force()

    def displayReports(self):
        #TODO
        """

        """
        self

    def viewOptions(self, new_settings: bool = True) -> None:
        """
        Opens a window to adjust various application settings such as fonts, colors, sizes, etc.
    
        Parameters
        ----------
        new_settings : bool, optional
            If True, initializes a temporary dictionary (self.temp_settings) with fresh Tk variables 
            based on current StyleConfig values. If False, reuses existing variables to avoid 
            overwriting user selections. Defaults to True.
    
        Returns
        -------
        None
            Displays a Toplevel window for selecting and applying style changes.
        """
        options_window = tk.Toplevel(self.main_dashboard)
        options_window.title("Application Settings")
        options_window.resizable(False, False)
    
        ttk.Label(
            options_window,
            text="Customize Appearance",
            font=(StyleConfig.FONT_FAMILY, StyleConfig.HEADING_FONT_SIZE, "bold")
        ).pack(pady=5)
    
        # If requested, initialize fresh references to style config variables
        if new_settings:
            self.temp_settings = {
                "FONT_FAMILY":          tk.StringVar(value=StyleConfig.FONT_FAMILY),
                "FONT_SIZE":            tk.IntVar(value=StyleConfig.FONT_SIZE),
                "HEADING_FONT_SIZE":    tk.IntVar(value=StyleConfig.HEADING_FONT_SIZE),
                "BUTTON_FONT_SIZE":     tk.IntVar(value=StyleConfig.BUTTON_FONT_SIZE),
                "ROW_HEIGHT":           tk.IntVar(value=StyleConfig.ROW_HEIGHT),
                "TEXT_COLOR":           tk.StringVar(value=StyleConfig.TEXT_COLOR),
                "BG_COLOR":             tk.StringVar(value=StyleConfig.BG_COLOR),
                "HEADER_COLOR":         tk.StringVar(value=StyleConfig.HEADER_COLOR),
                "BUTTON_COLOR":         tk.StringVar(value=StyleConfig.BUTTON_COLOR),
                "BAND_COLOR_1":         tk.StringVar(value=StyleConfig.BAND_COLOR_1),
                "BAND_COLOR_2":         tk.StringVar(value=StyleConfig.BAND_COLOR_2),
                "SCROLL_SPEED":         tk.IntVar(value=StyleConfig.SCROLL_SPEED),
                "BUTTON_STYLE":         tk.StringVar(value=StyleConfig.BUTTON_STYLE),
                "BUTTON_PADDING":       tk.IntVar(value=StyleConfig.BUTTON_PADDING),
                "BUTTON_BORDER_RADIUS": tk.IntVar(value=StyleConfig.BUTTON_BORDER_RADIUS),
                "DARK_MODE":            tk.BooleanVar(value=StyleConfig.DARK_MODE),
            }
    
        # Calculate a basic window size based on the number of settings
        window_height = len(self.temp_settings.keys()) * 28 + 100
        window_width = 260
        Windows.openRelativeWindow(
            options_window,
            main_width=self.main_dashboard.winfo_x(),
            main_height=self.main_dashboard.winfo_y(),
            width=window_width,
            height=window_height
        )
    
        def pickColor(var: tk.StringVar, entry_widget: tk.Entry) -> None:
            """
            Opens a color chooser dialog, updating var with the chosen color
            and the associated Tk Entry widget. Dynamically re-applies style changes.
            """
            options_window.lift()  # Ensure window is on top
    
            def openColorChooser():
                color_code = colorchooser.askcolor(title="Choose a Color")[1]  # Hex value
                if color_code:
                    var.set(color_code)
                    entry_widget.delete(0, tk.END)
                    entry_widget.insert(0, color_code)
    
                    # Update StyleConfig dynamically and re-apply styling
                    setattr(StyleConfig, var._name, color_code)
                    self.widget_dashboard.applyStyleChanges()
    
                self.viewOptions(new_settings=False)
    
            # Delayed call to open the color chooser
            options_window.after(10, openColorChooser)
    
        def createSettingRow(
            label: str,
            var: tk.Variable,
            parent: ttk.Frame,
            options: list[str] | None = None,
            is_color: bool = False
        ) -> None:
            """
            Creates a single row (label + input widget) within the settings window.
    
            Parameters
            ----------
            label : str
                The text to display for this row's label.
            var : tk.Variable
                The Tkinter variable that holds the current value for this setting.
            parent : ttk.Frame
                The parent container where the row widget is placed.
            options : list[str] | None, optional
                If provided, a list of values used to create a dropdown (ComboBox).
            is_color : bool, optional
                If True, creates a color-chooser button next to the entry widget.
            """
            frame = ttk.Frame(parent)
            frame.pack(fill="x", padx=10, pady=2)
    
            ttk.Label(frame, text=label, width=20, anchor="w").pack(side=tk.LEFT)
    
            if is_color:
                entry = ttk.Entry(frame, textvariable=var, width=10)
                entry.pack(side=tk.LEFT, padx=5)
    
                color_button = tk.Button(
                    frame,
                    text="🎨",
                    width=4,
                    command=lambda: pickColor(var, entry),
                    bg=StyleConfig.BUTTON_COLOR,
                    fg=StyleConfig.TEXT_COLOR,
                    relief=StyleConfig.BUTTON_STYLE
                )
                color_button.pack(side=tk.LEFT)
    
            elif isinstance(var, tk.StringVar) and not options:
                entry = ttk.Entry(frame, textvariable=var, width=15)
                entry.pack(side=tk.RIGHT, fill="x", expand=True)
    
            elif isinstance(var, tk.IntVar):
                entry = ttk.Spinbox(frame, textvariable=var, from_=1, to=30, width=5)
                entry.pack(side=tk.RIGHT, fill="x", expand=True)
    
            elif isinstance(var, tk.BooleanVar):
                checkbox = ttk.Checkbutton(frame, variable=var)
                checkbox.pack(side=tk.RIGHT)
    
            elif options:
                dropdown = ttk.Combobox(frame, textvariable=var, values=options, state="readonly", width=15)
                dropdown.pack(side=tk.RIGHT, fill="x", expand=True)
    
        # Create a row for each of the stored settings
        createSettingRow("Font Family:",        self.temp_settings["FONT_FAMILY"], options_window, sorted(list(font.families())))
        createSettingRow("Font Size:",          self.temp_settings["FONT_SIZE"], options_window)
        createSettingRow("Header Font Size:",   self.temp_settings["HEADING_FONT_SIZE"], options_window)
        createSettingRow("Button Font Size:",   self.temp_settings["BUTTON_FONT_SIZE"], options_window)
        createSettingRow("Row Height:",         self.temp_settings["ROW_HEIGHT"], options_window)
        createSettingRow("Scroll Speed:",       self.temp_settings["SCROLL_SPEED"], options_window)
        createSettingRow("Text Color:",         self.temp_settings["TEXT_COLOR"], options_window, is_color=True)
        createSettingRow("Background Color:",   self.temp_settings["BG_COLOR"], options_window, is_color=True)
        createSettingRow("Header Color:",       self.temp_settings["HEADER_COLOR"], options_window, is_color=True)
        createSettingRow("Button Color:",       self.temp_settings["BUTTON_COLOR"], options_window, is_color=True)
        createSettingRow("Band Color 1:",       self.temp_settings["BAND_COLOR_1"], options_window, is_color=True)
        createSettingRow("Band Color 2:",       self.temp_settings["BAND_COLOR_2"], options_window, is_color=True)
        createSettingRow("Button Style:",       self.temp_settings["BUTTON_STYLE"], options_window, ["flat", "groove", "sunken", "raised", "ridge"])
        createSettingRow("Button Padding:",     self.temp_settings["BUTTON_PADDING"], options_window)
        createSettingRow("Button Radius:",      self.temp_settings["BUTTON_BORDER_RADIUS"], options_window)
        createSettingRow("Enable Dark Mode:",   self.temp_settings["DARK_MODE"], options_window)
    
        def resetToStandard() -> None:
            """
            Resets all style settings to their defaults (from StyleConfig) and saves them to file.
            """
            default_settings = StyleConfig.getDefaultSettings()
    
            # Apply the default settings dynamically
            for key, value in default_settings.items():
                setattr(StyleConfig, key, value)
    
            self.widget_dashboard.applyStyleChanges()
            saveUserSettings(data=default_settings)
            closeWindow()
    
        def applyChanges(event: tk.Event | None = None) -> None:
            """
            Reads all current variables (temp_settings), updates StyleConfig,
            applies them in the UI, and saves to disk.
            """
            for key, var in self.temp_settings.items():
                setattr(StyleConfig, key, var.get())
    
            # Toggle Dark Mode if changed
            StyleConfig.applyDarkMode(self.temp_settings["DARK_MODE"].get())
    
            self.widget_dashboard.applyStyleChanges()
            saveUserSettings()
            closeWindow()
    
        def saveUserSettings(data: dict[str, any] | None = None) -> None:
            """
            Writes the current or default style settings to a pickle file.
            
            Parameters
            ----------
            data : dict[str, any] | None, optional
                If provided, this dictionary is saved to file. Otherwise, we write
                the user's current self.temp_settings. Defaults to None.
            """
            user_settings_path = self.main_dashboard.master.user_settings_file
            if data is None:
                with open(user_settings_path, "wb") as f:
                    pickle.dump({key: var.get() for key, var in self.temp_settings.items()}, f)
            else:
                with open(user_settings_path, "wb") as f:
                    pickle.dump({key: var for key, var in data.items()}, f)
    
        def closeWindow(event: tk.Event | None = None) -> None:
            """
            Closes the options window.
            """
            options_window.destroy()
    
        # Frame for the Apply, Standard, Cancel buttons
        button_frame = ttk.Frame(options_window)
        button_frame.pack(pady=10)
    
        apply_button = tk.Button(
            button_frame,
            text="Apply",
            command=applyChanges,
            bg=StyleConfig.BUTTON_COLOR,
            fg=StyleConfig.TEXT_COLOR,
            relief=StyleConfig.BUTTON_STYLE
        )
        apply_button.grid(row=0, column=0, padx=5, pady=5)
    
        standard_button = tk.Button(
            button_frame,
            text="Standard Options",
            command=resetToStandard,
            bg=StyleConfig.BUTTON_COLOR,
            fg=StyleConfig.TEXT_COLOR,
            relief=StyleConfig.BUTTON_STYLE
        )
        standard_button.grid(row=1, column=0, columnspan=2, padx=5, pady=5)
    
        cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            command=closeWindow,
            bg=StyleConfig.BUTTON_COLOR,
            fg=StyleConfig.TEXT_COLOR,
            relief=StyleConfig.BUTTON_STYLE
        )
        cancel_button.grid(row=0, column=1, padx=5, pady=5)
    
        # Bind Return/Escape keys for convenience
        options_window.bind("<Return>", applyChanges)
        options_window.bind("<Escape>", closeWindow)
    
        options_window.focus_force()
    
    def editCell(self, event: tk.Event | None = None) -> None:
        """
        Handles in-place editing of a cell in the Treeview based on its column type.
    
        This function:
        1. Identifies which row and column were clicked.
        2. If it's a date column, opens a calendar dialog for date selection.
        3. If it's a numeric or text column, replaces the cell with an Entry widget.
        4. If it's a dropdown column (Category/Account), shows a readonly Combobox.
        5. Validates or formats the entered text (e.g. removing $ from Payment columns),
           then updates the underlying DataFrame and refreshes the UI.
    
        Parameters
        ----------
        event : tk.Event | None, optional
            A Tkinter event object that provides the x,y location of the click, 
            or None if called manually. Defaults to None.
    
        Returns
        -------
        None
            The Treeview cell is replaced with an appropriate editing widget, 
            and on confirm, the underlying DataFrame is updated in-place.
        """
        
        def saveEdit(new_value: str) -> None:
            """
            Saves the new value into the DataFrame and updates the UI.
    
            Parameters
            ----------
            new_value : str
                The text or date selected by the user.
            """
            # Retrieve the 'No.' from the row's values, which identifies the record in the DataFrame
            selected_number = int(self.widget_dashboard.tree.item(item, "values")[0])
            index_to_update = self.main_dashboard.all_data[self.main_dashboard.all_data["No."] == selected_number].index

            if not index_to_update.empty:
                # Handle numeric columns (Payment, Deposit, Balance)
                if col_name in ["Payment", "Deposit", "Balance"]:
                    try:
                        new_value_converted  = float(new_value.replace("$", "").replace(",", "")) * 100
                    except ValueError:
                        messagebox.showerror("Invalid Input", "Please enter a valid number.")
                        return
    
                # Handle date column - store as standardized YYYY-MM-DD string
                elif col_name == "Date":
                    new_value_converted  = Utility.formatDateFromString(new_value)
                else:
                    new_value_converted = new_value
                    
                # Update the DataFrame in-place
                self.main_dashboard.all_data.at[index_to_update[0], col_name] = new_value_converted
    
                # Now update the corresponding cell in the Treeview without reloading the entire table
                current_values = list(self.widget_dashboard.tree.item(item, "values"))
                if col_name in ["Payment", "Deposit", "Balance"]:
                    display_value = f"${new_value_converted / 100:.2f}"
                elif col_name == "Date":
                    display_value = new_value_converted  # Already in YYYY-MM-DD format
                else:
                    display_value = new_value
                current_values[col_index] = display_value
                self.widget_dashboard.tree.item(item, values=current_values)
    
            cancelEdit()

        def cancelEdit(event: tk.Event | None = None) -> None:
            """
            Cancels editing by closing any open widget without saving changes.
            
            Parameters
            ----------
            event : tk.Event | None, optional
                Optional event object if the user triggered cancellation via a key 
                (Escape) or focus loss. Defaults to None.
            """
            if "entry_widget" in locals():
                entry_widget.destroy()
            if "cal_win" in locals():
                cal_win.destroy()
            if "dropdown" in locals():
                dropdown.destroy()
        
        # Identify which item (row) and column user clicked
        item = self.widget_dashboard.tree.identify_row(event.y)     # e.g. "I001"
        column = self.widget_dashboard.tree.identify_column(event.x)  # e.g. "#1"
        
        # If nothing was clicked or invalid, exit
        if not item or not column:
            return
    
        # Convert the "#1" style column ID to a zero-based index
        col_index = int(column[1:]) - 1
        # Get the column name from the Treeview columns list
        col_name = self.widget_dashboard.tree["columns"][col_index]
    
        # Get the current cell value
        current_value = self.widget_dashboard.tree.item(item, "values")[col_index]
    
        # Skip editing the 'No.' column (unique ID)
        if col_name == "No.":
            return 
    
        # =======================================
        #  Date Column Editing
        # =======================================
        if col_name == "Date":
            try:
                initial_date = datetime.strptime(current_value, "%Y-%m-%d").date()
            except ValueError:
                # If current_value is not a valid date, default to today
                initial_date = date.today()
    
            # Create a Toplevel window with a calendar
            cal_win = tk.Toplevel(self.main_dashboard)
            cal_win.title("Select Date")
            cal_win.geometry("250x250")
    
            cal = Calendar(
                cal_win,
                selectmode="day",
                year=initial_date.year,
                month=initial_date.month,
                day=initial_date.day,
                date_pattern='yyyy-mm-dd'
            )
            cal.pack(padx=10, pady=10)
    
            def pickDate(event: tk.Event | None = None) -> None:
                """
                Retrieves the selected date from the calendar and invokes saveEdit.
                
                Parameters
                ----------
                event : tk.Event | None, optional
                    If the user pressed Enter, or triggered the selection by a button click,
                    the event is passed. Defaults to None.
                """
                new_date = cal.get_date()
                saveEdit(new_date)
    
            # Buttons for confirming or canceling date selection
            tk.Button(cal_win, text="OK", command=pickDate).pack(pady=5, padx=5)
            tk.Button(cal_win, text="Cancel", command=cancelEdit).pack(pady=5, padx=5)
    
            # Key bindings for date selection
            cal_win.bind("<Return>", pickDate)
            cal_win.bind("<Escape>", cancelEdit)
            cal_win.focus_force()  # Bring this Toplevel to the front
    
        # =======================================
        #  Text / Numeric Editing Columns
        # =======================================
        if col_name in ["Payment", "Deposit", "Balance", "Note"]:
            x, y, width, height = self.widget_dashboard.tree.bbox(item, column)
            
            # Create an Entry widget over the cell
            entry_widget = tk.Entry(self.widget_dashboard.tree)
            entry_widget.place(x=x, y=y, width=width, height=height)
            
            # Populate the Entry with current cell value
            entry_widget.insert(0, current_value)
            entry_widget.select_range(0, tk.END)
            entry_widget.focus_set()
    
            # Bind keys to handle user acceptance or cancellation
            entry_widget.bind("<Return>", lambda e: saveEdit(entry_widget.get()))
            entry_widget.bind("<Tab>", lambda e: saveEdit(entry_widget.get()))
            entry_widget.bind("<FocusOut>", cancelEdit)
    
        # =======================================
        #  Dropdown Columns
        # =======================================
        elif col_name in ["Category", "Account", "Payee", "Account Type"]:
            x, y, width, height = self.widget_dashboard.tree.bbox(item, column)
            
            # Create a readonly Combobox over the cell
            dropdown = ttk.Combobox(self.widget_dashboard.tree, state="readonly")
            dropdown.place(x=x, y=y, width=width, height=height)
    
            # Provide the dropdown values
            if col_name == "Category":
                dropdown["values"] = self.main_dashboard.categories
            elif col_name == "Payee":
                dropdown["values"] = self.main_dashboard.payees
            elif col_name == "Account":
                accounts = self.main_dashboard.all_data["Account"].unique().tolist()
                dropdown["values"] = accounts
            elif col_name == "Account Type":
                dropdown["values"] = ['Banking', 'Investments']
    
            dropdown.set(current_value)
            
            # When user picks an item from the dropdown, call saveEdit
            dropdown.bind("<<ComboboxSelected>>", lambda e: saveEdit(dropdown.get()))
            dropdown.focus_set()
            
            # If user moves focus away, cancel editing
            dropdown.bind("<FocusOut>", cancelEdit)
    
    def smoothScroll(self, event=None) -> None:
        """
        Adjusts vertical scrolling speed for a Tkinter Listbox widget during mouse wheel events.
    
        This function:
        1. Verifies the widget receiving the event is a Listbox.
        2. Retrieves the user-configured scroll speed from StyleConfig.SCROLL_SPEED.
        3. Calls the Listbox's yview_scroll method with a speed-dependent delta,
           allowing for custom "smooth" or accelerated scrolling behavior.
    
        Parameters
        ----------
        event : tk.Event | None, optional
            The Tkinter event object triggered by the mouse wheel.
            If None, the function does nothing.
    
        Returns
        -------
        None
            Modifies the Listbox's scroll position in-place.
        """
        widget = event.widget
        if isinstance(widget, tk.Listbox):
            speed = StyleConfig.SCROLL_SPEED
            # event.delta > 0 means the wheel was scrolled 'up', 
            # so we negate the speed to scroll 'up' in the list.
            widget.yview_scroll(-speed if event.delta > 0 else speed, "units")
            
    def selectAllRows(self) -> None:
        """
        Selects all rows in the transaction table (Treeview).
    
        This method:
        1. Retrieves all item IDs from the Treeview via get_children().
        2. Calls selection_set(...) on those items, marking each row as selected.
        """
        self.widget_dashboard.tree.selection_set(
            self.widget_dashboard.tree.get_children()
        )
            
    def clearTable(self, event: tk.Event | None = None) -> None:
        """
        Prompts the user for confirmation and, if accepted, clears all transactions.
    
        This method:
        1. Checks if main_dashboard.all_data has entries.
        2. Asks the user to confirm deletion of all transactions.
        3. If confirmed, resets main_dashboard.all_data to an empty DataFrame,
           and removes all items from the accounts list, investments list, 
           and the Treeview.
    
        Parameters
        ----------
        event : tk.Event | None, optional
            A Tkinter event object, typically passed when bound to a GUI event.
            Defaults to None.
    
        Returns
        -------
        None
            Modifies the application's data and UI elements in-place.
        """
        if not self.main_dashboard.all_data.empty:
            confirm = messagebox.askyesno(
                "Confirm Delete",
                "Are you sure you want to delete all transaction(s)?"
            )
            
            if confirm is None or not confirm:  # User canceled or closed dialog
                return
            
            # If confirmed, clear everything
            self.main_dashboard.all_data = pd.DataFrame()
            self.widget_dashboard.accounts_list.delete(0, tk.END)
            self.widget_dashboard.investments_list.delete(0, tk.END)
            self.widget_dashboard.tree.delete(*self.widget_dashboard.tree.get_children())
    
    def searchData(
                    self,
                    single_query: str | None = None,
                    advanced_criteria: dict[str, str] | None = None
                ) -> None:
        """
        Filters self.main_dashboard.all_data based on either a single query
        or an advanced dictionary of per-column queries. Then updates the table.
    
        Parameters
        ----------
        single_query : str | None, optional
            A single user input that should be tested against all columns,
            by partial decimal substring in numeric columns or text match in others.
            If provided, advanced_criteria should be None.
        advanced_criteria : dict[str, str] | None, optional
            A dictionary mapping column -> user input. Each key's value is tested
            only against that particular column. If provided, single_query
            should be None.
    
        Returns
        -------
        None
            The DataFrame is filtered in-place, and the UI updated with the results.
    
        Notes
        -----
        - For numeric columns (Payment, Deposit, Balance), we do a substring match
          on the float-as-string (e.g. "123.45"). Thus "123." will match "123.45".
        - For text columns, we do a case-insensitive substring match.
        - If both single_query and advanced_criteria are None, we revert to showing all rows.
        - If the data is missing/empty, we show a warning and do nothing.
        """
        # 1) Make sure we have data
        if not hasattr(self.main_dashboard, "all_data") or self.main_dashboard.all_data.empty:
            messagebox.showwarning("Warning", "No data to search!")
            return
    
        original_df = self.main_dashboard.all_data.copy()
    
        # 2) Determine if we got a single_query or advanced_criteria
        if single_query and advanced_criteria:
            messagebox.showerror(
                "Search Error",
                "Cannot specify both single_query and advanced_criteria at once."
            )
            return
        elif not single_query and not advanced_criteria:
            # If neither is provided, just reset the table
            self.updateTable(original_df)
            return
    
        # We'll define a helper function that checks if
        # a row's numeric col matches a string (partial decimal) or if it has a text match.
        def numericMatches(row_val: float | int, user_str: str) -> bool:
            """
            Convert row_val from cents to a string (e.g. "123.45") and see if user_str
            is contained within it, ignoring case.
            """
            try:
                num_dollars = float(row_val) / 100
                numeric_str = f"{num_dollars:.2f}".lower()
                return user_str.lower() in numeric_str
            except (ValueError, TypeError):
                return False
    
        # 3) If single_query is given, apply it to all columns
        if single_query:
            q = single_query.strip().lower()
            if not q:
                # If user typed nothing, show everything
                self.updateTable(original_df)
                return
    
            def rowMatchesSingleQuery(row: pd.Series) -> bool:
                for col in row.index:
                    val_str = str(row[col]).lower()
                    if col in ["Payment", "Deposit", "Balance"]:
                        if numericMatches(row[col], q):
                            return True
                    # Also do a text-based match
                    if q in val_str:
                        return True
                return False
    
            filtered_df = original_df[original_df.apply(rowMatchesSingleQuery, axis=1)]
            self.updateTable(filtered_df)
            return
    
        # 4) Otherwise, if we have advanced_criteria (column -> user_input)
        else:
            filtered_df = original_df
            for col_name, user_input in advanced_criteria.items():
                user_input = user_input.strip().lower()
                if not user_input:
                    continue  # skip empty fields
    
                if col_name in ["Payment", "Deposit", "Balance"]:
                    # Build a mask using substring logic
                    def maskFn(row_val):
                        return numericMatches(row_val, user_input)
    
                    mask = filtered_df[col_name].apply(maskFn)
                    filtered_df = filtered_df[mask]
                else:
                    # For text columns, partial match
                    filtered_df = filtered_df[
                        filtered_df[col_name].astype(str).str.lower().str.contains(user_input, na=False)
                    ]
    
            self.updateTable(filtered_df)
            return
        
    def searchTransactions(self) -> None:
        """
        Handles the 'basic' (single-field) search from the search_entry in the toolbar.
        """
        query = self.widget_dashboard.search_entry.get().strip().lower()
        # If user typed nothing, just revert to entire dataset
        if not query:
            self.updateTable(self.main_dashboard.all_data)
            return
    
        self.searchData(single_query=query)  # Calls the unified search logic    

    def openAdvancedSearch(self) -> None:
        """
        Opens a small Toplevel window that provides an entry box for each column,
        enabling an advanced filtering mechanism.
    
        After the user clicks 'Search', we build a dict of column->user_input
        and call self.searchData(advanced_criteria=that_dict).
        """
        if not hasattr(self.main_dashboard, "all_data") or self.main_dashboard.all_data.empty:
            messagebox.showwarning("Warning", "No data to search!")
            return
    
        search_window = tk.Toplevel(self.main_dashboard)
        search_window.title("Advanced Search")
    
        ttk.Label(
            search_window,
            text="Advanced Search",
            font=(StyleConfig.FONT_FAMILY, StyleConfig.FONT_SIZE, "bold")
        ).pack(pady=5)
    
        input_frame = ttk.Frame(search_window)
        input_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
        # Build a dict of column->(Entry widget)
        entry_widgets = {}
    
        # Make a labeled Entry for each column
        for col_name in self.main_dashboard.all_data.columns:
            row_frame = ttk.Frame(input_frame)
            row_frame.pack(fill="x", pady=2)
    
            ttk.Label(
                row_frame,
                text=f"{col_name}:",
                width=12,
                anchor="w",
                font=(StyleConfig.FONT_FAMILY, StyleConfig.FONT_SIZE, "bold")
            ).pack(side=tk.LEFT)
    
            entry = ttk.Entry(row_frame, width=15)
            entry.pack(side=tk.RIGHT, expand=True, fill="x")
            entry_widgets[col_name] = entry
    
        def performAdvancedSearch(event: tk.Event | None = None) -> None:
            """Collect user inputs and pass them to unified searchData()."""
            # Build a dict of { column_name: user_string }
            adv_dict = {}
            for col, w in entry_widgets.items():
                user_text = w.get().strip()
                # We'll keep all entries, even empty,
                # because searchData() will skip empty ones
                adv_dict[col] = user_text
    
            # Now call the unified search function
            self.searchData(advanced_criteria=adv_dict)
    
            # Close the advanced search window
            search_window.destroy()
    
        # Create a "Search" button
        search_button = tk.Button(
            search_window,
            text="Search",
            command=performAdvancedSearch,
            bg=StyleConfig.BUTTON_COLOR,
            fg=StyleConfig.TEXT_COLOR,
            relief=StyleConfig.BUTTON_STYLE
        )
        search_button.pack(pady=10)
    
        # Handle geometry
        window_width, window_height = 300, (len(self.main_dashboard.all_data.columns) * 30) + 60
        search_window.geometry(f"{window_width}x{window_height}")
        search_window.resizable(False, False)
    
        # Key bindings
        search_window.bind("<Return>", performAdvancedSearch)
        search_window.bind("<Escape>", lambda e: search_window.destroy())
        
        search_window.focus_force()
    
    def filterByAccountType(self, account_type: str) -> None:
        """
        Filters the transactions based on a specified account type (e.g., "Banking" or "Investments").
        
        This method:
        1. Checks if main_dashboard.all_data has entries.
        2. Subsets the DataFrame where the "Account Type" column matches the given account_type.
        3. Calls updateTable() with the filtered DataFrame to refresh the UI.
    
        Parameters
        ----------
        account_type : str
            The type of account to filter by, e.g. "Banking" or "Investments".
    
        Returns
        -------
        None
            The Treeview is updated to show only rows whose "Account Type" matches the passed argument.
        """
        # Ensure all_data exists before filtering
        if not hasattr(self.main_dashboard, "all_data") or self.main_dashboard.all_data.empty:
            messagebox.showwarning("Warning", "No data available to filter!")
            return
    
        # Filter by account type and update the UI
        filtered_df = self.main_dashboard.all_data[
            self.main_dashboard.all_data["Account Type"] == account_type
        ]
        self.updateTable(filtered_df)
    
    def filterTransactionsByInvestmentAccount(self, event: tk.Event | None = None) -> None:
        """
        Filters transactions based on the selected investment account from the investments_list Listbox.
    
        This method:
        1. Retrieves the user's selection (e.g., "All Investment Accounts" or "AccountName $XXXX.XX").
        2. If "All Investment Accounts" is chosen, shows the entire dataset.
        3. Otherwise, extracts the account_name by splitting on " $" and filters rows
           where the "Account" column matches the extracted name.
        4. Updates the UI to display only the matching transactions.
    
        Parameters
        ----------
        event : tk.Event | None, optional
            The event triggered (generally on a listbox double-click). Defaults to None.
    
        Returns
        -------
        None
            The Treeview is updated to display only the filtered rows for the chosen investment account.
        """
        selected_index = self.widget_dashboard.investments_list.curselection()
        if not selected_index:
            return
    
        selected_text = self.widget_dashboard.investments_list.get(selected_index)
    
        # If "All Investment Accounts," revert to the full dataset
        if selected_text == "All Investment Accounts":
            filtered_df = self.main_dashboard.all_data.copy()
        else:
            # Extract the account name before the " $" suffix
            account_name = selected_text.split(" $")[0]
            filtered_df = self.main_dashboard.all_data[
                self.main_dashboard.all_data["Account"] == account_name
            ].copy()
    
        self.updateTable(filtered_df)
        
    def filterTransactionsByCategory(self, event: tk.Event | None = None) -> None:
        """
        Filters transactions by the selected category from the category_list Listbox.
    
        This method:
        1. Retrieves the user's category selection from self.widget_dashboard.category_list.
        2. If "All Categories" is selected, resets the table to show all data.
        3. Otherwise, displays only rows from main_dashboard.all_data
           where the 'Category' column matches the user's selection.
        4. Updates the Treeview widget with the filtered DataFrame.
    
        Parameters
        ----------
        event : tk.Event | None, optional
            The event object if triggered by a Listbox double-click.
            Defaults to None.
    
        Returns
        -------
        None
            The application's UI is updated to display the relevant transactions in-place.
        """
        selected_index = self.widget_dashboard.category_list.curselection()
        if not selected_index:
            return  # No selection made
    
        category = self.widget_dashboard.category_list.get(selected_index)
    
        if category == "All Categories":
            filtered_df = self.main_dashboard.all_data.copy()
        else:
            filtered_df = self.main_dashboard.all_data[
                self.main_dashboard.all_data["Category"] == category
            ].copy()
    
        self.updateTable(filtered_df)
        
    def filterTransactionsByPayee(self, event: tk.Event | None = None) -> None:
        """
        Filters transactions by the selected payee from the payee_list Listbox.
    
        This method:
        1. Retrieves the user's payee selection from self.widget_dashboard.payee_list.
        2. If "All Payees" is selected, resets the table to show all data.
        3. Otherwise, displays only rows from main_dashboard.all_data
           where the 'Payee' column matches the user's selection.
        4. Updates the Treeview widget with the filtered DataFrame.
    
        Parameters
        ----------
        event : tk.Event | None, optional
            The event object if triggered by a Listbox double-click.
            Defaults to None.
    
        Returns
        -------
        None
            The application's UI is updated to display the relevant transactions in-place.
        """
        selected_index = self.widget_dashboard.payee_list.curselection()
        if not selected_index:
            return  # No selection made
    
        payee = self.widget_dashboard.payee_list.get(selected_index)
    
        if payee == "All Payees":
            filtered_df = self.main_dashboard.all_data.copy()
        else:
            #TODO FIX EMPTY FILTERED DF
            filtered_df = self.main_dashboard.all_data[
                self.main_dashboard.all_data["Payee"] == payee
            ].copy()
    
        self.updateTable(filtered_df)
        
    def filterTransactionsByBankingAccount(self, event: tk.Event | None = None) -> None:
        """
        Filters transactions based on the selected banking account from the accounts_list Listbox.
    
        This method:
        1. Retrieves the user's selection (e.g., "All Banking Accounts" or "AccountName $XXXX.XX").
        2. If "All Banking Accounts" is chosen, shows the entire dataset.
        3. Otherwise, extracts the account_name by splitting on " $" and filters rows
           where the "Account" column matches the extracted name.
        4. Updates the UI to display only the matching transactions.
    
        Parameters
        ----------
        event : tk.Event | None, optional
            The event triggered (generally on a listbox double-click). Defaults to None.
    
        Returns
        -------
        None
            The Treeview is updated to display only the filtered rows for the chosen banking account.
        """
        selected_index = self.widget_dashboard.accounts_list.curselection()
        if not selected_index:
            return
    
        selected_text = self.widget_dashboard.accounts_list.get(selected_index)
    
        if selected_text == "All Banking Accounts":
            filtered_df = self.main_dashboard.all_data.copy()
        else:
            account_name = selected_text.split(" $")[0]
            filtered_df = self.main_dashboard.all_data[
                self.main_dashboard.all_data["Account"] == account_name
            ].copy()
    
        self.updateTable(filtered_df)
        

    
    
class Dashboard(tk.Frame):
    def __init__(self, master=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        
        self.master = master  # Reference to the FinanceTracker (Main Window)
        
        self.ui_manager = DashboardUI(parent_dashboard=self, master=self)
        self.ui_actions = DashboardActions(self, self.ui_manager)
        
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)
        
        self.grid(row=0, column=0, sticky="nsew") 
        self.rowconfigure(0, weight=1)    # So row 0 grows
        self.columnconfigure(0, weight=1)
        
        # Example data that might come from the Dashboard or be defined here
        self.banking_column_widths = {
            "No.": 40,
            "Date": 80,
            "Description": 350,
            "Payee": 150,
            "Category": 150,
            "Payment": 70,
            "Deposit": 70,
            "Balance": 90,
            "Account": 150,
            "Note": 250, 
            "Account Type": 0
        }      
        
        
        self.investment_column_widths = {
            "No.": 30,
            "Date": 60,
            "Payee": 350,
            "Category": 200,
            "Gain": 80,
            "Loss": 80,
            "Balance": 100,
            "Account": 100,
            "Note": 200, 
            "Account Type": 100
        }
        
        self.day_one = "1970-1-1"
        
        self.initial_account_balances = {}
        self.current_account_balances = {}
        self.account_cases = {}
        
        # 
        self.table_to_display = 'Banking'
        
        self.category_file = os.path.join(os.path.dirname(__file__), "Categories.txt")
        self.ui_actions.getCategories()
        
        self.payee_file = os.path.join(os.path.dirname(__file__), "Payees.txt")
        self.ui_actions.getPayees()
        
        self.all_data = pd.DataFrame()
        
        # Delay loading the saved file until UI is ready
        self.after(500, self.ui_actions.loadSaveFile)
        
    def openData(self) -> None:
        """
        Opens a data file (CSV or PKL) for parsing and loading into the application.
    
        Delegates the action to ui_actions.openData().
        """
        self.ui_actions.openData()
    
    def clearTable(self) -> None:
        """
        Clears all rows in the current transaction table.
    
        Delegates the action to ui_actions.clearTable().
        """
        self.ui_actions.clearTable()
    
    def saveData(self) -> None:
        """
        Saves data to a file in the default or previously used location.
    
        Delegates the action to ui_actions.saveData().
        """
        self.ui_actions.saveData()
    
    def saveDataAs(self) -> None:
        """
        Saves data to a new file location chosen by the user.
    
        Delegates the action to ui_actions.saveDataAs().
        """
        self.ui_actions.saveDataAs()
    
    def openSearch(self) -> None:
        """
        Opens the advanced search dialog for column-by-column filtering.
    
        Delegates the action to ui_actions.openAdvancedSearch().
        """
        self.ui_actions.openAdvancedSearch()
    
    def selectAllRows(self) -> None:
        """
        Selects all rows in the transaction table.
    
        Delegates the action to ui_actions.selectAllRows().
        """
        self.ui_actions.selectAllRows()
    
    def deleteTransaction(self) -> None:
        """
        Deletes the currently selected transaction(s) from the table and data.
    
        Delegates the action to ui_actions.deleteTransaction().
        """
        self.ui_actions.deleteTransaction()

    def trainClassifier(self) -> None:
        payee_classifier, category_classifier = Classifier.trainPayeeAndCategoryClassifier(self.all_data) 

        predicted_payee, predicted_category = Classifier.predictTransactionLabels(
                                                                description="Advance Auto Parts", 
                                                                payment = 8423,
                                                                deposit = 0, 
                                                                account = "Capital One Credit", 
                                                                payee_pipeline = payee_classifier, 
                                                                category_pipeline = category_classifier
                                                                )

        
class TEMPHOLDING:
        
    def updateBankingAccountsToolbox(self, df: pd.DataFrame) -> None:
        """Updates the sidebar listbox with only banking accounts and their balances."""
        self.accounts_list.delete(0, tk.END)  # Clear previous entries

        # Add "All Banking Accounts" option
        self.accounts_list.insert(tk.END, "All Banking Accounts")
     
        # Insert individual banking accounts
        for account, balance in self.current_account_balances.items():    
            self.accounts_list.insert(tk.END, f"{account} ${balance / 100:.2f}")  # Format balance
            
    def updateInvestmentAccountsToolbox(self, df: pd.DataFrame) -> None:
        """Updates the sidebar listbox with only investment accounts and their balances."""
        self.investments_list.delete(0, tk.END)  # Clear previous entries
    
        # Filter only investment accounts
        investment_df = df[df["Account Type"] == "Investment"]
    
        # Calculate account balances
        self.investment_balances = DataFrameProcessor.accountBalance(investment_df)
    
        # Add "All Investment Accounts" option
        self.investments_list.insert(tk.END, "All Investment Accounts")
    
        # Insert individual investment accounts
        for account, balance in self.investment_balances.items():
            self.investments_list.insert(tk.END, f"{account} ${balance / 100:.2f}")  # Format balance
            
    
        
    
        
    
     
    
        