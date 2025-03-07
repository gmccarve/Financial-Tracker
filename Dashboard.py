import os
import pandas as pd
import numpy as np
import pickle
import importlib

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

from Utility import Utility, Tables, Windows
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
        if 'Number' in df.columns:
            df = df.drop(columns=['Number'])
        df.insert(0, 'Number', df.index)
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
        computed_balances = computed_balances["Deposit"] - computed_balances["Payment"]  # Convert to Series
    
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
    def readXLSX(file_path):
        """
        Load financial data from an Excel (XLSX) file
        
        Parameters:
            file_path (str): Path to the CSV file.
    
        Returns:
            (pd.DataFrame): DataFrames of transactions
        """
        try:
            df = pd.read_excel(file_path)
            return df
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {e}")
            return pd.DataFrame()        
    @staticmethod 
    def retrieveData() -> List[Tuple[str, pd.DataFrame]]:
        """Opens a CSV file, parses it, and converts it into the expected format."""
        #file_paths = filedialog.askopenfilenames(filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")])
        
        file_paths = [
                        "C:/Users/Admin/OneDrive/Desktop/Documents/Budget/2025/AFCU Checking.csv",
                        "C:/Users/Admin/OneDrive/Desktop/Documents/Budget/2025/AFCU Credit.csv",
                        "C:/Users/Admin/OneDrive/Desktop/Documents/Budget/2025/AFCU Hyundai Loan.csv",
                        "C:/Users/Admin/OneDrive/Desktop/Documents/Budget/2025/AFCU Savings.csv", 
                        "C:/Users/Admin/OneDrive/Desktop/Documents/Budget/2025/Capital One Credit.csv",
                        "C:/Users/Admin/OneDrive/Desktop/Documents/Budget/2025/PFCU Checking.csv",
                        "C:/Users/Admin/OneDrive/Desktop/Documents/Budget/2025/PFCU Credit.csv",
                        "C:/Users/Admin/OneDrive/Desktop/Documents/Budget/2025/PFCU Savings.csv"]        
        
        if not file_paths:
            return [] # User cancelled file selection  
        
        parsed_data = []

        for file_path in file_paths:
            file_type       = file_path.split(".")[-1]
            account_name    = file_path.split("/")[-1].split(".")[0] 

            if file_type == 'csv':
                df = DataManager.readCSV(file_path)
            elif file_type == 'xlsx':
                df = DataManager.readXLSX(file_path)
            else:
                continue # Skip unsupported file types
            
            parsed_data.append((account_name, df))

        return parsed_data
    @staticmethod     
    def parseNewDF(df:pd.DataFrame, account_name: str, dashboard: "Dashboard") -> pd.DataFrame:
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
            "Transaction ID": "Number",
            "Transaction Date": "Date",
            "Description": "Payee",
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

        # Select only the relevant columns in the correct order
        df = df[expected_headers]
  
        return df       
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
    def reloadData() -> None:
        """
        Reloads financial data by triggering the file selection function.
    
        This function clears the current window and reloads data files.
    
        Retuns:
            None
        """
        #self.selectFilesAndFolders(reload=True) 
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
    def saveDataAs(df:pd.DataFrame, new_file: str) -> str:
        """Exports the transaction table to CSV or Excel."""
        if new_file == '':
            file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                     filetypes=[("Excel files", "*.xlsx"),
                                                                 ("CSV files", "*.csv")])
            if not file_path:
                return
        else:
            file_path = new_file
    
        if file_path.endswith(".csv"):
            df.to_csv(file_path, index=False)
        else:
            df.to_excel(file_path, index=False)
    
        messagebox.showinfo("Export Complete", f"Data saved to {file_path}")  
        
        return file_path

