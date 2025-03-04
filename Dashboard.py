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
    
    def convertCurrency(df: pd.DataFrame) -> pd.DataFrame:
        """
        Converts the 'Payment', 'Deposit', and 'Balance' columns in a DataFrame to cents (int) format

        Parameters:
        - df (pd.DataFrame): The input DataFrame containing a 'Date' column.

        Returns:
        - pd.DataFrame: Updated DataFrame
        """
        for col in ['Payment', 'Deposit', 'Balance']:
            df[col] = df[col].astype(str).replace({'\\$': '', ',': '', '\\(': '-', '\\)': ''}, regex=True)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            df[col] = (df[col] * 100).round().astype(int)
        return df
    
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
    
    def getStartEndDates(df: pd.DataFrame) -> Tuple[pd.Timestamp, pd.Timestamp]:
        """
        Retrieves the earliest and latest dates from the 'Date' column of the DataFrame.

        Parameters:
        - df (pd.DataFrame): The input DataFrame containing a 'Date' column.

        Returns:
        - Tuple[pd.Timestamp, pd.Timestamp]: A tuple containing the earliest and latest dates.
        """
        return df['Date'].min(), df['Date'].max()
    
    def getMinMaxVals(df: pd.DataFrame) -> Tuple[float, float]:
        """
        Computes the minimum and maximum values of the 'Amount' column in the DataFrame.

        Parameters:
        - df (pd.DataFrame): The input DataFrame containing an 'Amount' column.

        Returns:
        - Tuple[float, float]: A tuple containing (min_value, max_value) from the 'Amount' column.
        """
        return df['Amount'].min(), df['Amount'].max()
    
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

class DataHandling:
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
    
    def updateData() -> None:
        """
        Updates the financial data based on CSV files.
    
        This method triggers `selectFilesAndFolders` with `update=True`,
        ensuring that the data is refreshed with the latest available files.
        """
        #self.selectFilesAndFolders(update=True)
        return
    
    def reloadData() -> None:
        """
        Reloads financial data by triggering the file selection function.
    
        This function clears the current window and reloads data files.
    
        Retuns:
            None
        """
        #self.selectFilesAndFolders(reload=True) 
        return
    
    def selectFilesAndFolders(self, event=None, reload=False, update=False):
        """Open file dialog to select csv or pkl file(s)"""
        
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
                elif data_file.endswith(".csv"):
                    #TODO add in functionality
                    return
                    #inc, exp = loadCSVFile(data_file)
                
                self.income_data    = pd.concat([self.income_data, inc], ignore_index=False)
                self.expenses_data  = pd.concat([self.expenses_data, exp], ignore_index=False)
                    
                self.data_files.append(data_file)
                    
            self.setupDataFrames()
               
        else:
            messagebox.showinfo("Error", message = "No File Selected")
            
        return
    
 
