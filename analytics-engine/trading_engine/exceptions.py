class ModelNotFoundError(Exception):
    """Raised when a required persisted model is not found in load-only mode."""
    pass
