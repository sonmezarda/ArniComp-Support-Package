"""
ArniComp Emulator Web UI
Flask backend for the ArniComp CPU emulator web interface
"""

from flask import Flask, render_template, request, jsonify
import sys
import os
import tempfile
import json

# Add parent directory to path to import emulator modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from emulator.cpu import CPU
from modules.AssemblyHelper import AssemblyHelper

app = Flask(__name__)

# Global emulator instance
cpu = CPU()

# Assembly helper for compilation
assembly_helper = AssemblyHelper(
    comment_char=';', 
    label_char=':', 
    constant_keyword="const", 
    number_prefix='#',
    constant_prefix='$',
    label_prefix='@'
)

@app.route('/')
def index():
    """Serve the main emulator interface"""
    return render_template('index.html')

@app.route('/api/cpu_state', methods=['GET'])
def get_cpu_state():
    """Get current CPU state"""
    try:
        return jsonify({
            'success': True,
            'cpu': {
                'pc': cpu.pc,
                'registers': {
                    'ra': cpu.ra,
                    'rd': cpu.rd,
                    'acc': cpu.acc,
                    'marl': cpu.marl,
                    'marh': cpu.marh,
                    'prl': cpu.prl,
                    'prh': cpu.prh
                },
                'flags': {
                    'equal': cpu.flags.equal,
                    'lt': cpu.flags.lt,
                    'gt': cpu.flags.gt
                },
                'memory_mode': 'HIGH' if cpu.memory_mode_high else 'LOW',
                'data_addr': cpu.get_memory_address(),
                'halted': cpu.halted,
                'running': cpu.running,
                'output': {
                    'data': cpu.output_data,
                    'address': cpu.output_address
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/memory/<memory_type>', methods=['GET'])
def get_memory(memory_type):
    """Get memory contents"""
    try:
        start = int(request.args.get('start', 0))
        end = int(request.args.get('end', 31))
        
        if memory_type == 'data':
            memory = cpu.data_memory
        elif memory_type == 'program':
            memory = cpu.program_memory
        else:
            return jsonify({'success': False, 'error': 'Invalid memory type'})
        
        memory_data = []
        for addr in range(start, min(end + 1, len(memory))):
            memory_data.append({
                'address': addr,
                'value': memory[addr]
            })
        
        return jsonify({
            'success': True,
            'memory': memory_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/compile', methods=['POST'])
def compile_code():
    """Compile assembly code"""
    try:
        data = request.get_json()
        code = data.get('code', '')
        
        # Create temporary file for assembly code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.asm', delete=False) as temp_file:
            temp_file.write(code)
            temp_asm_path = temp_file.name
        
        try:
            # Compile assembly code
            assembly_lines = assembly_helper.parse_assembly(temp_asm_path)
            
            # Generate binary data
            binary_data = []
            lines_processed = 0
            
            for line in assembly_lines:
                if line.strip() and not line.strip().startswith(';'):
                    # This is a simplified compilation - you would need to implement
                    # full instruction encoding based on your instruction set
                    lines_processed += 1
                    
                    # For demonstration, just add some placeholder data
                    if 'ldi' in line.lower():
                        binary_data.append(0x01)  # LDI opcode
                    elif 'mov' in line.lower():
                        binary_data.append(0x02)  # MOV opcode
                    elif 'add' in line.lower():
                        binary_data.append(0x03)  # ADD opcode
                    elif 'out' in line.lower():
                        binary_data.append(0x08)  # OUT opcode
                    elif 'jne' in line.lower():
                        binary_data.append(0x07)  # JNE opcode
                    else:
                        binary_data.append(0x00)  # NOP
            
            return jsonify({
                'success': True,
                'binary_data': binary_data,
                'lines_processed': lines_processed,
                'message': f'Compiled {lines_processed} instructions'
            })
            
        finally:
            # Clean up temporary file
            os.unlink(temp_asm_path)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/load_program', methods=['POST'])
def load_program():
    """Load compiled program into emulator"""
    try:
        data = request.get_json()
        binary_data = data.get('binary_data', [])
        
        # Reset CPU before loading
        cpu.reset()
        
        # Load program into program memory
        for i, byte_val in enumerate(binary_data):
            if i < len(cpu.program_memory):
                cpu.program_memory[i] = byte_val
        
        return jsonify({
            'success': True,
            'loaded_bytes': len(binary_data)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/step', methods=['POST'])
def step_execution():
    """Execute one instruction"""
    try:
        cpu.step()
        
        return jsonify({
            'success': True,
            'halted': cpu.halted,
            'continued': not cpu.halted
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/run', methods=['POST'])
def run_execution():
    """Run the program"""
    try:
        data = request.get_json()
        max_cycles = data.get('max_cycles', 1000)
        
        cycles_executed = 0
        cpu.running = True
        
        while cycles_executed < max_cycles and not cpu.halted and cpu.running:
            cpu.step()
            cycles_executed += 1
        
        return jsonify({
            'success': True,
            'cycles_executed': cycles_executed,
            'halted': cpu.halted
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/reset', methods=['POST'])
def reset_emulator():
    """Reset the emulator"""
    try:
        cpu.reset()
        
        return jsonify({
            'success': True,
            'message': 'Emulator reset'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/disassemble', methods=['GET'])
def disassemble():
    """Disassemble program memory"""
    try:
        start = int(request.args.get('start', 0))
        count = int(request.args.get('count', 20))
        
        instructions = []
        
        for i in range(count):
            addr = start + i
            if addr >= len(cpu.program_memory):
                break
                
            opcode = cpu.program_memory[addr]
            if opcode == 0:
                continue
                
            # Basic disassembly
            hex_str = f"{opcode:02X}"
            
            # Simple instruction mapping
            instruction_map = {
                0x01: ("LDI", []),
                0x02: ("MOV", []),
                0x03: ("ADD", []),
                0x04: ("SUB", []),
                0x05: ("JMP", []),
                0x06: ("JEQ", []),
                0x07: ("JNE", []),
                0x08: ("OUT", []),
                0x09: ("IN", []),
                0x0A: ("STR", []),
                0x0B: ("LDR", []),
                0xFF: ("HLT", [])
            }
            
            if opcode in instruction_map:
                mnemonic, args = instruction_map[opcode]
            else:
                mnemonic, args = "UNK", [f"0x{opcode:02X}"]
            
            instructions.append({
                'address': addr,
                'hex': hex_str,
                'instruction': mnemonic,
                'args': args
            })
        
        return jsonify({
            'success': True,
            'instructions': instructions
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
