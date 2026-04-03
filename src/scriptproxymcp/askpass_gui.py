#!/usr/bin/env python3
"""
SUDO_ASKPASS GUI Script for ScriptProxyMCP

Displays a GUI dialog for sudo password input, showing the command being executed
along with risk assessment information from sampling analysis.
Used by setting SUDO_ASKPASS environment variable to this script's path.

Environment variables:
    SUDO_COMMAND: The command being executed
    SCRIPTPROXY_SUDO_COMMAND: ScriptProxy command preview for askpass
    SCRIPTPROXY_RISK: Risk level (low/medium/high/unknown)
    SCRIPTPROXY_PURPOSE: Purpose description from sampling
    SCRIPTPROXY_DESCRIPTION: Detailed description from sampling
    TEST_SUDO_PASSWORD: Test password for headless testing
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk


class SudoPasswordDialog:
    def __init__(self):
        self.result = None
        self.command = os.environ.get(
            "SCRIPTPROXY_SUDO_COMMAND",
            os.environ.get("SUDO_COMMAND", "Unknown command"),
        )
        self.risk = os.environ.get("SCRIPTPROXY_RISK", "unknown")
        self.purpose = os.environ.get("SCRIPTPROXY_PURPOSE", "")
        self.description = os.environ.get("SCRIPTPROXY_DESCRIPTION", "")

        # Create main window
        self.root = tk.Tk()
        self.root.title("Sudo Authentication")
        self.root.resizable(False, False)

        # Center the window
        self.root.eval("tk::PlaceWindow . center")

        # Make it modal
        self.root.attributes("-topmost", True)
        self.root.focus_force()

        self.setup_ui()

    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Icon/Title
        title_label = ttk.Label(
            main_frame,
            text="Authentication Required",
            font=("Helvetica", 14, "bold"),
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))

        # Risk indicator
        risk_colors = {
            "low": "#4CAF50",
            "medium": "#FF9800",
            "high": "#F44336",
            "unknown": "#9E9E9E",
        }
        risk_color = risk_colors.get(self.risk.lower(), "#9E9E9E")
        risk_label = ttk.Label(
            main_frame,
            text=f"Risk: {self.risk.upper()}",
            font=("Helvetica", 12, "bold"),
            foreground=risk_color,
        )
        risk_label.grid(row=1, column=0, columnspan=2, pady=(0, 10))

        # Purpose description (if available)
        if self.purpose or self.description:
            info_text = self.purpose or self.description
            info_frame = ttk.LabelFrame(main_frame, text="Analysis:", padding="10")
            info_frame.grid(row=2, column=0, columnspan=2, sticky="we", pady=(0, 10))
            info_label = ttk.Label(
                info_frame,
                text=info_text,
                wraplength=400,
                justify=tk.LEFT,
            )
            info_label.grid(row=0, column=0, sticky=tk.W)

        # Command display
        cmd_frame = ttk.LabelFrame(main_frame, text="Command to execute:", padding="10")
        cmd_frame.grid(row=3, column=0, columnspan=2, sticky="we", pady=(0, 15))

        cmd_text = tk.Text(
            cmd_frame,
            height=2,
            width=50,
            wrap=tk.WORD,
            font=("Courier", 9),
            state="normal",
        )
        cmd_text.insert("1.0", self.command)
        cmd_text.config(state="disabled")
        cmd_text.grid(row=0, column=0)

        # Password label
        pwd_label = ttk.Label(main_frame, text="Password:")
        pwd_label.grid(row=4, column=0, sticky=tk.W, pady=(0, 5))

        # Password entry
        self.pwd_entry = ttk.Entry(main_frame, show="*", width=30)
        self.pwd_entry.grid(row=5, column=0, columnspan=2, sticky="we", pady=(0, 20))
        self.pwd_entry.focus()

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2)

        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.cancel)
        cancel_btn.grid(row=0, column=0, padx=(0, 10))

        ok_btn = ttk.Button(button_frame, text="OK", command=self.ok, default=tk.ACTIVE)
        ok_btn.grid(row=0, column=1)

        # Bind Enter key to OK
        self.root.bind("<Return>", lambda e: self.ok())
        self.root.bind("<Escape>", lambda e: self.cancel())

        # Bind events
        self.pwd_entry.bind("<Return>", lambda e: self.ok())

    def ok(self):
        password = self.pwd_entry.get()
        if not password:
            messagebox.showerror("Error", "Password cannot be empty")
            return

        self.result = password
        self.root.quit()

    def cancel(self):
        self.result = None
        self.root.quit()

    def run(self):
        self.root.mainloop()
        self.root.destroy()
        return self.result


def main():
    # Check for test password first (for headless testing)
    test_password = os.environ.get("TEST_SUDO_PASSWORD")
    if test_password:
        print(test_password)
        sys.exit(0)

    # Check if we have a display for GUI
    display = os.environ.get("DISPLAY")
    if display:
        try:
            dialog = SudoPasswordDialog()
            password = dialog.run()
        except Exception as e:
            # Fallback to terminal input if GUI fails
            print(
                f"GUI failed ({e}), falling back to terminal input",
                file=sys.stderr,
            )
            password = get_password_terminal()
    else:
        # No display, use terminal
        password = get_password_terminal()

    if password:
        print(password)
        sys.exit(0)
    else:
        sys.exit(1)


def get_password_terminal():
    """Fallback password input for headless environments."""
    import getpass

    try:
        return getpass.getpass("Password: ")
    except KeyboardInterrupt:
        return None


if __name__ == "__main__":
    main()
