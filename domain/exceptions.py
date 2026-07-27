class SSMLNotSupportedError(Exception):
    """Raised when synthesis is requested with SSML input on an engine that can't parse it."""


class VoiceNotFoundError(Exception):
    """Raised when a requested voice identifier isn't available for the current engine."""


class TTSEngineUnavailableError(Exception):
    """Raised when a TTS engine adapter can't reach its backing service (e.g. a local server)."""


class LanguageNotSupportedError(Exception):
    """Raised when a requested language has no locale/voice mapping for the current engine."""


class TaskNotFoundError(Exception):
    """Raised when a requested task id doesn't exist in the queue."""


class QueueAlreadyProcessingError(Exception):
    """Raised when queue processing is started while a previous run is still in progress."""


class VoiceUploadNotSupportedError(Exception):
    """Raised when a new voice sample is uploaded to an engine whose adapter doesn't support it."""
