from asyncio import run
from platform import system
from src import App, Logger, Constants


async def main():
    if system() not in Constants.OS_COMPAT:
        raise Exception(
            f"OS not supported. Please use one of the following: {Constants.OS_COMPAT}"
        )
    app = App()
    await app.run()


if __name__ == "__main__":
    try:
        run(main())
    except Exception as exc:
        Logger.write(msg=str(exc), level="error", origin=__name__)
        input("Press enter to exit...")
    except KeyboardInterrupt:
        Logger.write(msg="Program interrupted by user.", origin=__name__)
        input("Press enter to exit...")
