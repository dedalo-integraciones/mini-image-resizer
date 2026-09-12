#!/usr/bin/env python3
"""Create or update the Desktop shortcut for MiniImageResizer using PowerShell."""

import os
import subprocess
import sys
from pathlib import Path


def main():
    here = Path(__file__).resolve().parent
    exe = here / "dist" / "MiniImageResizer.exe"
    icon = here / "assets" / "icon.ico"
    if not exe.is_file():
        print(f"ERROR: EXE not found: {exe}")
        sys.exit(1)

    # Target locations for shortcut
    desktop = Path(os.environ["USERPROFILE"]) / "Desktop"
    shortcut = desktop / "Mini Image Resizer.lnk"

    # Use PowerShell to create/update shortcut
    ps_script = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut}")
$Shortcut.TargetPath = "{exe}"
$Shortcut.WorkingDirectory = "{exe.parent}"
$Shortcut.IconLocation = "{exe}"
$Shortcut.Save()
'''
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_script],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Failed to create shortcut: {result.stderr}")
        sys.exit(1)

    print(f"Shortcut updated: {shortcut}")
    print(f"  Target: {exe}")
    print(f"  Icon: {exe} (embedded icon)")
    print("If the icon still does not appear, try refreshing the icon cache:")
    print("  1. Close all Explorer windows")
    print("  2. Run: ie4uinit.exe -ClearIconCache")
    print("  3. Restart Explorer or log off/on")


if __name__ == "__main__":
    main()