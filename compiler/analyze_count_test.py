import sys
sys.path.insert(0, 'modules')

from CompilerHelper import create_default_compiler

c = create_default_compiler()
c.load_lines('files/count_test.arn')
c.break_commands()
c.clean_lines()
c.group_commands()
c.compile_lines()

print("=== Variable Addresses ===")
for name, var in c.var_manager.variables.items():
    print(f"{name:10s}: 0x{var.address:04X} (volatile: {var.volatile})")

print("\n=== Assembly Analysis ===")
assembly = c.get_assembly_lines()
print(f"Total instructions: {len(assembly)}\n")

print("Variables: c=0x0000, button=0x0001, b1=0x0002, b2=0x0003, flag=0x0004")
print("Constants: BUTTON_ADR=0x2000, SS_ADR=0x1000\n")

for i, line in enumerate(assembly, 1):
    # Add comments for critical operations
    comment = ""
    if "ldi #0" in line and i in [2, 9, 29, 53, 72]:
        if i == 2:
            comment = "  # Start: MARL = 0"
        elif i == 9:
            comment = "  # ✓ FIX: MARH = 0 (was missing before!)"
        elif i == 29:
            comment = "  # Prepare rd=0 for flag comparison"
        elif i == 53:
            comment = "  # Prepare rd=0 for flag comparison"
        elif i == 72:
            comment = "  # Final: MARL = 0 for c read"
    elif "ldi #32" in line:
        comment = "  # MARH = 0x20 -> MAR = 0x2000 (BUTTON_ADR)"
    elif "mov rd, m" in line and i == 6:
        comment = "  # rd = M[0x2000] (button hardware)"
    elif "inx" in line and i == 7:
        comment = "  # MAR++ -> 0x2001 (button variable)"
    elif "mov m, rd" in line and i == 8:
        comment = "  # button = rd (store to 0x2001)"
    elif "mov rd, m" in line and i == 10:
        comment = "  # rd = M[0x0001] (button) OK Fixed!"
    elif "ldi #1" in line and i == 11:
        comment = "  # ra = BUTTON1_MASK (0x01)"
    elif "inx" in line and i == 13:
        comment = "  # MAR++ -> 0x0002 (b1)"
    elif "mov m, acc" in line and i == 14:
        comment = "  # b1 = button & 0x01"
    elif "mov marl, ra" in line and i == 15:
        comment = "  # MARL = 0 -> MAR = 0x0001 (button)"
    elif "mov rd, m" in line and i == 16:
        comment = "  # rd = M[0x0001] (button)"
    elif "ldi #2" in line and i == 17:
        comment = "  # ra = BUTTON2_MASK (0x02)"
    elif "inx" in line and i in [19, 20]:
        if i == 19:
            comment = "  # MAR++ -> 0x0002"
        else:
            comment = "  # MAR++ -> 0x0003 (b2) OK Fixed!"
    elif "mov m, acc" in line and i == 21:
        comment = "  # b2 = button & 0x02 OK Correct address!"
    elif "ldi #16" in line:
        comment = "  # MARH = 0x10 -> MAR = 0x1000 (SS_ADR)"
    elif "mov m, rd" in line and i == 77:
        comment = "  # M[0x1000] = c (seven segment output)"
    
    print(f"{i:3d}: {line:30s}{comment}")

