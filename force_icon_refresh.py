#!/usr/bin/env python3
"""Force icon refresh: delete all caches, recreate shortcut, verify."""

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

    print("=" * 60)
    print("FORCING ICON REFRESH")
    print("=" * 60)

    # Step 1: Kill Explorer to release icon cache
    print("\n[1] Stopping Explorer...")
    run_ps("taskkill /F /IM explorer.exe 2>$null")
    print("  Explorer stopped.")

    # Step 2: Delete ALL icon caches
    print("\n[2] Deleting all icon caches...")
    cache_paths = [
        "$env:LOCALAPPDATA\\Microsoft\\Windows\\Icons",
        "$env:LOCALAPPDATA\\IconCache.db",
        "$env:APPDATA\\Microsoft\\Windows\\Recent\\CustomIcons.db",
        "$env:LOCALAPPDATA\\Microsoft\\Windows\\Explorer",
    ]
    for path in cache_paths:
        ps = f'''
        try {{
            if (Test-Path "{path}") {{
                Get-ChildItem -Path "{path}" -Force -Recurse -ErrorAction SilentlyContinue | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
                Write-Host "Cleared: {path}"
            }}
        }} catch {{
            Write-Host "Failed: {path} - $_"
        }}
        '''
        run_ps(ps)

    # Step 3: Delete all shortcuts
    print("\n[3] Deleting all shortcuts...")
    desktop = Path(os.environ["USERPROFILE"]) / "Desktop"
    for f in desktop.glob("*.lnk"):
        if "mini" in f.name.lower() or "image" in f.name.lower() or "resizer" in f.name.lower():
            print(f"  Deleting: {f}")
            f.unlink()

    # Also check Start Menu
    start_menu = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu"
    for root, dirs, files in os.walk(start_menu):
        for f in files:
            if f.lower().endswith('.lnk') and ('mini' in f.lower() or 'image' in f.lower() or 'resizer' in f.lower()):
                fpath = Path(root) / f
                print(f"  Deleting Start Menu: {fpath}")
                fpath.unlink()

    # Step 4: Create fresh shortcut with icon.ico
    print("\n[4] Creating fresh shortcut...")
    shortcut = desktop / "Mini Image Resizer.lnk"
    ps_script = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut}")
$Shortcut.TargetPath = "{exe}"
$Shortcut.WorkingDirectory = "{exe.parent}"
$Shortcut.IconLocation = "{icon}"
$Shortcut.Save()
Write-Host "Shortcut created: {shortcut}"
'''
    rc, out, err = run_ps(ps_script)
    if rc != 0:
        print(f"Failed: {err}")
        sys.exit(1)
    print(out)

    # Step 5: Verify shortcut
    print("\n[5] Verifying shortcut...")
    verify_script = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut}")
Write-Host "Target:" $Shortcut.TargetPath
Write-Host "Icon:" $Shortcut.IconLocation
Write-Host "WorkingDir:" $Shortcut.WorkingDirectory
'''
    rc, out, err = run_ps(verify_script)
    print(out)

    # Step 6: Restart Explorer
    print("\n[6] Restarting Explorer...")
    run_ps("Start-Process explorer.exe")
    print("  Explorer restarted.")

    # Step 7: Run ie4uinit to refresh icon cache
    print("\n[7] Running ie4uinit.exe -ClearIconCache...")
    rc, out, err = run_ps("ie4uinit.exe -ClearIconCache")
    if rc != 0:
        print(f"  Note: ie4uinit returned {rc}")
    else:
        print("  Icon cache refreshed.")

    print("\n" + "=" * 60)
    print("DONE - Check Desktop for 'Mini Image Resizer.lnk'")
    print("=" * 60)


if __name__ == "__main__":
    main()