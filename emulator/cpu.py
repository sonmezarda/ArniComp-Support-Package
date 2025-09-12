"""
ArniComp CPU Emulator
8-bit CPU with 16-bit addressing
"""

import json
import os
from .bus import Bus
from .devices.seven_segment import SevenSegmentDevice

class CPUFlags:
    def __init__(self):
        self.equal = False  # Equal flag (EQ) - result == 0
        self.lt = False     # Less Than flag (LT) - signed comparison 
        self.gt = False     # Greater Than flag (GT) - signed comparison
        self.carry = False  # Carry flag (C) - add carry out / sub borrow
    
    def update_flags(self, alu_input_a, alu_input_b):
        """Update flags based on ALU inputs - ArniComp uses hardware comparator"""
        # Hardware comparator directly compares ALU inputs A and B
        # A is typically ACC, B is typically RD or immediate value
        
        # Ensure 8-bit unsigned values
        a_unsigned = alu_input_a & 0xFF
        b_unsigned = alu_input_b & 0xFF
        
        # Hardware comparator outputs: A<B, A=B, A>B (unsigned comparison)
        self.lt = a_unsigned > b_unsigned  # LT flag
        self.equal = a_unsigned == b_unsigned  # EQ flag  
        self.gt = a_unsigned < b_unsigned  # GT flag
    # carry not set here; handled in arithmetic ops
    
    def __str__(self):
        return f"EQ:{int(self.equal)} LT:{int(self.lt)} GT:{int(self.gt)} C:{int(self.carry)}"

