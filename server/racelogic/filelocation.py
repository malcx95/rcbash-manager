import os
import time


DRIVE_MOUNT_LOCATION = "/mnt/KingstonDrive/"
#DRIVE_MOUNT_LOCATION = "/media/malcolm/B1C5-B1C4/"


def find_and_read_latest_html_file():
    while not (os.path.isdir(DRIVE_MOUNT_LOCATION) and os.listdir(DRIVE_MOUNT_LOCATION)):
        print("Drive not found, retrying in 3 seconds...")
        time.sleep(3)

    folder_path = os.path.join(DRIVE_MOUNT_LOCATION)
    files = os.listdir(folder_path)

    numeric_files = [f for f in files if f.replace('_', '').replace('.html', '').isnumeric()]
    latest = max(numeric_files, key=lambda f: int(f.replace('_', '').replace('.html', '')))

    contents = None
    try:
        with open(os.path.join(DRIVE_MOUNT_LOCATION, latest)) as f:
            contents = f.read()
    except UnicodeDecodeError:
        with open(os.path.join(DRIVE_MOUNT_LOCATION, latest), encoding="utf-16-le") as f:
            contents = f.read()

    return contents


if __name__ == "__main__":
    find_and_read_latest_html_file()
