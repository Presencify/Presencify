import json
import os
import sys
import time
import presencify


if __name__ == "__main__":
    folders = os.listdir("presences")
    folders = [folder for folder in folders if not folder.endswith(".py")]
    presences = []
    for folder in folders:
        files = os.listdir(f"presences/{folder}")
        if not "metadata.json" in files:
            presencify.Logger.write(
                msg=f"metadata.json not found in {folder}", level="warning"
            )
            continue
        if not "main.py" in files:
            presencify.Logger.write(f"main.py not found in {folder}", level="warning")
            continue
        with open(f"presences/{folder}/metadata.json", "r") as metadata_file:
            metadata = json.load(metadata_file)
        with open(f"presences/{folder}/main.py", "r") as main_file:
            main_code = main_file.read()
        presence = presencify.Presence(
            name=metadata["name"],
            description=metadata["description"],
            author=metadata["author"],
            client_id=metadata["client_id"],
            uses_browser=metadata["uses_browser"],
            main_code=main_code,
            folder=folder,
        )
        presencify.Logger.write(msg=f"Loaded presence {presence}", origin=__name__)
        presences.append(presence)
    if len(presences) == 0:
        presencify.Logger.write(msg="No presences found, exiting", origin=__name__)
        sys.exit(0)
    presencify.Logger.write(msg=f"Loaded {len(presences)} presences", origin=__name__)
    presencify.Logger.write(msg="Starting presences...", origin=__name__)
    for presence in presences:
        presence.start()
        time.sleep(1)
    presencify.Logger.write(msg="Presences started", origin=__name__)
    presencify.Logger.write(msg="Press Ctrl+C to stop presences", origin=__name__)
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        for presence in presences:
            presence.stop()

    input("Press enter to exit")