class CPU:
    def __init__(self):
        # 8-bit registers
        self.ra = 0      # General purpose register
        self.rd = 0      # ALU input register
        self.acc = 0     # Accumulator
        self.marl = 0    # Memory Address Register Low
        self.marh = 0    # Memory Address Register High
        self.prl = 0     # Program Counter Low
        self.prh = 0     # Program Counter High

        # Separate memory spaces (Harvard Architecture)
        self.program_memory = bytearray(65536)  # EEPROM - Program storage
        # Data memory moved under a Bus abstraction (for MMIO devices)
        self.bus = Bus(ram_size=65536)
        # Back-compat: mirror underlying RAM for any legacy reads
        self.data_memory = self.bus.ram

        # Flags
        self.flags = CPUFlags()

        # Memory mode (True = MH mode, False = ML mode)
        self.memory_mode_high = False

        # Program counter
        self.pc = 0

        # Execution control
        self.running = False
        self.halted = False

        # Debug features
        self.debug_mode = False
        self.step_mode = False
        self.breakpoints = set()

        # Load instruction set
        self.load_instruction_set()

        # Output bus (for peripherals)
        self.output_data = 0
        self.output_address = 0

        # Devices
        self._install_default_devices()
        
    def load_instruction_set(self):
        """Load instruction set from config.json"""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        self.instructions = config['instructions']
        self.opcode_types = config['opcode_types']
        self.argcode_types = config['argcode_types']
    
    def reset(self):
        """Reset CPU to initial state"""
        self.ra = 0
        self.rd = 0
        self.acc = 0
        self.marl = 0
        self.marh = 0
        self.prl = 0
        self.prh = 0
        self.pc = 0
        self.flags = CPUFlags()
        self.memory_mode_high = False
        self.running = False
        self.halted = False
        self.output_data = 0
        self.output_address = 0
        # Don't clear program memory - it persists like real hardware
        # Clear data RAM and reset devices via bus
        if hasattr(self, 'bus'):
            self.bus.reset()
    
    def load_program(self, binary_data, start_address=0):
        """Load binary program into PROGRAM memory (EEPROM)"""
        self.program_memory = bytearray(65536)  # Reset program memory
        for i, byte in enumerate(binary_data):
            if start_address + i < len(self.program_memory):
                self.program_memory[start_address + i] = byte
    
    def load_program_from_file(self, filename, start_address=0):
        """Load program from binary file into PROGRAM memory"""
        with open(filename, 'rb') as f:
            binary_data = f.read()
        self.load_program(binary_data, start_address)
    
    def get_memory_address(self):
        """Get current DATA memory address based on mode"""
        if self.memory_mode_high:
            return (self.marh << 8) | self.marl
        else:
            return self.marl
    
    def read_memory(self):
        """Read from DATA memory at current address"""
        addr = self.get_memory_address() & 0xFFFF
        return self.bus.read8(addr)
    
    def write_memory(self, value):
        """Write to DATA memory at current address"""
        addr = self.get_memory_address() & 0xFFFF
        self.bus.write8(addr, value & 0xFF)

    # Device setup
    def _install_default_devices(self):
        try:
            # Example MMIO: seven-seg at 0xFF00
            self.sevenseg = SevenSegmentDevice(id="seg0", base=0xFF00, on_change=None)
            self.bus.attach(self.sevenseg)
        except Exception:
            # Devices are optional; keep CPU usable if device load fails
            self.sevenseg = None
    
    def get_register_value(self, reg_name):
        """Get register value by name"""
        name = reg_name.upper()
        if name == 'RA':
            return self.ra
        if name == 'RD':
            return self.rd
        if name == 'ACC':
            return self.acc
        if name == 'ML':
            # Force LOW mode read regardless of current mode
            prev = self.memory_mode_high
            self.memory_mode_high = False
            val = self.read_memory()
            self.memory_mode_high = prev
            return val
        if name == 'MH':
            # Force HIGH mode read regardless of current mode
            prev = self.memory_mode_high
            self.memory_mode_high = True
            val = self.read_memory()
            self.memory_mode_high = prev
            return val
        if name == 'PCL':
            return self.prl
        if name == 'PCH':
            return self.prh
        if name == 'MARL':
            return self.marl
        if name == 'MARH':
            return self.marh
        if name == 'PRL':
            return self.prl
        if name == 'PRH':
            return self.prh
        if name == 'P':
            return (self.prh << 8) | self.prl
        return 0
    
    def set_register_value(self, reg_name, value):
        """Set register value by name"""
        value = value & 0xFF  # Ensure 8-bit
        
        if reg_name.upper() == 'RA':
            self.ra = value
        elif reg_name.upper() == 'RD':
            self.rd = value
        elif reg_name.upper() == 'ACC':
            self.acc = value
        elif reg_name.upper() == 'MARL':
            self.marl = value
        elif reg_name.upper() == 'MARH':
            self.marh = value
        elif reg_name.upper() == 'PCL':
            self.prl = value
        elif reg_name.upper() == 'PCH':
            self.prh = value
        elif reg_name.upper() == 'PRL':
            self.prl = value
        elif reg_name.upper() == 'PRH':
            self.prh = value
        elif reg_name.upper() in ['ML', 'MH']:
            # Writing to ML/MH means writing to memory
            self.memory_mode_high = (reg_name.upper() == 'MH')
            self.write_memory(value)
        elif reg_name.upper() == 'P':
            # Writing to P sets both PRL and PRH
            self.prl = value & 0xFF
            self.prh = (value >> 8) & 0xFF
    
    def fetch_instruction(self):
        """Fetch next instruction from PROGRAM memory"""
        if self.pc >= len(self.program_memory):
            return None
        
        instruction = self.program_memory[self.pc]
        self.pc += 1
        return instruction
    
    def decode_instruction(self, instruction):
        """Decode 8-bit instruction according to new Sept 2025 encoding"""
        # LDI (bit7=1)
        if instruction & 0x80:
            return 'LDI', [instruction & 0x7F]

        bits = f"{instruction:08b}"

        # Fixed single-byte patterns
        if bits == '00000000' or bits == '00000010':
            return 'NOP', []
        if bits == '00000001':
            return 'HLT', []
        if bits == '00000011':
            return 'CRA', []

        # SUBI 000001ii
        if bits.startswith('000001'):
            imm = instruction & 0x03
            return 'SUBI', [imm]

        # Jump 00001ccc
        if bits.startswith('00001'):
            cond = bits[5:8]
            cond_map = {
                '000': 'JMP', '001': 'JEQ', '010': 'JGT', '011': 'JLT',
                '100': 'JGE', '101': 'JLE', '110': 'JNE', '111': 'JC'
            }
            return cond_map.get(cond, 'UNKNOWN'), []

        # ADDI 00011iii
        if bits.startswith('00011'):
            imm = instruction & 0x07
            return 'ADDI', [imm]

        # AND 00010src
        if bits.startswith('00010'):
            src = bits[5:8]
            return 'AND', [self._decode_src_reg(src)]

        # Arithmetic 001ooosrc
        if bits.startswith('001'):
            op = bits[3:5]
            src = bits[5:8]
            op_map = {'00': 'ADD', '01': 'SUB', '10': 'ADC', '11': 'SBC'}
            return op_map.get(op, 'UNKNOWN'), [self._decode_src_reg(src)]

        # MOV 01dddsrc
        if bits.startswith('01'):
            dest = bits[2:5]
            src = bits[5:8]
            return 'MOV', [self._decode_dest_reg(dest), self._decode_src_reg(src)]

        return 'UNKNOWN', []

    def _decode_dest_reg(self, bits3:str):
        mapping = {
            '000': 'RA', '001': 'RD', '010': 'MARL', '011': 'MARH',
            '100': 'PRL', '101': 'PRH', '110': 'ML', '111': 'MH'
        }
        return mapping.get(bits3, 'RA')

    def _decode_src_reg(self, bits3:str):
        mapping = {
            '000': 'RA', '001': 'RD', '010': 'ACC', '011': 'CLR',
            '100': 'PCL', '101': 'PCH', '110': 'ML', '111': 'MH'
        }
        return mapping.get(bits3, 'RA')
    
    def execute_instruction(self, inst_name, args):
        """Execute decoded instruction"""
        if self.debug_mode:
            print(f"Executing: {inst_name} {args}")
        
        if inst_name == 'NOP':
            return
        if inst_name == 'HLT':
            self.halted = True
            return
        if inst_name == 'CRA':
            # CRA only clears RA (original hardware semantic)
            self.ra = 0
            return
        if inst_name == 'LDI':
            self.ra = args[0] & 0x7F
            return
        if inst_name == 'MOV' and len(args) == 2:
            dest, src = args
            val = 0
            if src == 'CLR':
                val = 0
            else:
                val = self.get_register_value(src)
            self.set_register_value(dest, val)
            if dest in ['ML','MH']:
                self.memory_mode_high = (dest == 'MH')
            return
        if inst_name in ['ADD','SUB','ADC','SBC'] and len(args) == 1:
            src_val = self.get_register_value(args[0])
            # Comparator uses RD vs source
            self.flags.update_flags(self.rd, src_val)
            if inst_name in ['ADD','ADC']:
                base = self.rd + src_val
                if inst_name == 'ADC' and self.flags.carry:
                    base += 1
                self.flags.carry = base > 0xFF
                self.acc = base & 0xFF
            else:  # SUB / SBC
                minuend = self.acc if inst_name in ['SUB','SBC'] else self.rd
                subtrahend = src_val + (1 if (inst_name == 'SBC' and self.flags.carry) else 0)
                result = (minuend - subtrahend) & 0x1FF
                # Borrow occurred if minuend < subtrahend
                borrow = minuend < subtrahend
                # Convention: carry flag = NOT borrow (so JC means no borrow) OR keep borrow semantics?
                # We'll set carry=False on borrow for typical 6502-like SBC semantics
                self.flags.carry = not borrow
                self.acc = result & 0xFF
            return
        if inst_name == 'AND' and len(args) == 1:
            src_val = self.get_register_value(args[0])
            self.acc = self.acc & src_val
            # Flags from RD vs src (keep comparator policy)
            self.flags.update_flags(self.rd, src_val)
            return
        if inst_name == 'ADDI' and len(args) == 1:
            imm = args[0] & 0x07
            self.flags.update_flags(self.rd, imm)
            total = self.rd + imm
            self.flags.carry = total > 0xFF
            self.acc = total & 0xFF
            return
        if inst_name == 'SUBI' and len(args) == 1:
            imm = args[0] & 0x03
            self.flags.update_flags(self.rd, imm)
            result = (self.rd - imm) & 0x1FF
            borrow = self.rd < imm
            self.flags.carry = not borrow
            self.acc = result & 0xFF
            return
        if inst_name in ['JMP','JEQ','JGT','JLT','JGE','JLE','JNE','JC']:
            target = (self.prh << 8) | self.prl
            take = False
            if inst_name == 'JMP':
                take = True
            elif inst_name == 'JEQ':
                take = self.flags.equal
            elif inst_name == 'JGT':
                take = self.flags.gt
            elif inst_name == 'JLT':
                take = self.flags.lt
            elif inst_name == 'JGE':
                take = self.flags.gt or self.flags.equal
            elif inst_name == 'JLE':
                take = self.flags.lt or self.flags.equal
            elif inst_name == 'JNE':
                take = not self.flags.equal
            elif inst_name == 'JC':
                take = self.flags.carry
            if take:
                self.pc = target
            return
        if inst_name == 'OUT' and len(args) == 1:
            self.output_data = self.get_register_value(args[0])
            self.output_address = self.ra
            if self.debug_mode:
                print(f"OUTPUT: Data=0x{self.output_data:02X} Address=0x{self.output_address:02X}")
            return
        if inst_name == 'IN' and len(args) == 1:
            self.set_register_value(args[0], 0)
            return
        if self.debug_mode:
            print(f"Unknown instruction: {inst_name}")
    
    def step(self):
        """Execute one instruction"""
        if self.halted or self.pc >= len(self.program_memory):
            return False
        
        # Check breakpoints
        if self.pc in self.breakpoints:
            print(f"Breakpoint hit at PC=0x{self.pc:04X}")
            return False
        
        # Fetch, decode, execute
        instruction = self.fetch_instruction()
        if instruction is None:
            self.halted = True
            return False
        
        inst_name, args = self.decode_instruction(instruction)
        self.execute_instruction(inst_name, args)
        
        return True
    
    def run(self, max_cycles=10000):
        """Run program until halt or max cycles"""
        self.running = True
        cycles = 0
        
        while self.running and not self.halted and cycles < max_cycles:
            if not self.step():
                break
            cycles += 1
            
            if self.step_mode:
                self.print_debug_info()
                input("Press Enter to continue...")
        
        self.running = False
        print(f"Execution stopped after {cycles} cycles")
        return cycles
    
    def print_debug_info(self):
        """Print current CPU state"""
        print(f"\n=== CPU STATE ===")
        print(f"PC: 0x{self.pc:04X}")
        print(f"RA: 0x{self.ra:02X} ({self.ra:3d})  RD: 0x{self.rd:02X} ({self.rd:3d})  ACC: 0x{self.acc:02X} ({self.acc:3d})")
        print(f"MARL: 0x{self.marl:02X}  MARH: 0x{self.marh:02X}  Data Addr: 0x{self.get_memory_address():04X}")
        print(f"PRL: 0x{self.prl:02X}  PRH: 0x{self.prh:02X}  P: 0x{((self.prh << 8) | self.prl):04X}")
        print(f"Flags: {self.flags}")
        print(f"Memory Mode: {'HIGH' if self.memory_mode_high else 'LOW'}")
        print(f"Data Memory[{self.get_memory_address():04X}]: 0x{self.read_memory():02X}")
        
        # Show next instruction
        if self.pc < len(self.program_memory):
            next_inst = self.program_memory[self.pc]
            inst_name, args = self.decode_instruction(next_inst)
            print(f"Next: {inst_name} {args}")
    
    def print_memory_range(self, start, end, memory_type="data"):
        """Print memory content in range"""
        memory = self.data_memory if memory_type == "data" else self.program_memory
        print(f"\n=== {memory_type.upper()} MEMORY 0x{start:04X}-0x{end:04X} ===")
        for addr in range(start, min(end + 1, len(memory)), 16):
            line = f"{addr:04X}: "
            for i in range(16):
                if addr + i <= end and addr + i < len(memory):
                    line += f"{memory[addr + i]:02X} "
                else:
                    line += "   "
            
            # ASCII representation
            line += " |"
            for i in range(16):
                if addr + i <= end and addr + i < len(memory):
                    char = memory[addr + i]
                    line += chr(char) if 32 <= char <= 126 else "."
                else:
                    line += " "
            line += "|"
            
            print(line)
    
    def set_breakpoint(self, address):
        """Set breakpoint at address"""
        self.breakpoints.add(address)
        print(f"Breakpoint set at 0x{address:04X}")
    
    def clear_breakpoint(self, address):
        """Clear breakpoint at address"""
        self.breakpoints.discard(address)
        print(f"Breakpoint cleared at 0x{address:04X}")
