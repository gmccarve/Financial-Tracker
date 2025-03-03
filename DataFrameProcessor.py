import pandas as pd
from typing import Tuple

from Utility import Utility

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
        if 'Index' not in df:
            df.insert(0, 'Index', df.index)
        else:
            df = df.drop('Index', axis=1)
            df.insert(0, 'Index', df.index)
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
        Sorts a DataFrame based on 'Date', 'Amount', 'Account', and 'Category' columns.

        Sorting is done in ascending order for all specified columns.

        Parameters:
        - df (pd.DataFrame): The input DataFrame.

        Returns:
        - pd.DataFrame: Sorted DataFrame with a reset index.
        """
        df = df.sort_values(by=['Date', 'Amount', 'Account', 'Category'], ascending=True, inplace=False).reset_index(drop=True) 
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
    
    def removeEmptyAmounts(df: pd.DataFrame) -> pd.DataFrame:
        """
        Removes rows where the 'Amount' column is 0.00.

        Parameters:
        - df (pd.DataFrame): The input DataFrame containing an 'Amount' column.

        Returns:
        - pd.DataFrame: Cleaned DataFrame with non-zero 'Amount' values and reset index.
        """
        return df[df['Amount'] != 0].reset_index(drop=True)
    
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
