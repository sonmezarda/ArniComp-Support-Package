from intelhex import IntelHex
from six import StringIO


def save_intelHexFile(filename: str, lines: list[str], line_type: str = 'hex'):
    """Write a sequential list of byte values to an Intel HEX file.

    lines: list of strings representing byte values in the given base (hex/bin)
    line_type: 'hex' or 'bin' - determines how to parse each element in lines
    """
    # Digital circuit simulator is using IntelHex files as ROM input
    number_base = 16 if line_type == 'hex' else 2
    ih = IntelHex()
    for i, line in enumerate(lines):
        if isinstance(line, bytes):
            line = line.decode('utf-8')
        value = int(str(line).strip(), number_base) & 0xFF
        ih[i] = value
    sio = StringIO()
    ih.write_hex_file(sio)
    hexstr = sio.getvalue()
    with open(filename, 'w') as f:
        f.write(hexstr)
    sio.close()


def save_intelHexFile_from_pairs(
    filename: str,
    addr_value_lines: list[str],
    addr_base: str = 'bin',
    data_base: str = 'bin',
    sep: str | None = None,
):
    """Write address-aware pairs to Intel HEX.

    addr_value_lines: list of lines in the form "<address> <value>" (whitespace or custom sep)
      - Example (binary):  "00000010 01100100"
      - Example (hex):     "0x10 0x64" or "10 64" with addr_base='hex', data_base='hex'
      - Example (decimal): "16 100" with bases set to 'dec'
    addr_base/data_base: one of 'bin' | 'hex' | 'dec'
    sep: optional explicit separator; defaults to any whitespace
    """
    base_map = {
        'bin': 2,
        'hex': 16,
        'dec': 10,
    }
    try:
        a_base = base_map[addr_base.lower()]
        d_base = base_map[data_base.lower()]
    except KeyError:
        raise ValueError("addr_base and data_base must be one of: 'bin', 'hex', 'dec'")

    pairs: list[tuple[int, int]] = []

    for raw in addr_value_lines:
        if isinstance(raw, bytes):
            raw = raw.decode('utf-8', errors='ignore')
        line = str(raw).strip()
        if not line:
            continue
        # Strip comments after ';' or '#'
        for c in (';', '#'):
            if c in line:
                line = line.split(c, 1)[0].strip()
        if not line:
            continue
        parts = line.split(sep) if sep is not None else line.split()
        if len(parts) < 2:
            # skip malformed lines silently
            continue
        a_str, d_str = parts[0], parts[1]
        try:
            addr = int(a_str, a_base)
            data = int(d_str, d_base) & 0xFF
        except ValueError:
            # skip lines that cannot be parsed
            continue
        if addr < 0:
            continue
        pairs.append((addr, data))

    # Sort by address
    pairs.sort(key=lambda t: t[0])

    ih = IntelHex()
    for addr, data in pairs:
        ih[addr] = data

    sio = StringIO()
    ih.write_hex_file(sio)
    hexstr = sio.getvalue()
    with open(filename, 'w') as f:
        f.write(hexstr)
    sio.close()


if __name__ == "__main__":
    # Example usages
    lines = ['3E', '32', '00', 'C0', 'AF', '32', '01', 'C0']
    save_intelHexFile('output.hex', lines)
    addr_lines = [
        '00000000 00000001',
        '00000010 00000011',
        '00000001 00000010',
    ]
    save_intelHexFile_from_pairs('output_pairs.hex', addr_lines, addr_base='bin', data_base='bin')