#!/usr/bin/env python3
"""Fix icon display: clear cache, delete old shortcut, create new one with icon.ico directly."""

import os
import subprocess
import sys
from pathlib import Path


def run_ps(script):
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def main():
    here = Path(__file__).resolve().parent
    exe = here / "dist" / "MiniImageResizer.exe"
    icon = here / "assets" / "icon.ico"

    if not exe.is_file():
        print(f"ERROR: EXE not found: {exe}")
        sys.exit(1)

    if not icon.is_file():
        print(f"ERROR: Icon not found: {icon}")
        sys.exit(1)

    # Step 1: Clear Windows icon cache
    print("Step 1: Clearing Windows icon cache...")
    cache_script = """
    # Stop Windows Explorer temporarily
    taskkill /F /IM explorer.exe 2>$null
    # Clear icon cache files
    Remove-Item "$env:LOCALAPPDATA\\Microsoft\\Windows\\Icons\\*" -Force -Recurse -ErrorAction SilentlyContinue
    Remove-Item "$env:LOCALAPPDATA\\IconCache.db" -Force -ErrorAction SilentlyContinue
    Remove-Item "$env:APPDATA\\Microsoft\\Windows\\Recent\\CustomIcons.db" -Force -ErrorAction SilentlyContinue
    # Restart Explorer
    Start-Process "explorer.exe"
    """
    run_ps(cache_script)
    print("  Icon cache cleared.")

    # Step 2: Delete old shortcut
    desktop = Path(os.environ["USERPROFILE"]) / "Desktop"
    shortcut = desktop / "Mini Image Resizer.lnk"
    if shortcut.exists():
        print(f"Step 2: Deleting old shortcut: {shortcut}")
        shortcut.unlink()
        print("  Old shortcut deleted.")
    else:
        print("Step 2: No existing shortcut found.")

    # Step 3: Create new shortcut with icon.ico directly
    print("Step 3: Creating new shortcut with icon.ico directly...")
    ps_script = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut}")
$Shortcut.TargetPath = "{exe}"
$Shortcut.WorkingDirectory = "{exe.parent}"
$Shortcut.IconLocation = "{icon}"
$Shortcut.Save()
Write-Host "Shortcut created successfully"
'''
    rc, out, err = run_ps(ps_script)
    if rc != 0:
        print(f"Failed to create shortcut: {err}")
        sys.exit(1)
    print(f"  Shortcut created: {shortcut}")
    print(f"  Target: {exe}")
    print(f"  Icon: {icon} (direct .ico file)")

    # Step 4: Verify shortcut
    print("\nStep 4: Verifying shortcut...")
    verify_script = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut}")
Write-Host "Target:" $Shortcut.TargetPath
Write-Host "Icon:" $Shortcut.IconLocation
Write-Host "WorkingDir:" $Shortcut.WorkingDirectory
'''
    rc, out, err = run_ps(verify_script)
    print(out)
    if err:
        print(f"Errors: {err}")

    print("\nDone. If the icon still shows as Python, the icon.ico file itself may be the Python logo.")
    print("Please check the icon.ico file at:", icon)


if __name__ == "__main__":
    main()