from presencify import __version__, __author__, __title__
from cx_Freeze import setup, Executable

setup(
    name=__title__,
    version=__version__,
    description="Your discord presences, your way.",
    author=__author__,
    options={
        "build_exe": {
            "excludes": ["tkinter", "unittest"],
        }
    },
    executables=[
        Executable(
            "main.py",
            target_name="presencify.exe",
            base="Console",
            shortcut_name="Presencify",
            copyright="© 2020 - 2023 by " + __author__ + " - All rights reserved",
        )
    ],
)