import pickle

class StyleConfig:
    """Stores global UI settings such as font type, sizes, and colors."""
    
    ORIGINAL_SETTINGS = {}
    
    # Font settings
    FONT_FAMILY = "calibri"
    FONT_SIZE = 12
    SUB_FONT_SIZE = 10
    HEADING_FONT_SIZE = 14
    TITLE_FONT_SIZE = 16
    BUTTON_FONT_SIZE = 10

    # Colors
    BG_COLOR = "#B0B0B0"  # Background color
    TEXT_COLOR = "#333333"  # Dark text color
    HEADER_COLOR = "#4a90e2"  # Header background
    BUTTON_COLOR = "#eaeaea"  # Button background
    BAND_COLOR_1 = "#e6f2ff"  # Alternating row color 1
    BAND_COLOR_2 = "#ffffff"  # Alternating row color 2
    ERROR_COLOR = "#ff4d4d"  # Error messages
    SELECTION_COLOR = "#B0B0B0"
    
    # Row settings
    ROW_HEIGHT = 50
    
    # Mouse settings
    SCROLL_SPEED = 1
    
    # Button settings
    BUTTON_STYLE = "raised"  # Can be "flat", "sunken", "raised", or "ridge"
    BUTTON_PADDING = 5  # Adjust button padding
    BUTTON_BORDER_RADIUS = 10  # (Only works with themed buttons)
    
    # Dark mode
    DARK_MODE = False  # Default to light mode

    # Date format
    DATE_FORMAT = "%Y-%m-%d"
    
    @classmethod
    def getDefaultSettings(cls):
        """Returns a dictionary of default settings."""
        return {
            "FONT_FAMILY":          "calibri",
            "FONT_SIZE":            12,
            "SUB_FONT_SIZE":        10,
            "HEADING_FONT_SIZE":    14,
            "TITLE_FONT_SIZE":      16,
            "BUTTON_FONT_SIZE":     10,
            "BG_COLOR":             "#eeeeee",
            "TEXT_COLOR":           "#333333",
            "HEADER_COLOR":         "#4a90e2",
            "BUTTON_COLOR":         "#eaeaea",
            "BAND_COLOR_1":         "#e6f2ff",
            "BAND_COLOR_2":         "#ffffff",
            "ERROR_COLOR":          "#ff4d4d",
            "SELECTION_COLOR":      "#B0B0B0",
            "ROW_HEIGHT":           25,
            "SCROLL_SPEED":         1,
            "BUTTON_STYLE":         "raised",
            "BUTTON_PADDING":       5,
            "BUTTON_BORDER_RADIUS": 10,
            "DARK_MODE":            False,
            "DATE_FORMAT":          "%Y-%m-%d",
        }
    
    @classmethod
    def applyDarkMode(cls, enable_dark_mode):
        """Applies Dark Mode or Light Mode settings dynamically."""
        cls.DARK_MODE = enable_dark_mode

        if enable_dark_mode:
            # Store current settings before switching to dark mode
            if not cls.ORIGINAL_SETTINGS:  # Store only once
                cls.ORIGINAL_SETTINGS = {key: getattr(cls, key) for key in cls.getDefaultSettings().keys()}
            
            # Apply Dark Mode colors
            cls.BG_COLOR = "#2E2E2E"
            cls.TEXT_COLOR = "#FFFFFF"
            cls.HEADER_COLOR = "#444444"
            cls.BUTTON_COLOR = "#555555"
            cls.SELECTION_COLOR = "#666666"
            cls.BAND_COLOR_1 = "#3A3A3A"
            cls.BAND_COLOR_2 = "#2E2E2E"
        
        else:
            # Restore user-selected colors instead of default ones
            for key, value in cls.ORIGINAL_SETTINGS.items():
                setattr(cls, key, value)

            cls.ORIGINAL_SETTINGS = {}  # Reset after restoring
    
    @classmethod
    def loadUserSettings(cls, user_settings_file):
        """
        Loads user settings from a pickle file and updates the StyleConfig class.
        
        Parameters:
            user_settings_file (str): Path to the pickle file containing user settings.
        """
        try:
            with open(user_settings_file, "rb") as f:
                user_settings = pickle.load(f)
            
            for key, value in user_settings.items():
                if hasattr(cls, key):
                    setattr(cls, key, value)  # Update StyleConfig attributes with the saved values
                
                if key == "DARK_MODE":
                    cls.applyDarkMode(value)  # Apply dark mode if set

        except (FileNotFoundError, pickle.UnpicklingError):
            print("Error loading user settings. Using default settings.")
            # If there's an error, use default settings
            return