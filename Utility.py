import os
import pandas as pd
import pickle
from datetime import datetime, timedelta
from tkinter import messagebox, filedialog, ttk
from typing import List, Tuple, Union

from StyleConfig import StyleConfig

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
    
class SaveFiles:
    @staticmethod
    def saveState(save_file:str, inc_data: pd.DataFrame, exp_data: pd.DataFrame, init_data: pd.DataFrame) -> None:
        """
        Saves financial data based on the last saved file format.
    
        - If the last saved file is a `.pkl`, saves as a Pickle file.
        - If the last saved file is a `.xlsx`, saves as an Excel file.
        - If the last saved file is in CSV format (5 lines), saves as CSV.
        - If no valid file is found, prompts the user.
        
        Parameters:
            save_file (str) - the full-length path of the file to save
            inc_data (pd.DataFrame): dataframe of income data
            exp_data (pd.DataFrame): dataframe of expenses data
            init_data (pd.DataFrame): dataframe of initial values
        
        Retuns:
            None
        """ 
        
        try:
            with open(save_file, 'r') as ff:
                file_lines = ff.readlines()
    
            if len(file_lines) == 1:
                file_name = file_lines[0].strip()
                if file_name.endswith(".pkl"):
                    SaveFiles.saveToPickleFile(file_name, inc_data, exp_data, init_data)
                elif file_name.endswith(".xlsx"):
                    SaveFiles.saveToXLSX(file_name, inc_data, exp_data, init_data)
            elif len(file_lines) == 5:
                SaveFiles.saveToCSV(file_lines, inc_data, exp_data, init_data)
            else:
                messagebox.showinfo("Message", "No data to save")
        except FileNotFoundError:
            messagebox.showinfo("Message", "No previously saved file found.")
            
    def saveStateAs(inc_data: pd.DataFrame, exp_data: pd.DataFrame, init_data: pd.DataFrame) -> None:
        """
        Saves financial data with user-specified file format.
    
        Prompts the user to select a save location and file format (`.xlsx`, `.pkl`, `.csv`).
        
        Parameters:
            inc_data (pd.DataFrame): dataframe of income data
            exp_data (pd.DataFrame): dataframe of expenses data
            init_data (pd.DataFrame): dataframe of initial values
        
        Retuns:
            None
        """
        filetypes = [
            ("Excel Files", "*.xlsx"),
            ("Pickle Files", "*.pkl"),
            ("CSV Files", "*.csv"),
        ]
        
        file_name = filedialog.asksaveasfilename(
            title="Select Files",
            filetypes=filetypes,
            defaultextension=".xlsx"
        )
    
        if file_name:
            if file_name.endswith(".pkl"):
                SaveFiles.saveToPickleFile(file_name, inc_data, exp_data, init_data)
            elif file_name.endswith(".xlsx"):
                SaveFiles.saveToXLSX(file_name, inc_data, exp_data, init_data)
            elif file_name.endswith(".csv"):
                SaveFiles.saveToCSV(file_name, inc_data, exp_data, init_data)
        else:
            messagebox.showinfo("Message", "No saved file chosen.")        
    
    def saveToXLSX(file_name: str, inc_data: pd.DataFrame, exp_data: pd.DataFrame, init_data: pd.DataFrame) -> None:
        """
        Saves financial data to an Excel (.xlsx) file.
    
        Parameters:
            file_name (str): The file path for saving.
            inc_data (pd.DataFrame): dataframe of income data
            exp_data (pd.DataFrame): dataframe of expenses data
            init_data (pd.DataFrame): dataframe of initial values
        
        Retuns:
            None
        """
        data_frames = [inc_data, exp_data, init_data]
        sheet_names = ['Income', 'Expenses', 'Starting Balance']
    
        try:
            with pd.ExcelWriter(file_name) as writer:
                for df, sheet_name in zip(data_frames, sheet_names):
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
    
            messagebox.showinfo("File Saved", f"Data successfully saved to \n{file_name}")
            SaveFiles.updateLastSavedFile(file_name)
    
        except Exception as e:
            messagebox.showinfo("File Not Saved", f"Error - Data not saved to \n{file_name}\n\n{str(e)}")
    
    def saveToCSV(file_name: Union[str, List[str]], inc_data: pd.DataFrame, exp_data: pd.DataFrame, init_data: pd.DataFrame) -> None:
        """
        Saves financial data to CSV files.
    
        If the provided file name is a list (legacy behavior), extracts the directory and base name from the first item.
    
        Parameters:
            file_name (str): The file path or list of file paths.
            inc_data (pd.DataFrame): dataframe of income data
            exp_data (pd.DataFrame): dataframe of expenses data
            init_data (pd.DataFrame): dataframe of initial values
        
        Returns:
            None
        """
        
        try:
            if type(file_name) == str:
                dir_base = "/".join(file_name.split("/")[:-1])
                file_base = file_name.split("/")[-1].split(".")[0]
            else:
                dir_base = "/".join(file_name[0].split("/")[:-1])
                file_base = file_name[0].split("/")[-1].split("_")[0]
            
            list_dfs = [inc_data, exp_data, init_data]
            type_names = ['Income', 'Expenses', 'Starting Balance']
            file_names = []
            
            try:
                for idx, df in enumerate(list_dfs):
                    file_path = os.path.join(dir_base, file_base + "_" + type_names[idx] + ".csv")
                    df.to_csv(file_path, index=False)
                    file_names.append(file_path)
                    
                all_file_names = "\n\n".join(file_names)
                messagebox.showinfo("Files Saved", f"Data successfully saved to \n\n{all_file_names}")
                
                SaveFiles.updateLastSavedFile(all_file_names)
                
            except:
                messagebox.showinfo("File Not Saved", f"Error - Data not saved to \n{file_name}")     
    
        except Exception as e:
            messagebox.showinfo("File Not Saved", f"Error - Data not saved to \n{file_name}\n\n{str(e)}")
        
    def saveToPickleFile(file_name: str, inc_data: pd.DataFrame, exp_data: pd.DataFrame, init_data: pd.DataFrame) -> None:
        """
        Saves financial data to a Pickle (.pkl) file.
    
        Parameters:
            file_name (str): The file path for saving.
            inc_data (pd.DataFrame): dataframe of income data
            exp_data (pd.DataFrame): dataframe of expenses data
            init_data (pd.DataFrame): dataframe of initial values
        
        Returns:
            None
        """
        yearly_data = {
            'Income': inc_data,
            'Expenses': exp_data,
            'Initial': init_data,
        }
    
        try:
            with open(file_name, "wb") as f:
                pickle.dump(yearly_data, f)
    
            messagebox.showinfo("File Saved", f"Data successfully saved to \n{file_name}")
            SaveFiles.updateLastSavedFile(file_name)
    
        except Exception as e:
            messagebox.showinfo("File Not Saved", f"Error - Data not saved to \n{file_name}\n\n{str(e)}")
            
    def updateLastSavedFile(file_name):
        """
        Updates the record of the last saved file.
    
        Parameters:
            file_name: The file path that was last successfully saved.
        
        Results:
            None
        """
        save_file_location = os.path.join(os.path.dirname(__file__), "lastSavedFile.txt")
        try:
            with open(save_file_location, "w") as f:
                f.write(file_name)
        except Exception as e:
            messagebox.showinfo("Error", f"Could not update last saved file: \n\n{str(e)}") 
            
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
        new_x = main_width  + 50
        new_y = main_height + 50
    
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
        
    def sortTableByColumn(tv, col, reverse):
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
        Tables.applyBandedRows(tv)
    
        # Reverse sort next time
        tv.heading(col, command=lambda: Tables.sortTableByColumn(tv, col, not reverse))
        
    def applyBandedRows(tv):
        """Recolors Treeview rows to maintain alternating row stripes after sorting."""
        for index, row in enumerate(tv.get_children('')):
            tag = "evenrow" if index % 2 == 0 else "oddrow"
            tv.item(row, tags=(tag,))
            
            #TODO TOTAL ROW
    
        # Define colors for tags
        tv.tag_configure("evenrow", background=StyleConfig.BANDED_ROWS[0])
        tv.tag_configure("oddrow", background=StyleConfig.BANDED_ROWS[1]) 
        
        