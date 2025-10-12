#!/usr/bin/env python3
"""
Comprehensive test suite for compiler optimizations
Tests compile-time evaluation, volatile handling
"""

import subprocess
import os

class TestResult:
    def __init__(self, name, expected_instructions, actual_instructions, passed, details=""):
        self.name = name
        self.expected = expected_instructions
        self.actual = actual_instructions
        self.passed = passed
        self.details = details
    
    def __str__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"{status} | {self.name}: {self.actual} instr (expected: {self.expected}) {self.details}"

def compile_test(arn_file):
    """Compile .arn file and return statistics"""
    result = subprocess.run(
        ['python3.13', 'main.py', 'compile', arn_file],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(__file__)
    )
    
    # Parse output
    output = result.stdout
    instructions = 0
    variables = 0
    memory_used = 0
    
    for line in output.split('\n'):
        if 'Assembly instructions:' in line:
            instructions = int(line.split(':')[1].strip())
        elif 'Variables allocated:' in line:
            variables = int(line.split(':')[1].strip())
        elif 'Memory used:' in line:
            memory_used = int(line.split(':')[1].strip().split('/')[0])
    
    success = result.returncode == 0
    return success, instructions, variables, memory_used, output

def run_emulator_test(asm_file, expected_mem_values):
    """Run assembly file in emulator and check memory values"""
    cpu = CPU()
    
    # Load and run program
    try:
        cpu.load_program_from_asm_file(asm_file)
        
        # Run until HLT or max cycles
        max_cycles = 1000
        cycles = 0
        while cycles < max_cycles:
            if cpu.halted:
                break
            cpu.step()
            cycles += 1
        
        # Check expected memory values
        results = {}
        for addr, expected_val in expected_mem_values.items():
            actual_val = cpu.bus.read(addr)
            results[addr] = (actual_val, expected_val, actual_val == expected_val)
        
        return True, results, cycles
    except Exception as e:
        return False, str(e), 0

def test_suite():
    """Run all tests"""
    print("=" * 80)
    print("COMPILER OPTIMIZATION TEST SUITE")
    print("=" * 80)
    print()
    
    tests = []
    
    # Test 1: Pure compile-time evaluation
    print("Test 1: Pure Compile-Time Evaluation")
    print("-" * 80)
    success, instr, vars, mem, output = compile_test('./files/test_pure_compiletime.arn')
    test1 = TestResult(
        "Pure compile-time",
        expected_instructions=0,
        actual_instructions=instr,
        passed=(instr == 0),
        details=f"| {vars} vars, {mem} bytes"
    )
    tests.append(test1)
    print(test1)
    print()
    
    # Test 2: Volatile variables
    print("Test 2: Volatile Variables")
    print("-" * 80)
    success, instr, vars, mem, output = compile_test('./files/test_volatile.arn')
    test2 = TestResult(
        "Volatile variables",
        expected_instructions=">0",
        actual_instructions=instr,
        passed=(instr > 0),
        details=f"| {vars} vars, {mem} bytes"
    )
    tests.append(test2)
    print(test2)
    print()
    
    # Test 3: Basic operations
    print("Test 3: Basic Operations")
    print("-" * 80)
    success, instr, vars, mem, output = compile_test('./files/test_control_flow.arn')
    test3 = TestResult(
        "Basic operations",
        expected_instructions=0,
        actual_instructions=instr,
        passed=(instr == 0),
        details=f"| {vars} vars, {mem} bytes"
    )
    tests.append(test3)
    print(test3)
    print()
    
    # Test 4: Array operations
    print("Test 4: Array Operations")
    print("-" * 80)
    success, instr, vars, mem, output = compile_test('./files/test_array_ops.arn')
    test4 = TestResult(
        "Array operations",
        expected_instructions=0,
        actual_instructions=instr,
        passed=(instr == 0),
        details=f"| {vars} vars, {mem} bytes"
    )
    tests.append(test4)
    print(test4)
    print()
    
    # Test 5: Mixed scenario
    print("Test 5: Mixed Compile-Time + Runtime")
    print("-" * 80)
    success, instr, vars, mem, output = compile_test('./files/array_mixed_test.arn')
    test5 = TestResult(
        "Mixed scenario",
        expected_instructions=">0",
        actual_instructions=instr,
        passed=(instr > 0 and instr < 20),
        details=f"| {vars} vars, {mem} bytes"
    )
    tests.append(test5)
    print(test5)
    print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    passed = sum(1 for t in tests if t.passed)
    total = len(tests)
    print(f"Tests passed: {passed}/{total}")
    print()
    
    for test in tests:
        print(test)
    
    print()
    return passed == total

if __name__ == "__main__":
    success = test_suite()
    sys.exit(0 if success else 1)
