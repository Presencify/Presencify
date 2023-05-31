"""
Presencify - A Discord Rich Presence Manager for Windows
This application is not affiliated with Discord in any way.
"""

from .runtime import Runtime
from .logger import Logger
from .presence import Presence, PresenceEx

__title__ = "Presencify"
__version__ = "0.0.1"
__author__ = "Manuel Cabral"
__license__ = "GNU GPLv3"
__all__ = ["Runtime", "Logger", "Presence"]
