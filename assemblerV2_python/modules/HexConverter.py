from intelhex import IntelHex
from six import StringIO


def save_intelHexFile(filename:str, lines:list[str], line_type:str='hex'):
    # Digital circuit simulator is using IntelHex files as ROM input
    number_base = 16 if line_type == 'hex' else 2
    print(lines)
    ih = IntelHex()
    for i, line in enumerate(lines):
        ih[i] = int(line, number_base)
    sio = StringIO()
    ih.write_hex_file(sio)
    hexstr = sio.getvalue()
    with open(filename, 'w') as f:
        f.write(hexstr)
    sio.close()

if __name__ == "__main__":
    # Example usage
    lines = ['3E', '32', '00', 'C0', 'AF', '32', '01', 'C0']
    save_intelHexFile('output.hex', lines)