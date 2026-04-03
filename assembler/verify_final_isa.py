#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
import tempfile


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


def assert_listing_case(name, source_lines, expected_listing_fragments, mode="hex"):
    helper = AssemblyHelper()
    helper.convert_to_machine_code(source_lines, source_name="listing_case.asm")
    listing_lines = helper.format_listing(mode)
    listing_text = "".join(listing_lines)

    if not listing_lines:
        raise AssertionError(f"{name}: expected non-empty listing output")

    for fragment in expected_listing_fragments:
        if fragment not in listing_text:
            raise AssertionError(f"{name}: expected listing fragment '{fragment}' in:\n{listing_text}")


def assemble_file_case(name, root_file_contents, expected_hex, include_files=None, expected_warnings=0):
    include_files = include_files or {}
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        root_path = tmp_path / "root.asm"
        root_path.write_text(root_file_contents, encoding="utf-8")
        for rel_path, contents in include_files.items():
            file_path = tmp_path / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(contents, encoding="utf-8")

        helper = AssemblyHelper()
        binary_lines, _, _ = helper.convert_to_machine_code(root_path.read_text(encoding="utf-8").splitlines(), source_name=str(root_path))
        actual_hex = to_hex_list(binary_lines)

        if actual_hex != expected_hex:
            raise AssertionError(f"{name}: expected {expected_hex}, got {actual_hex}")

        if len(helper.last_warnings) != expected_warnings:
            raise AssertionError(
                f"{name}: expected {expected_warnings} warnings, got {len(helper.last_warnings)} -> {helper.last_warnings}"
            )


def expect_file_error(name, root_file_contents, expected_substring, include_files=None):
    include_files = include_files or {}
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        root_path = tmp_path / "root.asm"
        root_path.write_text(root_file_contents, encoding="utf-8")
        for rel_path, contents in include_files.items():
            file_path = tmp_path / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(contents, encoding="utf-8")

        helper = AssemblyHelper()
        try:
            helper.convert_to_machine_code(root_path.read_text(encoding="utf-8").splitlines(), source_name=str(root_path))
        except Exception as exc:
            message = str(exc)
            if expected_substring.lower() not in message.lower():
                raise AssertionError(f"{name}: expected error containing '{expected_substring}', got '{message}'")
            return
        raise AssertionError(f"{name}: expected assembly to fail")


