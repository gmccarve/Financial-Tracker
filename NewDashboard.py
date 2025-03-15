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

from typing import List, Tuple, Union, Optional

#from Utility import Utility, Tables, Windows, Classifier
from StyleConfig import StyleConfig

class InputHandling:
    """
    A utility class responsible for handling file input operations such as reading CSV and pickle (.pkl) files.
    
    This class provides methods to:
    - Open a file dialog for selecting .csv and .pkl files.
    - Read CSV files into DataFrames.
    - Read pickle files into Python dictionaries containing financial data.

    It ensures proper error handling for file loading and provides user-friendly messages if the file format is unsupported or if any errors occur during the reading process. The methods are designed to simplify the file loading process by managing different types of input files in a consistent manner.
    """
    @staticmethod 
    def parse_data_file_names() -> Tuple[str, List[str]]:
        """
        Opens a file dialog for .csv and .pkl files, allowing the user to choose multiple files.
        
        Returns:
            pkl_file (str or None): Path to a single .pkl file if found.
            csv_files (List[str]): List of .csv file paths if found (empty if pkl_file is found).
        """
        # Prompt user to pick multiple files
        file_paths = filedialog.askopenfilenames(filetypes=[("CSV and PKL files", "*.csv *.pkl")])
        
        if not file_paths:
            return [], []
        
        pkl_files, csv_files = [], []
        
        # Separate CSVs from PKL
        for path in file_paths:
            ext = os.path.splitext(path)[1].lower()
            if ext == ".csv":
                csv_files.append(path)
            elif ext == ".pkl":
                pkl_files.append(path)
            else:
                messagebox.showwarning("Unsupported File", f"Skipping file: {path}")
        
        return pkl_files, csv_files

    @staticmethod
    def read_csv(file_path: str) -> pd.DataFrame:
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
        
        except FileNotFoundError:
            messagebox.showerror("File Not Found", "The selected file could not be found.")
            return pd.DataFrame()
        
        except ValueError as e:
            messagebox.showerror("Invalid File", f"Error loading file: {e}")
            return pd.DataFrame()
        
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load data: {e}")
            return pd.DataFrame()

    @staticmethod    
    def read_pkl(file_path: str) -> dict:
        """
        Loads data from a pickle file.
        
        Parameters:
            file_path (str): Path to the PKL file.
        
        Returns:
            Tuple: Contains:
                - Banking Data (pd.DataFrame)
                - Investment Data (pd.DataFrame)
                - Initial Balances (dict)
                - Account Types (dict)
        """
        if not file_path:
            messagebox.showerror("Error", "No file selected!")
            return {}
         
        try:
            with open(file_path, "rb") as f:
                data = pickle.load(f)
            return data
            
        except FileNotFoundError:
            messagebox.showerror("File Not Found", "The selected file could not be found.")
            return {}
        
        except ValueError as e:
            messagebox.showerror("Invalid File", f"Error loading file: {e}")
            return  {}
        
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load data: {e}")
            return  {} 
        
class OutputHandling:
    """
    A utility class responsible for handling file output operations such as export to excel (.xlsx) and saving to pickle (.pkl) files.
    
    This class provides methods to:
    - Open a file dialog for selecting .xlsx or .pkl files.
    - Read CSV files into DataFrames.
    - Read pickle files into Python dictionaries containing financial data.

    It ensures proper error handling for file loading and provides user-friendly messages if the file format is unsupported or if any errors occur during the reading process. The methods are designed to simplify the file loading process by managing different types of input files in a consistent manner.
    """
    @staticmethod
    def save_data(banking_data: pd.DataFrame, 
                  investment_data: pd.DataFrame, 
                  initial_balances: dict, 
                  save_file: str = '', 
                  save_as: bool = False
                  ) -> Optional[str]:
        """
        Handles saving or exporting the data to either an Excel or Pickle file based on user input.
        
        Parameters:
            banking_data (pd.DataFrame): Banking transaction data.
            investment_data (pd.DataFrame): Investment transaction data.
            initial_balances (dict): Initial balances for each account.
            save_file (str, optional): The path to the file to save to. If empty, prompts the user.
            save_as (bool, optional): If True, prompts the user to choose a new file to save as.

        Returns: 
            str: The path of the saved file, or an empty string if the save operation failed.
        """
        # Determine file path (either default or prompted if save_as is True)
        file_path = save_file if not save_as else filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx"), ("Pickle Files", "*.pkl")])
        
        # User canceled the file selection dialog
        if not file_path:
            return ''

        # Determine the file extension and select the appropriate saving function
        file_ext = os.path.splitext(file_path)[-1].lower()

        save_function = {
            '.pkl': OutputHandling.save_to_pickle,
            '.xlsx': OutputHandling.save_to_excel
        }.get(file_ext)

        if not save_function:
            return ''  # Invalid file extension

        # Call the selected save function
        save_successful = save_function(banking_data, investment_data, initial_balances, file_path)

        # Return the file path if save was successful, otherwise return an empty string
        return file_path if save_successful else ''
          
    @staticmethod
    def save_to_pickle(banking_data: pd.DataFrame, investment_data: pd.DataFrame, initial_balances: dict, file_path: str) -> bool:
        """
        Saves the provided DataFrames and dictionary to a pickle file.

        This method serializes the 'Banking Data', 'Investment Data', and 'Initial Balances' into a dictionary
        and saves it as a pickle file. It provides feedback through message boxes to inform the user whether
        the save operation was successful or if an error occurred.

        Parameters:
        - banking_data (pd.DataFrame): The DataFrame containing banking transaction data.
        - investment_data (pd.DataFrame): The DataFrame containing investment transaction data.
        - initial_balances (dict): The dictionary containing the initial balances for each account.
        - file_path (str): The file path where the pickle file should be saved.

        Returns:
        - bool: Returns True if the save was successful, False otherwise.
        """
        
        try:
            with open(file_path, "wb") as f:
                pickle.dump(
                            {"Banking Data": banking_data, 
                             "Initial Balances": initial_balances, 
                             "Investment Data": investment_data
                             }, f)
        
            messagebox.showinfo("Save Complete", f"Data saved to {file_path}")  
        
            return True
        
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save data: {e}")
            return False

    @staticmethod
    def save_to_excel(banking_data: pd.DataFrame, investment_data: pd.DataFrame, initial_balances: dict, file_path: str) -> bool:
        """
        Saves the provided DataFrames and dictionary to an Excel (.xlsx) file.

        This method writes the 'Banking Data', 'Investment Data', and 'Initial Balances' into separate sheets
        of an Excel file. It provides feedback through message boxes to inform the user whether
        the save operation was successful or if an error occurred.

        Parameters:
        - banking_data (pd.DataFrame): The DataFrame containing banking transaction data.
        - investment_data (pd.DataFrame): The DataFrame containing investment transaction data.
        - initial_balances (dict): The dictionary containing the initial balances for each account.
        - file_path (str): The file path where the Excel file should be saved.

        Returns:
        - bool: Returns True if the save was successful, False otherwise.
        """

        try:
            with pd.ExcelWriter(file_path) as writer:
                banking_data.to_excel(writer, sheet_name="Banking Transactions", index=False)
                investment_data.to_excel(writer, sheet_name="Investments", index=False)
                initial_balances.to_excel(writer, sheet_name="Initial Balances", index=False)
                
            messagebox.showinfo("Export Complete", f"Data saved to {file_path}")

            return True
        
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save data: {e}")
            return False      
        
