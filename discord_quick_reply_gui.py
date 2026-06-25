"""
Niply - Discord Quick-Reply Tool

A modern multi-preset Discord quick-reply automation tool.

Features:
- Create multiple reply presets
- Each preset has its own name, messages, and trigger
- Global arm/disarm hotkey
- Persistent global listeners
- Audio cues for arm/disarm/send
- Saves settings automatically to config.json

Build .exe:
    python build_gui_exe.py
"""

import customtkinter as ctk
from tkinter import messagebox
from pynput import keyboard, mouse
import pyautogui
import json
import os
import sys
import time
import threading
import winsound
import copy


# ==================== CONFIG ====================
def get_config_path():
    """Get path to config.json (works as script and as .exe)."""
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), "config.json")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def load_config():
    """Load config from JSON file."""
    path = get_config_path()
    if not os.path.exists(path):
        default = {
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
                    "modifier": "none",
                    "send_mode": "line_by_line"
                }
            ],
            "delay_between_messages": 0.8,
            "typing_delay": 0.3,
            "cooldown": 2.0
        }
        save_config(default)
        return default

    with open(path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Migrate old configs to new format
    if "presets" not in config:
        config["presets"] = [{
            "name": "Default",
            "messages": config.get("messages", ["hello"]),
            "trigger_type": config.get("trigger_type", "triple_click"),
            "trigger_value": config.get("trigger_value", "left"),
            "modifier": config.get("modifier", "none"),
            "send_mode": "line_by_line"
        }]

    # Ensure all presets have send_mode
    for preset in config.get("presets", []):
        if "send_mode" not in preset:
            preset["send_mode"] = "line_by_line"

    if "global_arm_hotkey" not in config:
        config["global_arm_hotkey"] = {
            "type": "mouse",
            "value": "x1",
            "modifier": "none"
        }

    return config


def save_config(config):
    """Save config to JSON file."""
    path = get_config_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def get_icon_path():
    """Get path to icon.ico (works as script and as .exe)."""
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), "icon.ico")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")


# ==================== KEY HELPERS ====================
MODIFIER_KEYS = {
    "ctrl": {keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r},
    "shift": {keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r},
    "alt": {keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr},
}

SPECIAL_KEYS = {
    "f1": keyboard.Key.f1, "f2": keyboard.Key.f2, "f3": keyboard.Key.f3,
    "f4": keyboard.Key.f4, "f5": keyboard.Key.f5, "f6": keyboard.Key.f6,
    "f7": keyboard.Key.f7, "f8": keyboard.Key.f8, "f9": keyboard.Key.f9,
    "f10": keyboard.Key.f10, "f11": keyboard.Key.f11, "f12": keyboard.Key.f12,
    "esc": keyboard.Key.esc, "enter": keyboard.Key.enter,
    "space": keyboard.Key.space, "tab": keyboard.Key.tab,
    "ctrl": keyboard.Key.ctrl, "shift": keyboard.Key.shift,
    "alt": keyboard.Key.alt, "cmd": keyboard.Key.cmd,
}


def parse_key(value):
    """Convert string to pynput keyboard key."""
    value = value.lower()
    if value in SPECIAL_KEYS:
        return SPECIAL_KEYS[value]
    if len(value) == 1:
        return keyboard.KeyCode.from_char(value)
    raise ValueError(f"Unknown key: {value}")


def parse_mouse_button(value):
    """Convert string to pynput mouse button."""
    value = value.lower()
    if value == "x1":
        return mouse.Button.x1
    if value == "x2":
        return mouse.Button.x2
    if value == "left":
        return mouse.Button.left
    if value == "right":
        return mouse.Button.right
    if value == "middle":
        return mouse.Button.middle
    raise ValueError(f"Unknown mouse button: {value}")


def is_modifier_held(modifier, held_keys):
    """Check if a modifier key is currently held."""
    if modifier == "none":
        return True
    keys = MODIFIER_KEYS.get(modifier, set())
    return any(k in held_keys for k in keys)


