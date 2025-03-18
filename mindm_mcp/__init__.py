# Version information
try:
    from importlib.metadata import version as _version
    __version__ = _version("mindm")
except ImportError:
    __version__ = "unknown"
