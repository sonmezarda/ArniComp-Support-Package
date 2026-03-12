#!/bin/bash
# ArniComp CPU Synthesis and Visualization Script
# Requirements: yosys, graphviz (dot), web browser

echo "=== ArniComp CPU Synthesis and Visualization ==="
echo ""

# Check if yosys is installed
if ! command -v yosys &> /dev/null; then
    echo "Error: Yosys not found. Please install yosys first."
    echo "Ubuntu/Debian: sudo apt install yosys"
    echo "Windows: Install from https://github.com/YosysHQ/yosys"
    exit 1
fi

# Check if dot (graphviz) is installed
if ! command -v dot &> /dev/null; then
    echo "Warning: Graphviz not found. Install for better visualizations:"
    echo "Ubuntu/Debian: sudo apt install graphviz"
    echo "Windows: choco install graphviz"
fi

# Create output directory
mkdir -p synthesis_output
cd synthesis_output

echo "1. Running quick visualization..."
yosys ../visualize_arnicomp.ys

echo ""
echo "2. Running full synthesis..."
yosys ../synthesize_arnicomp.ys

echo ""
echo "3. Converting dot files to images..."
if command -v dot &> /dev/null; then
    for dotfile in *.dot; do
        if [ -f "$dotfile" ]; then
            basename="${dotfile%.dot}"
            echo "Converting $dotfile to ${basename}.png"
            dot -Tpng "$dotfile" -o "${basename}.png"
            echo "Converting $dotfile to ${basename}.svg"
            dot -Tsvg "$dotfile" -o "${basename}.svg"
        fi
    done
fi

echo ""
echo "4. Generating clean schematics with netlistsvg..."
if command -v netlistsvg &> /dev/null; then
    # Full design RTL-level view
    yosys -p "
        read_verilog $(find rtl_converted/ -name '*.v' | tr '\n' ' ')
        hierarchy -top arnicomp_top
        proc
        write_json synthesis_output/arnicomp_rtl.json
    " > /dev/null 2>&1
    netlistsvg synthesis_output/arnicomp_rtl.json -o synthesis_output/arnicomp_rtl_schematic.svg
    echo "  Generated: arnicomp_rtl_schematic.svg (full design)"

    # Per-module schematics
    for module in alu comparator control_decoder flag_reg jump_logic program_counter; do
        if [ -f "rtl_converted/${module}.v" ]; then
            yosys -p "
                read_verilog rtl_converted/${module}.v
                hierarchy -top ${module}
                proc
                write_json synthesis_output/${module}_rtl.json
            " > /dev/null 2>&1
            netlistsvg synthesis_output/${module}_rtl.json -o synthesis_output/${module}_schematic.svg
            echo "  Generated: ${module}_schematic.svg"
        fi
    done
else
    echo "netlistsvg not found. Install with: sudo npm install -g netlistsvg"
fi

echo ""
echo "=== Results ==="
echo "Generated files:"
ls -la *.png *.svg *.json *.v 2>/dev/null || echo "No output files found"

echo ""
echo "=== How to view results ==="
echo "1. PNG/SVG files: Open with image viewer or web browser"
echo "2. JSON file: Use netlistsvg or similar tools"
echo "3. Verilog file: Synthesized netlist (text)"
echo ""

# Try to open the main visualization
if [ -f "arnicomp_blocks.svg" ]; then
    echo "Opening main CPU architecture diagram..."
    xdg-open arnicomp_blocks.svg 2>/dev/null || open arnicomp_blocks.svg 2>/dev/null || echo "Please manually open arnicomp_blocks.svg"
elif [ -f "arnicomp_blocks.png" ]; then
    echo "Opening main CPU architecture diagram..."
    xdg-open arnicomp_blocks.png 2>/dev/null || open arnicomp_blocks.png 2>/dev/null || echo "Please manually open arnicomp_blocks.png"
fi

echo "Done!"