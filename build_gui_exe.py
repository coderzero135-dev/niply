"""
Build script to create a .exe from discord_quick_reply_gui.py

Run this to create a standalone executable:
    python build_gui_exe.py

The .exe, config.json, and icon.ico will be in the dist/ folder.
"""

import PyInstaller.__main__
import shutil
import os


def main():
    print("Building Niply executable...")

    PyInstaller.__main__.run([
        "discord_quick_reply_gui.py",
        "--onefile",
        "--name", "Niply",
        "--noconsole",
        "--icon", "icon.ico",
    ])

    # Copy config.json and icon.ico next to the .exe
    dist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")

    files_to_copy = ["config.json", "icon.ico"]
    for filename in files_to_copy:
        src = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        dst = os.path.join(dist_dir, filename)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"Copied {filename} to {dst}")

    print("\nBuild complete!")
    print(f"Find your files in: {dist_dir}")
    print("Run Niply.exe to use the app.")


if __name__ == "__main__":
    main()