class TransactionManager:            
    @staticmethod     
    def openTransactionWindow(dashboard: "Dashboard", edit=False):
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
                        value = "1970-01-01"
                    
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
            new_df = DataManager.parseNewDF(new_df, stored_values.get("Account", "Unknown"), dashboard)
        
            # Ensure proper data type conversion
            for col in ["Number", "Payment", "Deposit", "Balance"]:
                if col in new_df.columns:
                    new_df[col] = pd.to_numeric(new_df[col], errors='coerce').fillna(0).astype(int)  # Convert to int

            if prefill_data:
                # Editing an existing transaction
                selected_items = dashboard.tree.selection()
                selected_number = int(dashboard.tree.item(selected_items[0], "values")[0])  # Convert to int for index matching
        
                # Find the index of the selected transaction in all_data
                index_to_update = dashboard.master.all_data[dashboard.master.all_data["Number"] == selected_number].index
        
                if not index_to_update.empty:
                    # Ensure new_df has the same columns as all_data before assignment
                    new_df = new_df[dashboard.master.all_data.columns]
        
                    # Assign values row-wise
                    for col in dashboard.master.all_data.columns:
                        dashboard.master.all_data.loc[index_to_update, col] = new_df.iloc[0][col]
        
                else:
                    messagebox.showerror("Error", "Transaction not found for editing.")
                    return
            else:
                # Adding new transaction
                dashboard.master.all_data = pd.concat([dashboard.master.all_data, new_df], ignore_index=True)
        
            dashboard.master.all_data = DataFrameProcessor.getDataFrameIndex(dashboard.master.all_data)
            dashboard.updateTable(dashboard.master.all_data)
        
            transaction_window.destroy()
    
        def closeWindow(event=None):
            """Closes the transaction window."""
            transaction_window.destroy()
    
        if edit:
           selected_items = dashboard.tree.selection()
           if not selected_items:
               messagebox.showwarning("Warning", "No transaction selected for editing.")
               return
       
           selected_values = dashboard.tree.item(selected_items[0], "values")
           headers = list(dashboard.banking_column_widths.keys())
       
           prefill_data = dict(zip(headers, selected_values)) 
           
        else:
            prefill_data = None
    
        # Create transaction window
        transaction_window = tk.Toplevel(dashboard)
        window_width, window_height = 300, 330
        Windows.openRelativeWindow(transaction_window, main_width=dashboard.winfo_x(), main_height=dashboard.winfo_y(), width=window_width, height=window_height)
        transaction_window.title("Edit Transaction" if edit else "Add Transaction")
    
        transaction_window.bind("<Escape>", closeWindow)
        transaction_window.bind("<Return>", submitTransaction)
    
        entry_fields = {}
        columns = list(dashboard.banking_column_widths.keys())[1:]
    
        # Configure the second column to expand with window resizing
        transaction_window.grid_columnconfigure(1, weight=1)
    
        for idx, column in enumerate(columns):
            tk.Label(transaction_window, text=column, anchor="w").grid(row=idx, column=0, padx=10, pady=5, sticky="w")
    
            entry = tk.Entry(transaction_window)
            entry.grid(row=idx, column=1, padx=10, pady=5, sticky="ew")
    
            if prefill_data and column in prefill_data:
                entry.insert(0, prefill_data[column])
    
            entry_fields[column] = entry
    
        submit_button = tk.Button(transaction_window, text="Submit", command=submitTransaction)
        submit_button.grid(row=len(columns), column=0, columnspan=2, pady=10)
    
        submit_button.focus_set()
    
    @staticmethod 
    def deleteTransaction(dashboard: "Dashboard") -> None:
        """Deletes the selected transaction(s) from the data table."""
        selected_items = dashboard.tree.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "No transactions selected!")
            return
    
        selected_numbers = [dashboard.tree.item(item, "values")[0] for item in selected_items]
        selected_numbers = set(map(int, selected_numbers))
    
        indices_to_drop = dashboard.master.all_data[dashboard.master.all_data["Number"].isin(selected_numbers)].index
    
        confirm = messagebox.askyesno("Confirm Delete", 
                                      f"Are you sure you want to delete {len(indices_to_drop)} transaction(s)?", 
                                      parent=dashboard.master)
        if confirm is None or not confirm:  # Explicitly check for None
            return  # User canceled or closed the dialog, so exit
    
        dashboard.master.all_data = dashboard.master.all_data.drop(indices_to_drop).reset_index(drop=True)
        dashboard.master.all_data = DataFrameProcessor.getDataFrameIndex(dashboard.master.all_data)
    
        dashboard.updateTable(dashboard.master.all_data)
                    

#TODO RELATIVE WINDOW OPENINGS
    
