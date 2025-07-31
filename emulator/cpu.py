"""
ArniComp CPU Emulator
8-bit CPU with 16-bit addressing
"""

import json
import os

class CPUFlags:
    def __init__(self):
        self.equal = False  # Equal flag (EQ) - result == 0
        self.lt = False     # Less Than flag (LT) - signed comparison 
        self.gt = False     # Greater Than flag (GT) - signed comparison
    
    def update_flags(self, alu_input_a, alu_input_b):
        """Update flags based on ALU inputs - ArniComp uses hardware comparator"""
        # Hardware comparator directly compares ALU inputs A and B
        # A is typically ACC, B is typically RD or immediate value
        
        # Ensure 8-bit unsigned values
        a_unsigned = alu_input_a & 0xFF
        b_unsigned = alu_input_b & 0xFF
        
        # Hardware comparator outputs: A<B, A=B, A>B (unsigned comparison)
        self.lt = a_unsigned < b_unsigned  # LT flag
        self.equal = a_unsigned == b_unsigned  # EQ flag  
        self.gt = a_unsigned > b_unsigned  # GT flag
    
    def __str__(self):
        return f"EQ:{int(self.equal)} LT:{int(self.lt)} GT:{int(self.gt)}"

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
        self.data_memory = bytearray(65536)     # RAM - Data storage
        
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
        # Don't clear memories - they persist like real hardware
    
    def load_program(self, binary_data, start_address=0):
        """Load binary program into PROGRAM memory (EEPROM)"""
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
        addr = self.get_memory_address()
        return self.data_memory[addr] if addr < len(self.data_memory) else 0
    
    def write_memory(self, value):
        """Write to DATA memory at current address"""
        addr = self.get_memory_address()
        if addr < len(self.data_memory):
            self.data_memory[addr] = value & 0xFF
    
    def get_register_value(self, reg_name):
        """Get register value by name"""
        reg_map = {
            'RA': self.ra, 'ra': self.ra,
            'RD': self.rd, 'rd': self.rd,
            'ACC': self.acc, 'acc': self.acc,
            'ML': self.read_memory(), 'ml': self.read_memory(),
            'MH': self.read_memory(), 'mh': self.read_memory(),
            'PCL': self.prl, 'pcl': self.prl,
            'PCH': self.prh, 'pch': self.prh,
            'MARL': self.marl, 'marl': self.marl,
            'MARH': self.marh, 'marh': self.marh,
            'PRL': self.prl, 'prl': self.prl,
            'PRH': self.prh, 'prh': self.prh,
            'P': (self.prh << 8) | self.prl, 'p': (self.prh << 8) | self.prl
        }
        return reg_map.get(reg_name, 0)
    
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
        """Decode 8-bit instruction"""
        im7 = (instruction >> 7) & 1
        
        if im7 == 1:
            # LDI instruction - immediate load to RA
            value = instruction & 0x7F  # 7-bit immediate value
            return 'LDI', [value]
        else:
            # Normal instruction
            opcode = (instruction >> 3) & 0xF  # 4-bit opcode
            argcode = instruction & 0x7        # 3-bit argcode
            
            # Find instruction by opcode and argcode
            # First check constant opcodes (more specific)
            for inst_name, inst_data in self.instructions.items():
                if inst_name == 'LDI':
                    continue
                
                if inst_data.get('opcode_type') == 'constant':
                    expected_opcode = inst_data.get('opcode')
                    if expected_opcode and int(expected_opcode, 2) == opcode:
                        # Check argcode
                        if inst_data.get('argcode_type') == 'constant':
                            expected_argcode = inst_data.get('argcode')
                            if expected_argcode and int(expected_argcode, 2) == argcode:
                                return inst_name, []
                        elif inst_data.get('argcode_type') == 'out_reg':
                            # Find register by argcode
                            for reg_name, reg_code in self.argcode_types['out_reg'].items():
                                if int(reg_code, 2) == argcode:
                                    return inst_name, [reg_name.upper()]
                        elif inst_data.get('argcode_type') == 'number':
                            return inst_name, [argcode]
            
            # Then check register opcodes  
            for inst_name, inst_data in self.instructions.items():
                if inst_name == 'LDI':
                    continue
                
                if inst_data.get('opcode_type') == 'in_reg':
                    for source_reg, reg_code in self.opcode_types['in_reg'].items():
                        if int(reg_code, 2) == opcode:
                            if inst_data.get('argcode_type') == 'constant':
                                expected_argcode = inst_data.get('argcode')
                                if expected_argcode and int(expected_argcode, 2) == argcode:
                                    return inst_name, [source_reg.upper()]
                            elif inst_data.get('argcode_type') == 'out_reg':
                                # Two register instruction like MOV
                                for dest_reg, dest_code in self.argcode_types['out_reg'].items():
                                    if int(dest_code, 2) == argcode:
                                        return inst_name, [source_reg.upper(), dest_reg.upper()]
            
            return 'UNKNOWN', [opcode, argcode]
    
    def execute_instruction(self, inst_name, args):
        """Execute decoded instruction"""
        if self.debug_mode:
            print(f"Executing: {inst_name} {args}")
        
        if inst_name == 'LDI':
            # Load immediate to RA
            self.ra = args[0] & 0xFF
            
        elif inst_name == 'MOV':
            # MOV dest, source (args[0] = dest, args[1] = source)
            if len(args) >= 2:
                source_val = self.get_register_value(args[1])
                self.set_register_value(args[0], source_val)
                
                # Special handling for memory mode
                if args[0].upper() in ['ML', 'MH']:
                    self.memory_mode_high = (args[0].upper() == 'MH')
        
        elif inst_name == 'ADD':
            # ADD source - adds RD + source, stores in ACC
            if len(args) >= 1:
                source_val = self.get_register_value(args[0])
                # Hardware comparator: RD vs source_val
                self.flags.update_flags(self.rd, source_val)
                result = self.rd + source_val  # RD + source
                self.acc = result & 0xFF
        
        elif inst_name == 'SUB':
            # SUB source - subtracts source from ACC
            if len(args) >= 1:
                source_val = self.get_register_value(args[0])
                # Hardware comparator: RD vs source_val
                self.flags.update_flags(self.rd, source_val)
                result = self.acc - source_val
                self.acc = result & 0xFF
        
        elif inst_name == 'ADDI':
            # ADDI immediate - adds immediate to ACC
            if len(args) >= 1:
                immediate = args[0]
                # Hardware comparator: RD vs immediate
                self.flags.update_flags(self.rd, immediate)
                result = self.acc + immediate
                self.acc = result & 0xFF
        
        elif inst_name == 'SUBI':
            # SUBI immediate - subtracts immediate from ACC
            if len(args) >= 1:
                immediate = args[0]
                # Hardware comparator: RD vs immediate
                self.flags.update_flags(self.rd, immediate)
                result = self.acc - immediate
                self.acc = result & 0xFF
        
        elif inst_name == 'LDRL':
            # LDRL dest - load from memory to dest (low mode)
            if len(args) >= 1:
                self.memory_mode_high = False
                value = self.read_memory()
                self.set_register_value(args[0], value)
        
        elif inst_name == 'LDRH':
            # LDRH dest - load from memory to dest (high mode)
            if len(args) >= 1:
                self.memory_mode_high = True
                value = self.read_memory()
                self.set_register_value(args[0], value)
        
        elif inst_name == 'STRL':
            # STRL source - store source to memory (low mode)
            if len(args) >= 1:
                self.memory_mode_high = False
                value = self.get_register_value(args[0])
                self.write_memory(value)
        
        elif inst_name == 'STRH':
            # STRH source - store source to memory (high mode)
            if len(args) >= 1:
                self.memory_mode_high = True
                value = self.get_register_value(args[0])
                self.write_memory(value)
        
        elif inst_name == 'JMP':
            # Unconditional jump
            self.pc = (self.prh << 8) | self.prl
        
        elif inst_name == 'JEQ':
            # Jump if equal (Equal flag set)
            if self.flags.equal:
                self.pc = (self.prh << 8) | self.prl
        
        elif inst_name == 'JNE':
            # Jump if not equal (Equal flag clear)
            if not self.flags.equal:
                self.pc = (self.prh << 8) | self.prl
        
        elif inst_name == 'JLT':
            # Jump if less than (LT flag set)
            if self.flags.lt:
                self.pc = (self.prh << 8) | self.prl
        
        elif inst_name == 'JGT':
            # Jump if greater than (GT flag set)
            if self.flags.gt:
                self.pc = (self.prh << 8) | self.prl
        
        elif inst_name == 'JLE':
            # Jump if less than or equal (LT or Equal)
            if self.flags.lt or self.flags.equal:
                self.pc = (self.prh << 8) | self.prl
        
        elif inst_name == 'JGE':
            # Jump if greater than or equal (GT or Equal)
            if self.flags.gt or self.flags.equal:
                self.pc = (self.prh << 8) | self.prl
        
        elif inst_name == 'OUT':
            # Output to peripheral bus
            if len(args) >= 1:
                self.output_data = self.get_register_value(args[0])
                self.output_address = self.ra  # RA drives output address bus
                if self.debug_mode:
                    print(f"OUTPUT: Data=0x{self.output_data:02X} Address=0x{self.output_address:02X}")
        
        elif inst_name == 'IN':
            # Input from peripheral (placeholder - returns 0)
            if len(args) >= 1:
                # In real hardware, this would read from input bus
                input_value = 0  # Placeholder
                self.set_register_value(args[0], input_value)
        
        else:
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
