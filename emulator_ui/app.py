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

def decode_instruction(instruction_byte):
    """Decode a single instruction byte to human-readable format"""
    return assembly_helper.disassemble_instruction(instruction_byte)

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
        
        # Split code into lines
        raw_lines = code.strip().split('\n')
        
        # Process assembly code using AssemblyHelper step by step
        try:
            print(f"DEBUG: Starting compilation with {len(raw_lines)} lines")
            
            # Step 1: Upper lines
            clines = assembly_helper.upper_lines(raw_lines)
            print(f"DEBUG: After upper_lines: {len(clines)} lines")
            
            # Step 2: Remove whitespaces
            clines = assembly_helper.remove_whitespaces_lines(raw_lines)
            print(f"DEBUG: After remove_whitespaces: {len(clines)} lines")
            
            # Step 3: Get constants
            constants = assembly_helper.get_constants(clines)
            print(f"DEBUG: Found constants: {constants}")
            
            # Step 4: Remove constants
            clines = assembly_helper.remove_constants(clines)
            print(f"DEBUG: After remove_constants: {len(clines)} lines")
            
            # Step 5: Get labels
            labels = assembly_helper.get_labels(clines)
            print(f"DEBUG: Found labels: {labels}")
            
            # Step 6: Remove labels
            clines = assembly_helper.remove_labels(clines)
            print(f"DEBUG: After remove_labels: {len(clines)} lines")
            
            # Step 7: Change labels
            clines = assembly_helper.change_labels(clines, labels)
            print(f"DEBUG: After change_labels: {len(clines)} lines")
            
            # Step 8: Change constants
            clines = assembly_helper.change_constants(clines, constants)
            print(f"DEBUG: After change_constants: {len(clines)} lines")
            
            # Step 9: Convert to binary lines
            blines = assembly_helper.convert_to_binary_lines(clines)
            print(f"DEBUG: After convert_to_binary_lines: {len(blines)} lines")
            
            # Convert binary strings to integers
            binary_data = []
            for i, binary_str in enumerate(blines):
                if binary_str.strip():
                    try:
                        binary_data.append(int(binary_str.strip(), 2))
                    except ValueError as ve:
                        print(f"Invalid binary string at line {i}: {binary_str} - {ve}")
                        continue
            
            return jsonify({
                'success': True,
                'binary_data': binary_data,
                'lines_processed': len(blines),
                'message': f'Compiled {len(blines)} instructions',
                'constants': constants,
                'labels': labels,
                'debug_info': {
                    'raw_lines': len(raw_lines),
                    'cleaned_lines': len(clines),
                    'binary_lines': len(blines)
                }
            })
            
        except Exception as compile_error:
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False, 
                'error': f'Compilation error: {str(compile_error)}',
                'debug_info': {
                    'raw_lines': raw_lines[:5],  # First 5 lines for debugging
                    'error_type': type(compile_error).__name__,
                    'traceback': traceback.format_exc()
                }
            })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'General error: {str(e)}', 'traceback': traceback.format_exc()})

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
                
            # Decode instruction using our decoder
            decoded = decode_instruction(opcode)
            hex_str = f"{opcode:02X}"
            
            instructions.append({
                'address': addr,
                'hex': hex_str,
                'instruction': decoded
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

@app.route('/api/save_file', methods=['POST'])
def save_file():
    """Save assembly code to file"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        content = data.get('content')
        
        if not filename or not content:
            return jsonify({
                'success': False,
                'error': 'Filename and content required'
            })
        
        # Ensure files directory exists
        files_dir = os.path.join(os.path.dirname(__file__), '..', 'files')
        os.makedirs(files_dir, exist_ok=True)
        
        # Save file
        filepath = os.path.join(files_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({
            'success': True,
            'message': f'File {filename} saved successfully',
            'filepath': filepath
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/load_file', methods=['POST'])
def load_file():
    """Load assembly code from file"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({
                'success': False,
                'error': 'Filename required'
            })
        
        # Load file
        files_dir = os.path.join(os.path.dirname(__file__), '..', 'files')
        filepath = os.path.join(files_dir, filename)
        
        if not os.path.exists(filepath):
            return jsonify({
                'success': False,
                'error': f'File {filename} not found'
            })
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            'success': True,
            'content': content,
            'filename': filename
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/list_files', methods=['GET'])
def list_files():
    """List available assembly files"""
    try:
        files_dir = os.path.join(os.path.dirname(__file__), '..', 'files')
        
        if not os.path.exists(files_dir):
            return jsonify({
                'success': True,
                'files': []
            })
        
        # Get all .asm files
        files = []
        for filename in os.listdir(files_dir):
            if filename.endswith('.asm'):
                filepath = os.path.join(files_dir, filename)
                stat = os.stat(filepath)
                files.append({
                    'name': filename,
                    'size': stat.st_size,
                    'modified': stat.st_mtime
                })
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            'success': True,
            'files': files
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
