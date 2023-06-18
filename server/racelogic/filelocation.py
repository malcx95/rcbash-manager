import os
import time
import json
import sys

SETTINGS = {
    "drive": "D:"
}

if os.path.isfile("settings.json"):
    with open("settings.json") as f:
        SETTINGS = json.load(f)

DRIVE_MOUNT_LOCATION = SETTINGS["drive"]

def find_and_read_latest_html_file():
    while not (os.path.isdir(DRIVE_MOUNT_LOCATION) and os.listdir(DRIVE_MOUNT_LOCATION)):
        print("Hittade inte USB-minnet, försöker igen om 3 sekunder...")
        time.sleep(3)

    folder_path = os.path.join(DRIVE_MOUNT_LOCATION)
    files = os.listdir(folder_path)

    numeric_files = [f for f in files if f.replace('_', '').replace('.html', '').isnumeric()]
    if not numeric_files:
        print("Det finns inga resultat på USB-minnet!")
        sys.exit(-1)

    latest = max(numeric_files, key=lambda f: int(f.replace('_', '').replace('.html', '')))

    contents = None
    with open(os.path.join(DRIVE_MOUNT_LOCATION, latest), encoding="utf-16-le") as f:
        contents = f.read()

    return contents


if __name__ == "__main__":
    find_and_read_latest_html_file()