class Dashboard(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        
        self.master = master  # Reference to the FinanceTracker (Main Window)
        self.last_saved_file = os.path.join(os.path.dirname(__file__), "lastSavedFile.txt")
        
        # Define column widths for transaction table
        self.banking_column_widths = {
            "Number": 10,
            "Date": 70,
            "Payee": 450,
            "Category": 200,
            "Payment": 100,
            "Deposit": 100,
            "Balance": 100,
            "Account": 150,
            "Note": 500, 
            "Account Type": 0
        }
        
        self.investment_column_widths = {
            "Number": 10,
            "Date": 70,
            "Payee": 450,
            "Category": 200,
            "Payment": 100,
            "Deposit": 100,
            "Balance": 100,
            "Account": 150,
            "Note": 500, 
            "Account Type": 0
        }
        
        #TODO Fix spacing and remove account type from view
        
        self.account_balances = {}
        
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
        self.accounts_list.bind("<Double-Button-1>", self.filterTransactionsByAccount)
        
        
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
        self.investments_list.bind("<Double-Button-1>", self.filterTransactionsByAccount)
         
        """
        # Account widgets

        
        ttk.Label(self.sidebar, text="Investment Accounts", font=(StyleConfig.FONT_FAMILY, StyleConfig.SUB_FONT_SIZE, "bold")).pack(anchor='w', pady=5)
        self.investment_list = tk.Listbox(self.sidebar, height=2, width=45)  # Increased width
        self.investment_list.pack(fill='x', padx=5, pady=2)
        
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
        
        self.button_separators = [2, 5, 7]
        
        self.buttons = []
        button_data = [
            ("Add",      "add.png",      self.addTransaction),
            ("Edit",     "edit.png",     self.editTransaction),
            ("Delete",   "delete.png",   self.deleteTransaction),
            ("Retrieve", "retrieve.png", self.retrieveData),
            ("Account",  "account.png",  self.chooseAccounts),
            ("Category", "category.png", self.viewCategories),
            ("Payee",    "payee.png",    self.viewPayees),
            ("Budget",   "budget.png",   self.viewBudget),
            ("Options",  "options.png",  self.viewOptions),
        ]
        
        for index, (text, icon, command) in enumerate(button_data):
            img_path = os.path.join(self.button_image_loc, icon)
            img = Image.open(img_path)
            img = img.resize((36, 36))  # Resize image to 24x24 pixels
            self.images[icon] = ImageTk.PhotoImage(img)
            
            btn = ttk.Button(self.toolbar, text=text, image=self.images[icon], compound=tk.TOP, command=command, width=8)
            btn.pack(side=tk.LEFT, padx=4, pady=2)
            self.buttons.append(btn)
            
            if index in self.button_separators:  # Add a separator after the second button
                ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
    def createTransactionTable(self):
        """Creates the transaction table with scrolling."""
        
        table_frame = ttk.Frame(self.main_content)
        table_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
        
        self.tree = ttk.Treeview(table_frame, show='headings', height=15)
        
        columns = list(self.banking_column_widths.keys())
        self.tree['columns'] = columns
        
        for col in columns:
            self.tree.heading(col, text=col, anchor=tk.CENTER, command=lambda c=col: Tables.sortTableByColumn(self.tree, c, False))
            self.tree.column(col, width=self.banking_column_widths[col], anchor=tk.W)
        
        # Scrollbars
        y_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=y_scrollbar.set)
        
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Adjust layout
        self.main_content.grid_columnconfigure(0, weight=1)
        self.main_content.grid_rowconfigure(1, weight=1)
    
    def addTransaction(self):
        """Placeholder for adding a transaction."""
        print("Add transaction")
    
    def editTransaction(self):
        """Placeholder for editing a transaction."""
        print("Edit transaction")
    
    def deleteTransaction(self):
        """Placeholder for deleting a transaction."""
        print("Delete transaction")
        
    def retrieveData(self) -> None:
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
            return  # User cancelled file selection  

        for file_path in file_paths:
            file_type       = file_path.split(".")[-1]
            account_name    = file_path.split("/")[-1].split(".")[0] 

            if file_type == 'csv':
                df = DataHandling.readCSV(file_path)
            elif file_type == 'xlsx':
                df = DataHandling.readXLSX(file_path)
                
            df = self.parseNewDF(df, account_name)
            
            self.master.all_data = pd.concat([self.master.all_data, df]) 
            
            #print (df)
            
        self.master.all_data = DataFrameProcessor.getDataFrameIndex(self.master.all_data) 

        self.updateTable(self.master.all_data)
        messagebox.showinfo("Success", "Transactions successfully loaded and formatted!")
              
    def parseNewDF(self, df:pd.DataFrame, account: 'str') -> pd.DataFrame:
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
        investment_keywords = ["TSP", "IRA", "401K", "Investment", "Stocks", "Bonds", "Mutual Funds"]
        banking_keywords = ["Checking", "Savings", "Credit", "Loan"]
    
        # Guess account type based on filename
        account_type = "Banking"
        for keyword in investment_keywords:
            if keyword.lower() in account.lower():
                account_type = "Investment"
                break
        for keyword in banking_keywords:
            if keyword.lower() in account.lower():
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
            expected_headers = list(self.banking_column_widths)
        else:
            expecte_headers = list(self.investment_column_widths)
            
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
        
        # Convert numeric fields if applicable
        if account_type == "Banking":
            df = DataFrameProcessor.convertCurrency(df)
        
        # Assign account name and type
        df['Account'] = account
        df['Account Type'] = account_type

        # Select only the relevant columns in the correct order
        df = df[expected_headers]
        
        return df       
        
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
        
        # Insert new data into the table
        for _, row in df.iterrows():
            formatted_row = list(row)
            formatted_row[4] = f"${row['Payment'] / 100:.2f}"  # Format 'Payment'
            formatted_row[5] = f"${row['Deposit'] / 100:.2f}"  # Format 'Deposit'
            formatted_row[6] = f"${row['Balance'] / 100:.2f}"  # Format 'Balance'
            
            self.tree.insert("", tk.END, values=formatted_row[:-1])
            
        Tables.applyBandedRows(self.tree)
        
        # Update accounts listbox
        self.updateAccountsToolbox(df)
        
    def updateAccountsToolbox(self, df: pd.DataFrame) -> None:
        """Updates the sidebar listbox with accounts and their balances."""
        self.accounts_list.delete(0, tk.END)  # Clear previous entries
        
        # Store account balances
        self.account_balances = self.accountBalance(df)
    
        # Add "All Accounts" option first
        self.accounts_list.insert(tk.END, "All Accounts")
    
        for account, balance in self.account_balances.items():
            self.accounts_list.insert(tk.END, f"{account} ${balance / 100:.2f}")  # Format balance
            
    def accountBalance(self, df: pd.DataFrame) -> pd.Series:
        """Calculate the current balance for each account by summing deposits and subtracting payments."""
        if "Account" in df.columns and "Payment" in df.columns and "Deposit" in df.columns:
            balance = df.groupby("Account")["Deposit"].sum() - df.groupby("Account")["Payment"].sum()
            return balance
        else:
            return pd.Series(dtype=float)
        
    def smoothScroll(self, event=None) -> None:
        """Smooth scrolling for all sidebar listboxes."""
        widget = event.widget
        if isinstance(widget, tk.Listbox):
            widget.yview_scroll(-1 if event.delta > 0 else 1, "units")
        
    def filterTransactionsByAccount(self, event):
        """Filters transactions by selected account in the listbox."""
        selected_index = self.accounts_list.curselection()
        
        if not selected_index:  # If nothing selected, return
            return
        
        selected_text = self.accounts_list.get(selected_index)
        
        if selected_text == "All Accounts":
            filtered_df = self.master.all_data  # Show all data
        else:
            account_name = selected_text.split(" $")[0]  # Extract account name
            filtered_df = self.master.all_data[self.master.all_data["Account"] == account_name]
        
        self.updateTable(filtered_df)  # Update table with filtered results
        
        
    
