#!/usr/bin/env python3
"""
ArniComp Compiler CLI
A high-level language compiler for the ArniComp custom ISA architecture.

Compiles high-level source code to assembly, with memory management,
register allocation, and optimization support.

Usage:
    python main.py compile <input.arn> [options]
    python main.py config [options]
    python main.py validate <input.arn>
    python main.py info
"""

import sys
import os
import json
import argparse
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

# Add modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

from modules.CompilerHelper import Compiler, create_default_compiler


@dataclass
class CompilerConfig:
    """Compiler configuration with all tunable parameters"""
    comment_char: str = '//'
    variable_start_addr: int = 0x0000
    variable_end_addr: int = 0x0200
    stack_start_addr: int = 0x0100
    stack_size: int = 256
    memory_size: int = 65536
    output_format: str = 'asm'  # asm, hex, bin
    optimization_level: int = 0  # 0=none, 1=basic, 2=aggressive
    debug_mode: bool = False
    verbose: bool = False
    show_stats: bool = True
    
    @classmethod
    def from_file(cls, config_path: str) -> 'CompilerConfig':
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
            return cls(**data)
        except FileNotFoundError:
            return cls()  # Return defaults if file not found
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in config file: {e}")
            sys.exit(1)
    
    def to_file(self, config_path: str) -> None:
        """Save configuration to JSON file"""
        with open(config_path, 'w') as f:
            json.dump(asdict(self), f, indent=4)
        print(f"Configuration saved to: {config_path}")
    
    def display(self) -> None:
        """Display current configuration"""
        print("\n=== Compiler Configuration ===")
        print(f"  Comment character:        {self.comment_char}")
        print(f"  Variable memory range:    0x{self.variable_start_addr:04X} - 0x{self.variable_end_addr:04X}")
        print(f"  Stack start address:      0x{self.stack_start_addr:04X}")
        print(f"  Stack size:               {self.stack_size} bytes")
        print(f"  Total memory size:        {self.memory_size} bytes")
        print(f"  Output format:            {self.output_format}")
        print(f"  Optimization level:       {self.optimization_level}")
        print(f"  Debug mode:               {'enabled' if self.debug_mode else 'disabled'}")
        print(f"  Verbose output:           {'enabled' if self.verbose else 'disabled'}")
        print(f"  Show statistics:          {'enabled' if self.show_stats else 'disabled'}")
        print()


