#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.AssemblyHelper import AssemblyHelper


def to_hex_list(binary_lines):
    return [f"{int(line.strip(), 2):02X}" for line in binary_lines]


def assemble_case(name, source_lines, expected_hex, expected_warnings=0):
    helper = AssemblyHelper()
    binary_lines, _, _ = helper.convert_to_machine_code(source_lines)
    actual_hex = to_hex_list(binary_lines)

    if actual_hex != expected_hex:
        raise AssertionError(f"{name}: expected {expected_hex}, got {actual_hex}")

    if len(helper.last_warnings) != expected_warnings:
        raise AssertionError(
            f"{name}: expected {expected_warnings} warnings, got {len(helper.last_warnings)} -> {helper.last_warnings}"
        )


def expect_error(name, source_lines, expected_substring):
    helper = AssemblyHelper()
    try:
        helper.convert_to_machine_code(source_lines)
    except Exception as exc:
        message = str(exc)
        if expected_substring.lower() not in message.lower():
            raise AssertionError(f"{name}: expected error containing '{expected_substring}', got '{message}'")
        return
    raise AssertionError(f"{name}: expected assembly to fail")


def main():
    positive_cases = [
        ("LDL RA, #5", ["LDL RA, #5"], ["C5"]),
        ("LDL RD, #31", ["LDL RD, #31"], ["FF"]),
        ("LDH RA, #7", ["LDH RA, #7"], ["37"]),
        ("MOV RA, 0", ["MOV RA, 0"], ["84"]),
        ("MOV RA, #0", ["MOV RA, #0"], ["84"]),
        ("MOV RA, ZERO", ["MOV RA, ZERO"], ["84"]),
        ("CLR RA", ["CLR RA"], ["84"]),
        ("ADDI #3", ["ADDI #3"], ["4B"]),
        ("CMP RA", ["CMP RA"], ["78"]),
        ("AND RD", ["AND RD"], ["11"]),
        ("XOR RA", ["XOR RA"], ["08"]),
        ("PUSH RA", ["PUSH RA"], ["20"]),
        ("POP RD", ["POP RD"], ["29"]),
        ("INC #1", ["INC #1"], ["02"]),
        ("INC #2", ["INC #2"], ["03"]),
        ("DEC #1", ["DEC #1"], ["04"]),
        ("DEC #2", ["DEC #2"], ["05"]),
        ("JAL", ["JAL"], ["07"]),
        ("JEQ", ["JEQ"], ["18"]),
        ("JCS", ["JCS"], ["1A"]),
        ("JLT", ["JLT"], ["1E"]),
        ("JMP", ["JMP"], ["1F"]),
        ("JGT opcode", ["JGT"], ["06"]),
        ("JLE macro", ["JLE"], ["18", "1E"]),
        ("JGE macro", ["JGE"], ["18", "06"]),
        ("JZ alias", ["JZ"], ["18"]),
        ("JGEU alias", ["JGEU"], ["1A"]),
        (
            "LDL slice const",
            ["equ CONST 0xE5", "LDL RA, $CONST[4:0]"],
            ["C5"],
        ),
        (
            "LDH slice const",
            ["equ CONST 0xE5", "LDH RD, $CONST[7:5]"],
            ["3F"],
        ),
        (
            "LDL slice label",
            ["NOP", "NOP", "target:", "LDL RA, @target[4:0]"],
            ["00", "00", "C2"],
        ),
        (
            "LDH slice label",
            ["NOP", "NOP", "target:", "LDH RD, @target[7:5]"],
            ["00", "00", "38"],
        ),
        ("LDI #10", ["LDI #10"], ["CA"]),
        ("LDI RD, #125", ["LDI RD, #125"], ["FD", "3B"]),
        (
            "LDI forward label",
            ["LDI RA, @target", "NOP", "target:", "HLT"],
            ["C2", "00", "01"],
        ),
        (
            "LDI wide constant warning",
            ["equ WIDE 0x123", "LDI RD, $WIDE"],
            ["E3", "39"],
            1,
        ),
        (
            "equ char literal",
            ["equ ON_CHAR 'A'", "LDI $ON_CHAR"],
            ["C1", "32"],
        ),
        (
            "equ char expression",
            ["equ NEXT_CHAR 'A' + 1", "LDI $NEXT_CHAR"],
            ["C2", "32"],
        ),
        ("LDI char literal", ["LDI 'A'"], ["C1", "32"]),
        ("LDI hash char literal", ["LDI #'A'"], ["C1", "32"]),
        ("LDI nul char literal", [r"LDI '\0'"], ["C0"]),
    ]

    negative_cases = [
        ("LDL bad dest", ["LDL RB, #1"], "destination must be RA or RD"),
        ("LDH too large", ["LDH RA, #8"], "out of range"),
        ("LDL too large", ["LDL RD, #32"], "out of range"),
        ("ADDI too large", ["ADDI #8"], "out of range"),
        ("INC bad value", ["INC #3"], "only accepts #1 or #2"),
        ("DEC bad value", ["DEC #0"], "only accepts #1 or #2"),
        ("ADD immediate rejected", ["ADD #3"], "use ADDI"),
        ("SUB immediate rejected", ["SUB #2"], "use SUBI"),
        (
            "LDH wrong slice width",
            ["equ CONST 0xE5", "LDH RA, $CONST[4:0]"],
            "slice width of 3 bits",
        ),
        (
            "LDL wrong slice width",
            ["equ CONST 0xE5", "LDL RD, $CONST[7:5]"],
            "slice width of 5 bits",
        ),
        (
            "Malformed slice",
            ["equ CONST 0xE5", "LDL RA, $CONST[3:5]"],
            "high bit must be >=",
        ),
        (
            "Invalid multi-char literal",
            ["equ BAD 'AB'", "LDI $BAD"],
            "exactly one character",
        ),
        (
            "Invalid multi-char immediate literal",
            ["LDI 'AB'"],
            "exactly one character",
        ),
    ]

    passed = 0
    for case in positive_cases:
        name, source_lines, expected_hex, *rest = case
        expected_warnings = rest[0] if rest else 0
        assemble_case(name, source_lines, expected_hex, expected_warnings)
        passed += 1

    for name, source_lines, expected_substring in negative_cases:
        expect_error(name, source_lines, expected_substring)
        passed += 1

    print(f"verify_final_isa.py: {passed} checks passed")


if __name__ == "__main__":
    main()
