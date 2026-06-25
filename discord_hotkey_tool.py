"""
Discord Quick-Reply Tool

This tool listens for a mouse side button or keyboard key and automatically
types your support ticket response wherever your cursor is.

Use it inside Discord ticket channels (or any app) by clicking in the
message box and pressing your configured trigger.

Default trigger: Mouse back side button (XButton1)
Stop/exit: ESC

Setup:
1. Install requirements: pip install -r requirements.txt
2. Edit config.json to set your trigger and messages
3. Run this script: python discord_hotkey_tool.py
4. Open Discord, click in a ticket message box
5. Press your trigger to send the template messages

Build .exe:
1. Install pyinstaller: pip install pyinstaller
2. Run: python build_exe.py
3. Find the .exe in the dist/ folder
4. You can edit config.json next to the .exe to change settings
"""

import pyautogui
from pynput import keyboard, mouse
import time
import json
import os
import sys


# ==================== CONFIG LOADING ====================
def get_config_path():
    """Get the path to config.json (works both as script and as .exe)."""
    if getattr(sys, 'frozen', False):
        # Running as compiled .exe
        return os.path.join(os.path.dirname(sys.executable), "config.json")
    else:
        # Running as Python script
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def load_config():
    """Load configuration from config.json."""
    config_path = get_config_path()

    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"config.json not found at: {config_path}\n"
            "Please make sure config.json is in the same folder as this tool."
        )

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


CFG = load_config()

MESSAGES = CFG["messages"]
TRIGGER_TYPE = CFG["trigger_type"].lower()
TRIGGER_VALUE = CFG["trigger_value"].lower()
DELAY_BETWEEN_MESSAGES = CFG["delay_between_messages"]
TYPING_DELAY = CFG["typing_delay"]
COOLDOWN = CFG["cooldown"]


def get_trigger_button():
    """Convert config string to pynput mouse button."""
    if TRIGGER_VALUE == "x1":
        return mouse.Button.x1
    elif TRIGGER_VALUE == "x2":
        return mouse.Button.x2
    else:
        raise ValueError(f"Unknown mouse button: {TRIGGER_VALUE}. Use 'x1' or 'x2'.")


def get_trigger_key():
    """Convert config string to pynput keyboard key."""
    special_keys = {
        "f1": keyboard.Key.f1, "f2": keyboard.Key.f2, "f3": keyboard.Key.f3,
        "f4": keyboard.Key.f4, "f5": keyboard.Key.f5, "f6": keyboard.Key.f6,
        "f7": keyboard.Key.f7, "f8": keyboard.Key.f8, "f9": keyboard.Key.f9,
        "f10": keyboard.Key.f10, "f11": keyboard.Key.f11, "f12": keyboard.Key.f12,
        "esc": keyboard.Key.esc, "enter": keyboard.Key.enter,
        "space": keyboard.Key.space, "tab": keyboard.Key.tab,
        "ctrl": keyboard.Key.ctrl, "shift": keyboard.Key.shift,
        "alt": keyboard.Key.alt, "cmd": keyboard.Key.cmd,
    }

    if TRIGGER_VALUE in special_keys:
        return special_keys[TRIGGER_VALUE]

    if len(TRIGGER_VALUE) == 1:
        return keyboard.KeyCode.from_char(TRIGGER_VALUE)

    raise ValueError(f"Unknown keyboard key: {TRIGGER_VALUE}")


TRIGGER_BUTTON = get_trigger_button() if TRIGGER_TYPE == "mouse" else None
TRIGGER_KEY = get_trigger_key() if TRIGGER_TYPE == "keyboard" else None
# ========================================================

last_trigger_time = 0
running = True


def send_template_messages():
    """Type the configured messages at the current cursor position."""
    global last_trigger_time

    current_time = time.time()
    if current_time - last_trigger_time < COOLDOWN:
        print("Cooldown active. Wait a moment before triggering again.")
        return

    last_trigger_time = current_time
    print(f"Triggered! Sending {len(MESSAGES)} messages...")

    time.sleep(TYPING_DELAY)

    for i, message in enumerate(MESSAGES):
        pyautogui.typewrite(message, interval=0.01)
        pyautogui.press("enter")
        print(f"Sent ({i + 1}/{len(MESSAGES)}): {message}")

        # Don't delay after the last message
        if i < len(MESSAGES) - 1:
            time.sleep(DELAY_BETWEEN_MESSAGES)

    print("Done! Trigger again or press ESC to exit.\n")


def on_click(x, y, button, pressed):
    """Handle mouse click events."""
    if pressed and TRIGGER_TYPE == "mouse" and button == TRIGGER_BUTTON:
        send_template_messages()


def on_press(key):
    """Handle key press events."""
    global running

    if key == keyboard.Key.esc:
        print("ESC pressed. Exiting...")
        running = False
        return False  # Stop keyboard listener

    if TRIGGER_TYPE == "keyboard" and key == TRIGGER_KEY:
        send_template_messages()


def main():
    global running

    print("=" * 50)
    print("Discord Quick-Reply Tool")
    print("=" * 50)
    print("Make sure Discord message box is focused.")

    if TRIGGER_TYPE == "mouse":
        button_name = "back side button (XButton1)" if TRIGGER_VALUE == "x1" else "forward side button (XButton2)"
        print(f"Trigger: Click the {button_name}")
    else:
        print(f"Trigger: Press the '{TRIGGER_VALUE}' key")

    print("Press ESC to stop the tool.\n")

    # Safety: move mouse to any corner of the screen to stop pyautogui
    pyautogui.FAILSAFE = True

    # Start mouse listener in a separate thread
    mouse_listener = mouse.Listener(on_click=on_click)
    mouse_listener.start()

    # Start keyboard listener in main thread
    with keyboard.Listener(on_press=on_press) as keyboard_listener:
        keyboard_listener.join()

    # Stop mouse listener when ESC is pressed
    mouse_listener.stop()
    print("Tool stopped.")


if __name__ == "__main__":
    main()