class CompilerCLI:
    """Command-line interface for the ArniComp compiler"""
    
    DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'compiler.config.json')
    
    def __init__(self):
        self.config = CompilerConfig()
        self.compiler: Optional[Compiler] = None
    
    def load_config(self, config_path: Optional[str] = None) -> None:
        """Load configuration from file"""
        path = config_path or self.DEFAULT_CONFIG_PATH
        if os.path.exists(path):
            self.config = CompilerConfig.from_file(path)
            if self.config.verbose:
                print(f"Loaded configuration from: {path}")
    
    def create_compiler(self) -> Compiler:
        """Create compiler instance with current configuration"""
        return Compiler(
            comment_char=self.config.comment_char,
            variable_start_addr=self.config.variable_start_addr,
            variable_end_addr=self.config.variable_end_addr,
            stack_start_addr=self.config.stack_start_addr,
            stack_size=self.config.stack_size,
            memory_size=self.config.memory_size
        )
    
    def _setup_logging(self) -> None:
        """Configure logging based on debug/verbose mode"""
        # Determine logging level
        if self.config.debug_mode:
            level = logging.DEBUG
            fmt = '%(levelname)s [%(name)s]: %(message)s'
        elif self.config.verbose:
            level = logging.INFO
            fmt = '%(levelname)s: %(message)s'
        else:
            level = logging.WARNING
            fmt = '%(message)s'
        
        # Configure root logger
        logging.basicConfig(
            level=level,
            format=fmt,
            force=True  # Override any existing configuration
        )
    
    def compile(self, input_file: str, output_file: Optional[str] = None, 
                output_format: Optional[str] = None) -> None:
        """Compile source file to assembly"""
        # Setup logging based on debug/verbose settings
        self._setup_logging()
        
        # Validate input file
        if not os.path.exists(input_file):
            print(f"Error: Input file '{input_file}' not found")
            sys.exit(1)
        
        # Determine output file and format
        if output_file is None:
            base_name = os.path.splitext(input_file)[0]
            fmt = output_format or self.config.output_format
            extensions = {'asm': '.asm', 'hex': '.hex', 'bin': '.bin'}
            output_file = f"{base_name}{extensions.get(fmt, '.asm')}"
        
        fmt = output_format or self.config.output_format
        
        if self.config.verbose:
            print(f"\n=== ArniComp Compiler ===")
            print(f"Input:  {input_file}")
            print(f"Output: {output_file}")
            print(f"Format: {fmt}")
            print()
        
        # Create compiler
        self.compiler = self.create_compiler()
        
        try:
            # Load and process source file
            if self.config.verbose:
                print("Loading source file...")
            self.compiler.load_lines(input_file)
            
            if self.config.verbose:
                print(f"  Loaded {len(self.compiler.lines)} lines")
            
            # Preprocessing
            if self.config.verbose:
                print("Preprocessing...")
            self.compiler.break_commands()
            self.compiler.clean_lines()
            
            if self.config.verbose:
                print(f"  Processed {len(self.compiler.lines)} lines after cleanup")
            
            # Parse commands
            if self.config.verbose:
                print("Parsing commands...")
            self.compiler.group_commands()
            
            if self.config.verbose:
                print(f"  Grouped {len(self.compiler.grouped_lines)} commands")
            
            # Compile
            if self.config.verbose:
                print("Compiling to assembly...")
            self.compiler.compile_lines()
            
            assembly_lines = self.compiler.get_assembly_lines()
            
            if self.config.verbose:
                print(f"  Generated {len(assembly_lines)} assembly instructions")
            
            # Write output based on format
            self._write_output(output_file, assembly_lines, fmt)
            
            # Show statistics
            if self.config.show_stats:
                self._show_statistics(input_file, output_file, assembly_lines)
            
            print(f"\n✓ Compilation successful!")
            print(f"  Output written to: {output_file}")
            
        except Exception as e:
            print(f"\n✗ Compilation error: {e}")
            if self.config.debug_mode:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    def _write_output(self, output_file: str, assembly_lines: list[str], 
                     output_format: str) -> None:
        """Write compiled output in specified format"""
        if output_format == 'asm':
            # Write assembly directly
            with open(output_file, 'w') as f:
                for line in assembly_lines:
                    f.write(line + '\n')
        
        elif output_format == 'hex' or output_format == 'bin':
            # First need to assemble to binary (future: integrate assembler)
            print(f"Warning: Format '{output_format}' requires assembler integration")
            print(f"Writing assembly format instead...")
            with open(output_file, 'w') as f:
                for line in assembly_lines:
                    f.write(line + '\n')
        
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def _show_statistics(self, input_file: str, output_file: str, 
                        assembly_lines: list[str]) -> None:
        """Display compilation statistics"""
        print("\n=== Compilation Statistics ===")
        
        # File sizes
        input_size = os.path.getsize(input_file)
        output_size = os.path.getsize(output_file)
        
        print(f"  Input file size:          {input_size} bytes")
        print(f"  Output file size:         {output_size} bytes")
        print(f"  Assembly instructions:    {len(assembly_lines)}")
        
        # Memory usage
        if self.compiler:
            var_count = len(self.compiler.var_manager.variables)
            print(f"  Variables allocated:      {var_count}")
            
            # Calculate memory usage
            used_addresses = len(self.compiler.var_manager.addresses)
            total_var_memory = self.config.variable_end_addr - self.config.variable_start_addr
            usage_percent = (used_addresses / total_var_memory * 100) if total_var_memory > 0 else 0
            
            print(f"  Memory used:              {used_addresses}/{total_var_memory} bytes ({usage_percent:.1f}%)")
            print(f"  Stack size:               {self.config.stack_size} bytes")
        
        # Instruction type analysis
        inst_types: Dict[str, int] = {}
        for line in assembly_lines:
            line = line.strip()
            if line and not line.endswith(':'):
                inst = line.split()[0].upper()
                inst_types[inst] = inst_types.get(inst, 0) + 1
        
        if inst_types:
            print(f"\n  Instruction breakdown:")
            for inst, count in sorted(inst_types.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(assembly_lines) * 100)
                print(f"    {inst:8s} : {count:4d} ({percentage:5.1f}%)")
    
    def validate(self, input_file: str) -> None:
        """Validate source file syntax without compilation"""
        # Setup logging
        self._setup_logging()
        
        if not os.path.exists(input_file):
            print(f"Error: Input file '{input_file}' not found")
            sys.exit(1)
        
        print(f"\n=== Validating {input_file} ===\n")
        
        self.compiler = self.create_compiler()
        
        try:
            # Load and parse
            self.compiler.load_lines(input_file)
            self.compiler.break_commands()
            self.compiler.clean_lines()
            self.compiler.group_commands()
            
            print(f"✓ Syntax validation passed")
            print(f"  Total lines: {len(self.compiler.lines)}")
            print(f"  Commands: {len(self.compiler.grouped_lines)}")
            
        except Exception as e:
            print(f"✗ Validation failed: {e}")
            if self.config.debug_mode:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    def show_info(self) -> None:
        """Display compiler information and capabilities"""
        print("\n" + "="*60)
        print(" "*15 + "ArniComp Compiler")
        print("="*60)
        print("\nA high-level language compiler for the ArniComp ISA")
        print("\nSupported Features:")
        print("  • Variable declarations (byte, byte arrays, uint16)")
        print("  • Arithmetic expressions (+, -, &)")
        print("  • Control flow (if/elif/else, while loops)")
        print("  • Direct memory access (*address)")
        print("  • Array indexing with constant/variable indices")
        print("  • Memory management (automatic allocation/deallocation)")
        print("  • Register optimization and caching")
        print("  • Label management and jumps")
        print("  • Preprocessor macros (#define)")
        print("  • Direct assembly insertion (dasm/endasm)")
        
        print("\nMemory Layout:")
        print(f"  Variables:  0x{self.config.variable_start_addr:04X} - 0x{self.config.variable_end_addr:04X}")
        print(f"  Stack:      0x{self.config.stack_start_addr:04X} - 0x{self.config.stack_start_addr + self.config.stack_size - 1:04X}")
        
        print("\nCommand-Line Usage:")
        print("  python main.py compile <input.arn> [options]")
        print("  python main.py config [options]")
        print("  python main.py validate <input.arn>")
        print("  python main.py info")
        
        print("\nFor detailed help: python main.py --help")
        print("="*60 + "\n")


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser"""
    parser = argparse.ArgumentParser(
        prog='arnicomp-compiler',
        description='ArniComp High-Level Language Compiler',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compile with defaults
  python main.py compile program.arn
  
  # Compile with custom memory layout
  python main.py compile program.arn -o output.asm \\
      --var-start 0x0000 --var-end 0x0300 \\
      --stack-start 0x0300 --stack-size 512
  
  # Save configuration
  python main.py config --var-start 0x0000 --var-end 0x0400 --save
  
  # Validate syntax only
  python main.py validate program.arn
  
  # Show compiler info
  python main.py info
        """
    )
    
    # Global options
    parser.add_argument('-c', '--config', metavar='FILE',
                       help='Load configuration from JSON file')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('-d', '--debug', action='store_true',
                       help='Enable debug mode with full tracebacks')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Compile command
    compile_parser = subparsers.add_parser('compile', help='Compile source file')
    compile_parser.add_argument('input', help='Input source file (.arn)')
    compile_parser.add_argument('-o', '--output', metavar='FILE',
                               help='Output file (default: input.asm)')
    compile_parser.add_argument('-f', '--format', choices=['asm', 'hex', 'bin'],
                               default='asm', help='Output format (default: asm)')
    
    # Memory configuration
    mem_group = compile_parser.add_argument_group('Memory Configuration')
    mem_group.add_argument('--var-start', type=lambda x: int(x, 0), metavar='ADDR',
                          help='Variable memory start address (hex: 0x0000)')
    mem_group.add_argument('--var-end', type=lambda x: int(x, 0), metavar='ADDR',
                          help='Variable memory end address (hex: 0x0200)')
    mem_group.add_argument('--stack-start', type=lambda x: int(x, 0), metavar='ADDR',
                          help='Stack start address (hex: 0x0100)')
    mem_group.add_argument('--stack-size', type=int, metavar='BYTES',
                          help='Stack size in bytes (default: 256)')
    mem_group.add_argument('--memory-size', type=int, metavar='BYTES',
                          help='Total memory size (default: 65536)')
    
    # Compiler options
    opt_group = compile_parser.add_argument_group('Compiler Options')
    opt_group.add_argument('--comment-char', metavar='CHAR',
                          help='Comment character (default: //)')
    opt_group.add_argument('--no-stats', action='store_true',
                          help='Disable statistics output')
    opt_group.add_argument('-O', '--optimize', type=int, choices=[0, 1, 2],
                          metavar='LEVEL', help='Optimization level (0-2, default: 0)')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Manage configuration')
    config_parser.add_argument('--show', action='store_true',
                              help='Display current configuration')
    config_parser.add_argument('--save', action='store_true',
                              help='Save current configuration to file')
    config_parser.add_argument('--reset', action='store_true',
                              help='Reset to default configuration')
    
    # Config memory options (same as compile)
    cfg_mem = config_parser.add_argument_group('Memory Configuration')
    cfg_mem.add_argument('--var-start', type=lambda x: int(x, 0), metavar='ADDR')
    cfg_mem.add_argument('--var-end', type=lambda x: int(x, 0), metavar='ADDR')
    cfg_mem.add_argument('--stack-start', type=lambda x: int(x, 0), metavar='ADDR')
    cfg_mem.add_argument('--stack-size', type=int, metavar='BYTES')
    cfg_mem.add_argument('--memory-size', type=int, metavar='BYTES')
    cfg_mem.add_argument('--comment-char', metavar='CHAR')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate syntax')
    validate_parser.add_argument('input', help='Input source file (.arn)')
    
    # Info command
    subparsers.add_parser('info', help='Show compiler information')
    
    return parser


