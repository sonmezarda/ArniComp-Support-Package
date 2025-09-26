import sys
from pathlib import Path

# Add compiler/modules to sys.path to match project's absolute imports style
ROOT = Path(__file__).resolve().parents[1]
MODULES_DIR = ROOT / 'compiler' / 'modules'
sys.path.insert(0, str(MODULES_DIR))

from CompilerHelper import create_default_compiler


def main():
    c = create_default_compiler()
    # Load test program from compiler/files to match repo structure
    from pathlib import Path
    root = ROOT
    arn_path = root / 'compiler' / 'files' / 'count_test.arn'
    c.load_lines(str(arn_path))
    c.break_commands()
    c.clean_lines()
    c.group_commands()
    c.compile_lines()
    print('\n'.join(c.get_assembly_lines()))


if __name__ == '__main__':
    main()
