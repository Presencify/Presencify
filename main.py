import os
import time
import threading
import presencify


def sync_presences(local_presences: list, github_presences: list) -> None:
    """
    Sync presences from github repo to local presences
    """
    for local_presence in local_presences:
        if local_presence.folder_name not in list(github_presences.keys()):
            presencify.Logger.write(
                msg=f"If you want to create a new presence, please, check the documentation",
                origin=__name__,
                level="warning",
            )
            raise ValueError(
                f"{local_presence.name} not allowed, please use registered presences"
            )
        else:
            local_config = presencify.Utils.hash_string(local_presence.config_file)
            github_config = presencify.Utils.hash_string(
                github_presences[local_presence.folder_name]["config"]
            )
            local_main_code = presencify.Utils.hash_string(local_presence.main_code)
            github_main_code = presencify.Utils.hash_string(
                github_presences[local_presence.folder_name]["main"]
            )
            if local_main_code != github_main_code:
                raise ValueError(
                    f"{local_presence.folder_name} main.py is modified, please, don't modify it"
                )
            if local_config != github_config:
                raise ValueError(
                    f"{local_presence.folder_name} config.json is modified, please, don't modify it"
                )
    presencify.Logger.write(
        msg="Pass all checks, starting to sync presences", origin=__name__
    )


def main() -> None:
    presences = []
    os.system(f"title Presencify v{presencify.__version__}")
    if not presencify.Utils.exist_folder("presences"):
        os.mkdir("presences")
    subfolders = presencify.Utils.listdirEx("presences", ext=".py", exclude=True)
    for folder in subfolders:
        presences.append(presencify.Presence(location=f"presences/{folder}"))
    presences = [presence for presence in presences if presence.loaded]
    total = len(presences)
    if total == 0:
        presencify.Logger.write(msg="No presences found", origin=__name__)
        return []
    for presence in presences:
        for presence_ in presences:
            if presence == presence_:
                raise ValueError(
                    f"Repeated presence {presence.name} please, check your presences"
                )
    github_presences = presencify.Utils.fetch_github_presences()
    sync_presences(presences, github_presences)
    presencify.Logger.write(msg=f"Loaded {total} presence(s)", origin=__name__)
    free_port = presencify.Utils.get_free_port()
    presencify.Utils.open_remote_browser(free_port)
    for presence in presences:
        presence.start(port=free_port)
        time.sleep(2)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        presencify.Logger.write(msg="Exiting...", origin=__name__)
    for presence in presences:
        presence.stop()
    time.sleep(1)
    for presence in presences:
        presence.disconnect()
    return


if __name__ == "__main__":
    presencify.Logger.info("Presencify - A Discord Rich Presence Manager")
    presencify.Logger.info("This application is not affiliated with Discord in any way")
    presencify.Logger.info("Source code: www.github.com/Presencify")
    presencify.Logger.info("To stop the application, press CTRL+C")
    try:
        main()
    except Exception as exc:
        presencify.Logger.write(msg=exc, origin=__name__, level="error")
    input("Press ENTER to exit...")
