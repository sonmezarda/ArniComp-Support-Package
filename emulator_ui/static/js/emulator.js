/**
 * ArniComp Emulator Frontend
 * JavaScript logic for the web-based emulator interface
 */

class ArniCompEmulator {
    constructor() {
        this.editor = null;
        this.isRunning = false;
        this.compiledProgram = null;
        this.autoRefresh = true;
        this.dataFormat = 'hex'; // Default format
        
        // Breakpoint system
        this.breakpoints = new Set();
    this.selectedAddress = null; // disassembly selected line address
        
        // Settings
        this.settings = {
            dataMemoryStartAddress: '0000',
            dataMemoryEndAddress: '00FF',
            programMemoryStartAddress: '0000',
            programMemoryEndAddress: '00FF',
            disassemblyInstructionCount: 32,
            autoRefresh: true
        };
        
        // Tab system
        this.tabs = new Map();
        this.activeTabId = null;
        this.tabCounter = 1;
        
        this.loadSettings();
        this.initializeEditor();
        this.initializeEventListeners();
        this.initializeTabs();
        this.initializeResizers();
        // Collapsible panels removed due to new tab-based layout
        
        this.initializeDisassembly(); // Initialize disassembly with empty lines
        this.refreshAll();
        
        // Auto-refresh only when running (much slower interval)
        setInterval(() => {
            if (this.isRunning && this.autoRefresh) {
                this.refreshCPUState();
            }
        }, 500); // Reduced frequency from 100ms to 500ms
    }

    initializeEditor() {
        // Initialize ACE editor
        this.editor = ace.edit("editor");
        this.editor.setTheme("ace/theme/monokai");
        this.editor.session.setMode("ace/mode/assembly_x86");
        this.editor.setOptions({
            fontSize: 14,
            showLineNumbers: true,
            showGutter: true,
            highlightActiveLine: true,
            wrap: true
        });

        // Update cursor position
        this.editor.selection.on('changeCursor', () => {
            const cursor = this.editor.getCursorPosition();
            document.getElementById('cursor-position').textContent = 
                `Line: ${cursor.row + 1}, Col: ${cursor.column + 1}`;
        });

        // Track content changes for dirty state
        this.editor.session.on('change', () => {
            if (this.activeTabId) {
                const tab = this.tabs.get(this.activeTabId);
                if (tab && tab.saved) {
                    tab.saved = false;
                    this.updateTabTitle(this.activeTabId);
                }
            }
        });
    }

