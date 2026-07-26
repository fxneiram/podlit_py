class SSMLNotSupportedError(Exception):
    """Raised when synthesis is requested with SSML input on an engine that can't parse it."""


class VoiceNotFoundError(Exception):
    """Raised when a requested voice identifier isn't available for the current engine."""
