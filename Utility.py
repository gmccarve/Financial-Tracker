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
        
        