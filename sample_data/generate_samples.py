"""Generates synthetic sample_data files, anchored to the REAL part numbers
from the Weatherford BOM PDF (part 02736321 assembly, e.g. child 00158794),
per the "single anchored part" decision made in chat."""

import pandas as pd
import os

os.makedirs("sample_data", exist_ok=True)

# Real BOM data (transcribed from the actual Weatherford PDF, part 02736321)
bom_rows = [
    (1, "00234408", "234408", "Top Conn. HYD-IIAP 9.625 X 3.5 X 2.875 WS410", 1.0, "each"),
    (2, "00157317", "905-96-321", "Slip body, upper HDW2 9.625in WD002", 1.0, "each"),
    (3, "00229454", "00229454", "Upper Slip, 9.625 Hydrow IIP Packer WS601", 4.0, "each"),
    (4, "00161535", "480-70-900", "Spring,Slip, 7.000 Isolation Injection", 24.0, "each"),
    (5, "00157359", "905-96-910", "Screw, set SLTD 0.438 UNF 20TPI SLTD STD STL 1.188 LG", 4.0, "each"),
    (14, "00158794", "905-96-751", "Mandrel, Setting Hydrow II 9.625in 36-47# WD002", 1.0, "each"),
]
df = pd.DataFrame(bom_rows, columns=["Line Number", "Number", "Primary Legacy Number", "Name", "Quantity", "UOM"])
df.to_excel("sample_data/02736321_MBOM_RevD.xlsx", index=False)

# MBD stand-in: real title-block fields, saved as a small text/pdf placeholder
# (true native model file not available — this documents that gap explicitly)
with open("sample_data/00158794_MBD_RevB.6.txt", "w") as f:
    f.write(
        "Part Number: 00158794\nModel File: 00158794\nModel Version: B.6\n"
        "Drawing File: 00158794\nDrawing Version: B.6\n"
        "NOTE: stand-in for native MBD model file — real Creo/STEP file not yet received.\n"
    )

# SOP placeholder — synthetic, references real part/assembly numbers
with open("sample_data/02736321_SOP_RevA.txt", "w") as f:
    f.write(
        "Assembly SOP — PKR RETV Hydrow II A-P (Part 02736321)\n"
        "SYNTHETIC PLACEHOLDER — no real SOP sample received yet.\n\n"
        "Step 1: Install Top Connection (00234408)\n"
        "Step 2: Install Upper Slip Sub-Assembly (00157317, 00229454, 00161535)\n"
        "Step 3: Install Upper Cone & Sealing Elements (00157359, 00157370)\n"
        "Step 4: Install Setting Mandrel (00158794)\n"
    )

# NC placeholder — generic G-code structure, relabeled with real part number in header
with open("sample_data/00158794_NC_Rev1.nc", "w") as f:
    f.write(
        "; PART: 00158794 - Mandrel, Setting Hydrow II\n"
        "; SYNTHETIC PLACEHOLDER - generic G-code structure, no real NC sample received yet\n"
        "G21 G90 G17\n"
        "T1 M06\n"
        "G00 X0 Y0 Z50\n"
        "G01 Z-5 F100\n"
        "M30\n"
    )

print("Generated sample_data files:")
for f in sorted(os.listdir("sample_data")):
    if f != "generate_samples.py":
        print(" -", f)
