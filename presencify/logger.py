from datetime import datetime
from .constants import Constants


class Logger:
    @staticmethod
    def info(msg: str) -> None:
        Logger.write(msg=msg, level="info", origin="__main__")

    @staticmethod
    def write(**kwargs) -> None:
        msg = kwargs.get("msg", "")
        level = kwargs.get("level", "info")
        origin = kwargs.get("origin", "unknown")
        _print = kwargs.get("print", True)
        now = datetime.now()
        formatted_now = now.strftime("%d/%m/%Y %H:%M:%S")
        if origin == "__main__":
            origin = "App"
        origin = origin.__class__.__name__ if origin != "App" else origin
        output = f"{level.upper()} | {origin}: {msg}\r"
        if _print:
            print(output)
        with open(Constants.LOG_OUTPUT_FILENAME, "a", encoding="utf-8") as file:
            file.write(f"{formatted_now} | {output}")