class DataManager:
    """
    A utility class for managing and manipulating DataFrames, particularly in the context of merging financial data.

    This class provides several static methods for:
    - Joining two DataFrames by comparing specified columns and appending non-matching rows from one DataFrame to another.
    - Stripping down a DataFrame to specified columns for comparison or further processing.
    - Identifying non-matching entries between two DataFrames.
    - Merging DataFrames by appending new, unique entries to an existing DataFrame.

    The class ensures efficient handling of financial data by comparing, merging, and processing DataFrames, particularly when combining new data with existing datasets.
    """
    @staticmethod
    def join_df(df1: pd.DataFrame, df2: pd.DataFrame, matching_headers: List[str]) -> pd.DataFrame:
        """
        Joins two DataFrames by comparing specified columns and appending non-matching rows from df2 to df1.

        Parameters:
        - df1 (pd.DataFrame): The first DataFrame (new data).
        - df2 (pd.DataFrame): The second DataFrame (old data).
        - matching_headers (List[str]): List of headers to compare between the two DataFrames.

        Returns:
        - pd.DataFrame: The updated DataFrame with non-matching rows from df2 appended to df1.
        """
        # Strip both DataFrames to only the relevant columns
        condensed_df1 = DataManager.strip_df_columns(df1, matching_headers)
        condensed_df2 = DataManager.strip_df_columns(df2, matching_headers)

        # Find non-matching rows
        non_matching_entries = DataManager.find_non_matching_entries(condensed_df1, condensed_df2)

        # Extract indices of non-matching rows from df1
        non_matching_indices = non_matching_entries.index.tolist()

        # Append the non-matching rows from df2 to df1
        all_data = DataManager.add_new_entries(df2, df1.loc[non_matching_indices])

        return all_data
    
    @staticmethod
    def strip_df_columns(df: pd.DataFrame, headers: List[str]) -> pd.DataFrame:
        """
        Strips the DataFrame down to the specified columns.

        Parameters:
        - df (pd.DataFrame): The DataFrame to strip.
        - headers (List[str]): The list of column names to keep in the DataFrame.

        Returns:
        - pd.DataFrame: A DataFrame with only the specified columns.
        """
        return df[headers]
    
    @staticmethod
    def find_non_matching_entries(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
        """
        Compares two DataFrames and returns rows in df1 that are not in df2.

        Parameters:
        - df1 (pd.DataFrame): New DataFrame to compare.
        - df2 (pd.DataFrame): Old DataFrame to compare against.

        Returns:
        - pd.DataFrame: Rows in df1 that are not in df2.
        """
        return df1.loc[~df1.apply(tuple, axis=1).isin(df2.apply(tuple, axis=1))]
    
    @staticmethod
    def add_new_entries(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
        """
        Merges two DataFrames by appending rows from df2 to df1, ensuring unique entries.

        Parameters:
        - df1 (pd.DataFrame): First DataFrame (existing data).
        - df2 (pd.DataFrame): Second DataFrame (new data).

        Returns:
        - pd.DataFrame: Merged DataFrame with unique entries from df2 appended to df1.
        """
        return pd.concat([df1, df2], ignore_index=True).drop(columns=['Index'], errors='ignore')
    
class DataFrameFormatting:
    """
    A utility class for formatting and processing DataFrames related to financial data.
    This class includes methods for sorting, indexing, converting currency, and formatting dates.
    """

    @staticmethod
    def format_old_dataframe(df: pd.DataFrame, currency_factor: int = 100) -> pd.DataFrame:
        """
        Formats the given DataFrame by performing a series of transformations:
        - Sorting the DataFrame by 'Account' and 'Date'
        - Adding an 'Index' column
        - Converting the 'Payment', 'Deposit', and 'Balance' columns to cents format
        - Converting the 'Date' column to datetime format

        Parameters:
        - df (pd.DataFrame): The input DataFrame to format.
        - currency_factor (int): The factor to multiply by for currency conversion (default is 100, for dollars to cents).

        Returns:
        - pd.DataFrame: The formatted DataFrame after all transformations.
        """
        # Apply all formatting steps in sequence
        df = DataFrameFormatting.sort_dataframe(df)
        df = DataFrameFormatting.get_dataframe_index(df)
        df = DataFrameFormatting.convert_currency(df, currency_factor=currency_factor)
        df = DataFrameFormatting.convert_datetime(df)

        return df
    
    @staticmethod
    def format_new_dataframe(df: pd.DataFrame, expected_columns: list[str], account_name: str) -> pd.DataFrame:
        """
        Formats the given DataFrame by performing a series of transformations:
        - Normalizing the column headers
        - Add any missing columns
        - Adding in the account name information
        - Formatting the entire dataframe for consistency
        
        Then determines the type of dataframe based on the monetary columns

        Parameters:
        - df (pd.DataFrame): The input DataFrame to format.
        - dashboard ("Dashboard"): The main_dashboard widget
        - account_name (str): the name of the account

        Returns:
        - pd.DataFrame: The formatted DataFrame after all transformations.
        """
        # Apply all formatting steps in sequence
        df = DataFrameFormatting.normalize_columns(df)
        df = DataFrameFormatting.add_missing_columns(df, expected_columns)
        df = DataFrameFormatting.add_account_column(df, account_name)
        df = DataFrameFormatting.format_old_dataframe(df, currency_factor=100)

        case = AccountManager.categorize_account(df)

        return df, case

    @staticmethod 
    def sort_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        Sorts a DataFrame in ascending order based on the 'Account' and 'Date' columns.
        
        Parameters:
        - df (pd.DataFrame): The input DataFrame to sort.
        
        Returns:
        - pd.DataFrame: The sorted DataFrame with a reset index.
        """
        # Sort by 'Account' first, then by 'Date' in ascending order
        df = df.sort_values(by=['Date', 'Account'], ascending=True, inplace=False).reset_index(drop=True)
        return df

    @staticmethod
    def get_dataframe_index(df: pd.DataFrame) -> pd.DataFrame:
        """
        Ensures that the DataFrame has an 'Index' column as the first column.
        If 'No.' exists, it is renamed to 'Index' and set as the first column.

        Parameters:
        - df (pd.DataFrame): The input DataFrame to update.
        
        Returns:
        - pd.DataFrame: The updated DataFrame with 'Index' as the first column.
        """
        # Reset index and remove any existing 'No.' column
        df = df.reset_index(drop=True)
        if 'No.' in df.columns:
            df = df.drop(columns=['No.'])

        # Add the 'Index' column as the first column based on the DataFrame's current index
        df.insert(0, 'No.', df.index)
        return df
    
    @staticmethod 
    def convert_currency(df: pd.DataFrame, currency_factor: int = 100) -> pd.DataFrame:
        """
        Converts the 'Payment', 'Deposit', and 'Balance' columns in a DataFrame to cents format (integer).
        
        Parameters:
        - df (pd.DataFrame): The input DataFrame containing financial data.
        - currency_factor (int): The factor to multiply by for currency conversion (default is 100 for converting dollars to cents).

        Returns:
        - pd.DataFrame: The updated DataFrame with the 'Payment', 'Deposit', and 'Balance' columns converted to cents format.
        """
        # Iterate over the relevant financial columns and convert them to cents
        for col in ['Payment', 'Deposit', 'Balance']:
            if col in df.columns:
                # Ensure the column is treated as a string for processing (e.g., removing symbols, commas)
                df[col] = df[col].astype(str)  # Ensure strings for processing
                
                # Clean the column by removing dollar signs, commas, and handling negative parentheses
                df[col] = df[col].replace({'\\$': '', ',': '', '\\(': '-', '\\)': ''}, regex=True)
                
                # Convert to numeric, replace NaNs with 0
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

                # Apply the currency factor (e.g., 100 for dollars to cents)
                df[col] = (df[col] * currency_factor).round().astype(int)

        return df
    
    @staticmethod 
    def convert_datetime(df: pd.DataFrame) -> pd.DataFrame:
        """
        Converts the 'Date' column in a DataFrame to datetime format, ensuring proper formatting.
        
        Parameters:
        - df (pd.DataFrame): The input DataFrame containing a 'Date' column.

        Returns:
        - pd.DataFrame: The updated DataFrame with the 'Date' column converted to datetime format.
        """
        if 'Date' not in df.columns:
            df['Date'] = ''
        df['Date'] = pd.to_datetime(df['Date'], dayfirst=False, format='mixed').dt.date
        return df
    
    @staticmethod
    def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
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
    def add_missing_columns(df: pd.DataFrame, expected_columns: list[str]) -> pd.DataFrame:
        """
        Adds missing columns to the DataFrame based on the expected headers from the dashboard.
        If a column is missing, it is added with an empty value.

        Parameters:
        - dashboard (Dashboard): The dashboard instance from which expected headers are fetched.
        - df (pd.DataFrame): The DataFrame to be updated.

        Returns:
        - pd.DataFrame: The updated DataFrame with missing columns added and reordered.
        """
        # Add missing columns with empty values
        for col in expected_columns:
            if col not in df.columns:
                df[col] = ""

        df['Balance'] = 0

        # Reorder the DataFrame to match the expected headers
        df = df[expected_columns]
        
        return df
    
    @staticmethod
    def add_account_column(df: pd.DataFrame, account_name: str) -> pd.DataFrame:
        """
        Adds an 'Account' column to the DataFrame and fills it with the provided account name.

        Parameters:
        - df (pd.DataFrame): The DataFrame to be updated.
        - account_name (str): The account name to be added to the 'Account' column.

        Returns:
        - pd.DataFrame: The updated DataFrame with the 'Account' column.
        """
        # Add the 'Account' column with the specified account name
        df.loc[:,'Account'] = account_name

        return df
    
class AccountManager:
    @staticmethod
    def categorize_account(df: pd.DataFrame) -> str:
        """
        Categorizes the account based on transaction patterns (e.g., Payment, Deposit, Balance).
        
        Parameters:
            df (pd.DataFrame): DataFrame containing the financial data.
        
        Returns:
            str: Account type category (e.g., "Type 1", "Type 2").
        """
        if (
            (df["Payment"] <= 0.00).all() and 
            (df["Deposit"] >= 0.00).all() and 
            (df["Balance"] == 0.00).all()
        ):
            return "Type 1"
        elif (
            (df["Payment"] >= 0.00).all() and 
            (df["Deposit"] <= 0.00).all() and 
            (df["Balance"] == 0.00).all()
        ):
            return "Type 2"
        elif (
            (df["Payment"] >= 0.00).all() and 
            (df["Deposit"] >= 0.00).all() and 
            (df["Balance"] == 0.00).all()
        ):
            return "Type 3"
        elif (
            (df["Payment"] >= -999999.00).all() and 
            (df["Deposit"] == 0.00).all()
        ):
            return "Type 4"
        else:
            return "Type 0"
    
    @staticmethod  
    def update_account_cases(df: pd.DataFrame) -> dict[str: str]:
        """
        Identifies the account cases by categorizing each unique account in the given DataFrame.
        The categorization result is stored in the main_dashboard's account_cases dictionary.

        Parameters:
        - df (pd.DataFrame): The DataFrame containing transaction data, including the 'Account' column.

        Returns:
        dict[str: str]: Dictionary off accounts and their respective types

        """
        account_df = {}
        for account in df['Account'].unique():
            account_df = df[df['Account'] == account]
        return account_df

class Tables:
    @staticmethod
    def clear_table(tree: ttk.Treeview) -> None:
        """
        Clears all items from a Treeview widget.
    
        Parameters:
            tree: The ttk.Treeview widget to be cleared.
        """
        tree.delete(*tree.get_children())
    
    @staticmethod
    def select_all_rows(tree: ttk.Treeview) -> None:
        """
        Selects all rows in a Treeview widget
    
        Parameters:
            tree: the ttk.Treeview widget 
        """
        tree.selection_set(tree.get_children())

    @staticmethod    
    def sort_table_by_column(tv:ttk.Treeview, col: 'str', reverse: bool) -> None:
        """Sorts a Treeview column properly, handling currency values and reapplying row colors."""

        def convert_value(val):
            """Converts currency values ($XXX.XX) to float for sorting."""
            try:
                return float(val.replace("$", "").replace(",", "").replace("%", ""))
            except ValueError:
                return val.lower()
            
        # Get values and sort correctly
        l = [(convert_value(tv.set(k, col)), k) for k in tv.get_children('')]
        l.sort(reverse=reverse)
    
        # Rearrange items in sorted order
        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)
    
        # Reapply banded row styling
        Tables.apply_banded_rows(tv)
    
        # Reverse sort next time
        tv.heading(col, command=lambda: Tables.sort_table_by_column(tv, col, not reverse))

    @staticmethod   
    def apply_banded_rows(tv: ttk.Treeview) -> None:
        """Recolors Treeview rows to maintain alternating row stripes after sorting."""
        for index, row in enumerate(tv.get_children('')):
            tag = "evenrow" if index % 2 == 0 else "oddrow"
            tv.item(row, tags=(tag,))
    
        # Define colors for tags
        tv.tag_configure("evenrow", background=StyleConfig.BAND_COLOR_1)
        tv.tag_configure("oddrow", background=StyleConfig.BAND_COLOR_2) 

    @staticmethod
    def smooth_scroll():
        """

        """
        a = 5


class DatePicker:
    def __init__(self, parent: tk.Frame, initial_date: date = None, multiple_dates: date = False):
        """
        A class to create a calendar window for date selection.

        Parameters:
            parent (Tk.Frame): The parent Tkinter window.
            initial_date: The initial date to pre-select, if provided.
            multiple_dates: If True, will create two calendars for start and end date selection.
        """
        self.parent = parent
        self.initial_date = initial_date or date.today()
        self.multiple_dates = multiple_dates
        self.selected_dates = [initial_date, initial_date]  # [start_date, end_date]
        
    def open_calendar_window(self) -> None:
        """
        Opens a calendar window and allows date selection. Returns the selected date(s).
        If multiple_dates is True, it will return both start and end dates.
        """
        top = tk.Toplevel(self.parent)
        top.title("Select Date Range" if self.multiple_dates else "Select Date")

        # Open the window
        self.open_relative_window(top, width=550, height=300)

        if self.multiple_dates:
            # Two calendars for start and end dates
            self._create_calendar(top, "Select Start Date:", 0)
            self._create_calendar(top, "Select End Date:", 1)
        else:
            # Single calendar for date selection
            self._create_calendar(top, "Select Date:", 0)

        # Confirm button to save the selection
        confirm_button = tk.Button(top, 
                                    text="Confirm Dates", 
                                    command=lambda: top.destroy(), 
                                    width=20,
                                    relief=StyleConfig.BUTTON_STYLE
                                    )
        confirm_button.grid(row=2, column=0, columnspan=2, padx=10, pady=(10,20))

        # Bind Enter and Escape keys
        top.bind("<Return>", lambda event: top.destroy())
        top.bind("<Escape>", lambda event: self.cancel_selection(top))

        top.focus_set()

        # Wait for the user to confirm the date selection
        top.wait_window(top)
        return self.selected_dates

    def _create_calendar(self, parent: tk.Frame, label_text: str, idx: int) -> None:
        """
        Creates a calendar widget for selecting dates.

        Parameters:
            parent (tk.Frame): The parent widget (Toplevel).
            label_text (str): The text label for the calendar (Start or End Date).
            idx (int): The index to store the selected date (0 for start, 1 for end).
        """
        label = tk.Label(parent, 
                         text=label_text, 
                         font=(StyleConfig.FONT_FAMILY, StyleConfig.HEADING_FONT_SIZE, "bold"),
                         bg=StyleConfig.BG_COLOR,
                        fg=StyleConfig.TEXT_COLOR
        )
        label.grid(row=0, column=idx, sticky='ew', padx=10, pady=(10,5))

        cal = Calendar(parent, selectmode="day", 
                       year=self.initial_date.year, 
                       month=self.initial_date.month,
                       day=self.initial_date.day,
                       date_pattern='Y-mm-dd')
        cal.grid(row=1, column=idx, sticky='ew', padx=10, pady=(0,10))

        # Store the selected date in the appropriate index
        def set_selected_date():
            self.selected_dates[idx] = self.convert_str_to_date(cal.get_date())

        # When the user selects a date, update the selected date
        cal.bind("<<CalendarSelected>>", lambda event: set_selected_date())

        # Configure sidebar grid to expand
        parent.grid_columnconfigure(0, weight=1)

    def cancel_selection(self, top: tk.Frame) -> None:
        """
        Closes the window and resets the selected_dates
        """
        self.selected_dates = [None, None]
        top.destroy()

    def convert_str_to_date(self, date_str) -> None:
        """
        Converts a date string (YYYY-MM-DD) to a date object.
        """
        year, month, day = map(int, date_str.split("-"))
        return date(year, month, day)

    def open_relative_window(self, window: tk.Frame, width: int, height: int) -> None:
        """
        Opens a window relative to the main application window.

        Parameters:
            window (tk.Frame): The Toplevel window to open.
            width (int): The width of the window.
            height (int): The height of the window.
        """
        window.geometry(f"{width}x{height}+{self.parent.winfo_x()+250}+{self.parent.winfo_y()+250}")

class DataSearch:
    def __init__(self, parent: tk.Frame, dataframe: pd.DataFrame):
        """
        Initialize the DataSearch class with the parent window and the dataframe to search.
        
        Parameters:
            parent (tk.Tk or tk.Toplevel): The parent window where the search is initiated.
            dataframe (pd.DataFrame): The DataFrame to be searched.
        """
        self.parent = parent
        self.dataframe = dataframe
        self.search_criteria = {}

    def search_data(self, search_value=None, advanced_criteria=None):
        """
        Search through the dataframe either by a single search value or using advanced search criteria.
        
        Parameters:
            search_value (str, optional): A single value to search for. Defaults to None.
            advanced_criteria (bool, optional): A boolean to perform an advanced, column-by-column search.
        """
        if search_value:
            # Perform a basic search based on the search value in the text box
            return self.simple_search(search_value)
        elif advanced_criteria:
            # Perform an advanced search based on criteria entered in the advanced search window
            self.open_advanced_search_window()
        
        else:
            return self.dataframe

    def simple_search(self, search_value):
        """
        Filters the DataFrame based on the search value entered in the search text box.
        
        Parameters:
            search_value (str): The value to search for across all columns in the DataFrame.
        """
        if not search_value:
            return  # If no value, just return without filtering
        
        # Perform the search for the entered value across all columns
        search_value = search_value.strip().lower()  # Case-insensitive search

        # Apply the numeric matching logic for specific columns (Payment, Deposit, Balance)
        filtered_df = self.dataframe[
            self.dataframe.apply(lambda row: self.row_matches_single_query(row, search_value), axis=1)
        ]
        
        if filtered_df.empty:
            messagebox.showinfo("Search Results", "No matching results found.")
            return None
        else:
            return filtered_df
        
    def row_matches_single_query(self, row, search_value):
        """
        Check if a row matches the search query. Handles both text and numeric matching for specific columns.
        
        Parameters:
            row (pd.Series): The row to check for matching.
            search_value (str): The value to search for.
        
        Returns:
            bool: True if the row matches the search value, False otherwise.
        """
        for col in row.index:
            val_str = str(row[col]).lower()
            
            # If the column is numeric (Payment, Deposit, Balance), use numeric matching
            if col in ["Payment", "Deposit", "Balance"]:
                if self.numeric_matches(row[col], search_value):
                    return True
            
            # For text-based columns, check if the value contains the search term
            if search_value in val_str:
                return True
        return False
    
    def numeric_matches(self, row_val, user_str):
        """
        Converts row_val (in cents) to dollars and checks if it matches the user's input (in dollars).
        
        Parameters:
            row_val (float or int): The value in cents (e.g., 10000 for $100).
            user_str (str): The value in dollars (e.g., "100.00").
        
        Returns:
            bool: True if the value matches the user's input, False otherwise.
        """
        try:
            # Convert cents to dollars and format to match the user input
            num_dollars = float(row_val) / 100
            numeric_str = f"{num_dollars:.2f}".lower()
            return user_str.lower() in numeric_str
        except (ValueError, TypeError):
            return False

    def advanced_search(self) -> pd.DataFrame:
        """
        Filters the DataFrame based on column-specific criteria entered in the advanced search window.

        This method uses the search criteria for each column and applies filtering across the DataFrame.
        
        Parameters:
            None
        Returns:
            pd.DataFrame: The filtered DataFrame based on user inputs.
      """

        if self.search_criteria:

            filtered_df = self.dataframe

            for col, value in self.search_criteria.items():
                if value:  # Only apply filtering if the user has entered a value
                    if col in ["Payment", "Deposit", "Balance"]:
                        filtered_df = filtered_df[filtered_df.apply(lambda row: self.numeric_matches(row[col], value), axis=1)]
                    else:
                        filtered_df = filtered_df[filtered_df[col].astype(str).str.contains(value, case=False, na=False)]
            
            if filtered_df.empty:
                messagebox.showinfo("Search Results", "No matching results found.")
                return None
            else:
                return filtered_df
            
        else:
            return self.dataframe

    def open_advanced_search_window(self):
        """
        Opens the advanced search window where users can input search values for each column.
        """
        top = tk.Toplevel(self.parent)
        top.title("Advanced Search")

        # Open the window
        self.open_relative_window(top, width=300, height=len(self.dataframe.columns)*30 + 60)
    
        ttk.Label(
            top,
            text="Advanced Search",
            font=(StyleConfig.FONT_FAMILY, StyleConfig.FONT_SIZE, "bold")
        ).pack(pady=5)
    
        input_frame = ttk.Frame(top)
        input_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
        # Build a dict of column -> (Entry widget)
        entry_widgets = {}
    
        # Create an entry for each column in the DataFrame
        for col_name in self.dataframe.columns:
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
    
        def get_search_terms(event=None):
            """
            Collects the values from the input fields and performs the advanced search.
            """
            for col, entry in entry_widgets.items():
                value = entry.get().strip()
                if value:
                    self.search_criteria[col] = value  # Only add criteria with a value

            top.destroy()
        
        # Search button to confirm the advanced search
        search_button = tk.Button(
            top,
            text="Search",
            command=get_search_terms,
            font=(StyleConfig.FONT_FAMILY, StyleConfig.BUTTON_FONT_SIZE),
            bg=StyleConfig.BUTTON_COLOR,
            fg=StyleConfig.TEXT_COLOR,
            relief=StyleConfig.BUTTON_STYLE
        )
        search_button.pack(pady=10)

        # Bind Enter and Escape keys
        top.bind("<Return>", lambda event: get_search_terms(event))
        top.bind("<Escape>", lambda event: self.cancel_selection(top))

        top.focus_set()

        # Wait for the user to confirm the date selection
        top.wait_window(top)
    
    def cancel_selection(self, top: tk.Frame) -> None:
        """
        Closes the window and resets the selected_dates
        
        Parameters:
            top (tk.Frame): The parent tk Frame object.

        Returns:
            None
        """
        self.selected_dates = [None, None]
        top.destroy()
    
    def open_relative_window(self, window: tk.Frame, width: int, height: int) -> None:
        """
        Opens a window relative to the main application window.

        Parameters:
            window (tk.Frame): The Toplevel window to open.
            width (int): The width of the window.
            height (int): The height of the window.
        """
        window.geometry(f"{width}x{height}+{self.parent.winfo_x()+250}+{self.parent.winfo_y()+250}")

class ColorPicker:
    def __init__(self, parent: tk.Tk | tk.Toplevel, var: tk.StringVar):
        """
        Initializes the ColorPicker class to handle the color picking functionality.
        
        Parameters:
            parent (tk.Tk or tk.Toplevel): The parent window where the color picker will be displayed.
            var (tk.StringVar): The Tkinter variable that holds the selected color.
            entry_widget ( tk.Entry): The Entry widget that will display the selected color code.
        """
        self.parent = parent
        self.var = var
        self.selected_color = None

    def open_color_picker(self):
        """
        Opens a color chooser dialog and updates the associated Tk variable with the chosen color.
        """
        # Ensure the color chooser window is on top of the current window
        self.parent.lift()

        # Open the color chooser dialog
        color_code = colorchooser.askcolor(title="Choose a Color")[1]  # Get hex color code
        if color_code:
            self.selected_color = color_code  # Store the selected color in the class
            self.var.set(color_code)  # Update the Tkinter variable with the selected color

        # Return the selected color
        return self.selected_color

class Options:
    def __init__(self, parent, main_dashboard, widget_dashboard):
        """
        Initializes the Options class to handle the application settings window.
        
        Parameters:
            parent (tk.Tk): The main Tkinter window.
            main_dashboard (MainDashboard): The main dashboard object that stores application-wide settings.
            widget_dashboard (WidgetDashboard): The widget dashboard for UI updates.
        """
        self.parent = parent
        self.main_dashboard = main_dashboard
        self.widget_dashboard = widget_dashboard
        self.temp_settings = {}
        self.options_window = None

    def open_options_window(self, new_settings: bool = True) -> None:
        """
        Opens a window to adjust various application settings such as fonts, colors, sizes, etc.

        """
        self.top = tk.Toplevel(self.main_dashboard)
        self.top.title("Application Settings")
        self.top.resizable(False, False)

        #TODO Background color

        # Header label for the window
        tk.Label(
                self.top,
                text="Customize Appearance",
                font=(StyleConfig.FONT_FAMILY, StyleConfig.HEADING_FONT_SIZE, "bold"),
                bg=StyleConfig.BG_COLOR,
                fg=StyleConfig.TEXT_COLOR
        ).pack(pady=5)

        # Initialize the temporary settings dictionary based on current values
        self.temp_settings = {
            "FONT_FAMILY":          [tk.StringVar(value=StyleConfig.FONT_FAMILY), sorted(list(font.families()))],
            "FONT_SIZE":            [tk.IntVar(value=StyleConfig.FONT_SIZE), []],
            "SUB_FONT_SIZE":        [tk.IntVar(value=StyleConfig.SUB_FONT_SIZE), []],
            "HEADING_FONT_SIZE":    [tk.IntVar(value=StyleConfig.HEADING_FONT_SIZE), []],
            "TITLE_FONT_SIZE":      [tk.IntVar(value=StyleConfig.TITLE_FONT_SIZE), []],
            "BUTTON_FONT_SIZE":     [tk.IntVar(value=StyleConfig.BUTTON_FONT_SIZE), []],
            "ROW_HEIGHT":           [tk.IntVar(value=StyleConfig.ROW_HEIGHT), []],
            "TEXT_COLOR":           [tk.StringVar(value=StyleConfig.TEXT_COLOR), []],
            "BG_COLOR":             [tk.StringVar(value=StyleConfig.BG_COLOR), []],
            "HEADER_COLOR":         [tk.StringVar(value=StyleConfig.HEADER_COLOR), []],
            "BUTTON_COLOR":         [tk.StringVar(value=StyleConfig.BUTTON_COLOR), []],
            "BAND_COLOR_1":         [tk.StringVar(value=StyleConfig.BAND_COLOR_1), []],
            "BAND_COLOR_2":         [tk.StringVar(value=StyleConfig.BAND_COLOR_2), []],
            "ERROR_COLOR":          [tk.StringVar(value=StyleConfig.ERROR_COLOR), []],
            "SELECTION_COLOR":      [tk.StringVar(value=StyleConfig.SELECTION_COLOR), []],
            "SCROLL_SPEED":         [tk.IntVar(value=StyleConfig.SCROLL_SPEED), []],
            "BUTTON_STYLE":         [tk.StringVar(value=StyleConfig.BUTTON_STYLE), ["flat", "groove", "sunken", "raised", "ridge"]],
            "BUTTON_PADDING":       [tk.IntVar(value=StyleConfig.BUTTON_PADDING), []],
            "BUTTON_BORDER_RADIUS": [tk.IntVar(value=StyleConfig.BUTTON_BORDER_RADIUS), []],
            "DARK_MODE":            [tk.BooleanVar(value=StyleConfig.DARK_MODE), []],
            "DATE_FORMAT":          [tk.StringVar(value=StyleConfig.DATE_FORMAT), ["%Y-%m-%d"]],
        }

        # Read in the user settings from the pickle file
        try:
            with open(self.main_dashboard.user_settings_file, "rb") as f:
                user_settings = pickle.load(f)
        except (FileNotFoundError, pickle.UnpicklingError):
            # If there's an error loading the file (e.g., file not found or corrupted), use default settings
            user_settings = {}

        # Iterate over the settings and update the tk.Variable values with the user settings
        for key, (var, options) in self.temp_settings.items():
            # If the user setting exists in the pickle file, update the tk.Variable
            if key in user_settings:
                user_setting = user_settings[key]
                var.set(user_setting)  # Update the Tk variable with the user setting

        # Calculate window size based on the number of settings
        window_height = len(self.temp_settings) * 31 + 120
        window_width = 300
        #TODO throw into separate class
        self.open_relative_window(self.top, width=window_width, height=window_height)

        # Create setting rows for each option
        for label, (var, options) in self.temp_settings.items():
            self.create_setting_row(label, var, options)

        # Buttons to apply changes, reset to standard, or cancel
        self.create_buttons()

    def create_setting_row(self, label: str, var: tk.Variable, options: List = []) -> None:
        """
        Creates a single row (label + input widget) within the settings window.
        
        Parameters:
            label (str): The label for the setting.
            var (tk.Variable): The Tkinter variable holding the current setting value.
            options (list[str], optional): If provided, it creates a dropdown (ComboBox).
            is_color (bool, optional): If True, creates a color-chooser button next to the input widget.
        """
        frame = ttk.Frame(self.top)
        frame.pack(fill="x", padx=10, pady=2)

        formatted_text = ' '.join(label.split("_")).title() + ":"
        formatted_text = formatted_text.replace("Bg", "Background")

        tk.Label(frame, 
                 text=formatted_text, 
                 width=20, 
                 font=(StyleConfig.FONT_FAMILY, StyleConfig.FONT_SIZE),
                 bg=StyleConfig.BG_COLOR, 
                 fg=StyleConfig.TEXT_COLOR,
                 anchor='w'
        ).pack(side=tk.LEFT)

        if "color" in label.lower():
            entry = ttk.Entry(frame, textvariable=var, width=10)
            entry.pack(side=tk.LEFT, padx=5)

            color_button = tk.Button(
                frame,
                text="🎨",
                width=4,
                command=lambda: self.open_color_picker(var, entry),
                bg=StyleConfig.BUTTON_COLOR,
                fg=StyleConfig.TEXT_COLOR,
                relief=StyleConfig.BUTTON_STYLE
            )
            color_button.pack(side=tk.LEFT)

        elif isinstance(var, tk.StringVar) and not options:
            entry = ttk.Entry(frame, 
                              textvariable=var, 
                              width=30,
                              command=lambda: self.apply_live_changes(),
                              )
            entry.pack(side=tk.RIGHT, fill="x", expand=True)

        elif isinstance(var, tk.IntVar):
            entry = ttk.Spinbox(frame, 
                                textvariable=var, 
                                from_=1, 
                                to=30,
                                width=30, 
                                command=lambda: self.apply_live_changes(),
                                )
            entry.pack(side=tk.RIGHT, fill="x", expand=True)

        elif isinstance(var, tk.BooleanVar):
            var.set(StyleConfig.DARK_MODE)

            checkbox = ttk.Checkbutton(frame, 
                                       variable=var,
                                       command=lambda: self.apply_live_changes(),
                                       )
            checkbox.pack(side=tk.RIGHT)

        elif options:
            dropdown = ttk.Combobox(frame, 
                                    textvariable=var, 
                                    values=options, 
                                    state="readonly", 
                                    width=15,
                                    )
            dropdown.pack(side=tk.RIGHT, fill="x", expand=True)
            dropdown.bind("<<ComboboxSelected>>", lambda event: self.apply_live_changes())

    def open_color_picker(self, var, entry_widget) -> None:
        """
        Opens the color picker dialog and updates the selected color.

        Parameters:
            var (tk.StringVar): The Tkinter StringVar associated with the color setting.
            entry_widget (tk.Entry): The Entry widget to display the color code.
        """
        # Instantiate and open the ColorPicker
        color_picker = ColorPicker(self.main_dashboard.master, var)
        selected_color = color_picker.open_color_picker()  # Get selected color

        # Optionally, do something with the selected color (e.g., update the widget)
        if selected_color:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, selected_color)

            self.apply_live_changes()

        self.open_options_window(new_settings=False)

    def apply_live_changes(self) -> None:
        """
        
        """
        # Update the StyleConfig with the new values immediately
        for key, (var, options) in self.temp_settings.items():
            setattr(StyleConfig, key, var.get())

        self.save_user_settings()
        self.close_window()
        self.open_options_window(new_settings=False)

        # Apply changes in the widget dashboard
        self.widget_dashboard.apply_style_changes()

    def create_buttons(self) -> None:
        """
        Creates buttons for applying changes, resetting to standard settings, or canceling.
        """
        button_frame = ttk.Frame(self.top)
        button_frame.pack(pady=10)

        apply_button = tk.Button(
            button_frame,
            text="Apply",
            command=self.apply_changes,
            bg=StyleConfig.BUTTON_COLOR,
            fg=StyleConfig.TEXT_COLOR,
            relief=StyleConfig.BUTTON_STYLE
        )
        apply_button.grid(row=0, column=0, padx=5, pady=5)

        standard_button = tk.Button(
            button_frame,
            text="Standard Options",
            command=self.reset_to_standard,
            bg=StyleConfig.BUTTON_COLOR,
            fg=StyleConfig.TEXT_COLOR,
            relief=StyleConfig.BUTTON_STYLE
        )
        standard_button.grid(row=1, column=0, columnspan=2, padx=5, pady=5)

        cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            command=self.close_window,
            bg=StyleConfig.BUTTON_COLOR,
            fg=StyleConfig.TEXT_COLOR,
            relief=StyleConfig.BUTTON_STYLE
        )
        cancel_button.grid(row=0, column=1, padx=5, pady=5)

        # Bind Enter/Escape keys for convenience
        self.top.bind("<Return>", self.apply_changes)
        self.top.bind("<Escape>", lambda event: self.close_window(event))

    def apply_changes(self) -> None:
        """
        Applies the changes made in the options window and saves them.
        """
        # Update the StyleConfig with the new values
        for key, (var, options) in self.temp_settings.items():
            setattr(StyleConfig, key, var.get())
            print (key, var.get())

        # Toggle Dark Mode if changed
        StyleConfig.applyDarkMode(self.temp_settings["DARK_MODE"][0].get())

        # Apply the changes in the widget dashboard
        self.widget_dashboard.apply_style_changes()

        # Save user settings to a file
        self.save_user_settings()

        # Close the options window
        self.close_window()

    def reset_to_standard(self) -> None:
        """
        Resets all style settings to their default values and saves them.
        """
        default_settings = StyleConfig.getDefaultSettings()

        # Apply default settings dynamically
        for key, value in default_settings.items():
            setattr(StyleConfig, key, value)

        # Apply the changes in the widget dashboard
        self.widget_dashboard.apply_style_changes()

        # Save user settings to a file
        self.save_user_settings(data=default_settings)

        # Close the options window
        self.close_window()

    def save_user_settings(self, data: dict = None) -> None:
        """
        Saves the current or default style settings to a pickle file.
        
        Parameters:
            data (dict, optional): If provided, it saves the passed dictionary. If None, saves the current settings.
        """
        user_settings_path = self.main_dashboard.user_settings_file
        if data is None:
            with open(user_settings_path, "wb") as f:
                pickle.dump({key: var.get() for key, (var, options) in self.temp_settings.items()}, f)
        else:
            with open(user_settings_path, "wb") as f:
                pickle.dump({key: var for key, var in data.items()}, f)

    def close_window(self, event=None) -> None:
        """
        Closes the options window.
        """
        if self.top:
            self.top.destroy()

    def open_relative_window(self, window: tk.Frame, width: int, height: int) -> None:
        """
        Opens a window relative to the main application window.

        Parameters:
            window (tk.Frame): The Toplevel window to open.
            width (int): The width of the window.
            height (int): The height of the window.
        """
        window.geometry(f"{width}x{height}+{self.parent.winfo_x()+250}+{self.parent.winfo_y()+250}")



class Utility:
    @staticmethod
    def generate_month_year_list(start_date: datetime, end_date: datetime) -> List[Tuple[int, int]]:
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
    
    @staticmethod
    def format_month_year(month: int, year: int) -> datetime:
        """
        Convert a month and year into the format 'MM 'YY'.
        
        Parameters:
            month (int): The month
            year (int): The year
            
        Returns:
            A (str) in the format "Mon 'YY"
        """
        return datetime(year, month, 1).strftime("%b '%y")
    
    @staticmethod
    def format_month_last_day_year(month: int, year: int) -> datetime:
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
    
    @staticmethod
    def format_date_from_str(day: 'str') -> date:
        """
        Convert a str into date format. 
        
        Parameters:
            day (str): The day in "YYYY-MM-DD" format
            
        Returns:
            A date formated string.
        """
        return (lambda day: datetime(*(map(int, day.split("-")))).strftime("%Y-%m-%d"))

    
    
class TransactionManager:
    @staticmethod
    def open_entry_window():
        """

        """
        a = 5
        
    @staticmethod
    def validate_field():
        """

        """
        a = 5
    
    @staticmethod
    def collect_stored_values():
        """

        """
        a = 5
    
    @staticmethod
    def process_entry():
        """

        """
        a = 5
        
    @staticmethod
    def get_data_frame_to_update():
        """

        """
        a = 5

    @staticmethod
    def update_existing_entry():
        """

        """
        a = 5

    @staticmethod
    def add_new_entry():
        """

        """
        a = 5

    @staticmethod
    def create_input_field():
        """

        """
        a = 5
    
    @staticmethod
    def create_date_field():
        """

        """
        a = 5

    @staticmethod
    def create_numeric_field():
        """

        """
        a = 5

    @staticmethod
    def create_text_field():
        """

        """
        a = 5

    @staticmethod
    def create_immutable_field():
        """

        """
        a = 5

    @staticmethod
    def create_dropdown_field():
        """

        """
        a = 5

    @staticmethod
    def prepare_headers_and_prefill_data():
        """

        """
        a = 5

    @staticmethod
    def delete_entry():
        """

        """
        a = 5

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
        self.create_widgets()
        
    ########################################################
    # WIDGETS
    ########################################################
    def create_widgets(self):
        """Creates and places all main widgets for the dashboard."""
        
        # Sidebar widget
        self.sidebar = tk.Frame(self, width=350, relief=tk.RIDGE, bg=StyleConfig.BG_COLOR)
        self.sidebar.grid(row=0, column=0, sticky='nsew')
        self.create_sidebar()
        
        # Non-Sidebar Widgets
        self.main_content = tk.Frame(self)
        self.main_content.grid(row=0, column=1, sticky='nsew')
        self.main_content.grid_columnconfigure(0, weight=1)
        self.main_content.grid_rowconfigure(1, weight=1)
        
        # Toolbar widget
        self.create_toolbar()
        
        # Treeview widget
        self.create_transaction_table()
        
        # Configure layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Apply UI Style
        self.apply_style_changes()
        
    ########################################################
    # SIDEBAR
    ########################################################
    def create_sidebar(self):
        """Creates the sidebar with accounts, categories, payees, and reports."""
        self.sidebar_labels = []
        self.sidebar_listboxes = []
        self.sidebar_frames = []

        sidebar_items = ["Accounts", "Categories", "Payees", "Reports"]

        for idx, item in enumerate(sidebar_items):
            self._create_sidebar_label(item, idx)
            self._create_sidebar_listbox(idx)

        # Configure sidebar grid to expand
        self.sidebar.grid_columnconfigure(0, weight=1)

    def _create_sidebar_label(self, item, idx):
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

    def _create_sidebar_listbox(self, idx):
        """Creates a listbox with a scrollbar for the sidebar."""
        listbox_frame = ttk.Frame(self.sidebar)
        listbox_frame.grid(row=2*idx+1, column=0, sticky="ew", padx=5, pady=(0, 10))

        listbox = tk.Listbox(listbox_frame, height=6, width=35)
        listbox.pack(side=tk.LEFT, fill='x', expand=True)

        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill='y')
        listbox.config(yscrollcommand=scrollbar.set)

        # Bind events
        listbox.bind("<MouseWheel>", Tables.smooth_scroll)
        listbox.bind("<Double-Button-1>", lambda event, idx=idx: self.actions_manager.filter_entries(case=idx+1))

        self.sidebar_listboxes.append(listbox)
        self.sidebar_frames.append(listbox_frame)
        
    ########################################################
    # TOOLBAR
    ########################################################
    def create_toolbar(self):
        """Creates a toolbar with basic transaction actions."""
    
        self.toolbar = tk.Frame(self.main_content, relief=StyleConfig.BUTTON_STYLE, bg=StyleConfig.BG_COLOR)
        self.toolbar.grid(row=0, column=0, sticky='nsew')
        
        # Initialize the image and button storage
        self.button_image_loc = os.path.join(os.path.dirname(__file__), "Images")
        self.toolbar_buttons = []
        self.images = {}
        
        # Define button configurations
        button_data = self._get_button_data()
        btn_size = 50  # Button size
        
        # Create buttons and separators
        self._create_buttons_and_separators(button_data, btn_size)
        
        # Create search field and buttons
        self._create_search_bar()

    def _get_button_data(self):
        """Returns a list of button data for toolbar buttons."""
        return [
            ("Add",         "add.png",      self.actions_manager.add_entry),
            ("Edit",        "edit.png",     self.actions_manager.edit_entry),
            ("Delete",      "delete.png",   self.actions_manager.delete_entry),
            ("Open",        "open.png",     self.actions_manager.open_data),
            ("Balances",    "accounts.png", lambda: self.actions_manager.update_account_balances(input=True)),
            ("Payee",       "payee.png",    lambda: self.actions_manager.manage_items("Payees")),
            ("Category",    "category.png", lambda: self.actions_manager.manage_items("Categories")),
            ("Actions",     "actions.png",  lambda: self.actions_manager.manage_items("Actions")),
            ("Banking",     "banking.png",  lambda: self.actions_manager.switch_account_view("Banking")),
            ("Stocks",      "stonks.png",   lambda: self.actions_manager.switch_account_view("Investments")),
            ("Reports",     "budget.png",   self.actions_manager.display_reports),
            ("Export",      "export.png",   self.actions_manager.export_data),
            ("Options",     "options.png",  self.actions_manager.view_options),
        ]

    def _create_buttons_and_separators(self, button_data, btn_size):
        """Creates buttons and separators for the toolbar."""
        for index, (text, icon, command) in enumerate(button_data):
            button = self._create_button(text, icon, command, btn_size)
            button.pack(side=tk.LEFT, padx=4, pady=2)
            self.toolbar_buttons.append(button)
            
            if index in [3, 7, 9, 10]:
                self._create_separator()

    def _create_button(self, text, icon, command, btn_size):
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

    def _create_separator(self):
        """Helper method to create separators in the toolbar."""
        ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

    def _create_search_bar(self):
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
        self.search_entry.bind("<Return>", lambda event: self.actions_manager.simple_search())
        
        # Search button
        search_button = tk.Button(self.toolbar, 
                                text="Go",
                                command=self.actions_manager.simple_search, 
                                font=StyleConfig.FONT_FAMILY,
                                bg=StyleConfig.BUTTON_COLOR, 
                                relief=StyleConfig.BUTTON_STYLE)
        search_button.pack(side=tk.LEFT, padx=5)
        self.toolbar_buttons.append(search_button)
        
        # Advanced search button
        adv_search_button = tk.Button(self.toolbar, 
                                    text="Advanced Search", 
                                    command=self.actions_manager.advanced_search,
                                    font=StyleConfig.FONT_FAMILY,
                                    bg=StyleConfig.BUTTON_COLOR, 
                                    relief=StyleConfig.BUTTON_STYLE)
        adv_search_button.pack(side=tk.LEFT, padx=5)
        self.toolbar_buttons.append(adv_search_button)

    ########################################################
    # MAIN WORKING PORTION OF WINDOW
    ########################################################
    def create_transaction_table(self):
        """Creates the transaction table with scrolling, as a placeholder for future graphs/plots."""
        
        # Create the content frame (for table, graph, etc.)
        self._create_content_frame()
        
        # Initialize the treeview (transaction table)
        self._create_table_treeview()
        
        # Initialize the scrollbar
        self._create_table_scrollbar()
        
        # Bind events to the table
        self._bind_table_events()

    def _create_content_frame(self):
        """Creates the content frame that holds the table, plot, or other content."""
        # Create a frame where any content (table/graphs/reports) will go
        self.content_frame = tk.Frame(self.main_content)
        self.content_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
        
        # Configure layout
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

    def _create_table_treeview(self):
        """Creates the Treeview widget for displaying transaction data."""
        self.tree = ttk.Treeview(self.content_frame, 
                                show='headings',
                                yscrollcommand=lambda *args: self.y_scrollbar.set(*args),
                                height=15)
        self.tree.grid(row=0, column=0, sticky='nsew')

    def _create_table_scrollbar(self):
        """Creates the vertical scrollbar for the Treeview."""
        self.y_scrollbar = ttk.Scrollbar(self.content_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.y_scrollbar.set)
        self.y_scrollbar.grid(row=0, column=1, sticky='ns')

    def _bind_table_events(self):
        """Binds events to the Treeview widget."""
        # Bind double-click to edit cell
        self.tree.bind("<Double-1>", self.actions_manager.edit_cell)
        self.tree.bind("<Button-3>", lambda event: self.actions_manager.show_right_click_table_menu(event))

    def show_transaction_table(self, data):
        """Displays the transaction table (Treeview) in the content area."""
        # Remove any existing widgets in the content area
        self._clear_content_area()

        # Re-create the table with the provided data
        self.create_transaction_table()  # Or update the Treeview with new data

    def show_graph(self, plot):
        """Displays a Matplotlib graph in the content area."""
        self._clear_content_area()
        
        # Embed the Matplotlib figure into the Tkinter content area
        self.figure_canvas = FigureCanvasTkAgg(plot, master=self.content_frame)  # Create a canvas from the plot
        self.figure_canvas.draw()
        self.figure_canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew')  # Place the plot into the grid

    def show_report(self, report):
        """Displays a report in the content area (can be text, tables, etc.)."""
        self._clear_content_area()
        
        # Example for a text-based report
        report_label = tk.Label(self.content_frame, text=report, bg=StyleConfig.BG_COLOR, fg=StyleConfig.TEXT_COLOR)
        report_label.grid(row=0, column=0, sticky="nsew")

    def _clear_content_area(self):
        """Clears the content area (useful for swapping between views)."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()  # Destroy all widgets (treeview, plot, report) currently in the content frame

    ########################################################
    # UI STYLE
    ########################################################    
    def apply_style_changes(self):
        """Applies updated style settings dynamically to ttk and standard Tk widgets."""
        # Apply background color to main sections
        sections = [self.sidebar, self.toolbar, self.main_content, self.content_frame]
        for section in sections:
            section.config(bg=StyleConfig.BG_COLOR)

        style = ttk.Style()
        self._apply_treeview_style(style)
        self._apply_button_style()
        self._apply_sidebar_style()

        # Ensure the colors update immediately
        self.update_idletasks()

    def _apply_treeview_style(self, style):
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
        
        Tables.apply_banded_rows(self.tree)
        
        style.map("Treeview", 
                background=[("selected", StyleConfig.SELECTION_COLOR)],
                foreground=[("selected", "#FFFFFF" if StyleConfig.DARK_MODE else "#000000")])

    def _apply_button_style(self):
        for btn in self.toolbar_buttons:
            btn.config(bg=StyleConfig.BUTTON_COLOR,
                    fg=StyleConfig.TEXT_COLOR,  
                    relief=StyleConfig.BUTTON_STYLE, 
                    padx=StyleConfig.BUTTON_PADDING, 
                    pady=StyleConfig.BUTTON_PADDING, 
                    font=(StyleConfig.FONT_FAMILY, StyleConfig.BUTTON_FONT_SIZE))

    def _apply_sidebar_style(self):
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

    ###################
    # Input Functions #
    ###################
    def open_data(self) -> None:
        """
        Opens one or more data files and processes them accordingly.
        
        This function:
        - Parses the file names for `.pkl` and `.csv` files.
        - Calls respective parsing functions for `.pkl` and `.csv` files.
        - Updates account type information based on the loaded data.
        - Refreshes the table with the updated data.

        Parameters
        ----------
        None
            File names are gathered from the InputHandling class and passed to 
            respective pickle and csv file parsers.
        
        Returns
        -------
        None
            The imported file(s) are saved to disk, with no return value needed.
        """
        # Parse file names and get lists of pickle and CSV files
        pickle_files, csv_files = InputHandling.parse_data_file_names()

        # If there are pickle files, process them
        if pickle_files:
            self.parse_pickle_files(pickle_files)

        # If there are CSV files, process them
        if csv_files:
            self.parse_csv_files(csv_files)

        # If any files were loaded, update account type information
        if csv_files or pickle_files:
            self.main_dashboard.account_cases = AccountManager.update_account_cases(self.main_dashboard.all_banking_data)

        # Refresh the displayed table with the updated data
        self.update_table()

    def load_save_file(self) -> None:
        """
        Loads a pre-saved pickle file and processes it.

        This function uses the file path stored in `self.main_dashboard.save_file`, 
        loads the pickle file, and refreshes the table with the loaded data.

        Parameters
        ----------
        None
            The save_file is read from the self.main_dashboard.save_file variable.

        Returns
        -------
        None
            The imported file(s) are saved to disk, with no return value needed.
        """
        # Load the pre-saved pickle file specified in the save_file path
        self.parse_pickle_files([self.main_dashboard.save_file])

        # Refresh the table with the data from the saved pickle file
        self.update_table()

    ####################
    # Output Functions #
    ####################
    def export_data(self, event: tk.Event | None = None) -> None:
        """
        Exports transaction data to an Excel file.
    
        Uses the OutputHandling.export_data method to prompt for an Excel (.xlsx) save location,
        then writes the DataFrames to separate sheets.
    
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
        tmp = OutputHandling.save_data(
            self.main_dashboard.all_banking_data.copy(),
            self.main_dashboard.all_investment_data.copy(),
            self.main_dashboard.initial_balances.copy(),
            save_file = "", 
            save_as = True
        )    
        
    def save_data(self, event: tk.Event | None = None) -> None:
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
        new_save_file = OutputHandling.save_data(
            self.main_dashboard.all_banking_data.copy(),
            self.main_dashboard.all_investment_data.copy(),
            self.main_dashboard.initial_balances.copy(),
            save_file=self.main_dashboard.save_file,
            save_as = False
        )
        # Write the chosen file path to a tracking file for future reference
        if not new_save_file:
            self.main_dashboard.change_save_file(new_save_file)
    
    def save_data_as(self, event: tk.Event | None = None) -> None:
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
        new_save_file = OutputHandling.save_data(
            self.main_dashboard.all_banking_data.copy(),
            self.main_dashboard.all_investment_data.copy(),
            self.main_dashboard.initial_balances.copy(),
            save_file='', 
            save_as = True
        )
        # Update the last saved file record
        if not new_save_file:
            self.main_dashboard.change_save_file(new_save_file)

    #################################
    # Input Data Manipulation - PKL #
    #################################
    def parse_pickle_files(self, file_names: List[str]) -> None:
        """
        Parses the given pickle files and loads their contents into the main dashboard.
        Ensures all required keys are present in the loaded data and formats the dataframes.

        Parameters:
        - file_names (List[str]): List of pickle file paths to be parsed.
        """

        expected_keys = ["Banking Data", "Initial Balances", "Investment Data"]

        for file in file_names:
            data = InputHandling.read_pkl(file)

            # Ensure all expected keys are present in the data dictionary
            missing_keys = [key for key in expected_keys if key not in data]
            if missing_keys:
                messagebox.showwarning(f"Missing expected keys in {file}: {', '.join(missing_keys)}")
                continue
            
            # Extract data from the loaded dictionary
            banking_data        = data["Banking Data"]
            investment_data     = data["Investment Data"]
            initial_balances    = data["Initial Balances"]

            # Rename columns in initial_balances DataFrame
            initial_balances = initial_balances.rename(columns = {"Initial Value": "Balance", "Initial Date": "Date"})

            # Format the dataframes
            banking_data        = DataFrameFormatting.format_old_dataframe(banking_data, currency_factor=1)
            investment_data     = DataFrameFormatting.format_old_dataframe(investment_data, currency_factor=1)
            initial_balances    = DataFrameFormatting.format_old_dataframe(initial_balances, currency_factor=1)

            # Merge the new data with the main_dashboard dataframes
            self.main_dashboard.all_banking_data = self._merge_dataframes(banking_data, 
                                                                          self.main_dashboard.all_banking_data, 
                                                                          case=1)
            self.main_dashboard.all_investment_data = self._merge_dataframes(investment_data, 
                                                                             self.main_dashboard.all_investment_data, 
                                                                             case=2)
            self.main_dashboard.initial_balances = self._merge_dataframes(initial_balances, 
                                                                          self.main_dashboard.initial_balances, 
                                                                          case=3)

    def _merge_dataframes(self, new_df: pd.DataFrame, current_df: pd.DataFrame, case: int) -> pd.DataFrame:
        """
        Merges a new DataFrame with the current DataFrame using expected matching columns.

        Parameters:
        - new_df (pd.DataFrame): The new data to merge.
        - current_df (pd.DataFrame): The existing data to merge with.
        - case (int): The case number used to fetch the expected matching columns.

        Returns:
        - pd.DataFrame: The merged DataFrame.
        """
        matching_columns = self.get_expected_matching_columns(case=case)
        return DataManager.join_df(new_df, current_df, matching_columns)

    #################################
    # Input Data Manipulation - CSV #
    #################################
    def parse_csv_files(self, file_names: List[str]) -> None:
        """
        Parses the given CSV files, formats them, and merges them into the current DataFrame in the dashboard.

        Parameters:
        - file_names (List[str]): List of CSV file paths to be parsed.
        """

        for file in file_names:
            df = InputHandling.read_csv(file)

            if not df.empty:
                account_name = os.path.basename(file).split(".")[0]
                
                current_df = self.get_current_df()

                # Format the new DataFrame
                new_df, case = DataFrameFormatting.format_new_dataframe(df, current_df.columns, account_name)

                # Update account cases if necessary
                if account_name not in self.main_dashboard.account_cases:
                    self.main_dashboard.account_cases[account_name] = case

                # Get the expected matching columns based on the case
                matching_columns = self._get_matching_columns_based_on_case(current_df)

                # Merge the new data with the current DataFrame
                current_df = DataManager.join_df(new_df, current_df, matching_columns)

                # Update the current DataFrame in the dashboard
                self.update_current_df(current_df)

    def _get_matching_columns_based_on_case(self, current_df: pd.DataFrame) -> List[str]:
        """
        Returns the expected matching columns based on the case and the current DataFrame structure.

        Parameters:
        - current_df (pd.DataFrame): The DataFrame to be updated.

        Returns:
        - List[str]: List of matching column headers.
        """
        if 'Payee' in current_df.columns:
            return self.get_expected_matching_columns(case=1)
        else:
            return self.get_expected_matching_columns(case=2)

    ##############################
    # DataFrame Update Functions #
    ##############################
    def get_current_df(self) -> Optional[pd.DataFrame]:
        """
        Returns the DataFrame currently being displayed (either 'Banking' or 'Investment').

        Returns:
        - pd.DataFrame: The DataFrame corresponding to the currently selected table.
        """
        # Dictionary for table to DataFrame mapping
        table_to_df = {
            'Banking': self.main_dashboard.all_banking_data,
            'Investments': self.main_dashboard.all_investment_data
        }
        
        # Return the DataFrame for the currently selected table
        return table_to_df.get(self.main_dashboard.table_to_display, None)
        
    def update_current_df(self, df: pd.DataFrame) -> None:
        """
        Updates the DataFrame for the currently selected table (either 'Banking' or 'Investment').

        Parameters:
        - df (pd.DataFrame): The DataFrame to update the current table with.
        """
        # Dictionary for table to DataFrame setter
        table_to_setter = {
            'Banking': lambda: setattr(self.main_dashboard, 'all_banking_data', df),
            'Investment': lambda: setattr(self.main_dashboard, 'all_investment_data', df)
        }

        # Set the DataFrame for the current table
        table_to_setter.get(self.main_dashboard.table_to_display, lambda: None)()
        
        # Update the tableview widget with the current dataframe
        self.update_table(df)

    def get_expected_headers(self) -> list[str]:
        """
        Returns the expected headers based on the currently selected table ('Banking' or 'Investments').

        Returns:
        - list[str]: A list of column headers for the currently selected table.
        """
        # Dictionary for table to headers mapping
        table_to_headers = {
            'Banking': list(self.main_dashboard.banking_column_widths),
            'Investments': list(self.main_dashboard.investment_column_widths)
        }

        # Return the headers for the current table, or an empty list if not found
        return table_to_headers.get(self.main_dashboard.table_to_display, [])
    
    def get_table_header_widths(self) -> dict:
        """
        Returns the dictionary of column headers and their widths for the tableview object.

        Returns:
        - dict: A dictionary of column headers as keys and widths as items.
        """
        # Dictionary for table to headers mapping
        table_to_widths = {
            'Banking': self.main_dashboard.banking_column_widths,
            'Investments': self.main_dashboard.investment_column_widths
        }

        # Return the dictionary for the current table, or an empty list if not found
        return table_to_widths.get(self.main_dashboard.table_to_display, [])

    def get_expected_matching_columns(self, case: int) -> list[str]:
        """
        Returns a list of expected columns to match based on the provided case number.

        Parameters:
        - case (int): The case number that determines the expected columns for matching.

        Returns:
        - list[str]: A list of column names that should be used for matching in the specified case.

        This method returns different sets of expected column headers based on the case parameter:
        - Case 1: Returns columns for banking transactions.
        - Case 2: Returns columns for investment transactions.
        - Case 3: Returns a simpler set of columns for accounts.
        """
        # Return the expected matching columns based on the case number
        if case == 1:
            return ['Date', 'Description', 'Payment', 'Deposit', 'Account']
        elif case == 2:
            return ['Date', 'Account', 'Action', 'Asset', 'Symbol', 'Units']
        elif case == 3:
            return ['Account', 'Date']

    ####################################
    # Update the main Tableview widget #
    ####################################
    def update_table(self, df: pd.DataFrame = pd.DataFrame()) -> None:
        """
        Updates the main Tableview widget by configuring the table with the current data.
        
        This method retrieves the current DataFrame, configures the table's columns, and inserts rows 
        into the Treeview widget. It also handles currency formatting for specified columns and 
        applies banded rows to improve readability.

        Steps:
        - Retrieves the current DataFrame to display.
        - Sets up the columns for the Treeview widget.
        - Formats and inserts rows of data into the Treeview.
        - Applies special formatting to currency columns.
        - Adds column headers and sorting functionality.
        - Applies banded row styling for better visual organization.

        Parameters:
            df (pd.DataFrame) | optional. The dataframe to display if provided. Otherwise
                                            retrieve the current dataframe.

        Returns
            None
        """
        # Get the current dataframe to display
        if df.empty:
            df = self.get_current_df()

        # Retrieve column header widths and headers
        column_data = self.get_table_header_widths()  # Assuming this returns column widths as a dictionary
        column_headers = df.columns.tolist()  # Get column names as list
        
        # Display the current table using the DataFrame
        self.widget_dashboard.show_transaction_table(df)

        # Configure the Treeview widget to show columns
        self.widget_dashboard.tree["columns"] = column_headers
        self.widget_dashboard.tree.configure(show='headings')
        
        # Identify columns that should be treated as currency
        currency_columns = self._get_currency_columns(column_headers)

        # Create each column header and apply sorting functionality
        self._set_column_headers(column_headers, column_data)

        # Insert new data rows into the Treeview
        self._insert_data_rows(df, currency_columns)

        # Apply banded row styling to the Treeview
        Tables.apply_banded_rows(self.widget_dashboard.tree)

    def _get_currency_columns(self, column_headers: list) -> list:
        """
        Determines which columns should be formatted as currency.

        Parameters:
        - column_headers (list): List of column headers in the DataFrame.

        Returns:
        - list: List of column indices that should be formatted as currency.
        """
        return [5, 6, 7] if "Payee" in column_headers else []

    def _set_column_headers(self, column_headers: list, column_data: dict) -> None:
        """
        Sets up the headers and column widths in the Treeview widget.

        Parameters:
        - column_headers (list): List of column headers.
        - column_data (dict): Dictionary of column names and their corresponding widths.
        """
        for col_name in column_headers:
            self.widget_dashboard.tree.heading(
                col_name, 
                text=col_name, 
                anchor=tk.CENTER,
                command=lambda c=col_name: Tables.sort_table_by_column(self.widget_dashboard.tree, c, False)
            )
            self.widget_dashboard.tree.column(col_name, width=column_data.get(col_name, 100), anchor=tk.W)  # Default width if not in column_data

    def _insert_data_rows(self, df: pd.DataFrame, currency_columns: list) -> None:
        """
        Inserts rows of data into the Treeview widget.

        Parameters:
        - df (pd.DataFrame): The DataFrame containing the data to be inserted.
        - currency_columns (list): List of column indices to be treated as currency.
        """
        for index, row_data in df.iterrows():
            formatted_row = list(row_data)  # Convert row data to a list
            
            # Format currency columns as dollars
            for idx in currency_columns:
                if idx < len(formatted_row):  # Ensure index is within bounds
                    formatted_row[idx] = f"${float(formatted_row[idx]) / 100:.2f}"
    
            self.widget_dashboard.tree.insert("", tk.END, values=formatted_row)

    ############################################################
    # Directly manipulate the entries in main Tableview widget #
    ############################################################
    #TODO
    def add_entry(self):
        """

        """
        a = 5

    def edit_entry(self):
        """

        """
        a = 5

    def delete_entry(self):
        """

        """
        a = 5

    def edit_cell(self, tmp):
        """

        """
        a = 5

    ###############################################
    # Filter the entries in main Tableview widget #
    ###############################################
    def show_right_click_table_menu(self, event=None) -> None:
        """
        Displays a context menu based on the column clicked in the table header.
        
        The menu will offer different filter options depending on the column clicked, 
        such as filtering by date or numerical entries. The menu is displayed at 
        the position of the mouse click.

        Parameters:
            event (tk.Event, optional): The event object that triggered the right-click. Default is None.
        """
        # Get the region where the click occurred (header or cell)
        region = self.widget_dashboard.tree.identify_region(event.x, event.y)

        # If the region is not 'heading', do nothing (i.e., the click is on a cell)
        if region != "heading":
            return

        # Identify the column that was clicked based on the event's x-position
        col_id = self.widget_dashboard.tree.identify_column(event.x)
        col_name = self.widget_dashboard.tree.heading(col_id, "text")
        
        # Create a new menu object
        menu = tk.Menu(self.main_dashboard, tearoff=0)

        # Add specific menu options based on the column clicked
        if col_name == 'Date':
            self._add_date_filters(menu)
        elif col_name in ['Payment', 'Deposit', 'Balance', 'Units']:
            self._add_numerical_filters(menu, col_name)

        # Display the context menu at the mouse cursor position
        menu.post(event.x_root, event.y_root)

    def _add_date_filters(self, menu=tk.Menu) -> None:
        """
        Adds filtering options for the 'Date' column to the context menu.
        
        This includes predefined options to filter by a range of days (e.g., last 30, 60, 90, 180, or 365 days),
        as well as the option to define a custom date range via a calendar window.
        
        Parameters:
            menu (tk.Menu): The context menu to which date filter options are added.
        """
        # Predefined filters for the last N days
        quick_add_dates = [30, 60, 90, 180, 365]
        for date in quick_add_dates:
            menu.add_command(label=f"Show last {date} days", command=lambda date=date: self.filter_by_delta_days(delta=date))
        
        # Menu options for specifying the start and end date of the filter
        menu.add_separator()
        menu.add_command(label="Choose date window", command=lambda: self._add_calendar_window())
    
    def _add_calendar_window(self) -> None:
        """
        Opens a calendar window to allow the user to select a custom date range.
        
        Once the user selects a start and end date, the function will apply the selected date range filter.
        If the user cancels the selection, no filter is applied.
        """
        # Open the date picker window to select the start and end dates
        self.date_picker = DatePicker(self.main_dashboard.master, initial_date=date.today(), multiple_dates=True)
        selected_dates = self.date_picker.open_calendar_window()

        # If valid dates are selected, filter the data based on the selected date range
        if selected_dates[0] and selected_dates[1]:
            self._filter_by_date_window(selected_dates[0], selected_dates[1])

    def _filter_by_delta_days(self, delta: int = 0) -> None:
        """
        Filters the table data to include only rows within the past 'delta' number of days.
        
        The filter is applied by comparing the 'Date' column with the calculated start date, 
        which is the current date minus the specified delta.
        
        Parameters:
            delta (int): The number of days to filter by. Only rows with a 'Date' within the last 'delta' days are included.
        """
        if delta > 0:
            # Get the current dataframe to filter
            current_df = self.get_current_df()

            # Calculate the starting date based on the delta value
            starting_date = date.today() - timedelta(days=delta)

            # Filter the dataframe by the calculated date range
            filtered_df = current_df[current_df['Date'] >= starting_date]

            # Update the table with the filtered data
            self.update_table(df=filtered_df)

    def _filter_by_date_window(self, start_date: date = date.today(), end_date: date = date.today()) -> None:
        """
        Filters the table data to include only rows within the specified date range.
        
        The filter is applied by comparing the 'Date' column with the specified start and end dates.
        
        Parameters:
            start_date (date): The start date of the date range. Defaults to today's date.
            end_date (date): The end date of the date range. Defaults to today's date.
        """
        # Get the current dataframe to filter
        current_df = self.get_current_df()

        # Apply the date range filter
        filtered_df = current_df[(current_df['Date'] >= start_date) & (current_df['Date'] <= end_date)]

        # Update the table with the filtered data
        self.update_table(df=filtered_df)

    #TODO
    def _add_numerical_filters(self, column):
        """

        """
        self

    ##############################
    # Calculate account balances #
    ##############################
    #TODO
    def update_account_balances(self, input=False):
        """

        """
        a = 5

    #########################
    # Switch table displays #
    #########################
    def switch_account_view(self, table_to_view: str) -> None:
        """
        Switches the view between 'Banking' and 'Investment' tables. 
        If the current table is already the same as the requested table, it does nothing.

        Parameters:
        - table_to_view (str): The table to switch to. Can be 'Banking' or 'Investment'.
        """
        # Check if the current table is already the one being requested
        if self.main_dashboard.table_to_display == table_to_view:
            return  # Do nothing if it's the same table
        
        # Switch to the new table
        self.main_dashboard.table_to_display = table_to_view

        # Update the main tableview object
        self.update_table()

        # Update the toolbar buttons
        self.toggle_button_states()
        
    #####################
    # Toolbar functions #
    #####################
    def toggle_button_states(self) -> None:
        """
        Toggles visibility of the toolbar buttons given the currently
        displayed table.

        Parameters:
            show (bool): Which buttons to (de)activate
        """

        # Dictionary for table to DataFrame mapping
        table_to_state = {
            'Banking': [tk.NORMAL, tk.NORMAL, tk.DISABLED],
            'Investments': [tk.DISABLED, tk.DISABLED, tk.NORMAL]
        }

        button_states = table_to_state.get(self.main_dashboard.table_to_display, None)

        for state, button in enumerate([4, 5, 7]):
            self.widget_dashboard.toolbar_buttons[button].config(state=button_states[state])

    ####################
    # Search Functions #
    ####################
    def simple_search(self) -> None:
        """
        Filters the DataFrame based on the search value entered in the search text box.
        This function performs a search for the entered value across all columns in the DataFrame.
        If the search field is empty, it displays the original DataFrame.

        It uses the `DataSearch` class to perform the actual search logic.

        Returns:
            None
        """
        # Get the search value entered by the user, strip leading/trailing spaces, and convert to lowercase
        search_value = self.widget_dashboard.search_entry.get().strip().lower()

        if search_value:
            # If there's a search value, get the current DataFrame to search through
            current_df = self.get_current_df()

            # Initialize the search functionality with the current DataFrame
            search = DataSearch(self.main_dashboard.master, current_df)

            # Perform the search and get the filtered DataFrame
            filtered_df = search.search_data(search_value=search_value)

            # If filtered data is not empty, update the table with the filtered results
            if filtered_df is not None and not filtered_df.empty:
                self.update_table(df=filtered_df)

        else:
            # If no search value is provided, simply display the original DataFrame (unfiltered)
            self.update_table()

    def advanced_search(self) -> None:
        """
        Filters the DataFrame based on column-specific criteria entered in the advanced search window.
        This function opens an advanced search window where the user can specify search criteria for individual columns.

        Once the search criteria are collected, the function applies the filtering to the DataFrame and updates the table.

        Returns:
            None
        """
        # Get the current DataFrame to apply the advanced search
        current_df = self.get_current_df()

        # Initialize the DataSearch class for advanced search
        search = DataSearch(self.main_dashboard.master, current_df)

        # Perform the advanced search, passing True for advanced criteria
        filtered_df = search.advanced_search()

        # If the filtered DataFrame is not empty, update the table with the filtered results
        if filtered_df is not None and not filtered_df.empty:
            self.update_table(df=filtered_df)

    #TODO
    #####################
    # Sidebar functions #
    #####################
    def update_sidebar(self):
        """

        """
        a = 5

    def manage_items(self, action=''):
        """

        """
        a = 5

    def _update_sidebar_labels(self):
        """
        
        """
        a = 5

    def _update_sidebar_listboxes(self):
        """
        
        """
        a = 5

    def _get_list_of_payees(self):
        """

        """
        a = 5   
          
    def _get_list_of_categories(self):
        """

        """
        a = 5 

    def _get_list_of_assets(self):
        """

        """
        a = 5 

    def _get_list_of_investment_actions(self):
        """

        """
        a = 5

    def _get_list_of_investment_accounts(self):
        """

        """
        a = 5
    
    def _get_list_of_banking_accounts(self):
        """

        """
        a = 5

    #TODO
    ########################################################
    # Options window
    ########################################################
    def view_options(self):
        """

        """
        options = Options(self.main_dashboard.master,
                          self.main_dashboard, 
                          self.widget_dashboard)
        options.open_options_window()

    #TODO
    ########################################################
    # Reports Display
    ########################################################
    def display_reports(self):
        """

        """
        a = 5
        

    
    
class Dashboard(tk.Frame):
    def __init__(self, master=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        
        self.master = master  # Reference to the FinanceTracker (Main Window)

        # Load user settings (this applies them to StyleConfig immediately)
        self.user_settings_file = os.path.join(os.path.dirname(__file__), "user_settings.pkl")
        StyleConfig.loadUserSettings(self.user_settings_file)
        
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

        self.initial_balances_columns = ['No.', 'Account', 'Date', 'Balance']
        
        self.day_one = "1970-1-1"

        self.all_banking_data = pd.DataFrame(columns=self.banking_column_widths)
        self.all_investment_data = pd.DataFrame(columns=self.investment_column_widths)
        self.table_to_display = 'Banking' # Or Investments
        self.ui_actions.toggle_button_states()

        self.initial_balances = pd.DataFrame(columns=self.initial_balances_columns)
        self.current_balances = {}
        self.account_cases = {}

        self.save_file_loc = os.path.join(os.path.dirname(__file__), "lastSavedFile.txt")
        self.save_file = self.read_save_file()
        
        self.banking_categories_file  = os.path.join(os.path.dirname(__file__), "Banking_Categories.txt")
        self.investment_assets_file   = os.path.join(os.path.dirname(__file__), "Investments_Assets.txt")
        self.investment_actions_file  = os.path.join(os.path.dirname(__file__), "Investments_Actions.txt")
        self.payee_file = os.path.join(os.path.dirname(__file__), "Payees.txt")

        self.banking_accounts = []
        self.investment_accounts = []

        # Delay loading the saved file until UI is ready
        self.after(500, self.ui_actions.load_save_file)

    def read_save_file(self):
        try:
            with open(self.save_file_loc, 'r') as f:
                save_file = f.readlines()
            return save_file[0]
        except:
            return ''
        
    def change_save_file(self, file_path):
        self.save_file = file_path
        try:
            with open(self.save_file_loc, 'w') as f:
                f.write(self.save_file)
            return
        except:
            return
        
    def open_data(self) -> None:
        """
        Opens a data file (CSV or PKL) for parsing and loading into the application.
    
        Delegates the action to ui_actions.open_data().
        """
        self.ui_actions.open_data()
    
    def save_data(self) -> None:
        """
        Saves data to a file in the default or previously used location.
    
        Delegates the action to ui_actions.save_data().
        """
        self.ui_actions.save_data()
    
    def save_data_as(self) -> None:
        """
        Saves data to a new file location chosen by the user.
    
        Delegates the action to ui_actions.saveDataAs().
        """
        self.ui_actions.save_data_as()

    def export_data(self) -> None:
        """
        Saves data to a new file location chosen by the user.
    
        Delegates the action to ui_actions.saveDataAs().
        """
        self.ui_actions.export_data()
    
    def select_all_rows(self) -> None:
        """
        Selects all rows in the transaction table.
        """
        Tables.select_all_rows(self.ui_manager.tree)

    def clear_table(self) -> None:
        """
        Clears all rows in the current transaction table.
        """
        Tables.clear_table(self.ui_actions.tree)

    def open_search(self) -> None:
        """
        Opens the advanced search dialog for column-by-column filtering.
    
        Delegates the action to ui_actions.open_advanced_search().
        """
        self.ui_actions.open_advanced_search()
    
    def delete_entry(self) -> None:
        """
        Deletes the currently selected transaction(s) from the table and data.
    
        Delegates the action to ui_actions.delete_entry().
        """
        self.ui_actions.delete_entry()

    def add_investment_account(self) -> None:
        """
        Add investment account to list of investment accounts
    
        Delegates the action to ui_actions.manage_items().
        """
        self.ui_actions.manage_items('Investment Accounts')

    def add_banking_account(self) -> None:
        """
        Add banking account to list of banking accounts
    
        Delegates the action to ui_actions.manage_items().
        """
        self.ui_actions.manage_items('Banking Accounts')

    """
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
        
    """