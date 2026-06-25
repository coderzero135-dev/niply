"""
Build script to create a .exe from discord_hotkey_tool.py

Run this to create a standalone executable:
    python build_exe.py

The .exe and config.json will be in the dist/ folder.
You can edit config.json next to the .exe to change settings.
"""

import PyInstaller.__main__
import shutil
import os


def main():
    print("Building Discord Quick-Reply Tool executable...")

    PyInstaller.__main__.run([
        "discord_hotkey_tool.py",
        "--onefile",
        "--name", "DiscordQuickReply",
    ])

    # Copy config.json next to the .exe so users can edit it
    dist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")
    config_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    config_dst = os.path.join(dist_dir, "config.json")

    if os.path.exists(config_src):
        shutil.copy2(config_src, config_dst)
        print(f"Copied config.json to {config_dst}")

    print("\nBuild complete!")
    print(f"Find your files in: {dist_dir}")
    print("You can edit config.json next to the .exe to change triggers/messages.")


if __name__ == "__main__":
    main()
