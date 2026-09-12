#!/usr/bin/env python3
"""Diagnose icon issue: check icon file, shortcut, and fix."""

import os
import struct
import subprocess
import sys
from pathlib import Path


def run_ps(script):
    return subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        capture_output=True,
        text=True,
    )


def check_icon_ico(icon_path):
    """Check if icon.ico is actually a Python logo or custom."""
    from PIL import Image
    img = Image.open(icon_path)
    print(f"Icon file: {icon_path}")
    print(f"  Size: {img.size}")
    print(f"  Format: {img.format}")
    print(f"  Mode: {img.mode}")

    # Save as PNG for inspection
    png_path = icon_path.with_suffix('.png')
    img.save(png_path)
    print(f"  Saved PNG for inspection: {png_path}")

    # Check if it looks like Python logo (typically blue/yellow snake)
    # Convert to RGB and analyze colors
    rgb_img = img.convert('RGB')
    pixels = list(rgb_img.getdata())
    colors = {}
    for p in pixels:
        key = p
        colors[key] = colors.get(key, 0) + 1

    top_colors = sorted(colors.items(), key=lambda x: x[1], reverse=True)[:10]
    print("  Top colors:")
    for color, count in top_colors:
        percentage = count / len(pixels) * 100
        print(f"    RGB{color}: {percentage:.1f}%")

    # Python logo typically has specific colors
    # Check for Python blue (#306998) or yellow (#FFD43B)
    python_blue = (48, 105, 152)
    python_yellow = (255, 212, 59)
    has_blue = any(abs(c[0] - python_blue[0]) < 20 and abs(c[1] - python_blue[1]) < 20 and abs(c[2] - python_blue[2]) < 20 for c, _ in top_colors[:5])
    has_yellow = any(abs(c[0] - python_yellow[0]) < 20 and abs(c[1] - python_yellow[1]) < 20 and abs(c[2] - python_yellow[2]) < 20 for c, _ in top_colors[:5])

    if has_blue or has_yellow:
        print("  WARNING: Colors resemble Python logo!")
    else:
        print("  Colors do NOT match Python logo pattern.")


def check_shortcut_icon(shortcut_path):
    """Check what icon the shortcut is using."""
    print(f"\nShortcut: {shortcut_path}")
    if not os.path.exists(shortcut_path):
        print("  Not found!")
        return

    with open(shortcut_path, 'rb') as f:
        data = f.read()

    text = data.decode('utf-16-le', errors='ignore')
    lines = [l.strip() for l in text.split('\x00') if l.strip()]

    # Look for paths
    print("  Content snippets:")
    for line in lines:
        if any(ext in line.lower() for ext in ['.exe', '.ico', '.png', '.lnk', ':', '\\']):
            if len(line) < 500:
                print(f"    {line}")


def main():
    here = Path(__file__).resolve().parent
    exe = here / "dist" / "MiniImageResizer.exe"
    icon = here / "assets" / "icon.ico"
    desktop = Path(os.environ["USERPROFILE"]) / "Desktop"
    shortcut = desktop / "Mini Image Resizer.lnk"

    if not exe.is_file():
        print(f"ERROR: EXE not found: {exe}")
        sys.exit(1)

    if not icon.is_file():
        print(f"ERROR: Icon not found: {icon}")
        sys.exit(1)

    print("=" * 50)
    print("ICON DIAGNOSTIC")
    print("=" * 50)

    # Step 1: Check icon.ico contents
    print("\n[1] Checking icon.ico contents...")
    check_icon_ico(str(icon))

    # Step 2: Check shortcut contents
    print("\n[2] Checking shortcut contents...")
    check_shortcut_icon(str(shortcut))

    # Step 3: Check EXE icon
    print("\n[3] Checking EXE embedded icons...")
    rc, out, err = run_ps(f"powershell -Command \"(Get-Item '{exe}').Length\"")
    print(f"  EXE size: {out.strip()} bytes")

    # Step 4: Delete old shortcut and create new one with unique icon name
    print("\n[4] Creating new shortcut with unique icon name...")
    new_icon = here / "assets" / "app_icon.ico"
    import shutil
    shutil.copy2(str(icon), str(new_icon))
    print(f"  Copied icon to: {new_icon}")

    # Delete old shortcut
    if shortcut.exists():
        shortcut.unlink()
        print("  Deleted old shortcut")

    # Also delete any cached shortcut with different name
    for f in desktop.glob("*.lnk"):
        if "mini" in f.name.lower() or "image" in f.name.lower():
            print(f"  Deleting: {f}")
            f.unlink()

    # Create new shortcut using new icon name
    ps_script = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{desktop / 'MiniImageResizer_App.lnk'}")
$Shortcut.TargetPath = "{exe}"
$Shortcut.WorkingDirectory = "{exe.parent}"
$Shortcut.IconLocation = "{new_icon}"
$Shortcut.Save()
'''
    rc, out, err = run_ps(ps_script)
    if rc != 0:
        print(f"Failed: {err}")
        sys.exit(1)
    print("  Created: MiniImageResizer_App.lnk")

    # Step 5: Force clear icon cache
    print("\n[5] Forcing icon cache refresh...")
    ps_cache = '''
    try {
        # Clear icon cache
        $cachePath = "$env:LOCALAPPDATA\Microsoft\Windows\Explorer"
        Get-ChildItem -Path $cachePath -Name "iconcache*" | ForEach-Object {
            Remove-Item (Join-Path $cachePath $_) -Force -ErrorAction SilentlyContinue
        }
        Remove-Item "$env:LOCALAPPDATA\IconCache.db" -Force -ErrorAction SilentlyContinue
        Write-Host "Cache cleared"
    } catch {
        Write-Host "Cache clear failed: $_"
    }
    '''
    run_ps(ps_cache)

    print("\n" + "=" * 50)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Check Desktop for 'MiniImageResizer_App.lnk'")
    print("2. If icon still shows Python, the icon.ico file itself may be wrong")
    print("3. Run: ie4uinit.exe -ClearIconCache to force refresh")


if __name__ == "__main__":
    main()
