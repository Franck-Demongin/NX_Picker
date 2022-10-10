from math import floor
from mathutils import Color
from typing  import List
import json
import os

def write_palette(path: str, data: str) -> None:
    with open(path, 'w') as f:
        f.write(data)

def rgb_to_hex(color: List[float]) -> str:
    cols = list(map(lambda c: hex(floor( 255 if c >= 1.0 else c * 256.0))[2:], color))
    r, g, b = list(map(lambda c: c+c if len(c) == 1 else c, cols))

    return f"#{r}{g}{b}".upper()

def convert_color(color: List[float], mode: str) -> List[str]:
    if mode == 'R':
        return (f"{color[0]:.3f}", f"{color[1]:.3f}", f"{color[2]:.3f}")

    if mode == 'H':
        c = Color((color[0], color[1], color[2]))
        return (f"{c.h:.3f}", f"{c.s:.3f}", f"{c.v:.3f}")
    
    if mode == '8':
        c = list(map(lambda c: str(floor( 255 if c >= 1.0 else c * 256.0)), color))
        return (c[0], c[1], c[2])

    return (str(color[0]), str(color[2]), str(color[2]))

def export_colors_to_json(path: str, colors: List[Color], blend_path: str|None = None) -> None:
    
    cols = [{"hex": rgb_to_hex((c.r, c.g, c.b)), "rgb": (c.r, c.g, c.b)} for c in colors]
    output = {
        "name": f"{os.path.splitext(os.path.basename(path))[0]}",
        "blend": blend_path or "Not available",
        "number": len(colors),
        "colors": cols
    }  
    
    with open(path, 'w') as f:
        json.dump(output, f)

def export_colors_to_gpl(path: str, colors: List[Color], blend_path: str|None = None) -> None:
    output = (f"GIMP Palette\n"
            f"Name: {os.path.splitext(os.path.basename(path))[0]}\n"
            f"Columns: 5\n"
            f"#\n"
            f"# Blend : {blend_path}\n"
            f"# Number : {len(colors)}\n"
            f"#\n")
    for i, color in enumerate(colors):
        r, g, b = convert_color(color, '8')
        output += f"{r} {g} {b} Index {i}\n"

    write_palette(path, output)

def export_colors_to_css(path: str, colors: List[Color], blend_path: str|None = None) -> None:
    nl = "\n"
    output = (f"/* Name : {os.path.splitext(os.path.basename(path))[0]} */\n"
            f"/* Blend : {blend_path} */\n"
            f"/* Number : {len(colors)} */\n")
    for color in colors:
        r, g, b = convert_color(color, '8')
        output += f"rgb({r}, {g}, {b})\n"
    output += "}"
        
    write_palette(path, output)