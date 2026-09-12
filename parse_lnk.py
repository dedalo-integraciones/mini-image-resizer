import os
import struct
import sys
from pathlib import Path


def parse_lnk(filepath):
    """Basic LNK parser to check target and icon location."""
    with open(filepath, 'rb') as f:
        data = f.read()

    if len(data) < 76:
        print("File too small to be a valid LNK")
        return

    # Check signature
    sig = data[:4]
    if sig != b'\x4C\x00\x00\x00':
        print(f"Invalid LNK signature: {sig}")
        return

    print(f"Valid LNK file: {filepath}")
    print(f"File size: {len(data)} bytes")

    # Header (76 bytes)
    flags = struct.unpack('<I', data[4:8])[0]
    file_size = struct.unpack('<I', data[8:12])[0]
    mod_time = struct.unpack('<I', data[12:16])[0]
    attr = struct.unpack('<I', data[16:20])[0]
    file_size_low = struct.unpack('<I', data[20:24])[0]
    file_size_high = struct.unpack('<I', data[24:28])[0]
    icon_index = struct.unpack('<I', data[28:32])[0]
    show_cmd = struct.unpack('<I', data[32:36])[0]
    hot_key = struct.unpack('<H', data[36:38])[0]

    print(f"Flags: 0x{flags:08X}")
    print(f"Icon index: {icon_index}")
    print(f"Show command: {show_cmd}")

    # Parse link info structure
    offset = 76
    if flags & 0x1:  # Has_link_target_id_list
        # Skip id list
        size = struct.unpack('<I', data[offset:offset+4])[0]
        offset += size + 4

    if flags & 0x20:  # Has_link_info
        link_info_size = struct.unpack('<I', data[offset:offset+4])[0]
        link_info_header_size = struct.unpack('<I', data[offset+4:offset+8])[0]
        link_info_flags = struct.unpack('<I', data[offset+8:offset+12])[0]

        # Volume label and network provider info
        vol_label_offset = struct.unpack('<I', data[offset+12:offset+16])[0]

        # Local base path
        local_base_path_offset = struct.unpack('<I', data[offset+20:offset+24])[0]

        # Network provider
        net_provider_offset = struct.unpack('<I', data[offset+24:offset+28])[0]

        offset += link_info_size + 4

        if link_info_flags & 0x1:  # Has_volume_label_and_network_provider
            if vol_label_offset > 0:
                vol_start = offset + vol_label_offset - 20  # Adjust for header
                end = data.index(b'\x00\x00', vol_start)
                vol_label = data[vol_start:end].decode('utf-16-le', errors='ignore')
                print(f"Volume label: {vol_label}")

        if local_base_path_offset > 0:
            path_start = offset + local_base_path_offset - 20
            end = data.index(b'\x00\x00', path_start)
            local_path = data[path_start:end].decode('utf-16-le', errors='ignore')
            print(f"Local base path: {local_path}")

    # Parse strings
    if flags & 0x80000:  # Has_extra_data
        # Find string data
        extra_start = offset
        while extra_start < len(data):
            size = struct.unpack('<I', data[extra_start:extra_start+4])[0]
            if size == 0:
                break
            block_id = struct.unpack('<I', data[extra_start+4:extra_start+8])[0]
            if block_id == 0x00000005:  # Shell item ID list
                pass
            elif block_id == 0x00000007:  # Icon location
                icon_offset = extra_start + 8
                icon_end = data.index(b'\x00\x00', icon_offset)
                icon_loc = data[icon_offset:icon_end].decode('utf-16-le', errors='ignore')
                print(f"Icon location (from extra data): {icon_loc}")
            elif block_id == 0x00000009:  # Working directory
                wd_offset = extra_start + 8
                wd_end = data.index(b'\x00\x00', wd_offset)
                wd = data[wd_offset:wd_end].decode('utf-16-le', errors='ignore')
                print(f"Working directory (from extra data): {wd}")
            extra_start += 4 + size

    # Parse final data block for target and icon
    # The target path is usually near the end
    print(f"\nSearching for paths in raw data...")
    # Look for .exe references
    text = data.decode('utf-16-le', errors='ignore')
    for line in text.split('\x00'):
        line = line.strip()
        if '.exe' in line.lower() or '.ico' in line.lower():
            print(f"  Found: {line}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python parse_lnk.py <shortcut.lnk>")
        sys.exit(1)
    parse_lnk(sys.argv[1])