class Dashboard(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        
        self.master = master  # Reference to the FinanceTracker (Main Window)
        self.last_saved_file = os.path.join(os.path.dirname(__file__), "lastSavedFile.txt")
        
        # Define column widths for transaction table
        self.banking_column_widths = {
            "Number": 35,
            "Date": 50,
            "Payee": 350,
            "Category": 200,
            "Payment": 80,
            "Deposit": 80,
            "Balance": 100,
            "Account": 100,
            "Note": 200, 
            "Account Type": 100
        }
        
        self.investment_column_widths = {
            "Number": 35,
            "Date": 50,
            "Payee": 350,
            "Category": 200,
            "Gain": 80,
            "Loss": 80,
            "Balance": 100,
            "Account": 100,
            "Note": 200, 
            "Account Type": 100
        }
        
        self.account_balances = {}
        
        self.category_file = os.path.join(os.path.dirname(__file__), "Categories.txt")
        self.getCategories()
        with open(self.category_file, "r") as f:
            self.categories = [line.strip() for line in f.readlines()]
        self.categories = sorted(self.categories)
        
        self.createWidgets()  # Initialize UI elements

    def createWidgets(self):
        """Creates and places all main widgets for the dashboard."""
        
        # Increase Sidebar Width
        self.sidebar = tk.Frame(self, width=350, relief=tk.RIDGE, bg=StyleConfig.BG_COLOR)
        self.sidebar.grid(row=0, column=0, sticky='nsw')
        self.createSidebar()
        
        self.main_content = tk.Frame(self)
        self.main_content.grid(row=0, column=1, sticky='nsew')
        
        self.createToolbar()
        self.createTransactionTable()
        
        # Configure layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
    
    def createSidebar(self):
        """Creates the sidebar with accounts, reports, and actions."""
        
        # Accounts Listbox
        self.banking_label = tk.Label(self.sidebar, text="Banking Accounts",
                                      font=(StyleConfig.FONT_FAMILY, StyleConfig.HEADING_FONT_SIZE, "bold"),
                                      bg=StyleConfig.BG_COLOR, fg=StyleConfig.TEXT_COLOR)
        self.banking_label.pack(anchor='center', pady=5)
    
        # Add a frame to contain the listbox and scrollbar
        self.accounts_listbox_frame = ttk.Frame(self.sidebar)
        self.accounts_listbox_frame.pack(fill="x", padx=5, pady=2)
        
        # Create listbox with a scrollbar
        self.accounts_list = tk.Listbox(self.accounts_listbox_frame, height=10, width=35)  # Increased width
        self.accounts_list.pack(side=tk.LEFT, fill='x', expand=True)
    
        # Add scrollbar for smooth scrolling
        self.accounts_scrollbar = ttk.Scrollbar(self.accounts_listbox_frame, orient=tk.VERTICAL, command=self.accounts_list.yview)
        self.accounts_scrollbar.pack(side=tk.RIGHT, fill='y')
        self.accounts_list.config(yscrollcommand=self.accounts_scrollbar.set)
    
        # Bind smooth scrolling behavior
        self.accounts_list.bind("<MouseWheel>", self.smoothScroll)
        
        # Bind double-click event to filter transactions
        self.accounts_list.bind("<Double-Button-1>", self.filterTransactionsByBankingAccount)
        
        
        # Investments Listbox
        self.investment_label = tk.Label(self.sidebar, text="Investment Accounts",
                                         font=(StyleConfig.FONT_FAMILY, StyleConfig.HEADING_FONT_SIZE, "bold"),
                                         bg=StyleConfig.BG_COLOR, fg=StyleConfig.TEXT_COLOR)
        self.investment_label.pack(anchor='center', pady=5)
    
        # Add a frame to contain the listbox and scrollbar
        self.investment_listbox_frame = ttk.Frame(self.sidebar)
        self.investment_listbox_frame.pack(fill="x", padx=5, pady=2)
        
        # Create listbox with a scrollbar
        self.investments_list = tk.Listbox(self.investment_listbox_frame, height=6, width=35)  # Increased width
        self.investments_list.pack(side=tk.LEFT, fill='x', expand=True)
    
        # Add scrollbar for smooth scrolling
        self.investments_scrollbar = ttk.Scrollbar(self.investment_listbox_frame, orient=tk.VERTICAL, command=self.investments_list.yview)
        self.investments_scrollbar.pack(side=tk.RIGHT, fill='y')
        self.investments_list.config(yscrollcommand=self.investments_scrollbar.set)
    
        # Bind smooth scrolling behavior
        self.investments_list.bind("<MouseWheel>", self.smoothScroll)
        
        # Bind double-click event to filter transactions
        self.investments_list.bind("<Double-Button-1>", self.filterTransactionsByInvestmentAccount)
         
        """     
        ttk.Label(self.sidebar, text="Reports", font=(StyleConfig.FONT_FAMILY, StyleConfig.SUB_FONT_SIZE, "bold")).pack(anchor='w', pady=5)
        self.reports_list = tk.Listbox(self.sidebar, height=4, width=45)  # Increased width
        self.reports_list.pack(fill='x', padx=5, pady=2)
        
        ttk.Label(self.sidebar, text="Actions", font=(StyleConfig.FONT_FAMILY, StyleConfig.SUB_FONT_SIZE, "bold")).pack(anchor='w', pady=5)
        self.actions_list = tk.Listbox(self.sidebar, height=4, width=45)  # Increased width
        self.actions_list.pack(fill='x', padx=5, pady=2)
        """
        
    def createToolbar(self):
        """Creates a toolbar with basic transaction actions."""
        
        self.toolbar = tk.Frame(self.main_content, relief=tk.RIDGE, bg=StyleConfig.BG_COLOR)
        self.toolbar.grid(row=0, column=0, sticky='ew')
        
        self.button_image_loc = os.path.join(os.path.dirname(__file__), "Images")
        self.buttons = []
        self.separators = []
        self.images = {}
        
        self.button_separators = [3, 5, 7, 9]
        
        self.buttons = []
        button_data = [
            ("Add",         "add.png",      self.addTransaction),
            ("Edit",        "edit.png",     self.editTransaction),
            ("Delete",      "delete.png",   self.deleteTransaction),
            ("Retrieve",    "retrieve.png", self.retrieveData),
            ("Payee",       "payee.png",    self.viewPayees),
            ("Category",    "category.png", self.viewCategories),
            ("Banking",     "account.png",  lambda: self.filterByAccountType("Banking")),
            ("Stocks",      "stonks.png",   lambda: self.filterByAccountType("Investments")),
            ("Budget",      "budget.png",   self.viewBudget),
            ("Export",      "export.png",   self.saveDataAs),
            ("Options",     "options.png",  self.viewOptions),
        ]
        
        btn_size = 50  
        
        for index, (text, icon, command) in enumerate(button_data):
            img_path = os.path.join(self.button_image_loc, icon)
            img = Image.open(img_path)
            img = img.resize((36,36))  # Resize image to 24x24 pixels
            self.images[icon] = ImageTk.PhotoImage(img)
            
            try:
                btn = tk.Button(self.toolbar, 
                                text=text, 
                                image=self.images[icon], 
                                compound=tk.TOP, 
                                command=command, 
                                width=btn_size, 
                                height=btn_size, 
                                bg='white', 
                                relief=tk.RAISED)
            except:
                btn = tk.Button(self.toolbar, 
                                text=text, 
                                compound=tk.TOP, 
                                command=command, 
                                width=btn_size, 
                                height=btn_size, 
                                bg='white', 
                                relief=tk.RAISED)
                
            btn.pack(side=tk.LEFT, padx=4, pady=2)
            self.buttons.append(btn)
            
            if index in self.button_separators:
                ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
                
        # Search Bar
        self.search_label = tk.Label(self.toolbar, text="Search:", 
                                     font=(StyleConfig.FONT_FAMILY, StyleConfig.FONT_SIZE),
                                     bg=StyleConfig.BG_COLOR, fg=StyleConfig.TEXT_COLOR)
        self.search_label.pack(side=tk.LEFT, padx=5)
        
        self.search_entry = tk.Entry(self.toolbar, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind("<Return>", lambda event: self.searchTransactions())
        
        search_button = tk.Button(self.toolbar, text="Go", command=self.searchTransactions)
        search_button.pack(side=tk.LEFT, padx=5)
        self.buttons.append(search_button)
        
        adv_search_button = tk.Button(self.toolbar, text="Advanced Search", command=self.openAdvancedSearch)
        adv_search_button.pack(side=tk.LEFT, padx=5)
        self.buttons.append(adv_search_button)
        
    def filterByAccountType(self, account_type):
        """Filters transactions based on account type (Banking or Investment)."""
        
        # Ensure all_data exists before filtering
        if not hasattr(self.master, "all_data") or self.master.all_data.empty:
            messagebox.showwarning("Warning", "No data available to filter!")
            return
    
        filtered_df = self.master.all_data[self.master.all_data["Account Type"] == account_type]
        self.updateTable(filtered_df)
        
    def searchTransactions(self):
        """Filters transactions based on user input, including numbers."""
        
        query = self.search_entry.get().strip().lower()
    
        if not query:
            try:
                self.updateTable(self.master.all_data)  # Reset table if empty search
            except:
                pass
            return
        
        if not hasattr(self.master, "all_data") or self.master.all_data.empty:
            messagebox.showwarning("Warning", "No data to search!")
            return
    
        def match_query(row):
            """Checks if the query exists in any column, including numeric columns."""
            for col in row.index:
                cell_value = str(row[col]).lower()
    
                if col in ["Payment", "Deposit", "Balance"]:  # Convert numeric values
                    try:
                        num_val = float(row[col]) / 100  # Convert cents to dollars
                        if query.replace("$", "").replace(",", "").isdigit():
                            if float(query) == num_val:
                                return True
                    except ValueError:
                        continue
    
                if query in cell_value:
                    return True
    
            return False

        filtered_df = self.master.all_data[self.master.all_data.apply(match_query, axis=1)]
        self.updateTable(filtered_df)
        
    def openAdvancedSearch(self):
        """Opens a compact, well-structured window for advanced transaction searches."""
        
        # Ensure all_data exists before filtering
        if not hasattr(self.master, "all_data") or self.master.all_data.empty:
            messagebox.showwarning("Warning", "No data to search!")
            return
        
        search_window = tk.Toplevel(self)
        search_window.title("Advanced Search")
        search_window.geometry("300x370")
        search_window.resizable(False, False)
    
        ttk.Label(search_window, text="Advanced Search", font=(StyleConfig.FONT_FAMILY, StyleConfig.FONT_SIZE, "bold")).pack(pady=5)
    
        # Frame to neatly arrange labels and entry boxes
        input_frame = ttk.Frame(search_window)
        input_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
        search_entries = {}  # Store entry fields for each column
    
        # Create labeled entry fields for each column
        for column in self.master.all_data.columns:
            row_frame = ttk.Frame(input_frame)
            row_frame.pack(fill="x", pady=2)
    
            label = ttk.Label(row_frame, text=f"{column}:", width=12, anchor="w", font=(StyleConfig.FONT_FAMILY, StyleConfig.FONT_SIZE, "bold"))
            label.pack(side=tk.LEFT)
    
            entry = ttk.Entry(row_frame, width=15)
            entry.pack(side=tk.RIGHT, expand=True, fill="x")
            search_entries[column] = entry
    
        def performAdvancedSearch(event=None):
            """Filters transactions based on entered search values."""
            filtered_df = self.master.all_data.copy()
    
            for col, entry in search_entries.items():
                search_value = entry.get().strip().lower()
    
                if not search_value:
                    continue  # Skip empty fields
    
                if col in ["Payment", "Deposit", "Balance"]:  # Handle numeric columns
                    try:
                        search_value = float(search_value.replace("$", "").replace(",", ""))
                        filtered_df = filtered_df[filtered_df[col] / 100 == search_value]
                    except ValueError:
                        messagebox.showwarning("Warning", f"Invalid numeric value for {col}", parent=search_window)
                        return
                else:  # Text-based search
                    filtered_df = filtered_df[filtered_df[col].astype(str).str.lower().str.contains(search_value, na=False)]
    
            self.updateTable(filtered_df)
            closeWindow()
            
        def closeWindow(event=None):
            search_window.destroy()
    
        # Search button
        search_button = ttk.Button(search_window, text="Search", command=performAdvancedSearch)
        search_button.pack(pady=10)
        
        # Bind keys
        search_window.bind("<Return>", performAdvancedSearch)
        search_window.bind("<Escape>", closeWindow)
        
        search_window.focus_force()
        
    def createTransactionTable(self):
        """Creates the transaction table with scrolling."""
        
        self.table_frame = tk.Frame(self.main_content)
        self.table_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
        
        self.tree = ttk.Treeview(self.table_frame, show='headings', height=15)
        
        columns = list(self.banking_column_widths.keys())
        self.tree['columns'] = columns
        
        for col in columns:
            self.tree.heading(col, text=col, anchor=tk.CENTER, 
                              command=lambda c=col: self.sortTableByColumn(self.tree, c, False))
            
            # Check if the column should be hidden
            if self.banking_column_widths[col] == 0:
                self.tree.column(col, width=0, minwidth=0, stretch=False)
            else:
                self.tree.column(col, width=self.banking_column_widths[col], anchor=tk.W)
            
        # Scrollbars
        y_scrollbar = ttk.Scrollbar(self.table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=y_scrollbar.set)
        
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Adjust layout
        self.main_content.grid_columnconfigure(0, weight=1)
        self.main_content.grid_rowconfigure(1, weight=1)
        
        # Bind double-click to edit cell
        self.tree.bind("<Double-1>", self.editCell)
        
    def sortTableByColumn(self, tv: ttk.Treeview, col: str, sort_direction: bool) -> None:
        Tables.sortTableByColumn(tv, col, sort_direction)
        Tables.applyBandedRows(self.tree, colors=[StyleConfig.BAND_COLOR_1, StyleConfig.BAND_COLOR_2])
        
        
    def retrieveData(self):
        """
        Calls DataManager.retrieveData() once, processes each file using parseNewDF, and updates the UI.
        """
        retrieved_data = DataManager.retrieveData()  # Get list of (account_name, df) tuples
    
        if not retrieved_data:  # If no files selected, exit function
            return
    
        all_parsed_data = []
    
        for account_name, df in retrieved_data:
            if df is not None and not df.empty:
                # Ensure Dashboard instance is passed to parseNewDF
                parsed_df = DataManager.parseNewDF(df, account_name, self)
                all_parsed_data.append(parsed_df)
    
        if all_parsed_data:
            # Combine all parsed data into a single DataFrame
            final_df = pd.concat(all_parsed_data, ignore_index=True)
    
            # Store processed data in the app and update UI
            self.master.all_data = final_df.copy()
            self.master.all_data = DataFrameProcessor.getDataFrameIndex(self.master.all_data)
            self.updateTable(self.master.all_data.copy())
            
    def addTransaction(self):
        """Calls TransactionManager.addTransaction, passing the Dashboard instance."""
        TransactionManager.openTransactionWindow(self, edit=False)
    
    def editTransaction(self):
        """Calls TransactionManager.editTransaction, passing the Dashboard instance."""
        TransactionManager.openTransactionWindow(self, edit=True)
    
    def deleteTransaction(self):
        """Calls TransactionManager.deleteTransaction, passing the Dashboard instance."""
        TransactionManager.deleteTransaction(self)     
            
    def selectAllRows(self):
        """Selects all rows in the transaction table."""
        self.tree.selection_set(self.tree.get_children())

    def editCell(self, event):
        """Handles in-place editing of table cells based on column type."""
        
        # Function to save the new value
        def saveEdit(new_value):
            """Save changes to DataFrame and update UI."""
            selected_number = int(self.tree.item(item, "values")[0])  # Get the 'Number' field
            index_to_update = self.master.all_data[self.master.all_data["Number"] == selected_number].index
    
            if not index_to_update.empty:
                # Convert numerical columns to valid format
                if col_name in ["Payment", "Deposit", "Balance"]:
                    try:
                        new_value = float(new_value.replace("$", "").replace(",", "")) * 100
                    except ValueError:
                        messagebox.showerror("Invalid Input", "Please enter a valid number.")
                        return
    
                elif col_name == "Date":
                    # Ensure date is stored as string (YYYY-MM-DD) to avoid sorting errors
                    new_value = Utility.formatDateFromString(new_value)
    
                self.master.all_data.at[index_to_update[0], col_name] = new_value
                self.updateTable(self.master.all_data)  # Refresh table UI
    
            cancelEdit()

        def cancelEdit(event=None):
            """Closes the entry widget without saving changes."""
            if "entry_widget" in locals():
                entry_widget.destroy()
            if "cal_win" in locals():
                cal_win.destroy()
            if "dropdown" in locals():
                dropdown.destroy()
        
        item = self.tree.identify_row(event.y)  # Get selected row ID
        column = self.tree.identify_column(event.x)  # Get column ID (e.g., #1, #2, etc.)
        
        if not item or not column:
            return
        
        col_index = int(column[1:]) - 1  # Convert #1, #2, etc. to 0-based index
        col_name = self.tree["columns"][col_index]
        
        # Get current cell value
        current_value = self.tree.item(item, "values")[col_index]
        
        # Disable editing for 'Number' column
        if col_name == "Number":
            return  
    
        # Editing options based on column type
        if col_name == "Date":
            try:
                initial_date = datetime.strptime(current_value, "%Y-%m-%d").date()
            except ValueError:
                initial_date = date.today()  # Default to today if invalid
    
            cal_win = tk.Toplevel(self)
            cal_win.title("Select Date")
            cal_win.geometry("250x250")
            
            cal = Calendar(cal_win, 
                            selectmode="day", 
                            year=initial_date.year, 
                            month=initial_date.month, 
                            day=initial_date.day,
                            date_pattern = 'yyyy-mm-dd',
                            )
            
            cal.pack(padx=10, pady=10)
            
            def pickDate(event=None):
                """Selects the date from the calendar and updates the table."""
                new_date = cal.get_date()
                saveEdit(new_date)
    
            # Buttons
            tk.Button(cal_win, text="OK", command=pickDate).pack(pady=5, padx=5)
            tk.Button(cal_win, text="Cancel", command=cancelEdit).pack(pady=5, padx=5)
    
            # Bind keys
            cal_win.bind("<Return>", pickDate)
            cal_win.bind("<Escape>", cancelEdit)
            
            cal_win.focus_force()  # Make sure the window is active
    
        # Direct Text Editing
        if col_name in ["Payment", "Deposit", "Balance", "Note", "Payee"]:
            x, y, width, height = self.tree.bbox(item, column)  # Get cell coordinates

            # Create an entry box and place it exactly over the clicked cell
            entry_widget = tk.Entry(self.tree)
            entry_widget.place(x=x, y=y, width=width, height=height)
    
            # Insert current value into the entry box
            entry_widget.insert(0, current_value)
            entry_widget.select_range(0, tk.END)  # Highlight text for easy replacement
            entry_widget.focus_set()
    
            # Bind Enter and Escape keys
            entry_widget.bind("<Return>", lambda e: saveEdit(entry_widget.get()))
            entry_widget.bind("<Tab>", lambda e: saveEdit(entry_widget.get()))
            entry_widget.bind("<FocusOut>", cancelEdit)
            
        elif col_name in ["Category", "Account", "Account Type"]:
            x, y, width, height = self.tree.bbox(item, column)  # Get cell coordinates
            
            # Create Dropdown List
            dropdown = ttk.Combobox(self.tree, state="readonly")
            dropdown.place(x=x, y=y, width=width, height=height)
    
            if col_name == "Category":
                dropdown["values"] = self.categories
    
            elif col_name == "Account":
                accounts = self.master.all_data["Account"].unique().tolist()
                dropdown["values"] = accounts
                
            elif col_name == "Account Type":
                dropdown["values"] = ['Banking', 'Investments']
    
            dropdown.set(current_value)
            dropdown.bind("<<ComboboxSelected>>", lambda e: saveEdit(dropdown.get()))
            dropdown.focus_set()
            
            dropdown.bind("<FocusOut>", cancelEdit)
                         
    def smoothScroll(self, event=None) -> None:
        """Smooth scrolling for listboxes, dynamically adjusting speed."""
        widget = event.widget
        if isinstance(widget, tk.Listbox):
            speed = StyleConfig.SCROLL_SPEED  # Read the scroll speed
            widget.yview_scroll(-speed if event.delta > 0 else speed, "units")
                    
    def getCategories(self):
        # Load categories from file
        with open(self.category_file, "r") as f:
            file_categories = [line.strip() for line in f.readlines()]
        
        try:
            # Get unique categories from all_data that aren't in the file
            if "Category" in self.master.all_data.columns:
                data_categories = set(self.master.all_data["Category"].dropna().unique())
            else:
                data_categories = set()
        except AttributeError:
            data_categories = set()
        
        self.categories = sorted(set(file_categories) | data_categories)
    
    def viewCategories(self):
        """Opens a window to manage categories."""
        category_window = tk.Toplevel(self)
        category_window.title("Manage Categories")
        
        window_height, window_width = 350, 400
        Windows.openRelativeWindow(category_window, main_width=self.winfo_x(), main_height=self.winfo_y(), width=window_width, height=window_height)
    
        ttk.Label(category_window, text="Categories", font=(StyleConfig.FONT_FAMILY, StyleConfig.HEADING_FONT_SIZE, "bold")).pack(pady=5)
    
        # Listbox to display categories
        list_frame = ttk.Frame(category_window)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
        category_listbox = tk.Listbox(list_frame, height=15)
        category_listbox.pack(side=tk.LEFT, fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=category_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        category_listbox.config(yscrollcommand=scrollbar.set)
        
        def loadCategories():
            self.getCategories()
            
            # Populate the listbox
            category_listbox.delete(0, tk.END)
            for category in self.categories:
                category_listbox.insert(tk.END, category)
        
        loadCategories()
    
        def addCategory():
            new_category = simpledialog.askstring("Add Category", "Enter new category:")
            if new_category and new_category not in self.categories:
                self.categories.append(new_category)
                category_listbox.insert(tk.END, new_category)
                saveCategories()
    
        def modifyCategory():
            selected_index = category_listbox.curselection()
            if selected_index:
                old_category = category_listbox.get(selected_index)
                new_category = simpledialog.askstring("Modify Category", "Enter new name:", initialvalue=old_category)
                if new_category and new_category not in self.categories:
                    self.categories[selected_index[0]] = new_category
                    category_listbox.delete(selected_index)
                    category_listbox.insert(selected_index, new_category)
                    saveCategories()
    
        def deleteCategory():
            selected_index = category_listbox.curselection()
            if selected_index:
                confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this category?")
                if confirm:
                    sorted(self.categories.pop(selected_index[0]))
                    print (self.categories)
                    category_listbox.delete(selected_index)
                    saveCategories()
                    self.viewCategories()
    
        def saveCategories():
            with open(self.category_file, "w") as f:
                for category in self.categories:
                    f.write(category + "\n")
                    
        def closeWindow(event=None):
            category_window.destroy()
    
        # Buttons
        button_frame = ttk.Frame(category_window)
        button_frame.pack(pady=5)
    
        ttk.Button(button_frame, text="Add",    command=addCategory).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Modify", command=modifyCategory).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete", command=deleteCategory).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Exit", command=closeWindow).pack(side=tk.LEFT, padx=5)
        
        # Bind keys
        category_window.bind("<Escape>", closeWindow)
        
        category_window.focus_force()
        
    def viewPayees(self):
        """Placeholder for deleting a transaction."""
        print("View Payees")
        
    def viewBudget(self):
        """Placeholder for deleting a transaction."""
        print("View Budget")
        
    def saveDataAs(self, event=None):
        """Placeholder for exporting data."""
        save_file = DataManager.saveDataAs(self.master.all_data.copy(), new_file = '')
        
        if save_file != None:
            with open(self.master.save_file_loc, 'w') as f:
                f.write(save_file)
            self.master.save_file = save_file
            
    def saveData(self, event=None):
        """Placeholder for exporting data."""
        _ = DataManager.saveDataAs(self.master.all_data.copy(), new_file = self.master.save_file)
     
    def viewOptions(self, new_settings=True):
        """Opens a window to adjust application settings like fonts, colors, and sizes."""
        options_window = tk.Toplevel(self)
        options_window.title("Application Settings")
        options_window.resizable(False, False)
    
        ttk.Label(options_window, text="Customize Appearance", font=(StyleConfig.FONT_FAMILY, StyleConfig.HEADING_FONT_SIZE, "bold")).pack(pady=5)
    
        if new_settings:
            # Dictionary to store new settings
            self.temp_settings = {
                "FONT_FAMILY":          tk.StringVar(value=StyleConfig.FONT_FAMILY),
                "FONT_SIZE":            tk.IntVar(value=StyleConfig.FONT_SIZE),
                "HEADING_FONT_SIZE":    tk.IntVar(value=StyleConfig.HEADING_FONT_SIZE),
                "BUTTON_FONT_SIZE" :    tk.IntVar(value=StyleConfig.BUTTON_FONT_SIZE),
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
            
        # Set geometry of options window
        window_height = len(self.temp_settings.keys()) * 28 + 100
        window_width = 260
        
        # Open window relative to the position of the dashboard
        Windows.openRelativeWindow(options_window, main_width=self.winfo_x(), main_height=self.winfo_y(), width=window_width, height=window_height)   
    
        def pickColor(var, entry_widget):
            """Opens the color chooser asynchronously and updates the entry field."""
            options_window.lift()  # Bring options window to the front (optional)
            
            def openColorChooser():
                color_code = colorchooser.askcolor(title="Choose a Color")[1]  # Get hex value
                if color_code:
                    var.set(color_code)  # Update the variable
                    entry_widget.delete(0, tk.END)
                    entry_widget.insert(0, color_code)  # Update the entry field dynamically
                    
                    setattr(StyleConfig, var._name, color_code)  # Update StyleConfig dynamically
                    self.applyStyleChanges()
                    
                self.viewOptions(new_settings=False)
            options_window.after(10, openColorChooser)
    
        # Function to create labeled settings row
        def createSettingRow(label, var, parent, options=None, is_color=False):
            frame = ttk.Frame(parent)
            frame.pack(fill="x", padx=10, pady=2)
    
            ttk.Label(frame, text=label, width=20, anchor="w").pack(side=tk.LEFT)
    
            if is_color:
                entry = ttk.Entry(frame, textvariable=var, width=10)
                entry.pack(side=tk.LEFT, padx=5)
            
                color_button = ttk.Button(frame, text="🎨", width=3, command=lambda: pickColor(var, entry))
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
    
        # Create settings fields
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
        
        def resetToStandard():
            """Resets all settings to their default values dynamically from StyleConfig."""
    
            # Retrieve the default values
            default_settings = StyleConfig.getDefaultSettings()
        
            # Apply the default settings dynamically
            for key, value in default_settings.items():
                setattr(StyleConfig, key, value)
        
            self.applyStyleChanges()  # Apply the updated styles to the UI
            saveUserSettings(data=default_settings)  # Save user settings to file
            closeWindow()
    
        def applyChanges():
            """Applies settings dynamically without modifying StyleConfig.py"""
            for key, var in self.temp_settings.items():
                setattr(StyleConfig, key, var.get())
                
            # Toggle Dark Mode dynamically
            StyleConfig.applyDarkMode(self.temp_settings["DARK_MODE"].get())
    
            self.applyStyleChanges()
            saveUserSettings()  # Save user settings to file
            closeWindow()
    
        # Save settings function
        def saveUserSettings(data=None):
            if data == None:
                with open("user_settings.pkl", "wb") as f:
                    pickle.dump({key: var.get() for key, var in self.temp_settings.items()}, f)
            else:
               with open("user_settings.pkl", "wb") as f:
                   pickle.dump({key: var for key, var in data.items()}, f) 
                
        def closeWindow(event=None):
            options_window.destroy()
    
        # Buttons Frame
        button_frame = ttk.Frame(options_window)
        button_frame.pack(pady=10)
    
        apply_button = ttk.Button(button_frame, text="Apply", command=applyChanges)
        apply_button.grid(row=0, column=0, padx=5, pady=5)
    
        standard_button = ttk.Button(button_frame, text="Standard Options", command=resetToStandard)
        standard_button.grid(row=1, column=0, columnspan=2, padx=5, pady=5)
    
        cancel_button = ttk.Button(button_frame, text="Cancel", command=closeWindow)
        cancel_button.grid(row=0, column=1, padx=5, pady=5)
        
        # Bind keys
        options_window.bind("<Return>", applyChanges)
        options_window.bind("<Escape>", closeWindow)
        
        options_window.focus_force()
        
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
                       pady=StyleConfig.BUTTON_PADDING)
    
        # Update Sidebar Labels
        self.banking_label.config(bg=StyleConfig.BG_COLOR, fg=StyleConfig.TEXT_COLOR)
        self.investment_label.config(bg=StyleConfig.BG_COLOR, fg=StyleConfig.TEXT_COLOR)
    
        # Update Sidebar Account Lists
        self.accounts_list.config(bg=StyleConfig.BG_COLOR, fg=StyleConfig.TEXT_COLOR)
        self.investments_list.config(bg=StyleConfig.BG_COLOR, fg=StyleConfig.TEXT_COLOR)
    
        # Update Search Label in Toolbar
        self.search_label.config(bg=StyleConfig.BG_COLOR, fg=StyleConfig.TEXT_COLOR)
        self.search_entry.config(bg=StyleConfig.BG_COLOR, fg=StyleConfig.TEXT_COLOR)
    
        # Ensure the colors update immediately
        self.update_idletasks()
        
    def updateTable(self, df:pd.DataFrame) -> None:
        """comment"""
        
        # Clear existing data in the table
        for row in self.tree.get_children():
            self.tree.delete(row)
            
        df = DataFrameProcessor.getDataFrameIndex(df)
        df = DataFrameProcessor.convertToDatetime(df)
        
        # Ensure Payment, Deposit, and Balance columns exist
        if "Payment" not in df.columns:
            df["Payment"] = 0  # Default to zero if missing
        if "Deposit" not in df.columns:
            df["Deposit"] = 0  # Default to zero if missing
        if "Balance" not in df.columns:
            df["Balance"] = 0  # Default to zero if missing
        
        # Insert new data into the table
        for _, row in df.iterrows():
            formatted_row = list(row)
            formatted_row[4] = f"${row['Payment'] / 100:.2f}"  # Format 'Payment'
            formatted_row[5] = f"${row['Deposit'] / 100:.2f}"  # Format 'Deposit'
            formatted_row[6] = f"${row['Balance'] / 100:.2f}"  # Format 'Balance'
            
            self.tree.insert("", tk.END, values=formatted_row)

        Tables.applyBandedRows(self.tree, colors=[StyleConfig.BAND_COLOR_1, StyleConfig.BAND_COLOR_2])
        
        # Update accounts listbox
        self.updateBankingAccountsToolbox(df)
        self.updateInvestmentAccountsToolbox(df)
        
    def updateBankingAccountsToolbox(self, df: pd.DataFrame) -> None:
        """Updates the sidebar listbox with only banking accounts and their balances."""
        self.accounts_list.delete(0, tk.END)  # Clear previous entries
     
        # Filter only banking accounts
        banking_df = df[df["Account Type"] == "Banking"]

        # Calculate account balances
        self.account_balances = DataFrameProcessor.accountBalance(banking_df)
     
        # Add "All Banking Accounts" option
        self.accounts_list.insert(tk.END, "All Banking Accounts")
     
        # Insert individual banking accounts
        for account, balance in self.account_balances.items():
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
                    
    def filterTransactionsByBankingAccount(self, event):
        """Filters transactions by selected account in the listbox."""
        selected_index = self.accounts_list.curselection()
        
        if not selected_index:  # If nothing selected, return
            return
        
        selected_text = self.accounts_list.get(selected_index)
        
        if selected_text == "All Banking Accounts":
            filtered_df = self.master.all_data.copy()  # Make a copy to avoid modification issues
        else:
            account_name = selected_text.split(" $")[0]  # Extract account name
            filtered_df = self.master.all_data[self.master.all_data["Account"] == account_name].copy()
        
        self.updateTable(filtered_df)  # Update table with filtered results
        
    def filterTransactionsByInvestmentAccount(self, event):
        """Filters transactions by selected account in the listbox."""
        selected_index = self.investments_list.curselection()
        
        if not selected_index:  # If nothing selected, return
            return
        
        selected_text = self.investments_list.get(selected_index)
        
        if selected_text == "All Investment Accounts":
            filtered_df = self.master.all_data.copy()  # Make a copy to avoid modification issues
        else:
            account_name = selected_text.split(" $")[0]  # Extract account name
            filtered_df = self.master.all_data[self.master.all_data["Account"] == account_name].copy()
        
        self.updateTable(filtered_df)  # Update table with filtered results
        
    def clearTable(self, event=None):
        """comment"""
        
        if not self.master.all_data.empty:
            confirm = messagebox.askyesno("Confirm Delete", 
                                          "Are you sure you want to delete all transaction(s)?")
            
            if confirm is None or not confirm:  # Explicitly check for None
                return  # User canceled or closed the dialog, so exit
            
            if confirm:
                self.master.all_data = pd.DataFrame()
                self.accounts_list.delete(0, tk.END)
                self.investments_list.delete(0, tk.END)
                self.tree.delete(*self.tree.get_children())
    
