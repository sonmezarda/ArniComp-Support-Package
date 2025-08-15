from compiler.modules.CompilerHelper import create_default_compiler
from compiler.modules.Commands import AssignCommand, VarDefCommandWithoutValue


def main():
    c = create_default_compiler()
    # define scalar
    c.set_grouped_lines([
        VarDefCommandWithoutValue('byte x;'),
    ])
    c.compile_lines()

    # assign scalar
    c.set_grouped_lines([
        AssignCommand('x = 5'),
    ])
    c.compile_lines()

    # define array
    c.set_grouped_lines([
        VarDefCommandWithoutValue('byte[3] arr;'),
    ])
    c.compile_lines()

    # assign array element
    c.set_grouped_lines([
        AssignCommand('arr[1] = 7'),
    ])
    c.compile_lines()

    print('\n'.join(c.get_assembly_lines()))


if __name__ == '__main__':
    main()
