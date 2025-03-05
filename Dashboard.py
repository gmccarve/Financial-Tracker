import os
import pandas as pd
import numpy as np
import pickle

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, PhotoImage
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

from Utility import Utility, SaveFiles, Tables, Windows
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

class TransactionManager:    
    @staticmethod 
    def editTransaction(dashboard):
        """Edits a selected transaction from the table."""
        selected_items = dashboard.tree.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "No transaction selected for editing.")
            return
    
        selected_values = dashboard.tree.item(selected_items[0], "values")
        headers = list(dashboard.banking_column_widths.keys())
    
        prefill_data = dict(zip(headers, selected_values))
        TransactionManager.openTransactionWindow(prefill_data)
    @staticmethod     
    def openTransactionWindow(dashboard: "Dashboard", prefill_data=None):
        """Opens a transaction window for adding/editing a transaction, pre-filling if data is provided."""
        
        #TODO FIX
    
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
                    try:
                        parsed_date = datetime.strptime(value, "%Y-%m-%d").date()
                        entry_fields[header].delete(0, tk.END)
                        entry_fields[header].insert(0, parsed_date.strftime("%Y-%m-%d"))
                        entry.config(bg="white")
                    except ValueError:
                        errors.append(f"'{header}' must be a valid date (YYYY-MM-DD).")
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
    
        # Create transaction window
        transaction_window = tk.Toplevel(dashboard)
        transaction_window.title("Edit Transaction" if prefill_data else "Add Transaction")
        transaction_window.geometry("300x330")  # Increased size for better scaling
    
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
        with open(self.category_file, "r") as f:
            self.categories = [line.strip() for line in f.readlines()]
        self.categories = sorted(self.categories)
        
        self.createWidgets()  # Initialize UI elements
      
    def createWidgets(self):
        """Creates and places all main widgets for the dashboard."""
        
        # Increase Sidebar Width
        self.sidebar = ttk.Frame(self, width=350, relief=tk.RIDGE, padding=5)  # Increased width
        self.sidebar.grid(row=0, column=0, sticky='nsw')
        self.createSidebar()
        
        self.main_content = ttk.Frame(self)
        self.main_content.grid(row=0, column=1, sticky='nsew')
        
        self.createToolbar()
        self.createTransactionTable()
        
        # Configure layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
    
    def createSidebar(self):
        """Creates the sidebar with accounts, reports, and actions."""
        
        # Accounts Listbox
        ttk.Label(self.sidebar, text="Banking Accounts", font=(StyleConfig.FONT_FAMILY, StyleConfig.HEADING_FONT_SIZE, "bold")).pack(anchor='center', pady=5)
    
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
        ttk.Label(self.sidebar, text="Investment Accounts", font=(StyleConfig.FONT_FAMILY, StyleConfig.HEADING_FONT_SIZE, "bold")).pack(anchor='center', pady=5)
    
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
        
        self.toolbar = ttk.Frame(self.main_content, relief=tk.RIDGE, padding=5)
        self.toolbar.grid(row=0, column=0, sticky='ew')
        
        self.button_image_loc = os.path.join(os.path.dirname(__file__), "Images")
        self.buttons = []
        self.separators = []
        self.images = {}
        
        self.button_separators = [3, 6, 7]
        
        self.buttons = []
        button_data = [
            ("Add",         "add.png",      self.addTransaction),
            ("Edit",        "edit.png",     self.editTransaction),
            ("Delete",      "delete.png",   self.deleteTransaction),
            ("Retrieve",    "retrieve.png", self.retrieveData),
            ("Payee",       "payee.png",    self.viewPayees),
            ("Category",    "category.png", self.viewCategories),
            ("Accounts",    "account.png",  self.chooseAccounts),
            ("Stocks",      "stonks.png",   self.chooseAccounts),
            ("Budget",      "budget.png",   self.viewBudget),
            ("Options",     "options.png",  self.viewOptions),
        ]
        
        for index, (text, icon, command) in enumerate(button_data):
            img_path = os.path.join(self.button_image_loc, icon)
            img = Image.open(img_path)
            img = img.resize((36, 36))  # Resize image to 24x24 pixels
            self.images[icon] = ImageTk.PhotoImage(img)
            
            try:
                btn = ttk.Button(self.toolbar, text=text, image=self.images[icon], compound=tk.TOP, command=command, width=8)
            except:
                btn = ttk.Button(self.toolbar, text=text, command=command, width=8)
            btn.pack(side=tk.LEFT, padx=4, pady=2)
            self.buttons.append(btn)
            
            if index in self.button_separators:
                ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
    def createTransactionTable(self):
        """Creates the transaction table with scrolling."""
        
        table_frame = ttk.Frame(self.main_content)
        table_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
        
        self.tree = ttk.Treeview(table_frame, show='headings', height=15)
        
        columns = list(self.banking_column_widths.keys())
        self.tree['columns'] = columns
        
        for col in columns:
            self.tree.heading(col, text=col, anchor=tk.CENTER, 
                              command=lambda c=col: Tables.sortTableByColumn(self.tree, c, False))
            
            # Check if the column should be hidden
            if self.banking_column_widths[col] == 0:
                self.tree.column(col, width=0, minwidth=0, stretch=False)
            else:
                self.tree.column(col, width=self.banking_column_widths[col], anchor=tk.W)
            
        # Scrollbars
        y_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=y_scrollbar.set)
        
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Adjust layout
        self.main_content.grid_columnconfigure(0, weight=1)
        self.main_content.grid_rowconfigure(1, weight=1)
        
        # Bind double-click to edit cell
        self.tree.bind("<Double-1>", self.editCell)
        
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
        TransactionManager.openTransactionWindow(self, prefill_data=None)
    
    def editTransaction(self):
        """Calls TransactionManager.editTransaction, passing the Dashboard instance."""
        TransactionManager.editTransaction(self)
    
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
                        new_value = float(new_value.replace("$", "").replace(",", ""))
                        new_value = f"${new_value:.2f}"  # Ensure proper formatting
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
            entry_widget.bind("<FocusOut>", cancelEdit)
            
        elif col_name in ["Category", "Account"]:
            x, y, width, height = self.tree.bbox(item, column)  # Get cell coordinates
            
            # Create Dropdown List
            dropdown = ttk.Combobox(self.tree, state="readonly")
            dropdown.place(x=x, y=y, width=width, height=height)
    
            if col_name == "Category":
                dropdown["values"] = self.categories
    
            elif col_name == "Account":
                accounts = self.master.all_data["Account"].unique().tolist()
                dropdown["values"] = accounts
    
            dropdown.set(current_value)
            dropdown.bind("<<ComboboxSelected>>", lambda e: saveEdit(dropdown.get()))
            dropdown.focus_set()
            
            dropdown.bind("<FocusOut>", cancelEdit)
                         
    def chooseAccounts(self):
        """Placeholder for deleting a transaction."""
        print("Choose Accounts")
        
    def viewCategories(self):
        """Placeholder for deleting a transaction."""
        print("View Categories")
        
    def viewPayees(self):
        """Placeholder for deleting a transaction."""
        print("View Payees")
        
    def viewBudget(self):
        """Placeholder for deleting a transaction."""
        print("View Budget")
        
    def viewOptions(self):
        """Placeholder for deleting a transaction."""
        print("View Options")
        
    def updateTable(self, df:pd.DataFrame) -> None:
        """test"""
        
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
            
        Tables.applyBandedRows(self.tree)
        
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
            
    def smoothScroll(self, event=None) -> None:
        """Smooth scrolling for all sidebar listboxes."""
        widget = event.widget
        if isinstance(widget, tk.Listbox):
            widget.yview_scroll(-1 if event.delta > 0 else 1, "units")
        
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
        
        
    
