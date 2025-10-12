from modules.CompilerHelper import create_default_compiler

# Test dereference functionality
c = create_default_compiler()
c.load_lines('files/test_deref.arn')
c.break_commands()
c.clean_lines()
c.group_commands()
c.compile_lines()
print('\n'.join(c.get_assembly_lines()))