def play_sound(sound_type="arm"):
    """Play a short audio cue using Windows beep sounds."""
    try:
        if sound_type == "arm":
            winsound.Beep(1000, 150)
            time.sleep(0.05)
            winsound.Beep(1200, 150)
        elif sound_type == "disarm":
            winsound.Beep(600, 250)
        elif sound_type == "send":
            winsound.Beep(1500, 100)
    except Exception:
        pass


# ==================== PRESET WIDGET ====================
class PresetWidget(ctk.CTkFrame):
    """A single editable preset card."""

    TRIGGER_OPTIONS = {
        "triple_click": ["left"],
        "mouse": ["x1", "x2", "left", "right", "middle"],
        "keyboard": [
            "f1", "f2", "f3", "f4", "f5", "f6",
            "f7", "f8", "f9", "f10", "f11", "f12",
            "ctrl", "shift", "alt", "space", "enter"
        ]
    }

    def __init__(self, master, on_delete, on_change=None, preset=None, **kwargs):
        super().__init__(master, **kwargs)

        self.on_delete = on_delete
        self.on_change = on_change

        # Name
        self.name_entry = ctk.CTkEntry(
            self,
            placeholder_text="Preset name",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.name_entry.pack(padx=10, pady=(10, 5), fill="x")
        self.name_entry.bind("<KeyRelease>", lambda e: self._notify_change())

        # Messages
        self.messages_label = ctk.CTkLabel(
            self,
            text="Messages (one per line)",
            font=ctk.CTkFont(size=11)
        )
        self.messages_label.pack(anchor="w", padx=10)

        self.messages_text = ctk.CTkTextbox(self, height=70, font=ctk.CTkFont(size=12))
        self.messages_text.pack(padx=10, pady=2, fill="x")
        self.messages_text.bind("<KeyRelease>", lambda e: self._notify_change())

        # Trigger settings frame
        self.trigger_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.trigger_frame.pack(padx=10, pady=5, fill="x")

        self.type_var = ctk.StringVar(value="triple_click")
        self.type_menu = ctk.CTkOptionMenu(
            self.trigger_frame,
            values=["triple_click", "mouse", "keyboard"],
            variable=self.type_var,
            command=self.on_type_change,
            width=110
        )
        self.type_menu.grid(row=0, column=0, padx=2, pady=2)

        self.value_var = ctk.StringVar(value="left")
        self.value_menu = ctk.CTkOptionMenu(
            self.trigger_frame,
            values=["left"],
            variable=self.value_var,
            command=lambda x: self._notify_change(),
            width=100
        )
        self.value_menu.grid(row=0, column=1, padx=2, pady=2)

        self.modifier_var = ctk.StringVar(value="none")
        self.modifier_menu = ctk.CTkOptionMenu(
            self.trigger_frame,
            values=["none", "ctrl", "shift", "alt"],
            variable=self.modifier_var,
            command=lambda x: self._notify_change(),
            width=90
        )
        self.modifier_menu.grid(row=0, column=2, padx=2, pady=2)

        # Send mode
        self.send_mode_label = ctk.CTkLabel(
            self,
            text="Send Mode:",
            font=ctk.CTkFont(size=11)
        )
        self.send_mode_label.pack(anchor="w", padx=10, pady=(5, 0))

        self.send_mode_var = ctk.StringVar(value="line_by_line")
        self.send_mode_menu = ctk.CTkOptionMenu(
            self,
            values=["line_by_line", "block"],
            variable=self.send_mode_var,
            command=lambda x: self._notify_change(),
            width=180
        )
        self.send_mode_menu.pack(anchor="w", padx=10, pady=2)

        # Delete button
        self.delete_button = ctk.CTkButton(
            self,
            text="Delete Preset",
            command=self.delete_self,
            fg_color="darkred",
            hover_color="red",
            width=120,
            font=ctk.CTkFont(size=11)
        )
        self.delete_button.pack(padx=10, pady=(2, 10), anchor="e")

        if preset:
            self.load_preset(preset)

    def _notify_change(self):
        """Notify parent that something changed."""
        if self.on_change:
            self.on_change()

    def on_type_change(self, choice):
        """Update trigger value options."""
        values = self.TRIGGER_OPTIONS.get(choice, ["left"])
        self.value_menu.configure(values=values)
        if self.value_var.get() not in values:
            self.value_var.set(values[0])
        self._notify_change()

    def load_preset(self, preset):
        """Load preset data into UI."""
        self.name_entry.insert(0, preset.get("name", "New Preset"))
        self.messages_text.insert("1.0", "\n".join(preset.get("messages", [])))

        trigger_type = preset.get("trigger_type", "triple_click")
        self.type_var.set(trigger_type)
        self.on_type_change(trigger_type)

        trigger_value = preset.get("trigger_value", "left")
        self.value_var.set(trigger_value)

        modifier = preset.get("modifier", "none")
        self.modifier_var.set(modifier)

        send_mode = preset.get("send_mode", "line_by_line")
        self.send_mode_var.set(send_mode)

    def get_preset(self):
        """Get preset data from UI."""
        return {
            "name": self.name_entry.get().strip() or "Unnamed",
            "messages": [line.strip() for line in self.messages_text.get("1.0", "end").split("\n") if line.strip()],
            "trigger_type": self.type_var.get(),
            "trigger_value": self.value_var.get(),
            "modifier": self.modifier_var.get(),
            "send_mode": self.send_mode_var.get()
        }

    def delete_self(self):
        """Remove this preset widget."""
        self.on_delete(self)


# ==================== MAIN APP ====================
class QuickReplyApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.config_data = load_config()

        # State
        self.sending_enabled = False
        self.exiting = False
        self.last_trigger_time = {}

        # Listeners
        self.mouse_listener = None
        self.keyboard_listener = None

        # Track held keys and clicks
        self.held_keys = set()
        self.left_click_times = []
        self.triple_click_window = 0.5
        self.last_arm_hotkey_time = 0
        self.arm_hotkey_cooldown = 0.5

        self.title("Niply")
        self.geometry("850x800")
        self.resizable(False, False)

        # Set window icon
        icon_path = get_icon_path()
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.preset_widgets = []
        self.build_ui()
        self.load_settings()
        self.mark_saved()

        # Start persistent listeners immediately
        self.start_persistent_listeners()

    def build_ui(self):
        # Header
        self.header = ctk.CTkLabel(
            self,
            text="Niply",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        self.header.pack(pady=(15, 0))

        self.subheader = ctk.CTkLabel(
            self,
            text="Multi-Preset Discord Quick-Reply Automation",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.subheader.pack(pady=(0, 10))

        # Main scrollable content
        self.scroll_frame = ctk.CTkScrollableFrame(self, height=520)
        self.scroll_frame.pack(padx=15, pady=5, fill="both", expand=True)

        # Global arm hotkey section
        self.arm_frame = ctk.CTkFrame(self.scroll_frame)
        self.arm_frame.pack(padx=5, pady=5, fill="x")

        self.arm_label = ctk.CTkLabel(
            self.arm_frame,
            text="Global Arm/Disarm Hotkey",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.arm_label.grid(row=0, column=0, columnspan=4, padx=10, pady=(10, 5), sticky="w")

        self.arm_help = ctk.CTkLabel(
            self.arm_frame,
            text="Press this anywhere to enable/disable all presets",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.arm_help.grid(row=1, column=0, columnspan=4, padx=10, pady=(0, 5), sticky="w")

        self.arm_type_var = ctk.StringVar(value="mouse")
        self.arm_type_menu = ctk.CTkOptionMenu(
            self.arm_frame,
            values=["mouse", "keyboard"],
            variable=self.arm_type_var,
            command=lambda x: [self.on_arm_type_change(x), self.mark_unsaved()],
            width=110
        )
        self.arm_type_menu.grid(row=2, column=0, padx=5, pady=5)

        self.arm_value_var = ctk.StringVar(value="x1")
        self.arm_value_menu = ctk.CTkOptionMenu(
            self.arm_frame,
            values=["x1", "x2", "left", "right", "middle"],
            variable=self.arm_value_var,
            command=lambda x: self.mark_unsaved(),
            width=100
        )
        self.arm_value_menu.grid(row=2, column=1, padx=5, pady=5)

        self.arm_modifier_var = ctk.StringVar(value="none")
        self.arm_modifier_menu = ctk.CTkOptionMenu(
            self.arm_frame,
            values=["none", "ctrl", "shift", "alt"],
            variable=self.arm_modifier_var,
            command=lambda x: self.mark_unsaved(),
            width=90
        )
        self.arm_modifier_menu.grid(row=2, column=2, padx=5, pady=5)

        # Presets section
        self.presets_label = ctk.CTkLabel(
            self.scroll_frame,
            text="Reply Presets",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.presets_label.pack(anchor="w", padx=5, pady=(15, 5))

        self.presets_container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.presets_container.pack(padx=5, pady=5, fill="x")

        self.add_preset_button = ctk.CTkButton(
            self.scroll_frame,
            text="+ Add Preset",
            command=self.add_preset,
            width=150,
            font=ctk.CTkFont(size=13)
        )
        self.add_preset_button.pack(padx=5, pady=5, anchor="w")

        # Global delays section
        self.delays_frame = ctk.CTkFrame(self.scroll_frame)
        self.delays_frame.pack(padx=5, pady=10, fill="x")

        self.delay_label = ctk.CTkLabel(
            self.delays_frame,
            text="Delay Between Messages:",
            font=ctk.CTkFont(size=12)
        )
        self.delay_label.grid(row=0, column=0, padx=10, pady=8, sticky="w")

        self.delay_entry = ctk.CTkEntry(self.delays_frame, width=70, font=ctk.CTkFont(size=12))
        self.delay_entry.grid(row=0, column=1, padx=5, pady=8, sticky="w")
        self.delay_entry.bind("<KeyRelease>", lambda e: self.mark_unsaved())

        self.typing_delay_label = ctk.CTkLabel(
            self.delays_frame,
            text="Typing Delay:",
            font=ctk.CTkFont(size=12)
        )
        self.typing_delay_label.grid(row=1, column=0, padx=10, pady=8, sticky="w")

        self.typing_delay_entry = ctk.CTkEntry(self.delays_frame, width=70, font=ctk.CTkFont(size=12))
        self.typing_delay_entry.grid(row=1, column=1, padx=5, pady=8, sticky="w")
        self.typing_delay_entry.bind("<KeyRelease>", lambda e: self.mark_unsaved())

        self.cooldown_label = ctk.CTkLabel(
            self.delays_frame,
            text="Cooldown:",
            font=ctk.CTkFont(size=12)
        )
        self.cooldown_label.grid(row=2, column=0, padx=10, pady=8, sticky="w")

        self.cooldown_entry = ctk.CTkEntry(self.delays_frame, width=70, font=ctk.CTkFont(size=12))
        self.cooldown_entry.grid(row=2, column=1, padx=5, pady=8, sticky="w")
        self.cooldown_entry.bind("<KeyRelease>", lambda e: self.mark_unsaved())

        # Save status label
        self.save_status_label = ctk.CTkLabel(
            self.scroll_frame,
            text="Saved",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="green"
        )
        self.save_status_label.pack(padx=5, pady=5, anchor="e")

        # Bottom buttons
        self.buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.buttons_frame.pack(padx=15, pady=5, fill="x")

        self.save_button = ctk.CTkButton(
            self.buttons_frame,
            text="Save Settings",
            command=self.save_settings,
            width=160,
            height=35,
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.save_button.pack(side="left", padx=5)

        self.arm_button = ctk.CTkButton(
            self.buttons_frame,
            text="Arm",
            command=self.arm_tool,
            width=140,
            fg_color="green",
            hover_color="darkgreen",
            font=ctk.CTkFont(size=13)
        )
        self.arm_button.pack(side="left", padx=5)

        self.disarm_button = ctk.CTkButton(
            self.buttons_frame,
            text="Disarm",
            command=self.disarm_tool,
            width=140,
            fg_color="red",
            hover_color="darkred",
            font=ctk.CTkFont(size=13),
            state="disabled"
        )
        self.disarm_button.pack(side="left", padx=5)

        # Status
        self.status_label = ctk.CTkLabel(
            self,
            text="Status: Disarmed",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="red"
        )
        self.status_label.pack(pady=2)

        # Log
        self.log_area = ctk.CTkTextbox(
            self,
            height=80,
            font=ctk.CTkFont(size=11),
            state="disabled"
        )
        self.log_area.pack(padx=15, pady=2, fill="x")

        self.safety_label = ctk.CTkLabel(
            self,
            text="Move mouse to corner to stop typing | ESC closes app",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.safety_label.pack(pady=(0, 5))

    def on_arm_type_change(self, choice):
        """Update arm hotkey value options."""
        if choice == "mouse":
            self.arm_value_menu.configure(values=["x1", "x2", "left", "right", "middle"])
            if self.arm_value_var.get() not in ["x1", "x2", "left", "right", "middle"]:
                self.arm_value_var.set("x1")
        else:
            self.arm_value_menu.configure(values=[
                "f1", "f2", "f3", "f4", "f5", "f6",
                "f7", "f8", "f9", "f10", "f11", "f12",
                "ctrl", "shift", "alt", "space", "enter"
            ])
            if self.arm_value_var.get() in ["x1", "x2", "left", "right", "middle"]:
                self.arm_value_var.set("f9")

    def add_preset(self, preset=None):
        """Add a new preset widget."""
        widget = PresetWidget(
            self.presets_container,
            on_delete=self.remove_preset,
            on_change=self.mark_unsaved,
            preset=preset,
            fg_color="#1e293b"
        )
        widget.pack(padx=5, pady=5, fill="x")
        self.preset_widgets.append(widget)
        self.mark_unsaved()
        self.scroll_frame.update_idletasks()
        self.scroll_frame._parent_canvas.yview_moveto(1.0)

    def remove_preset(self, widget):
        """Remove a preset widget."""
        if len(self.preset_widgets) <= 1:
            messagebox.showwarning("Warning", "You must have at least one preset.")
            return
        widget.destroy()
        self.preset_widgets.remove(widget)
        self.mark_unsaved()

    def load_settings(self):
        """Load config into UI."""
        # Global arm hotkey
        arm = self.config_data.get("global_arm_hotkey", {})
        arm_type = arm.get("type", "mouse")
        self.arm_type_var.set(arm_type)
        self.on_arm_type_change(arm_type)
        self.arm_value_var.set(arm.get("value", "x1"))
        self.arm_modifier_var.set(arm.get("modifier", "none"))

        # Delays
        self.delay_entry.insert(0, str(self.config_data.get("delay_between_messages", 0.8)))
        self.typing_delay_entry.insert(0, str(self.config_data.get("typing_delay", 0.3)))
        self.cooldown_entry.insert(0, str(self.config_data.get("cooldown", 2.0)))

        # Presets
        for preset in self.config_data.get("presets", []):
            self.add_preset(preset)

    def save_settings(self, silent=False):
        """Save settings to config.json."""
        try:
            presets = []
            for widget in self.preset_widgets:
                preset = widget.get_preset()
                if not preset["messages"]:
                    if not silent:
                        messagebox.showerror("Error", f"Preset '{preset['name']}' has no messages.")
                    return False
                presets.append(preset)

            if not presets:
                if not silent:
                    messagebox.showerror("Error", "Please add at least one preset.")
                return False

            config = {
                "global_arm_hotkey": {
                    "type": self.arm_type_var.get(),
                    "value": self.arm_value_var.get(),
                    "modifier": self.arm_modifier_var.get()
                },
                "presets": presets,
                "delay_between_messages": float(self.delay_entry.get()),
                "typing_delay": float(self.typing_delay_entry.get()),
                "cooldown": float(self.cooldown_entry.get())
            }

            save_config(config)
            self.config_data = config
            self.mark_saved()
            self.log("Settings saved!")
            return True

        except ValueError:
            self.mark_unsaved()
            if not silent:
                messagebox.showerror("Error", "Please enter valid numbers for delays.")
            return False

    def log(self, message):
        """Add a message to the log area."""
        self.log_area.configure(state="normal")
        self.log_area.insert("end", f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_area.see("end")
        self.log_area.configure(state="disabled")

    def mark_unsaved(self):
        """Show unsaved changes indicator."""
        if hasattr(self, "save_status_label"):
            self.save_status_label.configure(text="Unsaved changes", text_color="orange")

    def mark_saved(self):
        """Show saved indicator."""
        if hasattr(self, "save_status_label"):
            self.save_status_label.configure(text="Saved", text_color="green")

    # ==================== LISTENERS ====================
    def start_persistent_listeners(self):
        """Start global listeners."""
        pyautogui.FAILSAFE = True

        self.mouse_listener = mouse.Listener(on_click=self.on_mouse_click)
        self.mouse_listener.start()

        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
        self.keyboard_listener.start()

        self.log("Listeners active. Arm to enable presets.")

    def stop_persistent_listeners(self):
        """Stop global listeners."""
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None

    def is_arm_hotkey(self, button_or_key, is_mouse):
        """Check if input matches global arm/disarm hotkey."""
        hotkey = self.config_data.get("global_arm_hotkey", {})
        hk_type = hotkey.get("type", "mouse")
        hk_value = hotkey.get("value", "x1")
        hk_modifier = hotkey.get("modifier", "none")

        if is_mouse and hk_type != "mouse":
            return False
        if not is_mouse and hk_type != "keyboard":
            return False

        try:
            target = parse_mouse_button(hk_value) if is_mouse else parse_key(hk_value)
        except ValueError:
            return False

        return button_or_key == target and is_modifier_held(hk_modifier, self.held_keys)

    def find_matching_preset(self, button_or_key, is_mouse):
        """Find which preset matches a mouse or keyboard trigger (not triple-click)."""
        if not self.sending_enabled:
            return None

        for preset in self.config_data.get("presets", []):
            trigger_type = preset.get("trigger_type", "triple_click")
            trigger_value = preset.get("trigger_value", "left")
            modifier = preset.get("modifier", "none")

            # Triple-click presets are handled separately
            if trigger_type == "triple_click":
                continue

            if trigger_type == "mouse":
                if not is_mouse:
                    continue
                try:
                    target = parse_mouse_button(trigger_value)
                except ValueError:
                    continue
                if button_or_key == target and is_modifier_held(modifier, self.held_keys):
                    return preset

            elif trigger_type == "keyboard":
                if is_mouse:
                    continue
                try:
                    target = parse_key(trigger_value)
                except ValueError:
                    continue
                # For keyboard triggers, check modifier if configured
                if button_or_key == target and is_modifier_held(modifier, self.held_keys):
                    return preset

        return None

    def find_triple_click_preset(self):
        """Find the first triple-click preset."""
        if not self.sending_enabled:
            return None
        for preset in self.config_data.get("presets", []):
            if preset.get("trigger_type") == "triple_click":
                return preset
        return None

    def detect_triple_click(self):
        """Check for triple left click."""
        now = time.time()
        self.left_click_times = [t for t in self.left_click_times if now - t < self.triple_click_window]
        self.left_click_times.append(now)
        return len(self.left_click_times) >= 3

    def on_mouse_click(self, x, y, button, pressed):
        """Handle mouse clicks."""
        if not pressed or self.exiting:
            return

        # Arm/disarm hotkey
        if self.is_arm_hotkey(button, is_mouse=True):
            now = time.time()
            if now - self.last_arm_hotkey_time >= self.arm_hotkey_cooldown:
                self.last_arm_hotkey_time = now
                self.toggle_arm()
            return

        if not self.sending_enabled:
            return

        # Triple-click detection (only for left button)
        if button == mouse.Button.left:
            if self.detect_triple_click():
                self.left_click_times.clear()
                preset = self.find_triple_click_preset()
                if preset:
                    self.send_messages(preset)
            # Single left click does nothing - don't fall through
            return

        # Other mouse triggers (side buttons, right, middle)
        preset = self.find_matching_preset(button, is_mouse=True)
        if preset:
            self.send_messages(preset)

    def on_key_press(self, key):
        """Handle keyboard presses."""
        if self.exiting:
            return

        self.held_keys.add(key)

        if key == keyboard.Key.esc:
            self.log("ESC pressed. Closing...")
            self.close_app()
            return False

        # Arm/disarm hotkey
        if self.is_arm_hotkey(key, is_mouse=False):
            now = time.time()
            if now - self.last_arm_hotkey_time >= self.arm_hotkey_cooldown:
                self.last_arm_hotkey_time = now
                self.toggle_arm()
            return

        if not self.sending_enabled:
            return

        preset = self.find_matching_preset(key, is_mouse=False)
        if preset:
            self.send_messages(preset)

    def on_key_release(self, key):
        """Handle keyboard releases."""
        self.held_keys.discard(key)

    # ==================== ARM/DISARM ====================
    def arm_tool(self):
        """Arm the tool."""
        threading.Thread(target=self.save_settings, args=(True,), daemon=True).start()
        self.sending_enabled = True
        self.update_status()
        self.log("ARMED - All presets active")
        threading.Thread(target=play_sound, args=("arm",), daemon=True).start()

    def disarm_tool(self):
        """Disarm the tool."""
        self.sending_enabled = False
        self.left_click_times.clear()
        self.update_status()
        self.log("DISARMED - All presets inactive")
        threading.Thread(target=play_sound, args=("disarm",), daemon=True).start()

    def toggle_arm(self):
        """Toggle armed state."""
        if self.sending_enabled:
            self.disarm_tool()
        else:
            self.arm_tool()

    def update_status(self):
        """Update status UI."""
        if self.sending_enabled:
            self.status_label.configure(text="Status: ARMED", text_color="green")
            self.arm_button.configure(state="disabled")
            self.disarm_button.configure(state="normal")
        else:
            self.status_label.configure(text="Status: Disarmed", text_color="red")
            self.arm_button.configure(state="normal")
            self.disarm_button.configure(state="disabled")

    # ==================== SEND MESSAGES ====================
    def send_messages(self, preset):
        """Type the preset's messages."""
        preset_name = preset.get("name", "Unnamed")
        cooldown = self.config_data.get("cooldown", 2.0)
        last_time = self.last_trigger_time.get(preset_name, 0)

        current_time = time.time()
        if current_time - last_time < cooldown:
            self.log(f"Cooldown: {preset_name}")
            return

        self.last_trigger_time[preset_name] = current_time
        messages = preset.get("messages", [])
        send_mode = preset.get("send_mode", "line_by_line")

        self.log(f"Sending '{preset_name}' ({len(messages)} lines, {send_mode})...")

        time.sleep(self.config_data.get("typing_delay", 0.3))

        if send_mode == "block":
            # Send all lines at once as one message with line breaks
            block_text = "\n".join(messages)
            pyautogui.typewrite(block_text, interval=0.01)
            pyautogui.press("enter")
            self.log(f"Sent block: {preset_name}")
        else:
            # Send line by line
            for i, msg in enumerate(messages):
                pyautogui.typewrite(msg, interval=0.01)
                pyautogui.press("enter")
                self.log(f"Sent ({i + 1}/{len(messages)}): {msg}")
                if i < len(messages) - 1:
                    time.sleep(self.config_data.get("delay_between_messages", 0.8))

        self.log(f"'{preset_name}' done!")
        threading.Thread(target=play_sound, args=("send",), daemon=True).start()

    # ==================== APP LIFECYCLE ====================
    def close_app(self):
        """Close the app."""
        self.exiting = True
        self.sending_enabled = False
        self.stop_persistent_listeners()
        self.destroy()

    def on_closing(self):
        """Handle window close."""
        self.close_app()


def main():
    app = QuickReplyApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
