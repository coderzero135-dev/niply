# Niply - Discord Quick-Reply Tool

Niply is a modern desktop app that lets you create multiple Discord message presets and send them with custom shortcuts. Built for support teams, moderators, or anyone who needs to send repetitive messages quickly.

## Features

- **Multiple Reply Presets**: Create unlimited presets with custom names, messages, and triggers
- **Custom Triggers**: Use keyboard keys, mouse side buttons, or triple-click
- **Global Arm/Disarm Hotkey**: Enable/disable all presets with one button
- **Persistent Listeners**: Runs in the background without stopping when idle
- **Audio Cues**: Beep sounds for arm/disarm/send actions
- **Modern GUI**: Clean dark interface built with customtkinter
- **No Discord Bot Required**: Works as a user-side automation tool

## Download

Download the latest `Niply.exe` from the [Releases](../../releases) page.

## How to Use

1. Run `Niply.exe`
2. Configure your reply presets in the app
3. Set a global arm/disarm hotkey (default: back side mouse button)
4. Click **Save Settings**
5. Click **Arm** or press your arm hotkey
6. Use your preset triggers in Discord

## Building from Source

### Requirements

- Python 3.10+
- Windows

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run

```bash
python discord_quick_reply_gui.py
```

### Build Executable

```bash
python build_gui_exe.py
```

The `.exe` will be in the `dist/` folder.

## Configuration

Settings are saved to `config.json` in the same folder as the app. You can edit it directly or use the GUI.

Example config:

```json
{
  "global_arm_hotkey": {
    "type": "mouse",
    "value": "x1",
    "modifier": "none"
  },
  "presets": [
    {
      "name": "Ticket Reply",
      "messages": [
        "hey whats the issue",
        "*checker",
        "send screenshot of checker tool"
      ],
      "trigger_type": "triple_click",
      "trigger_value": "left",
      "modifier": "none"
    }
  ],
  "delay_between_messages": 0.8,
  "typing_delay": 0.3,
  "cooldown": 2.0
}
```

## Disclaimer

This tool uses your mouse and keyboard to type messages. Only use it in servers/channels where you have permission to send automated messages. The developers are not responsible for any misuse or Discord account actions.

## License

MIT License
