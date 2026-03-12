# ArniComp CPU Synthesis & Visualization

Bu dizindeki dosyalar ArniComp CPU'yu Yosys ile sentezlemek ve devre yapısını görselleştirmek için hazırlanmıştır.

## Gereksinimler

### Zorunlu:
- **Yosys** - Open source Verilog synthesis tool
  - Windows: https://github.com/YosysHQ/yosys/releases veya `choco install yosys`  
  - Linux: `sudo apt install yosys` (Ubuntu/Debian)
  - macOS: `brew install yosys`

### İsteğe Bağlı:
- **Graphviz** - Grafik görselleştirme için
  - Windows: `choco install graphviz`
  - Linux: `sudo apt install graphviz`  
  - macOS: `brew install graphviz`

## Kullanım

### Otomatik (Önerilen):
```bash
# Linux/macOS:
chmod +x run_synthesis.sh
./run_synthesis.sh

# Windows:
run_synthesis.bat
```

### Manuel:
```bash
# Hızlı görselleştirme (sadece mimari)
yosys visualize_arnicomp.ys

# Tam sentez (daha detaylı)
yosys synthesize_arnicomp.ys

# DOT dosyalarını resimlere çevir
dot -Tpng arnicomp_circuit.dot -o arnicomp_circuit.png
dot -Tsvg arnicomp_blocks.dot -o arnicomp_blocks.svg
```

## Çıktı Dosyaları

### Görsel Dosyalar:
- `arnicomp_blocks.svg/png` - **Ana CPU mimarisi** (blok diyagram)
- `arnicomp_detailed.dot/png` - Detaylı bağlantı şeması
- `arnicomp_hierarchy.svg` - Modül hiyerarşisi

### Veri Dosyaları:
- `synthesized_arnicomp.v` - Sentezlenmiş Verilog netlist
- `arnicomp.json` - JSON formatında netlist (nextpnr vs. için)

## Dosya Açıklamaları

| Dosya | Açıklama |
|-------|----------|
| `synthesize_arnicomp.ys` | Tam sentez script'i |
| `visualize_arnicomp.ys` | Hızlı görselleştirme script'i |
| `run_synthesis.sh` | Linux/macOS otomatik script |
| `run_synthesis.bat` | Windows otomatik script |

## Ipuçları

### En İyi Görselleştirme için:
1. **arnicomp_blocks.svg** - Genel CPU yapısını anlamak için
2. **arnicomp_detailed.png** - Register ve ALU bağlantılarını görmek için  
3. **arnicomp_hierarchy.svg** - Modül organizasyonunu anlamak için

### Sorun Giderme:
- **"module not found" hatası**: Tüm .sv dosyalarının mevcut olduğundan emin olun
- **Görsel çıkmıyor**: Graphviz yüklü olduğundan emin olun  
- **Çok büyük görsel**: SVG formatını kullanın, zoom yapılabilir

### İleri Analiz:
```bash
# Sadece ALU'yu görmek için:
yosys -p "read_verilog -sv rtl/blocks/alu.sv; hierarchy -top alu; proc; show alu"

# Critical path analizi:
yosys -p "read_verilog -sv rtl/blocks/alu.sv; synth; sta"
```

## Yosys Komutları Referansı

- `read_verilog -sv file.sv` - SystemVerilog dosyası oku
- `hierarchy -top module` - Top modül belirle  
- `proc; opt` - Temel sentez işlemleri
- `show module` - Görselleştir
- `stat` - İstatistikler göster
- `write_verilog file.v` - Netlist yaz

Bu script'ler ArniComp CPU'nun tam yapısını analiz etmenizi ve anlamanızı sağlar!