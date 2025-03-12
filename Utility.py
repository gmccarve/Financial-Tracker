import os
import pandas as pd
import pickle
from datetime import datetime, timedelta
from tkinter import messagebox, filedialog, ttk
from typing import List, Tuple, Union
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

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
        try:
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=False, format='mixed').dt.date
        except KeyError:
            pass
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

class Utility:
    @staticmethod
    def getCategoryTypes(name: str) -> Tuple[List[str], str]:
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
    
    def generateMonthYearList(start_date: datetime, end_date: datetime) -> List[Tuple[int, int]]:
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
    
    def formatMonthYear(month: int, year: int) -> datetime:
        """
        Convert a month and year into the format 'MM 'YY'.
        
        Parameters:
            month (int): The month
            year (int): The year
            
        Returns:
            A (str) in the format "Mon 'YY"
        """
        return datetime(year, month, 1).strftime("%b '%y")
    
    def formatMonthLastDayYear(month: int, year: int) -> datetime:
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
    
    def formatDateFromString(day: 'str') -> datetime:
        """
        Convert a month and year into the format 'Mon 'YY'.
        
        Parameters:
            day (str): The day in YYYY-MM-DD format
            
        Returns:
            The last day of a month given as a string in the format "MM DD 'YY"
        """
        new_day = day.split("-")
        return datetime(int(new_day[0]), int(new_day[1]), int(new_day[2])).strftime("%Y-%m-%d")
            
class Windows:
    @staticmethod
    def openRelativeWindow(new_window, main_width: int, main_height: int, width: int, height: int) -> None:
        """
        Positions the new window relative to the main application window.
    
        This ensures that the new window appears slightly offset from the main window.
    
        Parameters:
            new_window: The new Tkinter window to be positioned.
            main_width  (int): The current width of new_window
            main_height (int): The current height of new_window
            width       (int): The width of the new window.
            height      (int): The height of the new window.
    
        Returns:
            None
        """    
        # Position new window slightly offset from the main window
        new_x = main_width  + 250
        new_y = main_height + 250
    
        new_window.geometry(f"{width}x{height}+{new_x}+{new_y}")  # Format: "WIDTHxHEIGHT+X+Y"
        
class Tables:
    # Define class-level variables (shared across all instances)

    @staticmethod
    def tableStyle(style: ttk.Style) -> None:
        """
        Applies a consistent style to Treeview tables.
    
        Parameters:
            style: The ttk.Style object used for configuring table appearance.
        """
        style.configure("Treeview", rowheight=25, font=(StyleConfig.FONT_FAMILY, StyleConfig.FONT_SIZE))  # Set row height and font
        style.configure("Treeview.Heading", font=(StyleConfig.FONT_FAMILY, StyleConfig.HEADING_FONT_SIZE, "bold"))  # Bold headers
        style.configure("Treeview.Heading", padding=(5,25), anchor='center', justify='center')
        style.layout("Treeview.Heading", [
                                            ("Treeheading.cell", {"sticky": "nswe"}),  # Stretches the header cell
                                            ("Treeheading.border", {"sticky": "nswe"}),  # Ensures full stretch
                                            ("Treeheading.padding", {"sticky": "nswe"}),  # Applies padding in all directions
                                            ("Treeheading.label", {"sticky": "nswe"})  # Ensures text is centered in the label
                                        ])

    def clearTable(tree: ttk.Treeview) -> None:
        """
        Clears all items from a Treeview widget.
    
        Parameters:
            tree: The ttk.Treeview widget to be cleared.
        """
        tree.delete(*tree.get_children())
        
    def sortTableByColumn(tv:ttk.Treeview, col: 'str', reverse: bool, colors: List) -> None:
        """Sorts a Treeview column properly, handling currency values and reapplying row colors."""

        def convertValue(val):
            """Converts currency values ($XXX.XX) to float for sorting."""
            try:
                return float(val.replace("$", "").replace(",", "").replace("%", ""))
            except ValueError:
                return val.lower()
            
        # Get values and sort correctly
        l = [(convertValue(tv.set(k, col)), k) for k in tv.get_children('')]
        l.sort(reverse=reverse)
    
        # Rearrange items in sorted order
        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)
    
        # Reapply banded row styling
        Tables.applyBandedRows(tv, colors=colors)
    
        # Reverse sort next time
        tv.heading(col, command=lambda: Tables.sortTableByColumn(tv, col, not reverse, colors))
        
    def applyBandedRows(tv: ttk.Treeview, colors: list[str, str]) -> None:
        """Recolors Treeview rows to maintain alternating row stripes after sorting."""
        for index, row in enumerate(tv.get_children('')):
            tag = "evenrow" if index % 2 == 0 else "oddrow"
            tv.item(row, tags=(tag,))
    
        # Define colors for tags
        tv.tag_configure("evenrow", background=colors[0])
        tv.tag_configure("oddrow", background=colors[1]) 
        