    initializeEventListeners() {
        // Control buttons
        document.getElementById('reset-btn').addEventListener('click', () => this.resetEmulator());
        document.getElementById('compile-btn').addEventListener('click', () => this.compileCode());
        document.getElementById('step-btn').addEventListener('click', () => this.stepExecution());
        document.getElementById('run-btn').addEventListener('click', () => this.runExecution());
        document.getElementById('stop-btn').addEventListener('click', () => this.stopExecution());

        // Breakpoint controls
    document.getElementById('toggle-breakpoint-btn').addEventListener('click', () => this.toggleSelectedOrPromptBreakpoint());
        document.getElementById('clear-breakpoints-btn').addEventListener('click', () => this.clearAllBreakpoints());

        // Settings button
        document.getElementById('settings-btn').addEventListener('click', () => this.openSettingsModal());

        // Memory refresh buttons
        document.getElementById('refresh-data-memory').addEventListener('click', () => this.refreshDataMemory());
        document.getElementById('refresh-program-memory').addEventListener('click', () => this.refreshProgramMemory());
        document.getElementById('refresh-cpu-btn').addEventListener('click', () => this.refreshCPUState());

        // Data format selector
        document.getElementById('data-format').addEventListener('change', (e) => {
            this.dataFormat = e.target.value;
            this.refreshCPUState(); // Update register display
        });

        // View tabs
        document.querySelectorAll('.view-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.switchView(e.target.dataset.view);
            });
        });

        // Memory address inputs
        ['data-memory-start', 'data-memory-end', 'program-memory-start', 'program-memory-end'].forEach(id => {
            document.getElementById(id).addEventListener('change', () => {
                if (id.includes('data')) {
                    this.refreshDataMemory();
                } else {
                    this.refreshProgramMemory();
                }
            });
        });
    }

    loadSampleCode() {
        const sampleCode = `; ArniComp Sample Program
; This program demonstrates basic functionality

const x = 5
const y = 10

ldi @main
mov prl, ra

ldi #0
mov rd, ra

main:
    ldi $x      ; Load constant x into RA
    add ra      ; Add RA to ACC (ACC = RD + RA)
    
    ldi $y      ; Load constant y into RA  
    add ra      ; Add RA to ACC (ACC = ACC + RA)
    
    ; Store result in memory
    ldi #0
    mov marl, ra
    strl acc
    
    ; Output result
    out acc
    
    ; Simple loop
    mov rd, acc
    ldi #15
    add ra      ; Compare RD with 15
    
    jne         ; Jump back if not equal

; End of program
ldi #0b11111111
`;
        this.editor.setValue(sampleCode, -1);
    }

    async apiCall(endpoint, method = 'GET', data = null) {
        try {
            const options = {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                }
            };

            if (data) {
                options.body = JSON.stringify(data);
            }

            const response = await fetch(endpoint, options);
            const result = await response.json();

            if (!result.success) {
                throw new Error(result.error || 'API call failed');
            }

            return result;
        } catch (error) {
            console.error('API Error:', error);
            this.showStatus(`Error: ${error.message}`, 'error');
            throw error;
        }
    }

    showStatus(message, type = 'info') {
        const statusElement = document.getElementById('emulator-status');
        statusElement.textContent = message;
        statusElement.className = `status-${type}`;
        
        // Auto-clear status after 3 seconds
        setTimeout(() => {
            if (statusElement.textContent === message) {
                statusElement.textContent = 'Ready';
                statusElement.className = '';
            }
        }, 3000);
    }

    async compileCode() {
        try {
            this.showStatus('Compiling...', 'info');
            document.getElementById('compile-status').textContent = 'Compiling...';

            const code = this.editor.getValue();
            const result = await this.apiCall('/api/compile', 'POST', { code });

            if (result.success) {
                document.getElementById('compile-status').textContent = 
                    `Compiled: ${result.instructions} instructions loaded`;
                
                this.showStatus('Compilation successful', 'success');
                
                // Refresh disassembly and state
                this.refreshAll();
            } else {
                document.getElementById('compile-status').textContent = 'Compilation failed';
                this.showStatus(`Compilation error: ${result.error}`, 'error');
            }
            
        } catch (error) {
            document.getElementById('compile-status').textContent = 'Compilation failed';
            this.showStatus(`Compilation error: ${error.message}`, 'error');
        }
    }

    async resetEmulator() {
        try {
            await this.apiCall('/api/reset', 'POST');
            this.showStatus('Emulator reset', 'info');
            this.isRunning = false;
            this.updateRunControls();
            this.refreshAll();
            
        } catch (error) {
            this.showStatus(`Reset error: ${error.message}`, 'error');
        }
    }

    async stepExecution() {
        try {
            const stepCount = parseInt(document.getElementById('step-count').value) || 1;
            const result = await this.apiCall('/api/step', 'POST', { count: stepCount });
            console.log('Step result:', result);
            
            if (result.success) {
                if (result.cpu.halted) {
                    this.showStatus(`Program halted after ${result.steps_executed} steps`, 'warning');
                    this.isRunning = false;
                    this.updateRunControls();
                } else if (result.cpu.hit_breakpoint) {
                    this.showStatus(`Hit breakpoint at address ${result.cpu.pc} after ${result.steps_executed} steps`, 'info');
                    this.isRunning = false;
                    this.updateRunControls();
                } else {
                    this.showStatus(`Executed ${result.steps_executed} step${result.steps_executed > 1 ? 's' : ''}`, 'success');
                }
                
                // Refresh all displays
                this.refreshAll();
            } else {
                this.showStatus(result.error, 'error');
            }
            
        } catch (error) {
            console.error('Step execution error:', error);
            this.showStatus(`Step error: ${error.message}`, 'error');
        }
    }

    async runExecution() {
        try {
            this.isRunning = true;
            this.updateRunControls();
            this.showStatus('Running...', 'info');
            
            const result = await this.apiCall('/api/run', 'POST');
            
            this.isRunning = false;
            this.updateRunControls();
            
            if (result.success) {
                document.getElementById('execution-info').textContent = 
                    `Executed ${result.steps_executed} steps`;
                
                if (result.hit_breakpoint) {
                    this.showStatus(`Hit breakpoint at address ${result.breakpoint_address}`, 'info');
                } else if (result.message.includes('finished')) {
                    this.showStatus('Program completed', 'success');
                } else {
                    this.showStatus(result.message, 'warning');
                }
            } else {
                this.showStatus(result.error, 'error');
            }
            
            this.refreshAll();
            
        } catch (error) {
            this.isRunning = false;
            this.updateRunControls();
            this.showStatus(`Run error: ${error.message}`, 'error');
        }
    }

    async stopExecution() {
        try {
            await this.apiCall('/api/stop', 'POST');
            this.isRunning = false;
            this.updateRunControls();
            this.showStatus('Execution stopped', 'info');
        } catch (error) {
            console.error('Stop error:', error);
        }
    }

    updateRunControls() {
        document.getElementById('step-btn').disabled = this.isRunning;
        document.getElementById('run-btn').disabled = this.isRunning;
        document.getElementById('stop-btn').disabled = !this.isRunning;
        document.getElementById('compile-btn').disabled = this.isRunning;
    }

    async refreshCPUState() {
        try {
            const result = await this.apiCall('/api/cpu_state');
            if (result.success) {
                this.updateCPUStateFromData(result.cpu);
            }
        } catch (error) {
            // Silently fail for auto-refresh
            if (!this.isRunning) {
                console.error('CPU state refresh error:', error);
            }
        }
    }

    updateCPUStateFromData(cpu) {
        // Update registers
        this.updateRegister('reg-ra', cpu.registers.ra);
        this.updateRegister('reg-rd', cpu.registers.rd);
        this.updateRegister('reg-rb', cpu.registers.rb);
        this.updateRegister('reg-acc', cpu.registers.acc);
        this.updateRegister('reg-marl', cpu.registers.marl);
        this.updateRegister('reg-marh', cpu.registers.marh);
        this.updateRegister('reg-prl', cpu.registers.prl);
        this.updateRegister('reg-prh', cpu.registers.prh);

        // Update special registers (16-bit)
        document.getElementById('reg-pc').textContent = this.formatValue(cpu.pc, 16);
        document.getElementById('data-addr').textContent = this.formatValue(cpu.data_addr, 16);

        // Update flags
        document.getElementById('flag-eq').textContent = `EQ: ${cpu.flags.eq ? 1 : 0}`;
        document.getElementById('flag-lt').textContent = `LT: ${cpu.flags.lt ? 1 : 0}`;
        document.getElementById('flag-gt').textContent = `GT: ${cpu.flags.gt ? 1 : 0}`;
        document.getElementById('flag-carry').textContent = `C: ${cpu.flags.carry ? 1 : 0}`;

        // Update I/O
        document.getElementById('output-data').textContent = this.formatValue(cpu.output.data);
        document.getElementById('output-addr').textContent = this.formatValue(cpu.output.address);

        // Update execution status
        if (cpu.halted) {
            document.getElementById('execution-info').textContent = 'Halted';
        } else if (cpu.running) {
            document.getElementById('execution-info').textContent = 'Running';
        } else {
            document.getElementById('execution-info').textContent = 'Stopped';
        }
        
        // Update disassembly highlight with current PC
        this.updateDisassemblyHighlightWithPC(cpu.pc);
    }

    formatValue(value, bits = 8) {
        switch (this.dataFormat) {
            case 'hex':
                return bits === 16 ? 
                    `0x${value.toString(16).padStart(4, '0').toUpperCase()}` :
                    `0x${value.toString(16).padStart(2, '0').toUpperCase()}`;
            case 'decimal':
                return value.toString();
            case 'binary':
                return bits === 16 ?
                    `0b${value.toString(2).padStart(16, '0')}` :
                    `0b${value.toString(2).padStart(8, '0')}`;
            default:
                return `0x${value.toString(16).padStart(2, '0').toUpperCase()}`;
        }
    }

    updateRegister(elementId, value, bits = 8) {
        const element = document.getElementById(elementId);
        const newValue = this.formatValue(value, bits);
        
        if (element.textContent !== newValue) {
            element.textContent = newValue;
            element.classList.add('changed');
            setTimeout(() => element.classList.remove('changed'), 500);
        }
    }

    async refreshDataMemory() {
        try {
            const start = parseInt(document.getElementById('data-memory-start').value) || 0;
            const end = parseInt(document.getElementById('data-memory-end').value) || 31;
            
            console.log(`Refreshing data memory: ${start}-${end}`);
            const result = await this.apiCall(`/api/memory/data?start=${start}&end=${end}`);
            console.log('Data memory result:', result);
            this.displayMemory('data-memory', result.memory);
            
        } catch (error) {
            console.error('Data memory refresh error:', error);
            this.showStatus(`Data memory error: ${error.message}`, 'error');
        }
    }

    async refreshProgramMemory() {
        try {
            const start = parseInt(document.getElementById('program-memory-start').value) || 0;
            const end = parseInt(document.getElementById('program-memory-end').value) || 31;
            
            console.log(`Refreshing program memory: ${start}-${end}`);
            const result = await this.apiCall(`/api/memory/program?start=${start}&end=${end}`);
            console.log('Program memory result:', result);
            this.displayMemory('program-memory', result.memory);
            
        } catch (error) {
            console.error('Program memory refresh error:', error);
            this.showStatus(`Program memory error: ${error.message}`, 'error');
        }
    }

    displayMemory(containerId, memoryData) {
        const container = document.getElementById(containerId);
        container.innerHTML = '';

        // If no memory data, show placeholder
        if (!memoryData || memoryData.length === 0) {
            container.innerHTML = '<div style="color: #888; padding: 20px; text-align: center;">No data in range</div>';
            return;
        }

        // Group by 16-byte lines
        const lines = {};
        memoryData.forEach(item => {
            const lineAddr = Math.floor(item.address / 16) * 16;
            if (!lines[lineAddr]) {
                lines[lineAddr] = [];
            }
            lines[lineAddr][item.address % 16] = item.value;
        });

        Object.keys(lines).sort((a, b) => parseInt(a) - parseInt(b)).forEach(lineAddr => {
            const addr = parseInt(lineAddr);
            const line = lines[lineAddr];
            
            const lineElement = document.createElement('div');
            lineElement.className = 'memory-line';
            
            // Address
            const addrElement = document.createElement('span');
            addrElement.className = 'memory-addr';
            addrElement.textContent = `${addr.toString(16).padStart(4, '0').toUpperCase()}:`;
            lineElement.appendChild(addrElement);
            
            // Hex values
            const hexElement = document.createElement('span');
            hexElement.className = 'memory-hex';
            for (let i = 0; i < 16; i++) {
                const byteElement = document.createElement('span');
                byteElement.className = 'memory-byte';
                const value = line[i] !== undefined ? line[i] : 0;
                byteElement.textContent = value.toString(16).padStart(2, '0').toUpperCase();
                if (value !== 0) {
                    byteElement.classList.add('highlight');
                }
                hexElement.appendChild(byteElement);
            }
            lineElement.appendChild(hexElement);
            
            // ASCII representation
            const asciiElement = document.createElement('span');
            asciiElement.className = 'memory-ascii';
            let ascii = '|';
            for (let i = 0; i < 16; i++) {
                const value = line[i] !== undefined ? line[i] : 0;
                ascii += (value >= 32 && value <= 126) ? String.fromCharCode(value) : '.';
            }
            ascii += '|';
            asciiElement.textContent = ascii;
            lineElement.appendChild(asciiElement);
            
            container.appendChild(lineElement);
        });
    }

    // Disassembly Management
    initializeDisassembly() {
        const container = document.getElementById('disassembly');
        if (!container) {
            console.error('Disassembly container not found');
            return;
        }
        
        // Initialize with lines based on settings
        container.innerHTML = '';
        const lineCount = this.settings.disassemblyInstructionCount || 32;
        for (let addr = 0; addr < lineCount; addr++) {
            const lineElement = document.createElement('div');
            lineElement.className = 'disassembly-line';
            lineElement.dataset.address = addr;
            
            lineElement.innerHTML = `
                <span class="disassembly-address">${addr.toString(16).padStart(4, '0').toUpperCase()}:</span>
                <span class="disassembly-hex">00</span>
                <span class="disassembly-instruction">NOP</span>
            `;
            
            container.appendChild(lineElement);
        }
        
        console.log(`Disassembly initialized with ${lineCount} empty lines`);
    }

    async refreshDisassembly(currentPC = null) {
        try {
            console.log('Refreshing disassembly with PC:', currentPC);
            
            const container = document.getElementById('disassembly');
            
            if (!container) {
                console.error('Disassembly container not found');
                return;
            }

            // Use provided PC or fetch if not provided
            let pcValue = currentPC;
            if (pcValue === null) {
                const cpuState = await this.apiCall('/api/cpu_state');
                pcValue = cpuState.cpu ? cpuState.cpu.pc : 0;
            }

            // Get program data from API using settings count
            const instructionCount = this.settings.disassemblyInstructionCount || 32;
            const result = await this.apiCall(`/api/disassemble?start=0&count=${instructionCount}`);
            console.log(`Displaying ${result.instructions.length} instructions, PC=${pcValue}`);
            
            // Clear container and rebuild all lines
            container.innerHTML = '';
            
            // Create lines for all instructions
            result.instructions.forEach(inst => {
                const lineElement = document.createElement('div');
                lineElement.className = 'disassembly-line';
                lineElement.setAttribute('data-address', inst.address);
                
                lineElement.innerHTML = `
                    <span class="disassembly-address">${inst.address.toString(16).padStart(4, '0').toUpperCase()}:</span>
                    <span class="disassembly-hex">${inst.hex}</span>
                    <span class="disassembly-instruction">${inst.instruction}</span>
                `;
                
                // Highlight current PC instruction
                if (inst.address === pcValue) {
                    lineElement.classList.add('current-instruction');
                }
                
                // Click selects line; Ctrl+Click toggles breakpoint
                lineElement.addEventListener('click', async (e) => {
                    if (e.ctrlKey) {
                        await this.toggleBreakpointAtAddress(inst.address);
                    } else {
                        this.selectDisassemblyAddress(inst.address);
                    }
                });

                // Double-click toggles breakpoint
                lineElement.addEventListener('dblclick', async () => {
                    await this.toggleBreakpointAtAddress(inst.address);
                });

                container.appendChild(lineElement);
            });

            // Reapply breakpoint markers and selection/current highlights
            this.updateDisassemblyBreakpoints();
            this.updateDisassemblyHighlightWithPC(pcValue);

        } catch (error) {
            console.error('Disassembly refresh error:', error);
        }
    }

    async refreshAll() {
        try {
            // Get CPU state once and use it for both CPU and disassembly updates
            const result = await this.apiCall('/api/cpu_state');
            if (result.success) {
                const cpu = result.cpu;
                
                // Update CPU state with the fetched data
                this.updateCPUStateFromData(cpu);
                
                // Update disassembly with the current PC to avoid redundant API call
                this.refreshDisassembly(cpu.pc);
            }
            
            // Refresh other components
            this.refreshDataMemory();
            this.refreshProgramMemory();
            // Sync breakpoint markers from backend
            this.loadBreakpoints();
            // Update devices view so MMIO changes (e.g., seven-seg) are reflected after step/run
            this.refreshDevices();
            
        } catch (error) {
            console.error('RefreshAll error:', error);
            // Fallback to individual refresh if combined approach fails
            this.refreshCPUState();
            this.refreshDataMemory();
            this.refreshProgramMemory();
            this.refreshDisassembly();
        }
    }

    // View Switching
    switchView(viewName) {
        console.log(`Switching to ${viewName} view`);
        
        // Update view tabs
        document.querySelectorAll('.view-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-view="${viewName}"]`).classList.add('active');

        // Update view content
        document.querySelectorAll('.view-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${viewName}-view`).classList.add('active');

        // Resize editor if switching to editor view
        if (viewName === 'editor' && this.editor) {
            setTimeout(() => {
                this.editor.resize();
            }, 100);
        }

        // Only update PC highlight when switching to disassembly (no API call)
        if (viewName === 'disassembly') {
            console.log('Updating disassembly PC highlight');
            this.updateDisassemblyHighlight();
        } else if (viewName === 'devices') {
            this.refreshDevices();
        }
    }

    async refreshDevices() {
        try {
            const result = await this.apiCall('/api/devices');
            const devices = result.devices || [];
            this.renderDevices(devices);
        } catch (e) {
            console.error('Devices refresh error:', e);
        }
    }

    renderDevices(devices) {
        // Render 7-seg if present
        const seg = devices.find(d => d.name === 'SevenSegment');
        const container = document.getElementById('sevenseg-display');
        if (container) {
            container.innerHTML = '';
            container.appendChild(this.buildSevenSegSvg(seg ? seg.segments : null));
        }
    }

    buildSevenSegSvg(segments) {
        // Basic SVG-based 7-seg. segments is a dict of a,b,c,d,e,f,g,dp booleans
        const on = (name) => segments && segments[name];
        const svgNS = 'http://www.w3.org/2000/svg';
        const svg = document.createElementNS(svgNS, 'svg');
        svg.setAttribute('width', '120');
        svg.setAttribute('height', '200');

        const mk = (points, lit) => {
            const p = document.createElementNS(svgNS, 'polygon');
            p.setAttribute('points', points);
            p.setAttribute('fill', lit ? '#ff5252' : '#330000');
            p.setAttribute('stroke', '#660000');
            p.setAttribute('stroke-width', '2');
            return p;
        };

        // Define segments positions (simple stylized)
        const A = '30,20 90,20 80,30 40,30';
        const B = '90,20 100,30 100,90 90,100 80,90 80,30';
        const C = '90,110 100,120 100,180 90,190 80,180 80,120';
        const D = '30,190 90,190 80,180 40,180';
        const E = '20,110 30,120 30,180 20,190 10,180 10,120';
        const F = '20,20 30,30 30,90 20,100 10,90 10,30';
        const G = '30,100 90,100 80,110 40,110';
        const DP = '105,195 115,195 115,185 105,185';

        svg.appendChild(mk(A, on('a')));
        svg.appendChild(mk(B, on('b')));
        svg.appendChild(mk(C, on('c')));
        svg.appendChild(mk(D, on('d')));
        svg.appendChild(mk(E, on('e')));
        svg.appendChild(mk(F, on('f')));
        svg.appendChild(mk(G, on('g')));
        svg.appendChild(mk(DP, on('dp')));

        return svg;
    }

    async updateDisassemblyHighlight() {
        try {
            // Get current PC without making disassembly API call
            const cpuState = await this.apiCall('/api/cpu_state');
            let pcValue = 0;
            if (cpuState.success) {
                pcValue = cpuState.cpu ? cpuState.cpu.pc : 0;
            }
            this.updateDisassemblyHighlightWithPC(pcValue);
            
        } catch (error) {
            console.error('Error updating disassembly highlight:', error);
        }
    }

    updateDisassemblyHighlightWithPC(pcValue) {
        const container = document.getElementById('disassembly');
        if (!container) return;
        
        // Clear all highlights
        container.querySelectorAll('.disassembly-line').forEach(line => {
            line.classList.remove('current-instruction');
            line.classList.remove('selected');
        });
        
        // Highlight current PC
        const currentLine = container.querySelector(`[data-address="${pcValue}"]`);
        if (currentLine) {
            currentLine.classList.add('current-instruction');
        }

        // Highlight selected address if any
        if (this.selectedAddress !== null) {
            const selLine = container.querySelector(`[data-address="${this.selectedAddress}"]`);
            if (selLine) selLine.classList.add('selected');
        }
    }

    selectDisassemblyAddress(address) {
        this.selectedAddress = address;
        this.updateDisassemblyHighlight();
    }

    async toggleSelectedOrPromptBreakpoint() {
        // No prompt: add breakpoint to selected address or current PC
        if (this.selectedAddress !== null) {
            await this.setBreakpointAtAddress(this.selectedAddress);
        } else {
            try {
                const result = await this.apiCall('/api/cpu_state');
                if (result.success) {
                    const pc = result.cpu.pc;
                    await this.setBreakpointAtAddress(pc);
                }
            } catch (e) {
                this.showStatus(`Breakpoint error: ${e.message}`, 'error');
            }
        }
    }

    async setBreakpointAtAddress(address) {
        try {
            const response = await this.apiCall('/api/breakpoints', 'POST', {
                address: address,
                enabled: true
            });
            if (response && response.success !== false) {
                this.breakpoints.add(address);
                this.updateDisassemblyBreakpoints();
                this.showStatus(`Breakpoint set at address ${address}`, 'success');
            }
        } catch (err) {
            this.showStatus(`Breakpoint error: ${err.message}`, 'error');
        }
    }

    // Tab System
    initializeTabs() {
        // Clear any existing tabs first
        document.querySelector('.tabs').innerHTML = '';
        this.tabs.clear();
        
        // Try to restore tabs from session storage
        this.restoreTabsFromStorage();
        
        // If no tabs were restored, create initial tab with sample code
        if (this.tabs.size === 0) {
            this.createTab('untitled-1', 'Untitled-1', '', false);
            this.setActiveTab('untitled-1');
            // Load sample code into the new empty tab
            this.loadSampleCode();
        }

        // Tab event listeners
        document.querySelector('.new-tab-btn').addEventListener('click', () => this.createNewTab());
        
        // File control event listeners
        document.getElementById('new-file-btn').addEventListener('click', () => this.createNewTab());
        document.getElementById('open-file-btn').addEventListener('click', () => this.openFileDialog());
        document.getElementById('save-file-btn').addEventListener('click', () => this.saveFile());
        document.getElementById('save-as-btn').addEventListener('click', () => this.saveAsDialog());
        
        // Save tabs state before page unload
        window.addEventListener('beforeunload', () => {
            this.saveTabsToStorage();
        });
        
        // Save tabs state periodically
        setInterval(() => {
            this.saveTabsToStorage();
        }, 5000); // Save every 5 seconds
    }

    saveTabsToStorage() {
        try {
            // Save current editor content to active tab
            if (this.activeTabId) {
                const currentTab = this.tabs.get(this.activeTabId);
                if (currentTab) {
                    currentTab.content = this.editor.getValue();
                }
            }
            
            const tabsData = {
                tabs: Array.from(this.tabs.entries()).map(([id, tab]) => ({
                    id: tab.id,
                    title: tab.title,
                    content: tab.content,
                    saved: tab.saved,
                    filepath: tab.filepath
                })),
                activeTabId: this.activeTabId,
                tabCounter: this.tabCounter
            };
            
            sessionStorage.setItem('arnicomp_tabs', JSON.stringify(tabsData));
        } catch (error) {
            console.warn('Failed to save tabs to storage:', error);
        }
    }

    restoreTabsFromStorage() {
        try {
            const stored = sessionStorage.getItem('arnicomp_tabs');
            if (!stored) return;
            
            const tabsData = JSON.parse(stored);
            this.tabCounter = tabsData.tabCounter || 1;
            
            // Restore tabs
            tabsData.tabs.forEach(tabData => {
                const tab = this.createTab(tabData.id, tabData.title, tabData.content, tabData.saved);
                tab.filepath = tabData.filepath;
            });
            
            // Restore active tab
            if (tabsData.activeTabId && this.tabs.has(tabsData.activeTabId)) {
                this.setActiveTab(tabsData.activeTabId);
            }
        } catch (error) {
            console.warn('Failed to restore tabs from storage:', error);
        }
    }

    createTab(id, title, content = '', saved = false) {
        const tab = {
            id: id,
            title: title,
            content: content,
            saved: saved,
            filepath: null
        };
        
        this.tabs.set(id, tab);
        this.renderTab(tab);
        return tab;
    }

    renderTab(tab) {
        const tabsContainer = document.querySelector('.tabs');
        
        const tabElement = document.createElement('div');
        tabElement.className = 'tab';
        tabElement.setAttribute('data-tab-id', tab.id);
        
        tabElement.innerHTML = `
            <span class="tab-title">${tab.title}${tab.saved ? '' : '*'}</span>
            <button class="tab-close" title="Close">×</button>
        `;
        
        // Tab click events
        tabElement.addEventListener('click', (e) => {
            if (!e.target.classList.contains('tab-close')) {
                this.setActiveTab(tab.id);
            }
        });
        
        tabElement.querySelector('.tab-close').addEventListener('click', (e) => {
            e.stopPropagation();
            this.closeTab(tab.id);
        });
        
        tabsContainer.appendChild(tabElement);
    }

    setActiveTab(tabId) {
        const tab = this.tabs.get(tabId);
        if (!tab) return;

        // Save current editor content to current tab
        if (this.activeTabId) {
            const currentTab = this.tabs.get(this.activeTabId);
            if (currentTab) {
                currentTab.content = this.editor.getValue();
                currentTab.saved = false;
                this.updateTabTitle(this.activeTabId);
            }
        }

        // Switch to new tab
        this.activeTabId = tabId;
        this.editor.setValue(tab.content, -1);
        
        // Reset dirty state for saved files
        if (tab.saved) {
            // For ACE editor: Clear undo manager to prevent false dirty state
            this.editor.session.getUndoManager().reset();
        }
        
        // Update UI
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelector(`[data-tab-id="${tabId}"]`).classList.add('active');
        
        // Update file status
        document.getElementById('file-status').textContent = 
            tab.filepath ? `File: ${tab.filepath}` : 'Unsaved';
    }

    updateTabTitle(tabId) {
        const tab = this.tabs.get(tabId);
        if (!tab) return;
        
        const tabElement = document.querySelector(`[data-tab-id="${tabId}"]`);
        if (tabElement) {
            tabElement.querySelector('.tab-title').textContent = 
                `${tab.title}${tab.saved ? '' : '*'}`;
        }
    }

    createNewTab() {
        const newId = `untitled-${this.tabCounter++}`;
        const newTab = this.createTab(newId, `Untitled-${this.tabCounter - 1}`, '');
        this.setActiveTab(newId);
    }

    closeTab(tabId) {
        const tab = this.tabs.get(tabId);
        if (!tab) return;

        if (!tab.saved && tab.content.trim()) {
            if (!confirm(`Close ${tab.title}? Unsaved changes will be lost.`)) {
                return;
            }
        }

        // Remove tab element
        const tabElement = document.querySelector(`[data-tab-id="${tabId}"]`);
        if (tabElement) {
            tabElement.remove();
        }

        // Remove from tabs map
        this.tabs.delete(tabId);

        // If this was the active tab, switch to another one
        if (this.activeTabId === tabId) {
            const remainingTabs = Array.from(this.tabs.keys());
            if (remainingTabs.length > 0) {
                this.setActiveTab(remainingTabs[0]);
            } else {
                // Create a new tab if no tabs remain
                this.createNewTab();
            }
        }
    }

    // File Operations
    async saveFile() {
        const tab = this.tabs.get(this.activeTabId);
        if (!tab) return;

        if (tab.filepath) {
            await this.saveToFile(tab.filepath, this.editor.getValue());
        } else {
            this.saveAsDialog();
        }
    }

    saveAsDialog() {
        const modal = document.getElementById('save-modal');
        const filenameInput = document.getElementById('save-filename');
        
        modal.style.display = 'block';
        filenameInput.focus();
        
        // Handle save
        document.getElementById('save-modal-save').onclick = async () => {
            const filename = filenameInput.value.trim();
            if (!filename) {
                alert('Please enter a filename');
                return;
            }
            
            const fullFilename = filename.endsWith('.asm') ? filename : filename + '.asm';
            await this.saveToFile(fullFilename, this.editor.getValue());
            modal.style.display = 'none';
            filenameInput.value = '';
        };
        
        // Handle cancel
        document.getElementById('save-modal-cancel').onclick = () => {
            modal.style.display = 'none';
            filenameInput.value = '';
        };
        
        // Handle modal close
        modal.querySelector('.modal-close').onclick = () => {
            modal.style.display = 'none';
            filenameInput.value = '';
        };
    }

    async saveToFile(filename, content) {
        try {
            const response = await fetch(`/api/files/${filename}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    content: content
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                const tab = this.tabs.get(this.activeTabId);
                tab.saved = true;
                tab.filepath = filename;
                tab.title = filename;
                this.updateTabTitle(this.activeTabId);
                
                document.getElementById('file-status').textContent = `Saved: ${filename}`;
                console.log('File saved successfully');
            } else {
                alert('Error saving file: ' + result.error);
            }
        } catch (error) {
            alert('Error saving file: ' + error.message);
        }
    }

    openFileDialog() {
        const modal = document.getElementById('file-modal');
        const fileList = document.getElementById('file-list');
        
        modal.style.display = 'block';
        
        // Initialize file source tabs (only once)
        if (!this.fileInputInitialized) {
            this.initializeFileSourceTabs();
            this.initializeFileInput();
            this.fileInputInitialized = true;
        }
        
        // Load example files list
        this.loadFileList();
        
        // Handle modal close
        modal.querySelector('.modal-close').onclick = () => {
            modal.style.display = 'none';
            this.resetFileModal();
        };
        
        document.getElementById('modal-cancel').onclick = () => {
            modal.style.display = 'none';
            this.resetFileModal();
        };
    }
    
    initializeFileSourceTabs() {
        const tabs = document.querySelectorAll('.file-source-tab');
        const contents = document.querySelectorAll('.file-source-content');
        
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                // Remove active class from all tabs and contents
                tabs.forEach(t => t.classList.remove('active'));
                contents.forEach(c => c.classList.remove('active'));
                
                // Add active class to clicked tab
                tab.classList.add('active');
                
                // Show corresponding content
                const source = tab.dataset.source;
                document.getElementById(`${source}-files`).classList.add('active');
                
                // Reset modal open button
                document.getElementById('modal-open').disabled = true;
            });
        });
    }
    
    initializeFileInput() {
        const fileInput = document.getElementById('file-input');
        const browseBtn = document.getElementById('browse-file-btn');
        const selectedFileInfo = document.getElementById('selected-file-info');
        const selectedFileName = document.getElementById('selected-file-name');
        const clearSelectionBtn = document.getElementById('clear-selection-btn');
        const modalOpenBtn = document.getElementById('modal-open');
        
        if (!fileInput || !browseBtn) {
            console.error('File input elements not found');
            return;
        }
        
        // Remove any existing listeners by cloning elements
        const newBrowseBtn = browseBtn.cloneNode(true);
        browseBtn.parentNode.replaceChild(newBrowseBtn, browseBtn);
        
        const newClearBtn = clearSelectionBtn.cloneNode(true);
        clearSelectionBtn.parentNode.replaceChild(newClearBtn, clearSelectionBtn);
        
        // Browse button click
        newBrowseBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('Browse button clicked');
            fileInput.click();
        });
        
        // File selection
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            console.log('File selected:', file?.name);
            if (file) {
                selectedFileName.textContent = file.name;
                selectedFileInfo.style.display = 'flex';
                modalOpenBtn.disabled = false;
                
                // Store file reference
                this.selectedLocalFile = file;
                
                // Set up open button to load local file
                modalOpenBtn.onclick = () => this.loadLocalFile(file);
            }
        });
        
        // Clear selection
        newClearBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            fileInput.value = '';
            selectedFileInfo.style.display = 'none';
            modalOpenBtn.disabled = true;
            this.selectedLocalFile = null;
        });
    }
    
    async loadLocalFile(file) {
        try {
            const content = await file.text();
            
            // Create new tab with file content
            const newId = `local-${file.name}-${Date.now()}`;
            const newTab = this.createTab(newId, file.name, content, false);
            newTab.filepath = null; // Local file, not from server
            this.setActiveTab(newId);
            
            document.getElementById('file-modal').style.display = 'none';
            this.resetFileModal();
            
            document.getElementById('compile-status').textContent = `Loaded: ${file.name}`;
        } catch (error) {
            alert('Error loading file: ' + error.message);
        }
    }
    
    resetFileModal() {
        // Reset file input
        const fileInput = document.getElementById('file-input');
        fileInput.value = '';
        document.getElementById('selected-file-info').style.display = 'none';
        
        // Reset tab selection
        document.querySelectorAll('.file-source-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.file-source-tab')[0].classList.add('active');
        document.querySelectorAll('.file-source-content').forEach(c => c.classList.remove('active'));
        document.getElementById('local-files').classList.add('active');
        
        // Reset file list selection
        document.querySelectorAll('.file-item').forEach(f => f.classList.remove('selected'));
        document.getElementById('modal-open').disabled = true;
    }

    async loadFileList() {
        const fileList = document.getElementById('file-list');
        fileList.innerHTML = '<div class="loading">Loading files...</div>';
        
        try {
            const response = await fetch('/api/files');
            const result = await response.json();
            
            if (result.success) {
                if (result.files.length === 0) {
                    fileList.innerHTML = '<div class="loading">No .asm files found</div>';
                    return;
                }
                
                fileList.innerHTML = '';
                result.files.forEach(file => {
                    const fileItem = document.createElement('div');
                    fileItem.className = 'file-item';
                    fileItem.innerHTML = `
                        <div>
                            <div class="file-name">${file.name}</div>
                            <div class="file-info">${file.size} bytes • ${new Date(file.modified * 1000).toLocaleString()}</div>
                        </div>
                    `;
                    
                    fileItem.addEventListener('click', () => {
                        document.querySelectorAll('.file-item').forEach(f => f.classList.remove('selected'));
                        fileItem.classList.add('selected');
                        document.getElementById('modal-open').disabled = false;
                        document.getElementById('modal-open').onclick = () => this.loadFile(file.name);
                    });
                    
                    fileList.appendChild(fileItem);
                });
            } else {
                fileList.innerHTML = '<div class="loading">Error loading files</div>';
            }
        } catch (error) {
            fileList.innerHTML = '<div class="loading">Error loading files</div>';
        }
    }

    async loadFile(filename) {
        try {
            const response = await fetch(`/api/files/${filename}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Check if file is already open
                let existingTab = null;
                for (const [id, tab] of this.tabs.entries()) {
                    if (tab.filepath === filename) {
                        existingTab = id;
                        break;
                    }
                }
                
                if (existingTab) {
                    this.setActiveTab(existingTab);
                } else {
                    const newId = `file-${filename}-${Date.now()}`;
                    const newTab = this.createTab(newId, filename, result.content, true);
                    newTab.filepath = filename;
                    this.setActiveTab(newId);
                }
                
                document.getElementById('file-modal').style.display = 'none';
            } else {
                alert('Error loading file: ' + result.error);
            }
        } catch (error) {
            alert('Error loading file: ' + error.message);
        }
    }

    // Resizer System
    initializeResizers() {
        this.initializeVerticalResizer();
        // Horizontal resizer removed due to new tab-based layout
    }

    initializeVerticalResizer() {
        const resizer = document.querySelector('.vertical-resizer');
        const leftPanel = document.querySelector('.left-panel');
        const rightPanel = document.querySelector('.right-panel');
        
        let isResizing = false;
        
        resizer.addEventListener('mousedown', (e) => {
            isResizing = true;
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
        });
        
        document.addEventListener('mousemove', (e) => {
            if (!isResizing) return;
            
            const containerRect = document.querySelector('.main-layout').getBoundingClientRect();
            const newLeftWidth = e.clientX - containerRect.left;
            const minWidth = 300;
            const maxWidth = containerRect.width - 300;
            
            if (newLeftWidth >= minWidth && newLeftWidth <= maxWidth) {
                leftPanel.style.width = newLeftWidth + 'px';
                rightPanel.style.width = (containerRect.width - newLeftWidth - 5) + 'px';
            }
        });
        
        document.addEventListener('mouseup', () => {
            isResizing = false;
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        });
    }

    // Settings methods
    loadSettings() {
        const savedSettings = localStorage.getItem('arnicomp-emulator-settings');
        if (savedSettings) {
            const settings = JSON.parse(savedSettings);
            this.settings = { ...this.settings, ...settings };
            
            // Update memory input fields when settings are loaded
            setTimeout(() => {
                if (this.settings.dataMemoryStartAddress && this.settings.dataMemoryEndAddress) {
                    const dataStartDecimal = parseInt(this.settings.dataMemoryStartAddress, 16);
                    const dataEndDecimal = parseInt(this.settings.dataMemoryEndAddress, 16);
                    
                    const dataStartInput = document.getElementById('data-memory-start');
                    const dataEndInput = document.getElementById('data-memory-end');
                    
                    if (dataStartInput) dataStartInput.value = dataStartDecimal;
                    if (dataEndInput) dataEndInput.value = dataEndDecimal;
                }
                
                if (this.settings.programMemoryStartAddress && this.settings.programMemoryEndAddress) {
                    const programStartDecimal = parseInt(this.settings.programMemoryStartAddress, 16);
                    const programEndDecimal = parseInt(this.settings.programMemoryEndAddress, 16);
                    
                    const programStartInput = document.getElementById('program-memory-start');
                    const programEndInput = document.getElementById('program-memory-end');
                    
                    if (programStartInput) programStartInput.value = programStartDecimal;
                    if (programEndInput) programEndInput.value = programEndDecimal;
                }
            }, 100);
        }
    }

    saveSettings() {
        localStorage.setItem('arnicomp-emulator-settings', JSON.stringify(this.settings));
        this.showStatus('Settings saved successfully');
    }

    openSettingsModal() {
        // Update UI with current settings
        document.getElementById('data-memory-start-hex').value = this.settings.dataMemoryStartAddress;
        document.getElementById('data-memory-end-hex').value = this.settings.dataMemoryEndAddress;
        document.getElementById('program-memory-start-hex').value = this.settings.programMemoryStartAddress;
        document.getElementById('program-memory-end-hex').value = this.settings.programMemoryEndAddress;
        document.getElementById('disassembly-count').value = this.settings.disassemblyInstructionCount;
        document.getElementById('auto-refresh').checked = this.settings.autoRefresh;
        
        // Show modal
        document.getElementById('settings-modal').style.display = 'block';
        
        // Add event listeners
        document.querySelector('#settings-modal .close-modal').onclick = () => this.closeSettingsModal();
        document.getElementById('settings-cancel').onclick = () => this.closeSettingsModal();
        document.getElementById('apply-settings').onclick = () => this.applySettings();
        document.getElementById('reset-settings').onclick = () => this.resetSettings();
        
        // Close on outside click
        document.getElementById('settings-modal').onclick = (e) => {
            if (e.target === e.currentTarget) {
                this.closeSettingsModal();
            }
        };
    }

    closeSettingsModal() {
        document.getElementById('settings-modal').style.display = 'none';
    }

    applySettings() {
        // Get values from UI
        const dataMemoryStart = document.getElementById('data-memory-start-hex').value;
        const dataMemoryEnd = document.getElementById('data-memory-end-hex').value;
        const programMemoryStart = document.getElementById('program-memory-start-hex').value;
        const programMemoryEnd = document.getElementById('program-memory-end-hex').value;
        const disassemblyCount = parseInt(document.getElementById('disassembly-count').value);
        const autoRefresh = document.getElementById('auto-refresh').checked;

        // Update settings
        this.settings.dataMemoryStartAddress = dataMemoryStart;
        this.settings.dataMemoryEndAddress = dataMemoryEnd;
        this.settings.programMemoryStartAddress = programMemoryStart;
        this.settings.programMemoryEndAddress = programMemoryEnd;
        this.settings.disassemblyInstructionCount = disassemblyCount;
        this.settings.autoRefresh = autoRefresh;

        // Update memory input fields with decimal values
        const dataStartDecimal = parseInt(dataMemoryStart, 16);
        const dataEndDecimal = parseInt(dataMemoryEnd, 16);
        const programStartDecimal = parseInt(programMemoryStart, 16);
        const programEndDecimal = parseInt(programMemoryEnd, 16);
        
        document.getElementById('data-memory-start').value = dataStartDecimal;
        document.getElementById('data-memory-end').value = dataEndDecimal;
        document.getElementById('program-memory-start').value = programStartDecimal;
        document.getElementById('program-memory-end').value = programEndDecimal;

        // Save and close
        this.saveSettings();
        this.closeSettingsModal();
        
        // Refresh displays
        this.refreshAll();
    }

    resetSettings() {
        this.settings = {
            dataMemoryStartAddress: '0000',
            dataMemoryEndAddress: '00FF',
            programMemoryStartAddress: '0000',
            programMemoryEndAddress: '00FF',
            disassemblyInstructionCount: 32,
            autoRefresh: true
        };
        
        // Update UI
        document.getElementById('data-memory-start-hex').value = this.settings.dataMemoryStartAddress;
        document.getElementById('data-memory-end-hex').value = this.settings.dataMemoryEndAddress;
        document.getElementById('program-memory-start-hex').value = this.settings.programMemoryStartAddress;
        document.getElementById('program-memory-end-hex').value = this.settings.programMemoryEndAddress;
        document.getElementById('disassembly-count').value = this.settings.disassemblyInstructionCount;
        document.getElementById('auto-refresh').checked = this.settings.autoRefresh;
        
        // Update memory input fields
        document.getElementById('data-memory-start').value = 0;
        document.getElementById('data-memory-end').value = 255;
        document.getElementById('program-memory-start').value = 0;
        document.getElementById('program-memory-end').value = 255;
        
        this.showStatus('Settings reset to defaults');
    }

    // Breakpoint Management
    async toggleCurrentBreakpoint() {
        try {
            const result = await this.apiCall('/api/cpu_state');
            if (result.success) {
                const pc = result.cpu.pc;
                const hasBreakpoint = this.breakpoints.has(pc);
                
                const response = await this.apiCall('/api/breakpoints', 'POST', {
                    address: pc,
                    enabled: !hasBreakpoint
                });
                
                if (response.success) {
                    if (hasBreakpoint) {
                        this.breakpoints.delete(pc);
                        this.showStatus(`Breakpoint removed from address ${pc}`, 'success');
                    } else {
                        this.breakpoints.add(pc);
                        this.showStatus(`Breakpoint set at address ${pc}`, 'success');
                    }
                    this.updateDisassemblyBreakpoints();
                }
            }
        } catch (error) {
            this.showStatus(`Breakpoint error: ${error.message}`, 'error');
        }
    }

    async clearAllBreakpoints() {
        try {
            const response = await this.apiCall('/api/breakpoints', 'DELETE');
            if (response.success) {
                this.breakpoints.clear();
                this.showStatus('All breakpoints cleared', 'success');
                this.updateDisassemblyBreakpoints();
            }
        } catch (error) {
            this.showStatus(`Clear breakpoints error: ${error.message}`, 'error');
        }
    }

    async loadBreakpoints() {
        try {
            const response = await this.apiCall('/api/breakpoints');
            if (response.success) {
                this.breakpoints = new Set(response.breakpoints);
                this.updateDisassemblyBreakpoints();
            }
        } catch (error) {
            console.error('Load breakpoints error:', error);
        }
    }

    async toggleBreakpointAtAddress(address) {
        try {
            const hasBreakpoint = this.breakpoints.has(address);
            const response = await this.apiCall('/api/breakpoints', 'POST', {
                address: address,
                enabled: !hasBreakpoint
            });
            if (response && response.success !== false) {
                if (hasBreakpoint) {
                    this.breakpoints.delete(address);
                    this.showStatus(`Breakpoint removed from address ${address}`, 'success');
                } else {
                    this.breakpoints.add(address);
                    this.showStatus(`Breakpoint set at address ${address}`, 'success');
                }
                this.updateDisassemblyBreakpoints();
            }
        } catch (err) {
            this.showStatus(`Breakpoint error: ${err.message}`, 'error');
        }
    }

    async promptToggleBreakpoint() {
        try {
            const input = prompt('Enter address (decimal or 0xHEX):');
            if (!input) return;
            let addr = 0;
            if (input.startsWith('0x') || input.startsWith('0X')) {
                addr = parseInt(input, 16);
            } else {
                addr = parseInt(input, 10);
            }
            if (Number.isNaN(addr) || addr < 0) {
                this.showStatus('Invalid address', 'error');
                return;
            }
            await this.toggleBreakpointAtAddress(addr);
        } catch (e) {
            this.showStatus(`Breakpoint prompt error: ${e.message}`, 'error');
        }
    }

    updateDisassemblyBreakpoints() {
        // Update disassembly view to show breakpoints
        const container = document.getElementById('disassembly');
        if (container) {
            const lines = container.querySelectorAll('.disassembly-line');
            lines.forEach(line => {
                const address = parseInt(line.getAttribute('data-address'));
                if (this.breakpoints.has(address)) {
                    line.classList.add('breakpoint');
                } else {
                    line.classList.remove('breakpoint');
                }
            });
        }
    }

}

// Initialize emulator when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.emulator = new ArniCompEmulator();
});
