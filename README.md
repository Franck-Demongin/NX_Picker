![hero](https://user-images.githubusercontent.com/54265936/194942683-c95ee842-d7a1-4aa1-ab2f-60c682499042.png)

# NX_Picker
Pick color and create palette in Image Editor and Compositor.
Palette could be saved and/or exported in several formats (Gimp and Photoshop are supported)

<img src="https://img.shields.io/badge/Blender-2.8.0-green" /> <img src="https://img.shields.io/badge/Python-3.10-blue" /> <img src="https://img.shields.io/badge/Addon-1.0.0.Stable-orange" /> 
[![GPLv3 license](https://img.shields.io/badge/License-GPLv3-blue.svg)](http://perso.crans.org/besson/LICENSE.html)

## Installation

Download ZIP file on your system.

In Blender, install addon from _Preferences > Add-ons > Install_...  
Activate the addon

## Usage

In the Image Editor (View mode) or in the Compositor Editor open toolbar (T) and select Picker tool (EYEDROPPER icon).
In Sidebar (N), open Tool panel.

### Picker

LMB (Left Button Mouse) display the color selected in Picker panel. You can choose to display color in three ways: RGB (R) from 0 to 1, HSV (H) or RGB 8bits (8) from 0 to 255. The code hexadecimal (#000000) is always visible.
To add the selected color to the palette, click on the last button (+)
You can also add directly the color to the palette by press Shit + click.

### Palette

The palette is a regular Blender's palette, remove and sort color in the same way (Add button is not realy usefull). The color selected in the palette is display just under in the same way of the color selected with the picker. 

#### Save the Palette
Save the palette in the blend file to use it in other editors.

### Export the Palette
Export the palette to use it in other programs. Choose beetwen:
- JSON
- GPL palette used by GIMP
- CSS palette usable with Photoshop

### Clear Palette
Remove all the color and reset palette