def main():
    positive_cases = [
        ("LDL RA, #5", ["LDL RA, #5"], ["C5"]),
        ("inline label instruction", ["start: NOP", "HLT"], ["00", "01"]),
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
        ("JEQ target default RA", ["JEQ done", "done:", "NOP"], ["C4", "A8", "B4", "18", "00"]),
        ("JMP target with RD", ["JMP done :RD", "done:", "NOP"], ["E4", "A9", "B4", "1F", "00"]),
        ("JLE target macro", ["JLE done", "done:", "NOP"], ["C5", "A8", "B4", "18", "1E", "00"]),
        ("JLEU macro", ["JLEU"], ["1B", "18"]),
        ("JLEU target macro", ["JLEU done", "done:", "NOP"], ["C5", "A8", "B4", "1B", "18", "00"]),
        ("JGT opcode", ["JGT"], ["06"]),
        ("JLE macro", ["JLE"], ["18", "1E"]),
        ("JGE macro", ["JGE"], ["18", "06"]),
        ("JGTU target macro", ["JGTU done", "done:", "NOP"], ["C9", "A8", "B4", "1B", "18", "C9", "A8", "B4", "1F", "00"]),
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
        ("equ LOW helper", ["equ LO LOW(0x1234)", "LDI $LO"], ["D4", "31"]),
        ("equ HIGH helper", ["equ HI HIGH(0x1234)", "LDI $HI"], ["D2"]),
        ("equ BITS helper", ["equ MID BITS(0xE5, 7, 5)", "LDI $MID"], ["C7"]),
        ("LDI LOW label", ["NOP", "NOP", "target:", "LDI LOW(@target)"], ["00", "00", "C2"]),
        ("LDI HIGH label", ["NOP", "target:", "LDI HIGH(@target)"], ["00", "C0"]),
        ("LDL BITS const", ["equ VALUE 0xE5", "LDL RA, BITS($VALUE, 4, 0)"], ["C5"]),
        ("LDH BITS const", ["equ VALUE 0xE5", "LDH RD, BITS($VALUE, 7, 5)"], ["3F"]),
        ("CALL bare label default RA", ["CALL target", "target:", "NOP"], ["C4", "A8", "B4", "07", "00"]),
        ("CALL label with RD temp", ["CALL target :RD", "target:", "NOP"], ["E4", "A9", "B4", "07", "00"]),
        (
            "CALL constant high byte",
            ["equ TARGET 0x0123", "CALL $TARGET"],
            ["C3", "31", "A8", "C1", "B0", "07"],
        ),
        ("JMPA bare label default RA", ["JMPA target", "target:", "NOP"], ["C4", "A8", "B4", "1F", "00"]),
        ("JMPA label with RD temp", ["JMPA target :RD", "target:", "NOP"], ["E4", "A9", "B4", "1F", "00"]),
        (
            "JMPA constant high byte",
            ["equ TARGET 0x0123", "JMPA $TARGET"],
            ["C3", "31", "A8", "C1", "B0", "1F"],
        ),
        ("RET via LR", ["RET"], ["AD", "B6", "1F"]),
        ("RET via stack", ["RET :STACK"], ["2E", "2D", "1F"]),
        ("PUSHI immediate default RA", ["PUSHI #5"], ["C5", "20"]),
        ("PUSHI char default RA", ["PUSHI 'A'"], ["C1", "32", "20"]),
        ("PUSHI immediate RD temp", ["PUSHI #5 :RD"], ["E5", "21"]),
        ("PUSHI nul char", [r"PUSHI '\0'"], ["C0", "20"]),
        (
            "PUSHI sliced constant",
            ["equ VALUE 0x1234", "PUSHI $VALUE[7:0] :RD"],
            ["F4", "39", "21"],
        ),
        ("PUSHSTR basic", ['PUSHSTR "OK"'], ["CB", "32", "20", "CF", "32", "20"]),
        ("PUSHSTR with terminator", ['PUSHSTR "A", \'\\0\''], ["C0", "20", "C1", "32", "20"]),
        ("PUSHSTR with RD temp", ['PUSHSTR "A" :RD'], ["E1", "3A", "21"]),
        ("fill default zero", [".fill 3"], ["00", "00", "00"]),
        ("fill custom byte", [".fill 3, #0xAA"], ["AA", "AA", "AA"]),
        ("org padding", ["NOP", ".org 4", "HLT"], ["00", "00", "00", "00", "01"]),
        ("org custom fill", ["NOP", ".org 4, #0xFF", "HLT"], ["00", "FF", "FF", "FF", "01"]),
        ("align padding", ["NOP", ".align 4", "HLT"], ["00", "00", "00", "00", "01"]),
        ("align custom fill", ["NOP", ".align 4, #0x7E", "HLT"], ["00", "7E", "7E", "7E", "01"]),
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
        (
            "CALL bad suffix",
            ["CALL target :RB", "target:", "NOP"],
            "temporary register suffix must be :RA or :RD",
        ),
        (
            "JMPA bad suffix",
            ["JMPA target :RB", "target:", "NOP"],
            "temporary register suffix must be :RA or :RD",
        ),
        (
            "JGTU bare not supported",
            ["JGTU"],
            "requires an explicit target operand",
        ),
        (
            "RET bad mode",
            ["RET :RD"],
            "RET supports only 'RET' or 'RET :STACK'",
        ),
        (
            "PUSHI bad suffix",
            ["PUSHI #1 :RB"],
            "temporary register suffix must be :RA or :RD",
        ),
        (
            "PUSHI bad slice width",
            ["equ VALUE 0x12", "PUSHI $VALUE[4:0]"],
            "exactly 8 bits wide",
        ),
        (
            "PUSHSTR bad string",
            ["PUSHSTR 5"],
            "quoted string literal",
        ),
        (
            "org backwards",
            ["NOP", ".org 0"],
            "behind current address",
        ),
        (
            "align zero",
            [".align 0"],
            "greater than zero",
        ),
        (
            "fill negative",
            [".fill -1"],
            "non-negative",
        ),
        (
            "fill byte too large",
            [".fill 1, 256"],
            "out of range",
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

    assemble_file_case(
        "include relative file",
        '.include "defs/common.inc"\nLDI $VALUE\n',
        ["C5"],
        include_files={"defs/common.inc": "equ VALUE 5\n"},
    )
    passed += 1

    assemble_file_case(
        "import selected function with nested include",
        '.import "lib/math.asm" mul_func\nstart: NOP\n',
        ["00", "C5", "AD", "B6", "1F"],
        include_files={
            "lib/math.asm": (
                '.include "defs.inc"\n'
                '.export mul_func\n'
                '.func\n'
                'mul_func:\n'
                '    ldi $VALUE\n'
                '    ret\n'
                '.endfunc\n'
                '.export unused_func\n'
                '.func\n'
                'unused_func:\n'
                '    hlt\n'
                '.endfunc\n'
            ),
            "lib/defs.inc": "equ VALUE 5\n",
        },
    )
    passed += 1

    assemble_file_case(
        "import duplicate function only once",
        '.import "lib/math.asm" mul_func\n.import "lib/math.asm" mul_func\nstart: NOP\n',
        ["00", "C5", "AD", "B6", "1F"],
        include_files={
            "lib/math.asm": (
                ".export mul_func\n"
                ".func\n"
                "mul_func:\n"
                "    ldi #5\n"
                "    ret\n"
                ".endfunc\n"
            ),
        },
    )
    passed += 1

    assemble_case(
        "repeat block",
        [
            ".repeat 3 {",
            "NOP",
            "}",
        ],
        ["00", "00", "00"],
    )
    passed += 1

    assemble_case(
        "nested repeat block",
        [
            ".repeat 2 {",
            ".repeat 2 {",
            "NOP",
            "}",
            "}",
        ],
        ["00", "00", "00", "00"],
    )
    passed += 1

    assemble_case(
        "define if true branch",
        [
            ".define FPGA 1",
            ".if FPGA",
            "NOP",
            ".else",
            "HLT",
            ".endif",
        ],
        ["00"],
    )
    passed += 1

    assemble_case(
        "define if false branch",
        [
            ".define FPGA 0",
            ".if FPGA",
            "NOP",
            ".else",
            "HLT",
            ".endif",
        ],
        ["01"],
    )
    passed += 1

    assemble_case(
        "nested if branch",
        [
            ".define OUTER 1",
            ".define INNER 0",
            ".if OUTER",
            ".if INNER",
            "HLT",
            ".else",
            "NOP",
            ".endif",
            ".else",
            "HLT",
            ".endif",
        ],
        ["00"],
    )
    passed += 1

    expect_file_error(
        "include missing file",
        '.include "missing.inc"\nNOP\n',
        "Included file not found",
    )
    passed += 1

    expect_file_error(
        "import missing export",
        '.import "lib/math.asm" mul_func\nNOP\n',
        "is not exported",
        include_files={
            "lib/math.asm": (
                ".func\n"
                "mul_func:\n"
                "    ret\n"
                ".endfunc\n"
            ),
        },
    )
    passed += 1

    expect_file_error(
        "import func requires label",
        '.import "lib/math.asm" mul_func\nNOP\n',
        "first line after .func must be a label",
        include_files={
            "lib/math.asm": (
                ".export mul_func\n"
                ".func\n"
                "    nop\n"
                ".endfunc\n"
            ),
        },
    )
    passed += 1

    expect_error(
        "repeat missing brace",
        [
            ".repeat 2 {",
            "NOP",
        ],
        "missing closing",
    )
    passed += 1

    expect_error(
        "if missing endif",
        [
            ".if 1",
            "NOP",
        ],
        "missing closing '.endif'",
    )
    passed += 1

    expect_error(
        "else without if",
        [
            ".else",
            "NOP",
        ],
        "unexpected .else",
    )
    passed += 1

    expect_error(
        "endif without if",
        [
            ".endif",
        ],
        "unexpected .endif",
    )
    passed += 1

    assert_listing_case(
        "listing output hex",
        [
            "start: NOP",
            "CALL done",
            "done: HLT",
        ],
        [
            "; Source: listing_case.asm",
            "0000  00",
            "[1] start: NOP",
            "[2] CALL done",
            "[3] done: HLT",
            "0001  C5 A8 B4 07",
            "0005  01",
        ],
    )
    passed += 1

    assert_listing_case(
        "listing output asm",
        [
            "start: NOP",
            "CALL done",
            "done: HLT",
        ],
        [
            "; Source: listing_case.asm",
            "0000  [1] start: NOP",
            "0001  [2] CALL done",
            "0005  [3] done: HLT",
            "0001  C5  LDL RA, #5",
            "0002  A8  MOV PRL, RA",
            "0003  B4  MOV PRH, ZERO",
            "0004  07  JAL",
            "0005  01  HLT",
        ],
        mode="asm",
    )
    passed += 1

    assert_listing_case(
        "listing output both",
        [
            "start: NOP",
            "CALL done",
            "done: HLT",
        ],
        [
            "; Source: listing_case.asm",
            "[2] CALL done",
            "0001  C5 A8 B4 07",
            "0001  C5  LDL RA, #5",
            "00",
        ],
        mode="both",
    )
    passed += 1

    print(f"verify_final_isa.py: {passed} checks passed")


if __name__ == "__main__":
    main()