class Classifier:
    
    def trainPayeeAndCategoryClassifier(df: pd.DataFrame) -> Tuple[Pipeline, Pipeline]:
        """
        Trains two machine learning pipelines to predict the Payee and Category for a transaction,
        based on the following input features:
        - Description (text)
        - Payment (numeric, assumed to be in cents)
        - Deposit (numeric, assumed to be in cents)
        - Account (categorical)

        The function uses a ColumnTransformer to process the features:
        - "Description" is vectorized via TF-IDF.
        - "Payment" and "Deposit" are scaled using StandardScaler.
        - "Account" is one-hot encoded.
        
        Two separate Logistic Regression classifiers are then trained—one for Payee and one for Category.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame containing the following columns:
            - "Description": Transaction description (string)
            - "Payment": Payment amount (numeric, in cents)
            - "Deposit": Deposit amount (numeric, in cents)
            - "Account": Account name (string)
            - "Payee": Target label for payee (string)
            - "Category": Target label for category (string)
        
        Returns
        -------
        Tuple[Pipeline, Pipeline]
            A tuple (payee_pipeline, category_pipeline) where each pipeline is a scikit‑learn Pipeline
            that has been fitted to the training data.
        
        Raises
        ------
        ValueError
            If any required column is missing or if no training data is available.
        """
        required_cols = ["Description", "Payment", "Deposit", "Account", "Payee", "Category"]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
        
        # Drop rows where either target is missing or blank
        train_df = df[
            df["Payee"].notnull() & (df["Payee"].str.strip() != "") &
            df["Category"].notnull() & (df["Category"].str.strip() != "")
        ].copy()
        if train_df.empty:
            raise ValueError("No training data available after filtering missing targets.")

        # Define the input features
        features = ["Description", "Payment", "Deposit", "Account"]
        
        # Create a preprocessor that handles different columns appropriately.
        preprocessor = ColumnTransformer(
            transformers=[
                ("desc", TfidfVectorizer(stop_words="english"), "Description"),
                ("num", StandardScaler(), ["Payment", "Deposit"]),
                ("acct", OneHotEncoder(handle_unknown="ignore"), ["Account"])
            ]
        )
        
        # Define and train the pipeline for Payee prediction.
        payee_pipeline = Pipeline(steps=[
            ("preprocessor", preprocessor),
            ("classifier", RandomForestClassifier(n_estimators=250, max_depth=10))
        ])
        payee_pipeline.fit(train_df[features], train_df["Payee"])
        
        # Define and train the pipeline for Category prediction.
        category_pipeline = Pipeline(steps=[
            ("preprocessor", preprocessor),
            ("classifier", RandomForestClassifier(n_estimators=250, max_depth=10))
        ])
        category_pipeline.fit(train_df[features], train_df["Category"])
        
        return payee_pipeline, category_pipeline

    def predictTransactionLabels(
        description: str,
        payment: float,
        deposit: float,
        account: str,
        payee_pipeline: Pipeline,
        category_pipeline: Pipeline
    ) -> Tuple[str, str]:
        """
        Predicts the Payee and Category for a transaction based on the input features.

        Parameters
        ----------
        description : str
            The transaction's description.
        payment : float
            The payment amount (in cents).
        deposit : float
            The deposit amount (in cents).
        account : str
            The account name.
        payee_pipeline : Pipeline
            A trained scikit‑learn pipeline for predicting the Payee.
        category_pipeline : Pipeline
            A trained scikit‑learn pipeline for predicting the Category.
        
        Returns
        -------
        Tuple[str, str]
            A tuple (predicted_payee, predicted_category).
        """
        # Create a single-row DataFrame with the input features.
        input_df = pd.DataFrame([{
            "Description": description,
            "Payment": payment,
            "Deposit": deposit,
            "Account": account
        }])
        
        predicted_payee = payee_pipeline.predict(input_df)[0]
        predicted_category = category_pipeline.predict(input_df)[0]
        
        return predicted_payee, predicted_category