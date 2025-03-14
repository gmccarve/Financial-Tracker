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

from Utility import Utility, Tables, Windows, Classifier, DataFrameProcessor
from StyleConfig import StyleConfig


class DataManager:
    @staticmethod
    def readCSV(file_path: str) -> pd.DataFrame:
        """
        Load financial data from a CSV file
        
        Parameters:
            file_path (str): Path to the CSV file.
    
        Returns:
            pd.DataFrame: DataFrame containing the transaction data or an empty DataFrame if loading failed.
        """
        try:
            df = pd.read_csv(file_path).fillna('')
            return df
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {e}")
            return pd.DataFrame() 
               
    @staticmethod 
    def parseDataFileNames() -> Tuple[str, List[str]]:
        """
        Opens a file dialog for .csv and .pkl files, allowing the user to choose multiple files.
        
        Returns:
            pkl_file (str or None): Path to a single .pkl file if found.
            csv_files (List[str]): List of .csv file paths if found (empty if pkl_file is found).
        """
        # Prompt user to pick multiple files
        file_paths = filedialog.askopenfilenames(filetypes=[("CSV and PKL files", "*.csv *.pkl")])
        
        if not file_paths:
            return None, []
        
        pkl_file, csv_files = None, []
        
        # Separate CSVs from PKL
        for path in file_paths:
            ext = os.path.splitext(path)[1].lower()
            if ext == ".csv":
                csv_files.append(path)
            elif ext == ".pkl" and pkl_file is None:
                    pkl_file = path
            else:
                messagebox.showwarning("Unsupported File", f"Skipping file: {path}")
        
        return pkl_file, csv_files
    
    @staticmethod     
    def parseNewDF(dashboard: "Dashboard", df:pd.DataFrame, account_name: str) -> Tuple[pd.DataFrame, str]:
        """
        Parses and formats new financial data according to account type and structure.
        
        Parameters:
            df (pd.DataFrame): DataFrame containing raw transaction data.
            account_name (str): Name of the account (used for categorization).
        
        Returns:
            pd.DataFrame: Formatted DataFrame ready for use in the application.
            case (str or int): Categorization of the account type (e.g., "Type 1").
        """
        df = DataManager.normalizeColumns(df)
        expected_headers = dashboard.getExpectedHeaders()

        # Add missing columns if necessary
        for col in expected_headers:
            if col not in df.columns:
                df[col] = ""  # Add missing columns with empty values

        # Reorder the DataFrame to match expected headers
        df = df[expected_headers]

        df['Account'] = account_name
        case = DataManager.categorizeAccount(df)

        # Final adjustments before returning
        df = DataFrameProcessor.getDataFrameIndex(df)
        df = DataFrameProcessor.convertCurrency(df)
        
        return df, case

    @staticmethod
    def categorizeAccount(df: pd.DataFrame) -> str:
        """
        Categorizes the account based on transaction patterns (e.g., Payment, Deposit, Balance).
        
        Parameters:
            df (pd.DataFrame): DataFrame containing the financial data.
        
        Returns:
            str: Account type category (e.g., "Type 1", "Type 2").
        """
        if (df["Payment"] <= 0.00).all() and (df["Deposit"] >= 0.00).all() and (df["Balance"] == 0.00).all():
            return "Type 1"
        elif (df["Payment"] >= 0.00).all() and (df["Deposit"] <= 0.00).all() and (df["Balance"] == 0.00).all():
            return "Type 2"
        elif (df["Payment"] >= 0.00).all() and (df["Deposit"] >= 0.00).all() and (df["Balance"] == 0.00).all():
            return "Type 3"
        elif (df["Payment"] >= -999999.00).all() and (df["Deposit"] == 0.00).all():
            return "Type 4"
        else:
            return "Type 0"
        
    @staticmethod
    def normalizeColumns(df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalizes column names to a standard format.
        
        Parameters:
            df (pd.DataFrame): DataFrame with raw columns.
        
        Returns:
            pd.DataFrame: DataFrame with normalized column names.
        """
        header_mapping = {
            "Transaction ID": "No.",
            "Transaction Date": "Date",
            "Amount": "Payment",
            "Credit": "Deposit",
            "Debit": "Payment",
            "Memo": "Note"
        }

        df.columns = [header_mapping.get(col, col) for col in df.columns]
        return df
    
    @staticmethod
    def findNewEntries(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
        """
        Compares two DataFrames and returns rows in df1 that are not in df2.
        
        Parameters:
            df1 (pd.DataFrame): New DataFrame.
            df2 (pd.DataFrame): Old DataFrame to compare against.
        
        Returns:
            pd.DataFrame: Rows in df1 that are not in df2.
        """
        return df1.loc[~df1.apply(tuple, axis=1).isin(df2.apply(tuple, axis=1))]
    
    @staticmethod
    def addNewEntries(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
        """
        Merges two DataFrames by appending rows from df2 to df1 while ensuring unique entries.
        
        Parameters:
            df1 (pd.DataFrame): First DataFrame.
            df2 (pd.DataFrame): Second DataFrame to merge with df1.
        
        Returns:
            pd.DataFrame: Merged DataFrame.
        """
        return pd.concat([df1, df2], ignore_index=True).drop(columns=['Index'], errors='ignore')

    @staticmethod
    def exportData(banking_data: pd.DataFrame, investment_data: pd.DataFrame, initial_balances: dict, new_file: str) -> str:
        """
        Exports all data to an Excel file.
        
        Parameters:
            banking_data (pd.DataFrame): Banking transaction data.
            investment_data (pd.DataFrame): Investment transaction data.
            initial_balances (dict): Initial balances for each account.
            new_file (str): Path for the new file or empty string to prompt the user.
        
        Returns:
            str: Path of the saved file.
        """
        if not new_file:
            file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
            if not file_path:
                return ""
        else:
            file_path = new_file
        
        with pd.ExcelWriter(file_path) as writer:
            banking_data.to_excel(writer, sheet_name="Banking Transactions", index=False)
            investment_data.to_excel(writer, sheet_name="Investments", index=False)
            initial_balances.to_excel(writer, sheet_name="Initial Balances", index=False)
            
        messagebox.showinfo("Export Complete", f"Data saved to {file_path}")
        return file_path
    
    @staticmethod
    def saveData(banking_data:pd.DataFrame, investment_data:pd.DataFrame, initial_balances:dict, account_types: dict, new_file: str) -> None:
        """
        Saves data to a specified .pkl file.
        
        Parameters:
            banking_data (pd.DataFrame): Banking transaction data.
            investment_data (pd.DataFrame): Investment transaction data.
            initial_balances (dict): Initial balances for each account.
            account_types (dict): Account types for each account.
            new_file (str): The file path to save the data.
            
        Returns:
            None
        """
        if new_file == '':
            file_path = filedialog.asksaveasfilename(defaultextension='pkl', filetypes=[("Save Files", "*.pkl")])
            if not file_path:
                return ''
        else:
            file_path = new_file

        try:
            # Check if the data is valid before saving
            if banking_data.empty and investment_data.empty:
                messagebox.showerror("Error", "No data to save!")
                return

            banking_data = DataFrameProcessor.convertToDatetime(banking_data)
            investment_data = DataFrameProcessor.convertToDatetime(investment_data)
        
            with open(file_path, "wb") as f:
                pickle.dump(
                            {"Banking Data": banking_data, 
                            "Initial Balances": initial_balances, 
                            "Account Types": account_types, 
                            "Investment Data": investment_data
                            }, f)
        
            messagebox.showinfo("Save Complete", f"Data saved to {file_path}")  
        
            return file_path
        
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save data: {e}")
            return ''
        
    @staticmethod
    def loadSaveFile(save_file: str) -> Tuple[pd.DataFrame, pd.DataFrame, dict, dict]:
        """
        Loads data from a pickle file.
        
        Parameters:
            save_file (str): Path to the saved .pkl file.
        
        Returns:
            Tuple: Contains:
                - Banking Data (pd.DataFrame)
                - Investment Data (pd.DataFrame)
                - Initial Balances (dict)
                - Account Types (dict)
        """
        if not save_file:
            messagebox.showerror("Error", "No file selected!")
            return pd.DataFrame(), pd.DataFrame(), {}, {}
         
        try:
            with open(save_file, "rb") as f:
                data = pickle.load(f)

            # Check if the loaded data has the expected structure
            required_keys = ["Banking Data", "Initial Balances", "Account Types", "Investment Data"]
            missing_keys = [key for key in required_keys if key not in data]
            if missing_keys:
                raise ValueError(f"Missing expected keys in file: {', '.join(missing_keys)}")

            banking_data = data["Banking Data"]
            investment_data = data["Investment Data"]
            initial_balances = data["Initial Balances"]
            account_types = data["Account Types"]

            # Ensure that the data is valid
            if banking_data.empty and investment_data.empty:
                messagebox.showwarning("Warning", "The data in the file is empty.")

            banking_data = banking_data.fillna(value='')
            investment_data = investment_data.fillna(value='')

            banking_data = DataFrameProcessor.getDataFrameIndex(banking_data)
            investment_data = DataFrameProcessor.getDataFrameIndex(investment_data)

            messagebox.showinfo("Load Complete", f"Data loaded from {save_file}")
    
            return banking_data, investment_data, initial_balances, account_types

        except FileNotFoundError:
            messagebox.showerror("File Not Found", "The selected file could not be found.")
            return pd.DataFrame(), pd.DataFrame(), {}, {}
        
        except ValueError as e:
            messagebox.showerror("Invalid File", f"Error loading file: {e}")
            return pd.DataFrame(), pd.DataFrame(), {}, {}
        
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load data: {e}")
            return pd.DataFrame(), pd.DataFrame(), {}, {}   

    @staticmethod
    def convertStrToDate(date_str: str) -> date:
        split_str = date_str.split("-")
        return date(int(split_str[0]), int(split_str[1]), int(split_str[2])) 

class TransactionManager:
    @staticmethod
    def openTransactionWindow(dashboard_actions: "Dashboard", 
                              dashboard: "Dashboard", 
                              edit=False) -> None:
        """Opens a transaction window for adding/editing a transaction."""

        # Define and call the necessary helper functions
        def validateInputs(entry_fields):
            """Validates all user inputs in the transaction form."""
            errors = []
            for header, widget in entry_fields.items():
                value = widget.get().strip()
                if not TransactionManager.validateField(header, value, widget, errors):
                    errors.append(f"'{header}' must be a valid number.")
                    continue
            if errors:
                messagebox.showerror("Input Error", "\n".join(errors))
                return False
            return True
        
        def submitTransaction(event=None):
            """Handles transaction submission (add/edit)."""
            if not validateInputs(entry_fields):
                return
            stored_values = TransactionManager.collectStoredValues(entry_fields)
            new_df = pd.DataFrame([stored_values])
            if not TransactionManager.processTransaction(dashboard, dashboard_actions, new_df, edit):
                return
            transaction_window.destroy()

        def createTransactionWindow(headers, prefill_data):
            """Creates the main transaction window with entries and widgets."""
            entry_fields = {}
            for idx, column in enumerate(headers):
                tk.Label(transaction_window, text=column, anchor="w").grid(row=idx, column=0, padx=10, pady=5, sticky="w")

                frame = ttk.Frame(transaction_window)
                frame.grid(row=idx, column=1, padx=10, pady=5, sticky="ew")

                TransactionManager.createInputField(dashboard, frame, column, prefill_data, entry_fields, edit)

            return entry_fields
        
        #TODO make it so only one entry can be edited.
        
        # Main code to open the window and manage transactions
        transaction_window = tk.Toplevel(dashboard)
        transaction_window.title("Edit Transaction" if edit else "Add Transaction")

        # Configure the second column to expand with window resizing
        transaction_window.grid_columnconfigure(1, weight=1)
        
        transaction_window.bind("<Escape>", lambda event: transaction_window.destroy())
        transaction_window.bind("<Return>", submitTransaction)

        headers, prefill_data = TransactionManager.prepareHeadersAndPrefillData(dashboard, edit)

        entry_fields = createTransactionWindow(headers, prefill_data)

        submit_button = tk.Button(transaction_window, 
                                  text="Submit", 
                                  command=submitTransaction,
                                  bg=StyleConfig.BUTTON_COLOR, 
                                  fg=StyleConfig.TEXT_COLOR, 
                                  relief=StyleConfig.BUTTON_STYLE)
        submit_button.grid(row=len(headers), column=0, columnspan=2, pady=10)
        
    @staticmethod
    def validateField(header: str, value: str, widget: tk.Entry, errors: list) -> bool:
        """Validates individual fields in the transaction form."""
        if header in ["Payment", "Deposit", "Balance", "Units", "Price"]:
            try:
                float(value.replace("$", "").replace(",", ""))
                widget.config(bg="white")
            except ValueError:
                errors.append(f"'{header}' must be a valid number.")
                widget.config(bg="lightcoral")
                return False
        elif header == "Date":
            try:
                datetime.strptime(value, "%Y-%m-%d")
                widget.config(bg="white")
            except ValueError:
                errors.append(f"Invalid date format for '{header}'. Use YYYY-MM-DD.")
                widget.config(bg="lightcoral")
                return False
        return True
    
    @staticmethod
    def collectStoredValues(entry_fields: dict) -> dict:
        """Collects values from the entry fields and returns a dictionary."""
        return {header: entry.get().strip() for header, entry in entry_fields.items()}
    
    @staticmethod
    def processTransaction(dashboard: "Dashboard", dashboard_actions: "DashboardActions", new_df: pd.DataFrame, edit: bool) -> bool:
        """Processes the transaction after submission (add or edit)."""

        df_to_update = TransactionManager.getDataFrameToUpdate(dashboard)

        if edit:
            return TransactionManager.updateExistingTransaction(dashboard_actions, new_df, df_to_update)
        else:
            return TransactionManager.addNewTransaction(dashboard, new_df, df_to_update)
        
    @staticmethod
    def getDataFrameToUpdate(dashboard: "Dashboard") -> pd.DataFrame:
        """Returns the appropriate DataFrame based on the account type."""
        if dashboard.table_to_display == 'Banking':
            return dashboard.all_banking_data
        elif dashboard.table_to_display == 'Investments':
            return dashboard.all_investment_data
        else:
            messagebox.showerror("Error", "Unknown table type.")
            return pd.DataFrame()

    @staticmethod
    def updateExistingTransaction(dashboard_actions: "DashboardActions", new_df: pd.DataFrame, df_to_update: pd.DataFrame) -> bool:
        """Handles updating an existing transaction."""
        selected_items = dashboard_actions.widget_dashboard.tree.selection()

        if not selected_items:
            messagebox.showwarning("Warning", "No row selected for editing.")
            return False

        selected_values = dashboard_actions.widget_dashboard.tree.item(selected_items[0], "values")

        index_to_update = int(selected_values[0])

        updated_values = new_df.iloc[0].copy()

        dashboard_actions.widget_dashboard.tree.item(selected_items[0], values=updated_values.values.tolist())

        new_df = DataFrameProcessor.convertCurrency(new_df)

        for col in df_to_update.columns:
            old_val = new_df.at[index_to_update, col]
            if pd.api.types.is_integer_dtype(df_to_update[col]):
                new_val = int(old_val)
            else:
                new_val = old_val
            df_to_update.at[index_to_update, col] = new_val

        return True

    @staticmethod
    def addNewTransaction(dashboard: "Dashboard", new_df: pd.DataFrame, df_to_update: pd.DataFrame) -> bool:
        """Handles adding a new transaction."""
        df_to_update = pd.concat([df_to_update, new_df], ignore_index=True)
        df_to_update = DataFrameProcessor.getDataFrameIndex(df_to_update)
        
        dashboard.updateCurrentDF(df_to_update)
        return True

    @staticmethod
    def createInputField(dashboard: "Dashboard", 
                         frame: ttk.Frame, 
                         column: str, 
                         prefill_data: dict, 
                         entry_fields: dict, 
                         edit: bool) -> tk.Entry:
        """Creates the appropriate input field for each column."""
        current_value = prefill_data.get(column, "")

        if column == "Date":
            return TransactionManager.createDateField(frame, current_value, entry_fields, column)

        elif column in ["Payment", "Deposit", "Balance", "Units"]:
            return TransactionManager.createNumericField(frame, current_value, entry_fields, edit, column)

        elif column in ["Note", "Symbol"]:
            return TransactionManager.createTextField(frame, current_value, entry_fields, column)

        elif column in ["Description", "No."]:
            return TransactionManager.createImmutableField(frame, current_value, entry_fields, edit, column)

        elif column in ["Category", "Account", "Payee", "Action", "Asset"]:
            return TransactionManager.createDropdownField(dashboard, frame, column, current_value, entry_fields)

        return None
    
    @staticmethod
    def createDateField(frame: ttk.Frame, current_value: str, entry_fields: dict, column: str) -> tk.Entry:
        """Creates a date input field with a calendar button."""
        try:
            initial_date = datetime.strptime(current_value, "%Y-%m-%d").date()
        except ValueError:
            initial_date = date.today()

        entry = tk.Entry(frame)
        entry.pack(side=tk.LEFT, fill='x', expand=True)
        entry_fields["Date"] = entry
        entry_fields["Date"].insert(0, initial_date)

        calendar_button = tk.Button(frame, text="📅", command=lambda e=entry_fields["Date"]: Windows.openCalendarWindow(e, initial_date))
        calendar_button.pack(side=tk.RIGHT)

        return entry

    @staticmethod
    def createNumericField(frame: ttk.Frame, current_value: str, entry_fields: dict, edit: bool, column: str) -> tk.Entry:
        """Creates numeric input fields such as Payment, Deposit, Balance, Units."""
        entry = tk.Entry(frame)
        entry.pack(side=tk.LEFT, fill='x', expand=True)
        entry_fields[column] = entry
        entry.insert(0, current_value)
        if edit:
            if column != "Units":
                entry.config(state=tk.DISABLED)

        return entry

    @staticmethod
    def createTextField(frame: ttk.Frame, current_value: str, entry_fields: dict, column: str) -> tk.Entry:
        """Creates text input fields such as Note or Symbol."""
        entry = tk.Entry(frame)
        entry.pack(side=tk.LEFT, fill='x', expand=True)
        entry_fields[column] = entry
        entry.insert(0, current_value)

        return entry

    @staticmethod
    def createImmutableField(frame: ttk.Frame, current_value: str, entry_fields: dict, edit: bool, column: str) -> tk.Entry:
        """Creates immutable fields such as Description."""
        entry = tk.Entry(frame)
        entry.pack(side=tk.LEFT, fill='x', expand=True)
        entry_fields[column] = entry
        entry.insert(0, current_value)
        if edit:
            entry.config(state=tk.DISABLED)

        return entry

    @staticmethod
    def createDropdownField(dashboard: "Dashboard", frame: ttk.Frame, column: str, current_value: str, entry_fields: dict) -> ttk.Combobox:
        """Creates a dropdown (ComboBox) field for categories, accounts, payees, etc."""
        entry = ttk.Combobox(frame, state="readonly")

        if column == "Category":
            dashboard.ui_actions.getCategories()
            entry["values"] = dashboard.categories
        elif column == "Payee":
            dashboard.ui_actions.getPayees()
            entry["values"] = dashboard.payees
        elif column == "Account":
            if dashboard.table_to_display == 'Banking':
                dashboard.ui_actions.getBankingAccounts()
                if len(dashboard.banking_accounts) == 0:
                    entry = tk.Entry(frame)
                    entry.pack(side=tk.LEFT, fill='x', expand=True)
                    entry_fields[column] = entry
                    entry.insert(0, current_value)
                    return entry
                else:
                    entry["values"] = dashboard.banking_accounts

            elif dashboard.table_to_display == 'Investments':
                dashboard.ui_actions.getInvestmentAccounts()
                if len(dashboard.investment_accounts) == 0:
                    entry = tk.Entry(frame)
                    entry.pack(side=tk.LEFT, fill='x', expand=True)
                    entry_fields[column] = entry
                    entry.insert(0, current_value)
                    return entry
                else:
                    entry["values"] = dashboard.investment_accounts
            
        elif column == "Asset":
            dashboard.ui_actions.getAssets()
            entry["values"] = dashboard.assets
        elif column == 'Action':
            dashboard.ui_actions.getInvestmentActions()
            entry["values"] = dashboard.actions

        entry.set(current_value)
        entry.pack(side=tk.LEFT, fill='x', expand=True)
        entry_fields[column] = entry

        return entry

    @staticmethod
    def prepareHeadersAndPrefillData(dashboard: "Dashboard", edit: bool) -> Tuple[List[str], dict]:
        """Prepares headers and prefill data for the form."""
        if edit:
            selected_items = dashboard.ui_manager.tree.selection()
            if not selected_items:
                messagebox.showwarning("Warning", "No transaction selected for editing.")
                return [], {}
            selected_values = dashboard.ui_manager.tree.item(selected_items, "values")
            headers = [dashboard.ui_manager.tree.heading(col)["text"] for col in dashboard.ui_manager.tree["columns"]]
            prefill_data = dict(zip(headers, selected_values))
        else:
            if dashboard.table_to_display == 'Banking':
                headers = list(dashboard.banking_column_widths.keys())[1:]
            elif dashboard.table_to_display == 'Investments':
                headers = list(dashboard.investment_column_widths.keys())[1:]

            prefill_data = {}
        return headers, prefill_data

    @staticmethod
    def deleteTransaction(dashboard_actions: "Dashboard", dashboard: "Dashboard") -> None:
        selected_items = dashboard_actions.widget_dashboard.tree.selection()

        if not selected_items:
            messagebox.showwarning("Warning", "No transactions selected!")
            return

        selected_numbers = {int(dashboard_actions.widget_dashboard.tree.item(item, "values")[0]) for item in selected_items}

        if dashboard.table_to_display == 'Banking':
            df_to_update = dashboard.all_banking_data
        elif dashboard.table_to_display == 'Investments':
            df_to_update = dashboard.all_investment_data
        else:
            messagebox.showerror("Error", f"Unknown table type: {dashboard.table_to_display}")
            return

        if dashboard.table_to_display == 'Banking':
            indices_to_drop = dashboard.all_banking_data[dashboard.all_banking_data["No."].isin(selected_numbers)].index
        elif dashboard.table_to_display == 'Investments': 
            indices_to_drop = dashboard.all_investment_data[dashboard.all_investment_data["No."].isin(selected_numbers)].index

        confirm = messagebox.askyesno("Confirm Delete",
                                    f"Are you sure you want to delete {len(indices_to_drop)} transaction(s)?",
                                    parent=dashboard)
        if not confirm:
            return  # User canceled

        if dashboard.table_to_display == 'Banking':
            # Perform deletion in-place
            dashboard.all_banking_data.drop(indices_to_drop, inplace=True)
            dashboard.all_banking_data.reset_index(drop=True, inplace=True)

            # Reindex the DataFrame
            dashboard.all_banking_data = DataFrameProcessor.getDataFrameIndex(dashboard.all_banking_data)
            
            # Update the displayed table immediately
            dashboard_actions.updateTable(dashboard.all_banking_data)

        elif dashboard.table_to_display == 'Investments': 
            # Perform deletion in-place
            dashboard.all_investment_data.drop(indices_to_drop, inplace=True)
            dashboard.all_investment_data.reset_index(drop=True, inplace=True)

            # Reindex the DataFrame
            dashboard.all_investment_data = DataFrameProcessor.getDataFrameIndex(dashboard.all_investment_data)
            
            # Update the displayed table immediately
            dashboard_actions.updateTable(dashboard.all_investment_data)


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
        self.main_content.grid_columnconfigure(0, weight=1)
        self.main_content.grid_rowconfigure(1, weight=1)
        
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
        """Creates the sidebar with accounts, categories, payees, and reports."""
        self.sidebar_labels = []
        self.sidebar_listboxes = []
        self.sidebar_frames = []

        sidebar_items = ["Accounts", "Categories", "Payees", "Reports"]

        for idx, item in enumerate(sidebar_items):
            self._createSidebarLabel(item, idx)
            self._createSidebarListbox(idx)

        # Configure sidebar grid to expand
        self.sidebar.grid_columnconfigure(0, weight=1)

    def _createSidebarLabel(self, item, idx):
        """Creates a label for the sidebar."""
        label = tk.Label(
            self.sidebar,
            text=item,
            font=(StyleConfig.FONT_FAMILY, StyleConfig.HEADING_FONT_SIZE, "bold"),
            bg=StyleConfig.BG_COLOR,
            fg=StyleConfig.TEXT_COLOR
        )
        label.grid(row=2*idx, column=0, sticky="ew", padx=5, pady=(10, 0))
        self.sidebar_labels.append(label)

    def _createSidebarListbox(self, idx):
        """Creates a listbox with a scrollbar for the sidebar."""
        listbox_frame = ttk.Frame(self.sidebar)
        listbox_frame.grid(row=2*idx+1, column=0, sticky="ew", padx=5, pady=(0, 10))

        listbox = tk.Listbox(listbox_frame, height=6, width=35)
        listbox.pack(side=tk.LEFT, fill='x', expand=True)

        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill='y')
        listbox.config(yscrollcommand=scrollbar.set)

        # Bind events
        listbox.bind("<MouseWheel>", self.actions_manager.smoothScroll)
        listbox.bind("<Double-Button-1>", lambda event, idx=idx: self.actions_manager.filterEntries(case=idx+1))

        self.sidebar_listboxes.append(listbox)
        self.sidebar_frames.append(listbox_frame)
        
    ########################################################
    # TOOLBAR
    ########################################################
    def createToolbar(self):
        """Creates a toolbar with basic transaction actions."""
    
        self.toolbar = tk.Frame(self.main_content, relief=StyleConfig.BUTTON_STYLE, bg=StyleConfig.BG_COLOR)
        self.toolbar.grid(row=0, column=0, sticky='nsew')
        
        # Initialize the image and button storage
        self.button_image_loc = os.path.join(os.path.dirname(__file__), "Images")
        self.buttons = []
        self.images = {}
        
        # Define button configurations
        button_data = self._getButtonData()
        btn_size = 50  # Button size
        
        # Create buttons and separators
        self._createButtonsAndSeparators(button_data, btn_size)
        
        # Create search field and buttons
        self._createSearchBar()

    def _getButtonData(self):
        """Returns a list of button data for toolbar buttons."""
        return [
            ("Add",         "add.png",      self.actions_manager.addEntry),
            ("Edit",        "edit.png",     self.actions_manager.editTransaction),
            ("Delete",      "delete.png",   self.actions_manager.deleteTransaction),
            ("Open",        "open.png",     self.actions_manager.openData),
            ("Balances",    "accounts.png", self.actions_manager.trackBankBalances),
            ("Payee",       "payee.png",    lambda: self.actions_manager.manageItems("Payees")),
            ("Category",    "category.png", lambda: self.actions_manager.manageItems("Categories")),
            ("Actions",     "actions.png",  lambda: self.actions_manager.manageItems("Actions")),
            ("Banking",     "banking.png",  lambda: self.actions_manager.switchAccountView("Banking")),
            ("Stocks",      "stonks.png",   lambda: self.actions_manager.switchAccountView("Investments")),
            ("Reports",     "budget.png",   self.actions_manager.displayReports),
            ("Export",      "export.png",   self.actions_manager.exportData),
            ("Options",     "options.png",  self.actions_manager.viewOptions),
        ]

    def _createButtonsAndSeparators(self, button_data, btn_size):
        """Creates buttons and separators for the toolbar."""
        for index, (text, icon, command) in enumerate(button_data):
            button = self._createButton(text, icon, command, btn_size)
            button.pack(side=tk.LEFT, padx=4, pady=2)
            self.buttons.append(button)
            
            if index in [3, 7, 9, 10]:
                self._createSeparator()

    def _createButton(self, text, icon, command, btn_size):
        """Helper method to create individual buttons."""
        img_path = os.path.join(self.button_image_loc, icon)
        img = Image.open(img_path)
        img = img.resize((36,36))  # Resize image to 24x24 pixels
        self.images[icon] = ImageTk.PhotoImage(img)
        
        try:
            button = tk.Button(
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
            button = tk.Button(
                self.toolbar, 
                text=text, 
                compound=tk.TOP, 
                command=command, 
                width=btn_size, 
                height=btn_size, 
                bg=StyleConfig.BUTTON_COLOR, 
                relief=StyleConfig.BUTTON_STYLE
            )
        return button

    def _createSeparator(self):
        """Helper method to create separators in the toolbar."""
        ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

    def _createSearchBar(self):
        """Creates the search label, entry, and buttons in the toolbar."""
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
        self.search_entry = tk.Entry(self.toolbar, width=30, bg=StyleConfig.BUTTON_COLOR)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind("<Return>", lambda event: self.actions_manager.searchTransactions())
        
        # Search button
        search_button = tk.Button(self.toolbar, 
                                text="Go",
                                command=self.actions_manager.searchTransactions, 
                                bg=StyleConfig.BUTTON_COLOR, 
                                relief=StyleConfig.BUTTON_STYLE)
        search_button.pack(side=tk.LEFT, padx=5)
        self.buttons.append(search_button)
        
        # Advanced search button
        adv_search_button = tk.Button(self.toolbar, 
                                    text="Advanced Search", 
                                    command=self.actions_manager.openAdvancedSearch,
                                    bg=StyleConfig.BUTTON_COLOR, 
                                    relief=StyleConfig.BUTTON_STYLE)
        adv_search_button.pack(side=tk.LEFT, padx=5)
        self.buttons.append(adv_search_button)

    ########################################################
    # MAIN WORKING PORTION OF WINDOW
    ########################################################
    def createTransactionTable(self):
        """Creates the transaction table with scrolling, as a placeholder for future graphs/plots."""
        
        # Create the content frame (for table, graph, etc.)
        self._createContentFrame()
        
        # Initialize the treeview (transaction table)
        self._createTableTreeview()
        
        # Initialize the scrollbar
        self._createTableScrollbar()
        
        # Bind events to the table
        self._bindTableEvents()

    def _createContentFrame(self):
        """Creates the content frame that holds the table, plot, or other content."""
        # Create a frame where any content (table/graphs/reports) will go
        self.content_frame = tk.Frame(self.main_content)
        self.content_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
        
        # Configure layout
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

    def _createTableTreeview(self):
        """Creates the Treeview widget for displaying transaction data."""
        self.tree = ttk.Treeview(self.content_frame, 
                                show='headings',
                                yscrollcommand=lambda *args: self.y_scrollbar.set(*args),
                                height=15)
        self.tree.grid(row=0, column=0, sticky='nsew')

    def _createTableScrollbar(self):
        """Creates the vertical scrollbar for the Treeview."""
        self.y_scrollbar = ttk.Scrollbar(self.content_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.y_scrollbar.set)
        self.y_scrollbar.grid(row=0, column=1, sticky='ns')

    def _bindTableEvents(self):
        """Binds events to the Treeview widget."""
        # Bind double-click to edit cell
        self.tree.bind("<Double-1>", self.actions_manager.editCell)
        self.tree.bind("<Button-3>", lambda event: self.actions_manager.showRightClickTableMenu(event))

    def showTransactionTable(self, data):
        """Displays the transaction table (Treeview) in the content area."""
        # Remove any existing widgets in the content area
        self._clearContentArea()

        # Re-create the table with the provided data
        self.createTransactionTable()  # Or update the Treeview with new data

    def showGraph(self, plot):
        """Displays a Matplotlib graph in the content area."""
        self._clearContentArea()
        
        # Embed the Matplotlib figure into the Tkinter content area
        self.figure_canvas = FigureCanvasTkAgg(plot, master=self.content_frame)  # Create a canvas from the plot
        self.figure_canvas.draw()
        self.figure_canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew')  # Place the plot into the grid

    def showReport(self, report):
        """Displays a report in the content area (can be text, tables, etc.)."""
        self._clearContentArea()
        
        # Example for a text-based report
        report_label = tk.Label(self.content_frame, text=report, bg=StyleConfig.BG_COLOR, fg=StyleConfig.TEXT_COLOR)
        report_label.grid(row=0, column=0, sticky="nsew")

    def _clearContentArea(self):
        """Clears the content area (useful for swapping between views)."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()  # Destroy all widgets (treeview, plot, report) currently in the content frame

    ########################################################
    # UI STYLE
    ########################################################    
    def applyStyleChanges(self):
        """Applies updated style settings dynamically to ttk and standard Tk widgets."""
        # Apply background color to main sections
        sections = [self.sidebar, self.toolbar, self.main_content, self.content_frame]
        for section in sections:
            section.config(bg=StyleConfig.BG_COLOR)

        style = ttk.Style()
        self._applyTreeviewStyle(style)
        self._applyButtonStyle()
        self._applySidebarStyle()

        # Ensure the colors update immediately
        self.update_idletasks()

    def _applyTreeviewStyle(self, style):
        style.configure("Treeview", 
                        rowheight=StyleConfig.ROW_HEIGHT, 
                        font=(StyleConfig.FONT_FAMILY, StyleConfig.FONT_SIZE),
                        background=StyleConfig.BG_COLOR,
                        foreground=StyleConfig.TEXT_COLOR,
                        fieldbackground=StyleConfig.BG_COLOR)

        style.configure("Treeview.Heading", 
                        font=(StyleConfig.FONT_FAMILY, StyleConfig.HEADING_FONT_SIZE, "bold"),
                        background=StyleConfig.HEADER_COLOR, 
                        foreground='black',
                        fieldbackground=StyleConfig.BG_COLOR,
                        relief="flat")
        
        Tables.applyBandedRows(self.tree, colors=[StyleConfig.BAND_COLOR_1, StyleConfig.BAND_COLOR_2])
        
        style.map("Treeview", 
                background=[("selected", StyleConfig.SELECTION_COLOR)],
                foreground=[("selected", "#FFFFFF" if StyleConfig.DARK_MODE else "#000000")])

    def _applyButtonStyle(self):
        for btn in self.buttons:
            btn.config(bg=StyleConfig.BUTTON_COLOR,
                    fg=StyleConfig.TEXT_COLOR,  
                    relief=StyleConfig.BUTTON_STYLE, 
                    padx=StyleConfig.BUTTON_PADDING, 
                    pady=StyleConfig.BUTTON_PADDING, 
                    font=(StyleConfig.FONT_FAMILY, StyleConfig.BUTTON_FONT_SIZE))

    def _applySidebarStyle(self):
        for label in self.sidebar_labels:
            label.config(bg=StyleConfig.BG_COLOR, 
                        fg=StyleConfig.TEXT_COLOR, 
                        font=(StyleConfig.FONT_FAMILY, StyleConfig.HEADING_FONT_SIZE, "bold"))

        for listbox in self.sidebar_listboxes:
            listbox.config(bg=StyleConfig.BG_COLOR, 
                        fg=StyleConfig.TEXT_COLOR, 
                        font=(StyleConfig.FONT_FAMILY, StyleConfig.BUTTON_FONT_SIZE))

        self.search_label.config(bg=StyleConfig.BG_COLOR, 
                                fg=StyleConfig.TEXT_COLOR, 
                                font=(StyleConfig.FONT_FAMILY, StyleConfig.BUTTON_FONT_SIZE))
        self.search_entry.config(bg=StyleConfig.BG_COLOR, 
                                fg=StyleConfig.TEXT_COLOR, 
                                font=(StyleConfig.FONT_FAMILY, StyleConfig.BUTTON_FONT_SIZE))


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

    def getCurrentDF(self):
        if self.main_dashboard.table_to_display == 'Banking':
            return self.main_dashboard.all_banking_data
        elif self.main_dashboard.table_to_display == 'Investment':
            return self.main_dashboard.all_investment_data 
        
    def updateCurrentDF(self, df):
        if self.main_dashboard.table_to_display == 'Banking':
            self.main_dashboard.all_banking_data = df
        elif self.main_dashboard.table_to_display == 'Investment':
            self.main_dashboard.all_investment_data = df

        self.finalizeDataUpdate(df)

    ########################################################
    # Modify Entries
    ########################################################
    def addEntry(self) -> None:
        """
        Opens a transaction window in 'add' mode.

        This method calls the TransactionManager to display a form for creating a new transaction.
        Once submitted, the new transaction is appended to the main_dashboard's data.
        """
        TransactionManager.openTransactionWindow(self, self.main_dashboard, edit=False)

    def editTransaction(self) -> None:
        """
        Opens a transaction window in 'edit' mode.

        This method calls the TransactionManager to display a form for modifying the currently
        selected transaction in the Treeview. Once submitted, the changes are saved back to
        the main_dashboard's data.
        """
        TransactionManager.openTransactionWindow(self, self.main_dashboard, edit=True)

    def deleteTransaction(self) -> None:
        """
        Deletes the currently selected transaction(s) from the data.

        This method calls the TransactionManager to remove the selected transaction(s)
        from the main_dashboard's data, and then refreshes the UI to reflect the changes.
        """
        TransactionManager.deleteTransaction(self, self.main_dashboard) 

    ########################################################
    # Data Manipulation
    ########################################################
    def openData(self) -> None:
        """
        Opens one or more data files and merges the results into the main Dashboard's DataFrame.
        """
        pkl_file, csv_files = DataManager.openData()

        if pkl_file:
            self.loadPklFile(pkl_file)
            return

        if csv_files:
            self.loadCsvFiles(csv_files)

    def loadPklFile(self, pkl_file: str) -> None:
        """Handles loading a .pkl file."""
        self.main_dashboard.master.save_file = pkl_file
        self.loadSaveFile()  # Load and display data from the PKL

    def loadCsvFiles(self, csv_files: list) -> None:
        """Handles loading and processing CSV files."""
        parsed_data = []
        for csv_path in csv_files:
            df = DataManager.readCSV(csv_path)
            if not df.empty:
                account_name = os.path.basename(csv_path).split(".")[0]

                # Convert DataFrame to a standardized format
                parsed_df, case = DataManager.parseNewDF(self.main_dashboard, df, account_name)
                parsed_df = DataFrameProcessor.convertToDatetime(parsed_df)

                # Check for existing data in the DataFrame
                leftover_df = self.checkAndMergeData(parsed_df, account_name)

                df_to_check = self.getCurrentDF()

                if not df_to_check.empty:
                    # Check for existing data in the DataFrame
                    self.checkAndMergeData(parsed_df, account_name)

                else:
                    if self.main_dashboard.table_to_display == 'Banking':
                        self.main_dashboard.all_banking_data = parsed_df
                    elif self.main_dashboard.table_to_display == 'Investments':
                        self.main_dashboard.all_investment_data = parsed_data

                    parsed_data.append(pd.DataFrame(columns=parsed_df.columns))

    def checkAndMergeData(self, parsed_df: pd.DataFrame, account_name: str) -> None:

        if self.main_dashboard.table_to_display == 'Banking':
            headers_to_compare = ["Description", "Date", "Payment", "Deposit"]
            
        elif self.main_dashboard.table_to_display == 'Investments':
            headers_to_compare = ["Date", "Action", "Asset", "Symbol", "Units"]

        df_to_compare = self.getCurrentDF()
        df_to_compare = df_to_compare.copy()

        if account_name in df_to_compare["Account"].values:

            df_to_compare = df_to_compare[df_to_compare["Account"] == account_name]

            df_to_compare = DataFrameProcessor.convertToDatetime(df_to_compare)
            df_to_compare = df_to_compare[headers_to_compare]

            parsed_df = DataFrameProcessor.convertToDatetime(parsed_df)
            parsed_df = parsed_df[headers_to_compare]

            new_df = DataManager.findNewEntries(parsed_df, df_to_compare)

            if not new_df.empty:
                self.addNewEntries(new_df, account_name)

        else:
            self.addNewEntries(parsed_df, account_name)
        
    def addNewEntries(self, new_df: pd.DataFrame, account_name: str) -> bool:
        """

        """

        all_data_df = self.getCurrentDF()

        all_headers = all_data_df.columns

        for column in all_headers:
            if column not in new_df.columns:
                if column == 'Balance':
                    new_df[column] = 0
                elif column == 'Account':
                    new_df[column] = account_name
                else:
                    new_df[column] = ''
        
        new_df = new_df[all_headers].fillna('')

        all_data_df = DataManager.addNewEntries(all_data_df, new_df)

        self.updateCurrentDF(all_data_df)

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
            self.main_dashboard.all_banking_data.copy(),
            self.main_dashboard.all_investment_data.copy(),
            self.main_dashboard.initial_account_balances.copy(),
            new_file=''
        )       
        
    def saveData(self, event: tk.Event | None = None) -> None:
        """
        Saves the current data to a .pkl file.
    
        Uses DataManager.saveData to write the main_dashboard's all_banking_data, initial_account_balances,
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
            self.main_dashboard.all_banking_data.copy(),
            self.main_dashboard.all_investment_data.copy(),
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
            self.main_dashboard.all_banking_data.copy(),
            self.main_dashboard.all_investment_data.copy(),
            self.main_dashboard.initial_account_balances.copy(),
            self.main_dashboard.account_cases,
            new_file=''
        )
        # Update the last saved file record
        if self.main_dashboard.master.save_file is not None:
            self.main_dashboard.master.changeSaveFile()
            
    def loadSaveFile(self, event: tk.Event | None = None) -> None:
        """
        Loads previously saved financial data from a .pkl file into the main Dashboard.
    
        This function:
        1. Uses DataManager.loadSaveFile(...) to load pickled data: transaction DataFrame, 
           initial account balances, and account types.
        2. If data is retrieved successfully, it updates self.main_dashboard.all_banking_data 
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

        all_banking_data_df, all_investment_data_df, init_bal_df, acc_type_dict = DataManager.loadSaveFile(
            self.main_dashboard.master.save_file
        )

        # Ensure proper assignment
        if isinstance(all_banking_data_df, pd.DataFrame):
            self.main_dashboard.all_banking_data = all_banking_data_df.copy()
            self.main_dashboard.all_banking_data = DataFrameProcessor.sortDataFrame(self.main_dashboard.all_banking_data)
        else:
            self.main_dashboard.all_banking_data = pd.DataFrame()  # Fallback to an empty DataFrame

        # Ensure proper assignment
        if isinstance(all_investment_data_df, pd.DataFrame):
            self.main_dashboard.all_investment_data = all_investment_data_df.copy()
            self.main_dashboard.all_investment_data = DataFrameProcessor.sortDataFrame(self.main_dashboard.all_investment_data)
        else:
            self.main_dashboard.all_investment_data = pd.DataFrame()  # Fallback to an empty DataFrame
    
        self.main_dashboard.initial_account_balances = init_bal_df
        self.main_dashboard.account_cases = acc_type_dict
    
        self.updateTable(self.main_dashboard.all_banking_data)

        self.getCategories()
        self.getAssets()
        self.getInvestmentActions()
        self.getPayees()
 
    ########################################################
    # Table Widget Manipulation
    ########################################################   
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
            #float_cols = ["Payment", "Deposit", "Balance"]  # Indices that contain monetary data
            float_cols = [5, 6, 7]
            column_data = self.main_dashboard.banking_column_widths
        else:
            desired_columns = [0, 1, 2, 3, 4, 5, 6, 7]
            float_cols = []
            column_data = self.main_dashboard.investment_column_widths

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
                formatted_row[idx] = f"${float(formatted_row[idx]) / 100:.2f}"
                            
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

        print (df)

        if self.main_dashboard.table_to_display == 'Banking':
            self.updateBalancesInDataFrame() 
        self.updateSideBar(df)
        
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
            
    def toggleButtonStates(self, show: bool) -> None:
        """
        Toggles visibility of the Payee listbox and its label.

        Parameters:
            show (bool): True to show, False to hide.
        """
        if show:
            self.widget_dashboard.buttons[4].config(state=tk.NORMAL)
            self.widget_dashboard.buttons[5].config(state=tk.NORMAL)
            self.widget_dashboard.buttons[7].config(state=tk.DISABLED)
        else:
            self.widget_dashboard.buttons[4].config(state=tk.DISABLED)
            self.widget_dashboard.buttons[5].config(state=tk.DISABLED)
            self.widget_dashboard.buttons[7].config(state=tk.NORMAL)
    
    def filterEntries(self, event=None, case=None) -> None:
        """
        Filters Tableview entries.
        """
        # Filter by account
        if case == 1:
            if self.main_dashboard.table_to_display == 'Banking':
                column = 'Account'
            elif self.main_dashboard.table_to_display == 'Investments':
                column = 'Account'

        # Filter by category
        elif case == 2:
            if self.main_dashboard.table_to_display == 'Banking':
                column = 'Category'
            elif self.main_dashboard.table_to_display == 'Investments':
                column = 'Asset'

        # Filter by payee/asset
        elif case == 3:
            if self.main_dashboard.table_to_display == 'Banking':
                column = 'Payee'
            elif self.main_dashboard.table_to_display == 'Investments':
                return

        # Reports - does not filter. 
        elif case == 4:
            return
        
        listbox = self.widget_dashboard.sidebar_listboxes[case-1]
    
        selected_index = listbox.curselection()
        if not selected_index:
            return  # No selection made
        
        item = listbox.get(selected_index)

        if case == 1:
            item = item.split(" $")[0]
        if "All" in item:
            filtered_df = self.getCurrentDF()

        else:
            if self.main_dashboard.table_to_display == 'Banking':
                filtered_df = self.main_dashboard.all_banking_data[
                    self.main_dashboard.all_banking_data[column] == item
                ].copy()
            elif self.main_dashboard.table_to_display == 'Investments':
                filtered_df = self.main_dashboard.all_investment_data[
                    self.main_dashboard.all_investment_data[column] == item
                ].copy()

        self.updateTable(filtered_df.copy())

    def switchAccountView(self, account_type: str) -> None:
        """
        Filters the data displayed based on a specified account type (e.g., "Banking" or "Investments").

        """
       
        if self.main_dashboard.table_to_display == "Banking" :
            if account_type == "Banking":
                return
            elif account_type == "Investments":
                new_df = self.main_dashboard.all_investment_data

        if self.main_dashboard.table_to_display == "Investments" :
            if account_type == "Investments":
                return
            elif account_type == "Banking":
                new_df = self.main_dashboard.all_banking_data

        self.main_dashboard.table_to_display = account_type
        self.updateTable(new_df)
    
    def trackBankBalances(self) -> None:
        #TODO Make less monolithic
        """
        Opens a Toplevel window to manually review and update the latest balance for each banking account.

        The window displays three columns:
        - Account name (from main_dashboard.all_banking_data)
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
    
        if "Account" not in self.main_dashboard.all_banking_data:
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
    
         # Get unique banking accounts from all_banking_data
        banking_accounts = self.main_dashboard.all_banking_data["Account"].unique().tolist()
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
        Propagates balance changes in the transactions DataFrame (master.all_banking_data) based on the
        latest initial account balances stored in initial_account_balances.

        For each account in initial_account_balances:
        - If the "Initial Date" is not equal to self.day_one, the function calculates the
            propagated balance using calculateBalancesPerType and updates current_account_balances.
        - Otherwise, sets the current balance for that account to 0.00.
        Finally, the updated master.all_banking_data DataFrame is displayed by calling updateTable.

        Returns
        -------
        None
            The master.all_banking_data DataFrame is updated in-place and the UI refreshed.
        """
        if self.main_dashboard.all_banking_data.empty:
            return
        
        # Iterate over each row in the initial_account_balances DataFrame.
        for _, row in self.main_dashboard.initial_account_balances.iterrows():
            account     = row["Account"]
            init_date   = row["Initial Date"]
            init_value  = row["Initial Value"]
            if init_date != self.main_dashboard.day_one:
                # Calculate the propagated balance for this account and update current_account_balances.
                self.main_dashboard.all_banking_data, self.main_dashboard.current_account_balances[account] = self.calculateBalancesPerType(
                                                                                self.main_dashboard.all_banking_data.copy(), 
                                                                                account, 
                                                                                init_date, 
                                                                                init_value)

            else:
                self.main_dashboard.current_account_balances[account] = 0.00

        self.updateSideBar(self.main_dashboard.all_banking_data)
        
    def calculateBalancesPerType(self, df: pd.DataFrame, account: str, given_date: str, given_balance: float) -> pd.DataFrame:
        #TODO Make less monolithic
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

        #TODO Fix for non-consecutive data

        return pd.DataFrame(), 0
        
        # Ensure the 'Date' column is in datetime format
        df = DataFrameProcessor.convertToDatetime(df)
        given_date = DataManager.convertStrToDate(given_date)
    
        # Filter transactions for the specified account
        account_df = df[df["Account"] == account].copy()
        account_df = account_df.reset_index()
    
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
    
    def showRightClickTableMenu(self, event=None):
        """Shows the context menu based on the column clicked."""
        # Get the column that was clicked

        # Check if the click happened in the header region
        region = self.widget_dashboard.tree.identify_region(event.x, event.y)

        # If the region is not 'heading', do nothing (i.e., the click is on a cell)
        if region != "heading":
            return  # Skip displaying the menu if the click was in a cell

        col_id = self.widget_dashboard.tree.identify_column(event.x)
        col_name = self.widget_dashboard.tree.heading(col_id, "text")
        
        menu = tk.Menu(self.main_dashboard, tearoff=0)

        # Determine the menu options based on the column clicked
        if col_name == 'Date':
            menu.add_command(label="Show last 30 days", command=lambda: self.filterTableByDate(delta=30))
            menu.add_command(label="Show last 60 days", command=lambda: self.filterTableByDate(delta=60))
            menu.add_command(label="Show last 90 days", command=lambda: self.filterTableByDate(delta=90))
            menu.add_command(label="Show last 180 days", command=lambda: self.filterTableByDate(delta=180))
            menu.add_command(label="Show last 365 days", command=lambda: self.filterTableByDate(delta=365))

        # Display the context menu at the mouse cursor position
        menu.post(event.x_root, event.y_root)

    def filterTableByDate(self, delta=30) -> None:
        """
        Filters the DataFrame to only include rows where the 'Date' column is within 
        the past `delta` number of days from today.

        Parameters:
        - delta (int): The number of days in the past to filter by.

        Returns:
        - None
        """
        if self.main_dashboard.table_to_display == 'Banking':
            df_to_filter = self.main_dashboard.all_banking_data
        elif self.main_dashboard.table_to_display == 'Investments':
            df_to_filter = self.main_dashboard.all_investment_data

        threshold_date = datetime.today() - timedelta(days=delta)

        # Filter the DataFrame to include only rows where 'Date' is >= threshold_date
        df_to_filter = df_to_filter[df_to_filter['Date'] >= threshold_date]

        self.updateTable(df_to_filter)
    
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
            if self.main_dashboard.table_to_display == 'Banking':
                df_to_update = self.main_dashboard.all_banking_data
            elif self.main_dashboard.table_to_display == 'Investments':
                df_to_update = self.main_dashboard.all_investment_data

            index_to_update = df_to_update[df_to_update["No."] == selected_number].index

            if not index_to_update.empty:
                # Handle numeric columns (Payment, Deposit, Balance)
                if col_name in ["Payment", "Deposit", "Balance"]:
                    try:
                        new_value_converted  = float(new_value.replace("$", "").replace(",", "")) * 100
                    except ValueError:
                        messagebox.showerror("Invalid Input", "Please enter a valid number.")
                        return
                    
                elif col_name in ["Units"]:
                    try:
                        new_value_converted  = float(new_value)
                    except ValueError:
                        messagebox.showerror("Invalid Input", "Please enter a valid number.")
                        return
    
                # Handle date column - store as standardized YYYY-MM-DD string
                elif col_name == "Date":
                    new_value_converted  = Utility.formatDateFromString(new_value)
                else:
                    new_value_converted = new_value
                    
                # Update the DataFrame in-place
                df_to_update.at[index_to_update[0], col_name] = new_value_converted
    
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
        if col_name in ["Note", "Symbol", "Units"]:
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
        elif col_name in ["Category", "Account", "Payee", "Action", "Asset"]:
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
                accounts = self.getBankingAccounts()
                dropdown["values"] = accounts
            elif col_name == "Asset":
                dropdown["values"] = self.main_dashboard.assets
            elif col_name == 'Action':
                dropdown["values"] = self.main_dashboard.actions
    
            dropdown.set(current_value)
            
            # When user picks an item from the dropdown, call saveEdit
            dropdown.bind("<<ComboboxSelected>>", lambda e: saveEdit(dropdown.get()))
            dropdown.focus_set()
            
            # If user moves focus away, cancel editing
            dropdown.bind("<FocusOut>", cancelEdit)
    
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
        1. Checks if main_dashboard.all_banking_data has entries.
        2. Asks the user to confirm deletion of all transactions.
        3. If confirmed, resets main_dashboard.all_banking_data to an empty DataFrame,
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
        if not self.main_dashboard.all_banking_data.empty:
            confirm = messagebox.askyesno(
                "Confirm Delete",
                "Are you sure you want to delete all transaction(s)?"
            )
            
            if confirm is None or not confirm:  # User canceled or closed dialog
                return
            
            # If confirmed, clear everything
            self.main_dashboard.all_banking_data = pd.DataFrame()
            self.main_dashboard.all_investment_data = pd.DataFrame()
            self.main_dashboard.table_to_display = 'Banking' # Or Investments
            self.main_dashboard.initial_account_balances = pd.DataFrame(columns=['Account', 'Initial Date', 'Initial Value'])

            self.main_dashboard.current_account_balances = {}
            self.main_dashboard.account_cases = {}

            self.widget_dashboard.tree.delete(*self.widget_dashboard.tree.get_children())

            for listbox in self.widget_dashboard.sidebar_listboxes:
                listbox.delete(0, tk.END)

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

    ########################################################
    # Sidebar Manipulation
    ########################################################
    def updateSideBar(self, df: pd.DataFrame) -> None:
        """
        Updates the sidebar objects.
    
        Parameters
        ----------
        df : pd.DataFrame
            A DataFrame representing transaction data (not directly used in this function).
        
        Returns
        -------
        None
            Updates the UI in-place.
        """
        
        if self.main_dashboard.table_to_display == 'Banking':
            allX = ['All Accounts', 'All Categories', 'All Payees', 'Reports']
        elif self.main_dashboard.table_to_display == 'Investments':
            allX = ['All Accounts', 'All Assets', 'All Actions', 'Reports']

        for idx, listbox in enumerate(self.widget_dashboard.sidebar_listboxes):
            listbox.delete(0, tk.END)   # Clear previous entries
            listbox.insert(tk.END, allX[idx])

            # Update based on banking dataframe
            if self.main_dashboard.table_to_display == 'Banking':
                # Update all accounts and balances
                if idx == 0:
                    self.widget_dashboard.sidebar_labels[idx].config(text="Accounts")
                    for account, balance in self.main_dashboard.current_account_balances.items():    
                        listbox.insert(tk.END, f"{account} ${balance / 100:.2f}")
                # Update all banking categories
                elif idx == 1:
                    self.getCategories()
                    self.widget_dashboard.sidebar_labels[idx].config(text="Categories")
                    for category in self.main_dashboard.categories:
                        listbox.insert(tk.END, category)
                # Update all payees
                elif idx == 2:
                    self.toggleButtonStates(True)
                    self.widget_dashboard.sidebar_labels[idx].config(text="Payees")
                    self.getPayees()
                    for payee in self.main_dashboard.payees:
                        listbox.insert(tk.END, payee)
                # Update reports
                elif idx == 3:
                    self.widget_dashboard.sidebar_labels[idx].config(text="Reports")
            
            # Update based on investment dataframe
            elif self.main_dashboard.table_to_display == 'Investments':
                # Update all accounts and balances
                if idx == 0:
                    self.widget_dashboard.sidebar_labels[idx].config(text="Accounts")
                # Update investment assets
                elif idx == 1:
                    self.getAssets()
                    self.widget_dashboard.sidebar_labels[idx].config(text="Assets")
                    for category in self.main_dashboard.assets:
                        listbox.insert(tk.END, category)
                # Update investement actions
                elif idx == 2:
                    self.toggleButtonStates(False)
                    self.getInvestmentActions()
                    self.widget_dashboard.sidebar_labels[idx].config(text="Actions")
                    for action in self.main_dashboard.actions:
                        listbox.insert(tk.END, action)
                # Update reports
                elif idx == 3:
                    self.widget_dashboard.sidebar_labels[idx].config(text="Reports")

    ########################################################
    # Get lists of items (actions/categories/payees/assets/accounts)
    ########################################################

    def getPayees(self)-> None:
        """
        Loads payees from a text file and merges them with any existing
        payees found in the main_dashboard.all_banking_data DataFrame.
    
        This function:
        1. Reads lines from main_dashboard.payee_file.
        2. Gathers unique 'Payees' entries from the all_banking_data DataFrame (if present).
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
            if "Payee" in self.main_dashboard.all_banking_data.columns:
                data_payees = set(self.main_dashboard.all_banking_data["Payee"].dropna().unique())
            else:
                data_payees = set()
        except AttributeError:
            # If all_banking_data is missing or not set, fall back to empty
            data_payees = set()
        
        # 3) Merge both sets of payees; 4) sort and store in main_dashboard.payees
        self.main_dashboard.payees = sorted(set(file_payees) | data_payees)   
          
    def getCategories(self) -> None:
        """
        Loads categories from a text file and merges them with any existing
        categories found in the main_dashboard.all_banking_data DataFrame.
    
        This function:
        Reads lines from main_dashboard.category_file.
        Stores the final list of categories in main_dashboard.categories.
    
        Returns
        -------
        None
            The main_dashboard.categories list is updated in-place; nothing is returned.
        """
        with open(self.main_dashboard.banking_categories_file, "r") as f:
            file_categories = [line.strip() for line in f.readlines()]
        
        self.main_dashboard.categories = sorted(file_categories)   

    def getAssets(self) -> None:
        """
        Loads assets from a text file
    
        This function:
        Reads lines from asset_file.
        Stores the final list of categories in main_dashboard.categories.
    
        Returns
        -------
        None
            The main_dashboard.categories list is updated in-place; nothing is returned.
        """

        with open(self.main_dashboard.investment_assets_file, "r") as f:
            assets = [line.strip() for line in f.readlines()]
        
        self.main_dashboard.assets = sorted(assets)   

    def getInvestmentActions(self) -> None:
        """
        Loads actions from a text file
    
        This function:
        Reads lines from asset_file.
        Stores the final list of categories in main_dashboard.categories.
    
        Returns
        -------
        None
            The main_dashboard.categories list is updated in-place; nothing is returned.
        """

        with open(self.main_dashboard.investment_actions_file, "r") as f:
            actions = [line.strip() for line in f.readlines()]
        
        self.main_dashboard.actions = sorted(actions)   

    def getInvestmentAccounts(self) -> None:
        try:
            current_accounts =  self.main_dashboard.all_investment_data["Account"].unique().tolist()
        except:
            current_accounts = []
        for account in current_accounts:
            if account not in self.main_dashboard.investment_accounts:
                self.main_dashboard.investment_accounts.append(account)
        self.main_dashboard.investment_accounts = sorted(self.main_dashboard.investment_accounts)
    
    def getBankingAccounts(self) -> None:
        try:
            current_accounts =  self.main_dashboard.all_banking_data["Account"].unique().tolist()
        except:
            current_accounts = []
        for account in current_accounts:
            if account not in self.main_dashboard.banking_accounts:
                self.main_dashboard.banking_accounts.append(account)
        self.main_dashboard.banking_accounts = sorted(self.main_dashboard.banking_accounts)

    def manageItems(self, item_type):
        """General function to manage (add, modify, delete) items such as categories or accounts."""

        def loadItems():
            # Clear and repopulate the listbox
            listbox.delete(0, tk.END)
            for item in sorted(item_list, key=str.lower):
                listbox.insert(tk.END, item)

        def addItem():
            new_item = simpledialog.askstring(f"Add {item_type}", f"Enter new {item_type}:")
            if new_item and new_item not in item_list:
                item_list.append(new_item)
                listbox.insert(tk.END, new_item)
            saveItems()

        def modifyItem():
            selected_index = listbox.curselection()
            if selected_index:
                old_item = listbox.get(selected_index)
                new_item = simpledialog.askstring("Modify Item", "Enter new name:", initialvalue=old_item)
                if new_item and new_item not in item_list:
                    selected_value = listbox.get(selected_index)
                    item_list.remove(selected_value)
                    item_list.append(new_item)
                    listbox.delete(selected_index)
                    listbox.insert(selected_index, new_item)
                saveItems()

        def deleteItem():
            selected_index = listbox.curselection()
            if selected_index:
                confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this item?")
                if confirm:
                    selected_value = listbox.get(selected_index)
                    if selected_value in item_list:
                        item_list.remove(selected_value)
                    listbox.delete(selected_index)
                    saveItems()
                self.manageItems(item_type)

        def saveItems():
            # Call functions to populate the listbox
            if item_type == 'Categories':
                file = self.main_dashboard.banking_categories_file

                with open(file, "w") as f:
                    for item in item_list:
                        f.write(item + "\n")

                self.getCategories()

            elif item_type == 'Assets':
                file = self.main_dashboard.investment_assets_file

                with open(file, "w") as f:
                    for item in item_list:
                        f.write(item + "\n")

                self.getAssets()

            if item_type == 'Payees':
                file = self.main_dashboard.payee_file

                with open(file, "w") as f:
                    for item in item_list:
                        f.write(item + "\n")

                self.getPayees()

            if item_type == 'Actions':
                file = self.main_dashboard.investment_actions_file

                with open(file, "w") as f:
                    for item in item_list:
                        f.write(item + "\n")

                self.getInvestmentActions()

            if item_type == 'Banking Accounts':
                self.main_dashboard.banking_accounts = sorted(item_list, key=str.lower)
                
                self.getBankingAccounts()

            if item_type == 'Investment Accounts':
                self.main_dashboard.investment_accounts = sorted(item_list, key=str.lower)
                
                self.getInvestmentAccounts()

        def closeWindow(event=None):
            manage_window.destroy()

        # Create a Toplevel window anchored relative to the main dashboard
        manage_window = tk.Toplevel(self.main_dashboard)
        manage_window.title("Manage Items")
        
        # Set window dimensions and position
        window_height, window_width = 400, 300
        Windows.openRelativeWindow(
            manage_window, 
            main_width=self.main_dashboard.winfo_x(),
            main_height=self.main_dashboard.winfo_y(),
            width=window_width, 
            height=window_height
        )
        
        # Title label

        if item_type == 'Categories' and self.main_dashboard.table_to_display == 'Investments':
            item_type = 'Assets'

        ttk.Label(
            manage_window, 
            text=item_type,
            font=(StyleConfig.FONT_FAMILY, StyleConfig.HEADING_FONT_SIZE, "bold")
        ).pack(pady=5)

        # Frame for the Listbox and scrollbar
        frame = tk.Frame(manage_window, bg=StyleConfig.BG_COLOR)
        frame.pack(fill="both", expand=True, padx=10, pady=5)
    
        # Create a Listbox to display existing values
        listbox = tk.Listbox(frame, height=15, bg=StyleConfig.BG_COLOR)
        listbox.pack(side=tk.LEFT, fill="both", expand=True)
    
        # Attach a vertical scrollbar to the listbox
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        listbox.config(yscrollcommand=scrollbar.set)

        # Frame to hold the Add / Modify / Delete / Exit buttons
        button_frame = tk.Frame(manage_window, bg=StyleConfig.BG_COLOR)
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
        add_button = tk.Button(button_frame, text="Add", command=addItem, **button_attributes)
        modify_button = tk.Button(button_frame, text="Modify", command=modifyItem, **button_attributes)
        delete_button = tk.Button(button_frame, text="Delete", command=deleteItem, **button_attributes)
        exit_button = tk.Button(button_frame, text="Exit", command=closeWindow, **button_attributes)
    
        # Lay out buttons: Add, Modify, Delete in the first row, Exit in the second row
        add_button.grid(row=0, column=0, padx=5, pady=5)
        modify_button.grid(row=0, column=1, padx=5, pady=5)
        delete_button.grid(row=0, column=2, padx=5, pady=5)
        exit_button.grid(row=1, column=0, columnspan=3, padx=5, pady=5)

        # Call functions to populate the listbox
        if item_type == 'Categories':
            self.getCategories()
            item_list = self.main_dashboard.categories
            
        elif item_type == 'Assets':
            self.getAssets()
            item_list = self.main_dashboard.assets

        elif item_type == 'Payees':
            self.getPayees()
            item_list = self.main_dashboard.payees

        elif item_type == 'Actions':
            self.getInvestmentActions()
            item_list = self.main_dashboard.actions

        elif item_type == 'Banking Accounts':
            self.getBankingAccounts()
            item_list = self.main_dashboard.banking_accounts

        elif item_type == 'Investment Accounts':
            self.getInvestmentAccounts()
            item_list = self.main_dashboard.investment_accounts

        item_list = sorted(item_list)

        # Populate the listbox
        loadItems()

        # Bind Escape key to close the window, and give focus to it
        manage_window.bind("<Escape>", lambda event: closeWindow())
        manage_window.bind("<Return>", lambda event: closeWindow())
        manage_window.bind("<Delete>", lambda event: deleteItem())
        manage_window.focus_force()

    ########################################################
    # Options Window
    ########################################################
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

    ########################################################
    # Reports Display
    ########################################################
    def displayReports(self):
        #TODO
        """

        """
        self
    
    ########################################################
    # Search Functions
    ########################################################
    def searchData(
                    self,
                    single_query: str | None = None,
                    advanced_criteria: dict[str, str] | None = None
                ) -> None:
        #TODO Change for both banking and investment data
        """
        Filters self.main_dashboard.all_banking_data based on either a single query
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
        if not hasattr(self.main_dashboard, "all_banking_data") or self.main_dashboard.all_banking_data.empty:
            messagebox.showwarning("Warning", "No data to search!")
            return
    
        original_df = self.main_dashboard.all_banking_data.copy()
    
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
        #TODO Change for both banking and investment data
        """
        Handles the 'basic' (single-field) search from the search_entry in the toolbar.
        """
        query = self.widget_dashboard.search_entry.get().strip().lower()
        # If user typed nothing, just revert to entire dataset
        if not query:
            self.updateTable(self.main_dashboard.all_banking_data)
            return
    
        self.searchData(single_query=query)  # Calls the unified search logic    

    def openAdvancedSearch(self) -> None:
        #TODO Change for both banking and investment data
        """
        Opens a small Toplevel window that provides an entry box for each column,
        enabling an advanced filtering mechanism.
    
        After the user clicks 'Search', we build a dict of column->user_input
        and call self.searchData(advanced_criteria=that_dict).
        """
        if not hasattr(self.main_dashboard, "all_banking_data") or self.main_dashboard.all_banking_data.empty:
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
        for col_name in self.main_dashboard.all_banking_data.columns:
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
        window_width, window_height = 300, (len(self.main_dashboard.all_banking_data.columns) * 30) + 60
        search_window.geometry(f"{window_width}x{window_height}")
        search_window.resizable(False, False)
    
        # Key bindings
        search_window.bind("<Return>", performAdvancedSearch)
        search_window.bind("<Escape>", lambda e: search_window.destroy())
        
        search_window.focus_force()
        

    
    
