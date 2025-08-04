"""
ArniComp Emulator Web UI
FastAPI backend for the ArniComp CPU emulator web interface
"""

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
import sys
import os
import tempfile
import json
import asyncio

# Add parent directory to path to import emulator modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


from emulator.cpu import CPU
from assembler.modules.AssemblyHelper import AssemblyHelper

app = FastAPI(title="ArniComp Emulator", description="8-bit CPU Emulator Web Interface")

# Static files and templates
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

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

# Breakpoints set
breakpoints = set()

# Pydantic models for request/response
class CompileRequest(BaseModel):
    code: str

class StepRequest(BaseModel):
    count: int = 1

class BreakpointRequest(BaseModel):
    address: int
    enabled: bool = True

class FileContent(BaseModel):
    filename: str
    content: str

class SaveFileRequest(BaseModel):
    content: str

def decode_instruction(instruction_byte):
    """Decode a single instruction byte to human-readable format"""
    try:
        # Get binary representation
        binary = format(instruction_byte, '08b')
        
        # Check if it's LDI instruction (IM7 = 1)
        if binary[0] == '1':
            # LDI instruction - immediate value
            value = instruction_byte & 0x7F  # Remove IM7 bit
            return f"LDI #{value}"
        
        # Extract opcode (bits 1-4) and argcode (bits 5-7)
        opcode = binary[1:5]
        argcode = binary[5:8]
        
        # Opcode to instruction mapping
        opcode_map = {
            '0010': 'JMP',
            '0011': 'ADDI',
            '0100': 'ADD',
            '0101': 'SUB',
            '0110': 'SUBI',
            '1000': 'MOV RA',
            '1001': 'MOV RD', 
            '1010': 'STRL/LDRL',
            '1011': 'STRH/LDRH',
            '1100': 'MOV PRL',
            '1101': 'MOV PRH',
            '1110': 'MOV MARL',
            '1111': 'OUT/IN',
            '0001': 'MOV MARH'
        }
        
        # Argcode to register mapping
        argcode_map = {
            '000': 'RA',
            '001': 'RD',
            '010': 'ML',
            '011': 'MH',
            '100': 'PCL',
            '101': 'PCH',
            '110': 'ACC',
            '111': 'P'
        }
        
        instruction = opcode_map.get(opcode, f'UNK_{opcode}')
        
        # Handle specific instructions
        if opcode == '0010':  # Jump instructions
            jump_map = {
                '000': 'JMP',
                '001': 'JGT',
                '010': 'JLT',
                '100': 'JEQ',
                '101': 'JGE',
                '110': 'JLE',
                '111': 'JNE'
            }
            return jump_map.get(argcode, f'JMP_{argcode}')
        elif opcode == '1010':  # STRL/LDRL
            if argcode in ['010', '011']:
                return f'LDR{argcode_map.get(argcode, argcode)}'
            else:
                return f'STRL {argcode_map.get(argcode, argcode)}'
        elif opcode == '1011':  # STRH/LDRH
            if argcode in ['010', '011']:
                return f'LDR{argcode_map.get(argcode, argcode)}'
            else:
                return f'STRH {argcode_map.get(argcode, argcode)}'
        elif opcode == '1111':  # OUT/IN
            if argcode == '111':
                return 'IN'
            else:
                return f'OUT {argcode_map.get(argcode, argcode)}'
        elif opcode in ['0100', '0101']:  # ADD/SUB
            base_inst = 'ADD' if opcode == '0100' else 'SUB'
            return f'{base_inst} {argcode_map.get(argcode, argcode)}'
        elif opcode.startswith('10'):  # MOV instructions
            src_reg = instruction.split()[-1] if ' ' in instruction else 'UNK'
            dst_reg = argcode_map.get(argcode, argcode)
            return f'MOV {src_reg}, {dst_reg}'
        else:
            return f'{instruction} {argcode_map.get(argcode, argcode)}'
            
    except Exception as e:
        return f"ERR_{instruction_byte:02X}"

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main emulator interface"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/cpu_state")
async def get_cpu_state():
    """Get current CPU state"""
    try:
        return {
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
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/memory/{memory_type}")
async def get_memory(
    memory_type: str,
    start: int = Query(0, ge=0),
    end: int = Query(31, ge=0)
):
    """Get memory contents"""
    try:
        if memory_type == 'data':
            memory = cpu.data_memory
        elif memory_type == 'program':
            memory = cpu.program_memory
        else:
            raise HTTPException(status_code=400, detail="Invalid memory type")
        
        memory_data = []
        for addr in range(start, min(end + 1, len(memory))):
            memory_data.append({
                'address': addr,
                'value': memory[addr]
            })
        
        return {
            'success': True,
            'memory': memory_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/compile")
async def compile_code(request: CompileRequest):
    """Compile assembly code"""
    try:
        
        lines = request.code.strip().split('\n')
        print(f"Raw lines: {lines}")  # Debug
        binary_lines, labels, constants = assembly_helper.convert_to_machine_code(lines)
        print(f"Binary lines: {binary_lines}")  # Debug
        if not binary_lines:
            return {'success': False, 'error': 'No valid instructions found'}
        
        # Convert binary strings to integers and load into CPU
        program = []
        for binary_line in binary_lines:
            if binary_line:
                program.append(int(binary_line, 2))
        
        print(f"Program: {program[:5]}...")  # Debug
        
        # Reset CPU and load program
        cpu.reset()
        cpu.load_program(program)
        
        return {
            'success': True,
            'message': f'Program compiled successfully. {len(program)} instructions loaded.',
            'instructions': len(program),
            'labels': labels,
            'constants': constants
        }
    except Exception as e:
        print(f"Compilation error: {str(e)}")  # Debug
        import traceback
        traceback.print_exc()  # Debug
        return {'success': False, 'error': str(e)}

@app.post("/api/step")
async def step_execution(request: StepRequest):
    """Execute one or more CPU steps"""
    try:
        if cpu.halted:
            return {'success': False, 'error': 'CPU is halted'}
        
        steps_executed = 0
        for i in range(request.count):
            if cpu.halted or cpu.pc in breakpoints:
                break
            
            cpu.step()
            steps_executed += 1
            
            # Small async yield to prevent blocking
            if i % 10 == 0:
                await asyncio.sleep(0)
        
        return {
            'success': True,
            'steps_executed': steps_executed,
            'cpu': {
                'pc': cpu.pc,
                'halted': cpu.halted,
                'hit_breakpoint': cpu.pc in breakpoints
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/run")
async def run_execution():
    """Run CPU until halt or breakpoint"""
    try:
        if cpu.halted:
            return {'success': False, 'error': 'CPU is halted'}
        
        cpu.running = True
        steps_executed = 0
        max_steps = 10000  # Safety limit
        
        while not cpu.halted and cpu.running and steps_executed < max_steps:
            # Check for breakpoint
            if cpu.pc in breakpoints:
                cpu.running = False
                return {
                    'success': True,
                    'message': f'Hit breakpoint at address {cpu.pc}',
                    'steps_executed': steps_executed,
                    'hit_breakpoint': True,
                    'breakpoint_address': cpu.pc
                }
            
            cpu.step()
            steps_executed += 1
            
            # Yield control periodically for responsiveness
            if steps_executed % 100 == 0:
                await asyncio.sleep(0)
        
        if steps_executed >= max_steps:
            cpu.running = False
            return {
                'success': False,
                'error': f'Execution stopped after {max_steps} steps (infinite loop protection)',
                'steps_executed': steps_executed
            }
        
        return {
            'success': True,
            'message': 'Program finished' if cpu.halted else 'Execution stopped',
            'steps_executed': steps_executed,
            'hit_breakpoint': False
        }
    except Exception as e:
        cpu.running = False
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stop")
async def stop_execution():
    """Stop CPU execution"""
    try:
        cpu.running = False
        return {'success': True, 'message': 'Execution stopped'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reset")
async def reset_cpu():
    """Reset CPU state"""
    try:
        cpu.reset()
        return {'success': True, 'message': 'CPU reset successfully'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/breakpoints")
async def get_breakpoints():
    """Get all breakpoints"""
    return {
        'success': True,
        'breakpoints': list(breakpoints)
    }

@app.post("/api/breakpoints")
async def set_breakpoint(request: BreakpointRequest):
    """Set or unset a breakpoint"""
    try:
        if request.enabled:
            breakpoints.add(request.address)
            message = f'Breakpoint set at address {request.address}'
        else:
            breakpoints.discard(request.address)
            message = f'Breakpoint removed from address {request.address}'
        
        return {
            'success': True,
            'message': message,
            'breakpoints': list(breakpoints)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/breakpoints")
async def clear_breakpoints():
    """Clear all breakpoints"""
    try:
        breakpoints.clear()
        return {
            'success': True,
            'message': 'All breakpoints cleared',
            'breakpoints': []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/disassemble")
async def disassemble(
    start: int = Query(0, ge=0),
    count: int = Query(32, ge=1, le=1024)
):
    """Disassemble program memory"""
    try:
        instructions = []
        
        for addr in range(start, min(start + count, len(cpu.program_memory))):
            instruction_byte = cpu.program_memory[addr]
            decoded = decode_instruction(instruction_byte)
            
            instructions.append({
                'address': addr,
                'hex': f"{instruction_byte:02X}",
                'binary': f"{instruction_byte:08b}",
                'instruction': decoded
            })
        
        return {
            'success': True,
            'instructions': instructions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files")
async def list_files():
    """List available assembly files"""
    try:
        files_dir = os.path.join(os.path.dirname(__file__), '..', 'files')
        if not os.path.exists(files_dir):
            return {'success': True, 'files': []}
        
        files = []
        for filename in os.listdir(files_dir):
            if filename.endswith('.asm'):
                file_path = os.path.join(files_dir, filename)
                stat = os.stat(file_path)
                files.append({
                    'name': filename,
                    'size': stat.st_size,
                    'modified': stat.st_mtime
                })
        
        return {'success': True, 'files': files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files/{filename}")
async def load_file(filename: str):
    """Load an assembly file"""
    try:
        files_dir = os.path.join(os.path.dirname(__file__), '..', 'files')
        file_path = os.path.join(files_dir, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        if not filename.endswith('.asm'):
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            'success': True,
            'filename': filename,
            'content': content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/files/{filename}")
async def save_file(filename: str, request: SaveFileRequest):
    """Save an assembly file"""
    try:
        files_dir = os.path.join(os.path.dirname(__file__), '..', 'files')
        os.makedirs(files_dir, exist_ok=True)
        
        # Ensure .asm extension
        if not filename.endswith('.asm'):
            filename += '.asm'
        
        file_path = os.path.join(files_dir, filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(request.content)
        
        return {
            'success': True,
            'message': f'File {filename} saved successfully',
            'filename': filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000, reload=False)
