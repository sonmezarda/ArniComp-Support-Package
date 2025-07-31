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
        
        // Tab system
        this.tabs = new Map();
        this.activeTabId = null;
        this.tabCounter = 1;
        
        this.initializeEditor();
        this.initializeEventListeners();
        this.initializeTabs();
        this.initializeResizers();
        this.initializeCollapsiblePanels();
        this.loadSampleCode();
        this.refreshAll();
        
        // Auto-refresh CPU state every 100ms when running
        setInterval(() => {
            if (this.autoRefresh) {
                this.refreshCPUState();
            }
        }, 100);
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
    }

    initializeEventListeners() {
        // Control buttons
        document.getElementById('reset-btn').addEventListener('click', () => this.resetEmulator());
        document.getElementById('compile-btn').addEventListener('click', () => this.compileCode());
        document.getElementById('step-btn').addEventListener('click', () => this.stepExecution());
        document.getElementById('run-btn').addEventListener('click', () => this.runExecution());
        document.getElementById('stop-btn').addEventListener('click', () => this.stopExecution());

        // Memory refresh buttons
        document.getElementById('refresh-data-memory').addEventListener('click', () => this.refreshDataMemory());
        document.getElementById('refresh-program-memory').addEventListener('click', () => this.refreshProgramMemory());

        // Data format selector
        document.getElementById('data-format').addEventListener('change', (e) => {
            this.dataFormat = e.target.value;
            this.refreshCPUState(); // Update register display
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

            const response = await fetch(`/api${endpoint}`, options);
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
            const result = await this.apiCall('/compile', 'POST', { code });

            this.compiledProgram = result.binary_data;
            
            document.getElementById('compile-status').textContent = 
                `Compiled: ${result.lines_processed} instructions, ${result.binary_data.length} bytes`;
            
            this.showStatus('Compilation successful', 'success');
            
            // Auto-load compiled program
            await this.loadProgram();
            
            // Refresh disassembly
            this.refreshDisassembly();
            
        } catch (error) {
            document.getElementById('compile-status').textContent = 'Compilation failed';
            this.showStatus(`Compilation error: ${error.message}`, 'error');
        }
    }

    async loadProgram() {
        if (!this.compiledProgram) {
            this.showStatus('No compiled program to load', 'warning');
            return;
        }

        try {
            await this.apiCall('/load_program', 'POST', { 
                binary_data: this.compiledProgram 
            });
            
            this.showStatus('Program loaded', 'success');
            this.refreshAll();
            
        } catch (error) {
            this.showStatus(`Load error: ${error.message}`, 'error');
        }
    }

    async resetEmulator() {
        try {
            await this.apiCall('/reset', 'POST');
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
            const result = await this.apiCall('/step', 'POST');
            
            if (result.halted) {
                this.showStatus('Program halted', 'warning');
                this.isRunning = false;
                this.updateRunControls();
            } else if (!result.continued) {
                this.showStatus('Execution stopped', 'info');
                this.isRunning = false;
                this.updateRunControls();
            } else {
                this.showStatus('Step executed', 'success');
            }
            
            this.refreshAll();
            
        } catch (error) {
            this.showStatus(`Step error: ${error.message}`, 'error');
        }
    }

    async runExecution() {
        try {
            this.isRunning = true;
            this.updateRunControls();
            this.showStatus('Running...', 'info');
            
            const result = await this.apiCall('/run', 'POST', { max_cycles: 1000 });
            
            this.isRunning = false;
            this.updateRunControls();
            
            document.getElementById('execution-info').textContent = 
                `Executed ${result.cycles_executed} cycles`;
            
            if (result.halted) {
                this.showStatus('Program completed', 'success');
            } else {
                this.showStatus('Execution stopped (max cycles)', 'warning');
            }
            
            this.refreshAll();
            
        } catch (error) {
            this.isRunning = false;
            this.updateRunControls();
            this.showStatus(`Run error: ${error.message}`, 'error');
        }
    }

    stopExecution() {
        this.isRunning = false;
        this.updateRunControls();
        this.showStatus('Execution stopped', 'info');
    }

    updateRunControls() {
        document.getElementById('step-btn').disabled = this.isRunning;
        document.getElementById('run-btn').disabled = this.isRunning;
        document.getElementById('stop-btn').disabled = !this.isRunning;
        document.getElementById('compile-btn').disabled = this.isRunning;
    }

    async refreshCPUState() {
        try {
            const result = await this.apiCall('/cpu_state');
            const cpu = result.cpu;

            // Update registers
            this.updateRegister('reg-ra', cpu.registers.ra);
            this.updateRegister('reg-rd', cpu.registers.rd);
            this.updateRegister('reg-acc', cpu.registers.acc);
            this.updateRegister('reg-marl', cpu.registers.marl);
            this.updateRegister('reg-marh', cpu.registers.marh);
            this.updateRegister('reg-prl', cpu.registers.prl);
            this.updateRegister('reg-prh', cpu.registers.prh);

            // Update special registers (16-bit)
            document.getElementById('reg-pc').textContent = this.formatValue(cpu.pc, 16);
            document.getElementById('data-addr').textContent = this.formatValue(cpu.data_addr, 16);

            // Update flags
            document.getElementById('flag-eq').textContent = `EQ: ${cpu.flags.equal ? 1 : 0}`;
            document.getElementById('flag-lt').textContent = `LT: ${cpu.flags.lt ? 1 : 0}`;
            document.getElementById('flag-gt').textContent = `GT: ${cpu.flags.gt ? 1 : 0}`;
            document.getElementById('memory-mode').textContent = `Mode: ${cpu.memory_mode}`;

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

        } catch (error) {
            // Silently fail for auto-refresh
            if (!this.isRunning) {
                console.error('CPU state refresh error:', error);
            }
        }
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
            const result = await this.apiCall(`/memory/data?start=${start}&end=${end}`);
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
            const result = await this.apiCall(`/memory/program?start=${start}&end=${end}`);
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

    async refreshDisassembly() {
        try {
            const result = await this.apiCall('/disassemble?start=0&count=20');
            const container = document.getElementById('disassembly');
            container.innerHTML = '';

            result.instructions.forEach(inst => {
                const lineElement = document.createElement('div');
                lineElement.className = 'disassembly-line';
                
                lineElement.innerHTML = `
                    <span class="disassembly-address">${inst.address.toString(16).padStart(4, '0').toUpperCase()}:</span>
                    <span class="disassembly-hex">${inst.hex}</span>
                    <span class="disassembly-instruction">${inst.instruction}</span>
                `;
                
                container.appendChild(lineElement);
            });

        } catch (error) {
            console.error('Disassembly refresh error:', error);
        }
    }

    refreshAll() {
        this.refreshCPUState();
        this.refreshDataMemory();
        this.refreshProgramMemory();
    }

    // Tab System
    initializeTabs() {
        // Clear any existing tabs first
        document.querySelector('.tabs').innerHTML = '';
        this.tabs.clear();
        
        // Create initial tab
        this.createTab('untitled-1', 'Untitled-1', '', false);
        this.setActiveTab('untitled-1');

        // Tab event listeners
        document.querySelector('.new-tab-btn').addEventListener('click', () => this.createNewTab());
        
        // File control event listeners
        document.getElementById('new-file-btn').addEventListener('click', () => this.createNewTab());
        document.getElementById('open-file-btn').addEventListener('click', () => this.openFileDialog());
        document.getElementById('save-file-btn').addEventListener('click', () => this.saveFile());
        document.getElementById('save-as-btn').addEventListener('click', () => this.saveAsDialog());
    }

    initializeCollapsiblePanels() {
        // Disassembly panel collapse
        const disassemblyHeader = document.getElementById('disassembly-header');
        const disassemblyPanel = document.querySelector('.disassembly-panel');
        const collapseBtn = disassemblyHeader.querySelector('.collapse-btn');
        
        disassemblyHeader.addEventListener('click', () => {
            disassemblyPanel.classList.toggle('collapsed');
            collapseBtn.textContent = disassemblyPanel.classList.contains('collapsed') ? '+' : '−';
            
            // Resize ace editor after animation
            setTimeout(() => {
                if (this.editor) {
                    this.editor.resize();
                }
            }, 300);
        });
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
            const response = await fetch('/api/save_file', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    filename: filename,
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
        this.loadFileList();
        
        // Handle modal close
        modal.querySelector('.modal-close').onclick = () => {
            modal.style.display = 'none';
        };
        
        document.getElementById('modal-cancel').onclick = () => {
            modal.style.display = 'none';
        };
    }

    async loadFileList() {
        const fileList = document.getElementById('file-list');
        fileList.innerHTML = '<div class="loading">Loading files...</div>';
        
        try {
            const response = await fetch('/api/list_files');
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
            const response = await fetch('/api/load_file', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ filename: filename })
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
        this.initializeHorizontalResizer();
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

    initializeHorizontalResizer() {
        const resizer = document.querySelector('.horizontal-resizer');
        const editorPanel = document.querySelector('.editor-panel');
        const disassemblyPanel = document.querySelector('.disassembly-panel');
        
        let isResizing = false;
        
        resizer.addEventListener('mousedown', (e) => {
            isResizing = true;
            document.body.style.cursor = 'row-resize';
            document.body.style.userSelect = 'none';
        });
        
        document.addEventListener('mousemove', (e) => {
            if (!isResizing) return;
            
            const leftPanelRect = document.querySelector('.left-panel').getBoundingClientRect();
            const newEditorHeight = e.clientY - leftPanelRect.top;
            const minHeight = 200;
            const maxHeight = leftPanelRect.height - 150;
            
            if (newEditorHeight >= minHeight && newEditorHeight <= maxHeight) {
                editorPanel.style.height = newEditorHeight + 'px';
                editorPanel.style.flex = 'none';
                disassemblyPanel.style.height = (leftPanelRect.height - newEditorHeight - 5) + 'px';
            }
        });
        
        document.addEventListener('mouseup', () => {
            isResizing = false;
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        });
    }
}

// Initialize emulator when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.emulator = new ArniCompEmulator();
});
