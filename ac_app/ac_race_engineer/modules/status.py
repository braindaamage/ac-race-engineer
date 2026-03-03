"""Status indicator module for AC Race Engineer.

Defines recording status states and their visual representations.
Python 3.3 compatible.
"""

STATUS_IDLE = 0
STATUS_RECORDING = 1
STATUS_FLUSHING = 2
STATUS_ERROR = 3

_COLOR_MAP = {
    STATUS_IDLE: (0.5, 0.5, 0.5),
    STATUS_RECORDING: (0.0, 0.8, 0.0),
    STATUS_FLUSHING: (0.9, 0.8, 0.0),
    STATUS_ERROR: (0.8, 0.0, 0.0),
}

_TEXT_MAP = {
    STATUS_IDLE: "IDLE",
    STATUS_RECORDING: "REC",
    STATUS_FLUSHING: "FLUSH",
    STATUS_ERROR: "ERR",
}


def get_status_display(state):
    """Get the display text and color for a status state.

    Args:
        state: one of STATUS_IDLE, STATUS_RECORDING, STATUS_FLUSHING, STATUS_ERROR

    Returns:
        tuple: (text, r, g, b) where r/g/b are floats 0.0-1.0
    """
    text = _TEXT_MAP.get(state, "???")
    color = _COLOR_MAP.get(state, (0.5, 0.5, 0.5))
    return (text, color[0], color[1], color[2])
