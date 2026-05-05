
class Color:
    """Color palette."""

    GROUND_WHITE = (240, 237, 212)
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    ALMOST_WHITE = (240, 240, 240)
    DARK_RED = (183, 4, 4)
    LIGHT_GRAY = (207, 210, 207)
    DARK_GRAY = (67, 66, 66)
    LIGHT_BLACK = (34, 34, 34)
    RED_TRANSPARENT = (160, 100, 100, 180)
    RED_LIGHT_TRANS = (200, 50, 50, 40)
    WHITE_TRANSPARENT = (255, 255, 255, 80)
    HEALTH_RED = (205, 24, 24)
    ENERGY_BLUE = (77, 166, 255)
    DARK_GREEN = (65, 100, 74)
    BRIGHT_GREEN = (114, 176, 29)
    YELLOW = (255, 215, 0)
    # For multiplier only
    MUL_GREEN = [76, 187, 23, 255]
    MUL_YELLOW = [255, 215, 0, 255]
    MUL_ORANGE = [255, 79, 0, 255]
    MUL_RED = [255, 36, 0, 255]


class Style:
    """Design styles."""

    BUTTON_DEFAULT = {
        "font_name": ("Cubic 11"),
        "font_size": 16,
        "font_color": Color.WHITE,
        "border_width": 2,
        "border_color": Color.BLACK,
        "bg_color": Color.DARK_GRAY,

        # used if button is pressed
        "bg_color_pressed": Color.LIGHT_GRAY,
        "border_color_pressed": Color.WHITE,  # also used when hovered
        "font_color_pressed": Color.BLACK,
    }