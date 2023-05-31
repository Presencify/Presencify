import os
import time
import presencify


def exist_folder(folder_name: str) -> bool:
    return os.path.exists(folder_name)


def exists_file(file_name: str) -> bool:
    return os.path.exists(file_name)


def listdirEx(name: str, ext: str = None, exclude: bool = False) -> list:
    if not exists_file(name):
        return []
    if ext is None:
        return os.listdir(name)
    files = os.listdir(name)
    if exclude:
        return [file for file in files if not file.endswith(ext)]
    return [file for file in files if file.endswith(ext)]


def main() -> None:
    presences = []
    if not exist_folder("presences"):
        os.mkdir("presences")
    subfolders = listdirEx("presences", ext=".py", exclude=True)
    for folder in subfolders:
        presences.append(presencify.PresenceTwo(location=f"presences/{folder}"))
    presences = [presence for presence in presences if presence.loaded]
    total = len(presences)
    if total == 0:
        raise ValueError("No presences found")
    for presence in presences:
        for presence_ in presences:
            if presence == presence_:
                raise ValueError(
                    f"Repeated presence {presence.name} please, check your presences"
                )
    presencify.Logger.write(msg=f"Loaded {total} presence(s)", origin=__name__)
    return presences


if __name__ == "__main__":
    presences = main()
    try:
        for presence in presences:
            presence.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        presencify.Logger.write(msg="Exiting...", origin=__name__)
    except Exception as exc:
        presencify.Logger.write(msg=f"Error: {exc}", level="error", origin=__name__)
    for presence in presences:
        presence.stop()
    input("Press enter to exit...")
