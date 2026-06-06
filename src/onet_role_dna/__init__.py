"""
O*NET Role DNA analysis package.
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("onet_role_dna")
except PackageNotFoundError:
    # Safe fallback for standalone scripts and development
    __version__ = "0.1.0"
