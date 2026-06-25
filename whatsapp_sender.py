"""
WhatsApp Message Sender

Use this responsibly and ONLY with the recipient's consent.
Repeated unsolicited messages can be considered harassment.

How to use:
1. Install requirements: pip install -r requirements.txt
2. Open WhatsApp Web (https://web.whatsapp.com) in your browser
3. Open the chat you want to message
4. Run this script: python whatsapp_sender.py
5. When it says "Click in WhatsApp message box and press Enter..."
   click inside the WhatsApp message input area
6. Press Enter in this terminal to start sending
"""

import pyautogui
import time
import random

# Safety feature: move mouse to any corner of the screen to instantly stop pyautogui
pyautogui.FAILSAFE = True


def get_user_input():
    """Get message and count from user, with default values pre-filled."""
    default_message = "I love you CHOTU"
    default_count = 100

    print(f"Default message: \"{default_message}\"")
    message = input(f"Press Enter to use default, or type a new message: ").strip()
    if not message:
        message = default_message

    while True:
        count_input = input(f"Press Enter to send {default_count} times, or type a number: ").strip()
        if not count_input:
            count = default_count
            break
        try:
            count = int(count_input)
            if count <= 0:
                print("Please enter a number greater than 0.")
                continue
            if count > 500:
                confirm = input(f"That's a lot of messages ({count}). Are you sure? (yes/no): ").strip().lower()
                if confirm != "yes":
                    continue
            break
        except ValueError:
            print("Please enter a valid number.")

    return message, count


def wait_for_ready():
    """Wait until user has focused WhatsApp and pressed Enter."""
    print("\n" + "=" * 50)
    print("IMPORTANT:")
    print("1. Click on your WhatsApp Web window")
    print("2. Click inside the message input box (where you normally type)")
    print("3. Come back here and press ENTER to start")
    print("=" * 50)
    input("\nPress Enter when WhatsApp is ready...")
    print("\nSending messages now! Press Ctrl+C to stop.\n")


def send_messages(message, count):
    """Type and send messages using pyautogui."""
    try:
        for i in range(1, count + 1):
            pyautogui.typewrite(message, interval=0.01)
            pyautogui.press("enter")
            print(f"Sent {i}/{count}")

            # Small random delay to avoid looking too robotic
            time.sleep(random.uniform(0.3, 0.8))

        print("\nAll messages sent!")
    except KeyboardInterrupt:
        print("\nStopped by user.")


def main():
    print("=" * 50)
    print("WhatsApp Message Sender")
    print("=" * 50)
    print("NOTE: Only use this with the recipient's consent.\n")

    message, count = get_user_input()
    wait_for_ready()
    send_messages(message, count)


if __name__ == "__main__":
    main()
