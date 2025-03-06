class StyleConfig:
    """Stores global UI settings such as font type, sizes, and colors."""
    
    """
    # Font settings
    FONT_FAMILY = "calibri"
    FONT_SIZE = 12
    SUB_FONT_SIZE = 10
    HEADING_FONT_SIZE = 14
    TITLE_FONT_SIZE = 16
    BUTTON_FONT_SIZE = 10

    # Colors
    BG_COLOR = "#dce7f5"  # Background color
    TEXT_COLOR = "#333333"  # Dark text color
    HEADER_COLOR = "#4a90e2"  # Header background
    BUTTON_COLOR = "#eaeaea"  # Button background
    BAND_COLOR_1 = "#e6f2ff"  # Alternating row color 1
    BAND_COLOR_2 = "#ffffff"  # Alternating row color 2
    ERROR_COLOR = "#ff4d4d"  # Error messages
    
    # Row settings
    ROW_HEIGHT = 50
    """
    
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
            "BG_COLOR":             "#dce7f5",
            "TEXT_COLOR":           "#333333",
            "HEADER_COLOR":         "#4a90e2",
            "BUTTON_COLOR":         "#eaeaea",
            "BAND_COLOR_1":         "#e6f2ff",
            "BAND_COLOR_2":         "#ffffff",
            "ERROR_COLOR":          "#ff4d4d",
            "ROW_HEIGHT":           25,
        }
    
# Initialize StyleConfig attributes dynamically from defaults
for key, value in StyleConfig.getDefaultSettings().items():
    setattr(StyleConfig, key, value)
