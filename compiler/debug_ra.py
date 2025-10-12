#!/usr/bin/env python3
"""Debug test for RA register conflict"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

from CompilerHelper import create_default_compiler

# Create simple test
test_code = """volatile byte output_port;
output_port = 42;
"""

compiler = create_default_compiler()
compiler.lines = test_code.strip().split('\n')
compiler.break_commands()
compiler.clean_lines()
compiler.group_commands()

print("Commands:")
for i, cmd in enumerate(compiler.grouped_lines):
    print(f"  {i}: {type(cmd).__name__} - {cmd}")

print("\nCompiling...")
compiler.compile_lines()

print("\nAssembly:")
for line in compiler.get_assembly_lines():
    print(f"  {line}")
