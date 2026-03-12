@echo off
REM ArniComp CPU Synthesis and Visualization Script for Windows
REM Requirements: yosys, graphviz (dot)

echo === ArniComp CPU Synthesis and Visualization ===
echo.

REM Check if yosys is installed
yosys --version >nul 2>&1
if errorlevel 1 (
    echo Error: Yosys not found. Please install yosys first.
    echo Download from: https://github.com/YosysHQ/yosys
    echo Or use: choco install yosys
    pause
    exit /b 1
)

REM Check if dot (graphviz) is installed
dot -V >nul 2>&1
if errorlevel 1 (
    echo Warning: Graphviz not found. Install for better visualizations:
    echo choco install graphviz
    echo.
)

REM Create output directory
if not exist synthesis_output mkdir synthesis_output
cd synthesis_output

echo 1. Running quick visualization...
yosys ..\visualize_arnicomp.ys

echo.
echo 2. Running full synthesis...
yosys ..\synthesize_arnicomp.ys

echo.
echo 3. Converting dot files to images...
for %%f in (*.dot) do (
    if exist "%%f" (
        echo Converting %%f to %%~nf.png
        dot -Tpng "%%f" -o "%%~nf.png" >nul 2>&1
        echo Converting %%f to %%~nf.svg
        dot -Tsvg "%%f" -o "%%~nf.svg" >nul 2>&1
    )
)

echo.
echo === Results ===
echo Generated files:
dir /b *.png *.svg *.json *.v 2>nul

echo.
echo === How to view results ===
echo 1. PNG/SVG files: Open with image viewer or web browser
echo 2. JSON file: Use netlistsvg or similar tools
echo 3. Verilog file: Synthesized netlist (text)
echo.

REM Try to open the main visualization
if exist "arnicomp_blocks.svg" (
    echo Opening main CPU architecture diagram...
    start arnicomp_blocks.svg
) else if exist "arnicomp_blocks.png" (
    echo Opening main CPU architecture diagram...
    start arnicomp_blocks.png
)

echo Done!
pause