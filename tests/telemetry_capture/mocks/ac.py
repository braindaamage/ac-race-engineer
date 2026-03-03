"""Mock ac module for testing.

Stubs all AC Python API functions used by the telemetry capture app.
Configurable return values for per-channel testing.
"""

# Configurable return values for getCarState
_car_state_values = {}
_labels = {}
_label_counter = [0]


def configure_car_state(channel, value):
    """Configure the return value for a specific channel."""
    _car_state_values[channel] = value


def reset():
    """Reset all configured values to defaults."""
    _car_state_values.clear()
    _labels.clear()
    _label_counter[0] = 0


def getCarState(carIndex, channel):
    """Return configured value for channel, or sensible default."""
    if channel in _car_state_values:
        return _car_state_values[channel]
    return 0.0


def getCarName(i):
    return "test_car"


def getTrackName(i):
    return "test_track"


def getTrackConfiguration(i):
    return ""


def getTrackLength(i):
    return 5000.0


def getDriverName(i):
    return "Test Driver"


def getCarTyreCompound(i):
    return "Soft"


def isCarInPitlane(i):
    return 0


def isCarInPit(i):
    return 0


def newApp(name):
    return 1


def addLabel(appId, text):
    _label_counter[0] += 1
    label_id = _label_counter[0]
    _labels[label_id] = text
    return label_id


def setSize(appId, w, h):
    pass


def setPosition(appId, x, y):
    pass


def setBackgroundColor(appId, r, g, b):
    pass


def drawBackground(appId, value):
    pass


def setBackgroundOpacity(appId, opacity):
    pass


def setFontColor(appId, r, g, b, a):
    pass


def setFontSize(appId, size):
    pass


def setText(appId, text):
    if appId in _labels:
        _labels[appId] = text


def setTitle(appId, title):
    pass


def log(msg):
    pass