def main() -> None:
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Show help if no command provided
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Initialize CLI
    cli = CompilerCLI()
    
    # Load configuration
    if args.config:
        cli.load_config(args.config)
    else:
        cli.load_config()  # Try to load default config
    
    # Apply global flags
    if args.verbose:
        cli.config.verbose = True
    if args.debug:
        cli.config.debug_mode = True
    
    # Execute command
    if args.command == 'compile':
        # Apply memory configuration from command line
        if args.var_start is not None:
            cli.config.variable_start_addr = args.var_start
        if args.var_end is not None:
            cli.config.variable_end_addr = args.var_end
        if args.stack_start is not None:
            cli.config.stack_start_addr = args.stack_start
        if args.stack_size is not None:
            cli.config.stack_size = args.stack_size
        if args.memory_size is not None:
            cli.config.memory_size = args.memory_size
        if args.comment_char is not None:
            cli.config.comment_char = args.comment_char
        if args.optimize is not None:
            cli.config.optimization_level = args.optimize
        if args.no_stats:
            cli.config.show_stats = False
        
        cli.compile(args.input, args.output, args.format)
    
    elif args.command == 'config':
        # Apply configuration changes
        if args.var_start is not None:
            cli.config.variable_start_addr = args.var_start
        if args.var_end is not None:
            cli.config.variable_end_addr = args.var_end
        if args.stack_start is not None:
            cli.config.stack_start_addr = args.stack_start
        if args.stack_size is not None:
            cli.config.stack_size = args.stack_size
        if args.memory_size is not None:
            cli.config.memory_size = args.memory_size
        if args.comment_char is not None:
            cli.config.comment_char = args.comment_char
        
        if args.reset:
            cli.config = CompilerConfig()
            print("Configuration reset to defaults")
        
        if args.save:
            cli.config.to_file(cli.DEFAULT_CONFIG_PATH)
        
        if args.show or not (args.save or args.reset):
            cli.config.display()
    
    elif args.command == 'validate':
        cli.validate(args.input)
    
    elif args.command == 'info':
        cli.show_info()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)
