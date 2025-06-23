import sys, os

from config import *
from modules.AssemblyHelper import AssemblyHelper
from modules.EepromLoader import EepromLoader

assembly_helper  = AssemblyHelper(comment_char=';', label_char=':', constant_keyword="const", number_prefix='#')

def convert_to_machine_code(in_file:str, out_file:str):
    f = open(in_file, 'r')
    raw_lines = f.readlines()
    f.close()
    
    clines = assembly_helper.upper_lines(raw_lines)
    clines = assembly_helper.remove_whitespaces_lines(raw_lines)
    print(f"Cleaned lines: {clines}")
    constants = assembly_helper.get_constants(clines)
    print(f"Constants found: {constants}")
    clines = assembly_helper.remove_constants(clines)
    labels = assembly_helper.get_labels(clines)
    clines = assembly_helper.remove_labels(clines)
    print(f"Labels found: {labels}")
    clines = assembly_helper.change_labels(clines, labels)
    clines = assembly_helper.change_constants(clines, constants)
    
    blines = assembly_helper.convert_to_binary_lines(clines)

    lines_to_write_bin = [f"{line}{'\n'}" for line in blines]

    f = open(out_file, 'w')
    f.writelines(lines_to_write_bin)
    f.close()

def machine_code_to_bin(in_file:str, out_file:str):
    program = bytearray(65536) 

    with open(in_file, "rb") as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            program[i] = int(line.strip(), 2)
        

    with open(out_file, "wb") as f:
        f.write(program)

def load_bin_file(bin_file: str):
    eeprom_loader = EepromLoader()
    eeprom_loader.write(bin_file)

def load_assembly_file(asm_file: str):
    tmp_machine = "_tmp_machine.txt"
    tmp_bin = "_tmp_program.bin"
    convert_to_machine_code(asm_file, tmp_machine)
    machine_code_to_bin(tmp_machine, tmp_bin)
    load_bin_file(tmp_bin)
    os.remove(tmp_machine)
    os.remove(tmp_bin)

def print_help():
    print("Kullanım:")
    print("  assemble <in.asm> [out.txt]       - Assembly -> machine code (binary string)")
    print("  createbin <in.txt> [out.bin]      - Machine code -> .bin file")
    print("  load <in.bin>                     - EEPROM yüklemesi yapar")
    print("  loadAssembly <in.asm>             - Assembly -> yükleme (geçici dosya üretir)")
    print("  help                              - Bu mesajı gösterir")



def main():
    if len(sys.argv) < 2:
        print_help()
        return

    command = sys.argv[1]

    if command == "assemble":
        if len(sys.argv) < 3:
            print("Hata: input dosya adı gerekli.")
            return
        in_file = sys.argv[2]
        out_file = sys.argv[3] if len(sys.argv) >= 4 else os.path.splitext(in_file)[0] + ".binary"
        convert_to_machine_code(in_file, out_file)
        print(f"Makine kodu üretildi: {out_file}")

    elif command == "createbin":
        if len(sys.argv) < 3:
            print("Hata: input dosya adı gerekli.")
            return
        in_file = sys.argv[2]
        out_file = sys.argv[3] if len(sys.argv) >= 4 else os.path.splitext(in_file)[0] + ".bin"
        machine_code_to_bin(in_file, out_file)
        print(f"BIN dosyası üretildi: {out_file}")

    elif command == "load":
        if len(sys.argv) < 3:
            print("Hata: .bin dosya adı gerekli.")
            return
        load_bin_file(sys.argv[2])
        print("EEPROM yükleme tamamlandı.")
    
    elif command == "checkFile":
        eeprom_loader = EepromLoader()
        top = eeprom_loader.check_file(sys.argv[2], int(sys.argv[3]))
        print(f"İlk {sys.argv[3]} bayt: {top}")
        
    elif command == "checkSerial":
        eeprom_loader = EepromLoader()
        eeprom_loader.check_serial()


    elif command == "loadAssembly":
        if len(sys.argv) < 3:
            print("Hata: .asm dosya adı gerekli.")
            return
        load_assembly_file(sys.argv[2])
        print("Assembly dosyası başarıyla yüklendi.")

    else:
        print_help()
    
if __name__ == "__main__":    
    main()