class Dashboard(tk.Frame):
    def __init__(self, master=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        
        self.master = master  # Reference to the FinanceTracker (Main Window)
        
        self.ui_manager = DashboardUI(parent_dashboard=self, master=self)
        self.ui_actions = DashboardActions(self, self.ui_manager)
        self.ui_actions.toggleButtonStates(True)
        
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
        }      
        
        self.investment_column_widths = {
            "No.": 50,
            "Date": 100,
            "Account": 350,
            "Action": 200,
            "Asset": 150,
            "Symbol": 120,
            "Units": 120,
            "Note": 300,
        }
        
        self.day_one = "1970-1-1"

        self.all_banking_data = pd.DataFrame()
        self.all_investment_data = pd.DataFrame()
        self.table_to_display = 'Banking' # Or Investments
        
        self.initial_account_balances = pd.DataFrame(columns=['Account', 'Initial Date', 'Initial Value'])
        self.current_account_balances = {}
        self.account_cases = {}
        
        self.banking_categories_file  = os.path.join(os.path.dirname(__file__), "Banking_Categories.txt")
        self.investment_assets_file   = os.path.join(os.path.dirname(__file__), "Investments_Assets.txt")
        self.investment_actions_file  = os.path.join(os.path.dirname(__file__), "Investments_Actions.txt")
        self.payee_file = os.path.join(os.path.dirname(__file__), "Payees.txt")

        self.banking_accounts = []
        self.investment_accounts = []

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

    def addInvestmentAccount(self) -> None:
        """
        Add investment account to list of investment accounts
    
        Delegates the action to ui_actions.addInvestmentAccount().
        """
        self.ui_actions.manageItems('Investment Accounts')

    def addBankingAccount(self) -> None:
        """
        Add banking account to list of banking accounts
    
        Delegates the action to ui_actions.addBankingAccount().
        """
        self.ui_actions.manageItems('Banking Accounts')

    def getExpectedHeaders(self) -> str:
        if self.table_to_display == 'Banking':
            return list(self.banking_column_widths)
        elif self.table_to_display == 'Investments':
            return list(self.investment_column_widths)

    def trainClassifier(self) -> None:
        payee_classifier, category_classifier = Classifier.trainPayeeAndCategoryClassifier(self.all_banking_data) 

        predicted_payee, predicted_category = Classifier.predictTransactionLabels(
                                                                description="Advance Auto Parts", 
                                                                payment = 8423,
                                                                deposit = 0, 
                                                                account = "Capital One Credit", 
                                                                payee_pipeline = payee_classifier, 
                                                                category_pipeline = category_classifier
                                                                )