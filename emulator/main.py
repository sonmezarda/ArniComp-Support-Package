"""
ArniComp CPU Emulator - Main Interface
Interactive debugger and emulator for the ArniComp 8-bit CPU
"""

import sys
import os
from cpu import CPU

class Emulator:
    def __init__(self):
        self.cpu = CPU()
        self.running = True
    
    def load_binary_file(self, filename):
        """Load a binary program file"""
        try:
            self.cpu.load_program_from_file(filename)
            print(f"Program loaded from {filename}")
            return True
        except FileNotFoundError:
            print(f"File not found: {filename}")
            return False
        except Exception as e:
            print(f"Error loading file: {e}")
            return False
    
    def run_interactive(self):
        """Run interactive debugger"""
        print("ArniComp CPU Emulator")
        print("Type 'help' for commands")
        
        while self.running:
            try:
                command = input(f"(PC:0x{self.cpu.pc:04X})> ").strip().split()
                if not command:
                    continue
                
                self.execute_command(command)
                
            except KeyboardInterrupt:
                print("\nEmulator interrupted")
                break
            except EOFError:
                print("\nEmulator exiting")
                break
    
    def execute_command(self, command):
        """Execute debugger command"""
        cmd = command[0].lower()
        
        if cmd in ['help', 'h']:
            self.print_help()
        
        elif cmd in ['load', 'l']:
            if len(command) > 1:
                self.load_binary_file(command[1])
            else:
                print("Usage: load <filename>")
        
        elif cmd in ['reset', 'r']:
            self.cpu.reset()
            print("CPU reset")
        
        elif cmd in ['step', 's']:
            count = 1
            if len(command) > 1:
                try:
                    count = int(command[1])
                except ValueError:
                    print("Invalid step count")
                    return
            
            for _ in range(count):
                if not self.cpu.step():
                    print("Execution stopped")
                    break
                if count == 1:  # Only show debug info for single steps
                    self.cpu.print_debug_info()
        
        elif cmd in ['run']:
            max_cycles = 10000
            if len(command) > 1:
                try:
                    max_cycles = int(command[1])
                except ValueError:
                    print("Invalid cycle count")
                    return
            
            self.cpu.run(max_cycles)
        
        elif cmd in ['continue', 'c']:
            self.cpu.step_mode = False
            self.cpu.run()
        
        elif cmd in ['debug', 'd']:
            self.cpu.print_debug_info()
        
        elif cmd in ['memory', 'm', 'mem']:
            memory_type = "data"  # default
            if len(command) >= 4 and command[3] in ['data', 'program']:
                memory_type = command[3]
            
            if len(command) >= 3:
                try:
                    start = int(command[1], 0)  # Support hex with 0x prefix
                    end = int(command[2], 0)
                    self.cpu.print_memory_range(start, end, memory_type)
                except ValueError:
                    print("Invalid address format")
            elif len(command) == 2:
                try:
                    addr = int(command[1], 0)
                    self.cpu.print_memory_range(addr, addr + 15, memory_type)
                except ValueError:
                    print("Invalid address format")
            else:
                print("Usage: memory <start> [end] [data|program] or memory <address> [data|program]")
        
        elif cmd in ['set']:
            if len(command) >= 3:
                reg_name = command[1].upper()
                try:
                    value = int(command[2], 0)
                    self.cpu.set_register_value(reg_name, value)
                    print(f"{reg_name} = 0x{value:02X}")
                except ValueError:
                    print("Invalid value format")
            else:
                print("Usage: set <register> <value>")
        
        elif cmd in ['get']:
            if len(command) >= 2:
                reg_name = command[1].upper()
                value = self.cpu.get_register_value(reg_name)
                print(f"{reg_name} = 0x{value:02X} ({value})")
            else:
                print("Usage: get <register>")
        
        elif cmd in ['breakpoint', 'bp']:
            if len(command) >= 2:
                try:
                    addr = int(command[1], 0)
                    self.cpu.set_breakpoint(addr)
                except ValueError:
                    print("Invalid address format")
            else:
                print("Usage: breakpoint <address>")
        
        elif cmd in ['clear']:
            if len(command) >= 2:
                try:
                    addr = int(command[1], 0)
                    self.cpu.clear_breakpoint(addr)
                except ValueError:
                    print("Invalid address format")
            else:
                print("Usage: clear <address>")
        
        elif cmd in ['disasm', 'dis']:
            start = self.cpu.pc
            count = 10
            if len(command) >= 2:
                try:
                    start = int(command[1], 0)
                except ValueError:
                    print("Invalid address format")
                    return
            if len(command) >= 3:
                try:
                    count = int(command[2])
                except ValueError:
                    print("Invalid count")
                    return
            
            self.disassemble(start, count)
        
        elif cmd in ['write', 'w']:
            memory_type = "data"  # default
            if len(command) >= 4:
                try:
                    addr = int(command[1], 0)
                    value = int(command[2], 0)
                    if len(command) >= 4 and command[3] == "program":
                        memory_type = "program"
                    
                    if memory_type == "data":
                        self.cpu.data_memory[addr] = value & 0xFF
                        print(f"Data Memory[0x{addr:04X}] = 0x{value:02X}")
                    else:
                        self.cpu.program_memory[addr] = value & 0xFF
                        print(f"Program Memory[0x{addr:04X}] = 0x{value:02X}")
                except (ValueError, IndexError):
                    print("Invalid address or value")
            else:
                print("Usage: write <address> <value> [data|program]")
        
        elif cmd in ['stepmode']:
            self.cpu.step_mode = not self.cpu.step_mode
            print(f"Step mode: {'ON' if self.cpu.step_mode else 'OFF'}")
        
        elif cmd in ['debugmode']:
            self.cpu.debug_mode = not self.cpu.debug_mode
            print(f"Debug mode: {'ON' if self.cpu.debug_mode else 'OFF'}")
        
        elif cmd in ['quit', 'q', 'exit']:
            self.running = False
        
        else:
            print(f"Unknown command: {cmd}")
    
    def disassemble(self, start_addr, count):
        """Disassemble instructions"""
        print(f"\n=== DISASSEMBLY FROM 0x{start_addr:04X} ===")
        addr = start_addr
        
        for i in range(count):
            if addr >= len(self.cpu.program_memory):
                break
            
            instruction = self.cpu.program_memory[addr]
            inst_name, args = self.cpu.decode_instruction(instruction)
            
            # Format instruction
            inst_str = f"{inst_name}"
            if args:
                if inst_name == 'LDI':
                    inst_str += f" #0x{args[0]:02X}"
                else:
                    inst_str += " " + ", ".join(str(arg) for arg in args)
            
            marker = " -> " if addr == self.cpu.pc else "    "
            print(f"{marker}0x{addr:04X}: 0x{instruction:02X}  {inst_str}")
            addr += 1
    
    def print_help(self):
        """Print help message"""
        print("""
ArniComp CPU Emulator Commands:

File Operations:
  load <file>           - Load binary program file
  
Execution Control:
  reset                 - Reset CPU to initial state
  step [count]          - Execute one or more instructions
  run [max_cycles]      - Run until halt or max cycles
  continue              - Continue execution (turn off step mode)
  
Debugging:
  debug                 - Show CPU state
  memory <start> [end] [data|program] - Show memory content
  disasm [addr] [count] - Disassemble instructions
  breakpoint <addr>     - Set breakpoint
  clear <addr>          - Clear breakpoint
  stepmode              - Toggle step-by-step mode
  debugmode             - Toggle debug output
  
Register/Memory Access:
  set <reg> <value>     - Set register value
  get <reg>             - Get register value
  write <addr> <value> [data|program] - Write to memory
  
Registers: RA, RD, ACC, MARL, MARH, PCL, PCH, PRL, PRH

Other:
  help                  - Show this help
  quit                  - Exit emulator
        """)

def main():
    emulator = Emulator()
    
    if len(sys.argv) > 1:
        # Load program from command line
        if emulator.load_binary_file(sys.argv[1]):
            print("Program loaded. Type 'run' to execute or 'step' to debug.")
    
    emulator.run_interactive()

if __name__ == "__main__":
    main()
