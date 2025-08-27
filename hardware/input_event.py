class InputEvent:
    """Represents a standardized input event from any device."""
    def __init__(self, device_type, value, meta=None):
        self.device_type = device_type
        self.value = value
        self.meta = meta or {}

    def __repr__(self):
        return f"InputEvent({self.device_type!r}, {self.value!r}, {self.meta!r})"
