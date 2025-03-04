class StyleConfig:
    """Stores global UI settings such as font type, sizes, and colors."""
    
    # Font settings
    FONT_FAMILY = "calibri"
    FONT_SIZE = 16
    SUB_FONT_SIZE = 10
    HEADING_FONT_SIZE = 14
    TITLE_FONT_SIZE = 16

    # Colors
    BG_COLOR = "#dce7f5"  # Background color
    TEXT_COLOR = "#333333"  # Dark text color
    HEADER_COLOR = "#4a90e2"  # Header background
    BAND_COLOR_1 = "#e6f2ff"  # Alternating row color 1
    BAND_COLOR_2 = "#ffffff"  # Alternating row color 2
    ERROR_COLOR = "#ff4d4d"  # Error messages
    
    # Row settings
    ROW_HEIGHT = 25
    BANDED_ROWS = ["#e6f2ff", "#ffffff", '#D3D3D3']