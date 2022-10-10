# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "NX_Picker",
    "author" : "Franck Demongin",
    "description" : "Pick color and create palette",
    "blender" : (2, 80, 0),
    "version" : (0, 1, 0),
    "location" : "TooBar in Image and Node Editors",
    "category" : "Generic"
}

import gpu
import numpy as np
import bpy
from bpy_extras.io_utils import ExportHelper
from .utils.colors import (
    convert_color, 
    rgb_to_hex, 
    export_colors_to_json, 
    export_colors_to_gpl,
    export_colors_to_css
)

PALETTE_NAME = 'PickerPalette'

class NXPICKER_OT_palette_clean(bpy.types.Operator):
    bl_idname = 'nxpicker.palette_clean'
    bl_label = 'Clean palette'
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return bpy.data.palettes.get(PALETTE_NAME)

    def execute(self, context):
        pal = bpy.data.palettes.get(PALETTE_NAME)
        pal.colors.clear()    

        return {'FINISHED'}


class NXPICKER_OT_palette_save(bpy.types.Operator):
    bl_idname = 'nxpicker.palette_save'
    bl_label = 'Save palette'
    bl_options = {'INTERNAL'}

    name: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return bpy.data.palettes.get(PALETTE_NAME)

    def execute(self, context):
        if len(self.name) == 0:
            self.report({'ERROR'}, "Name is empty")
            return {'CANCELLED'}

        pal = bpy.data.palettes.get(PALETTE_NAME)
        p = pal.copy()            
        p.name = self.name
        p.use_fake_user = True

        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


def update_format(self, context):    
    sfile = context.space_data
    if not isinstance(sfile, bpy.types.SpaceFileBrowser):
        return
    if not sfile.active_operator:
        return
    if sfile.active_operator.bl_idname != "NXPICKER_OT_palette_export":
        return

    ext = '.json'
    if self.type == 'GPL':
        ext = '.gpl'
    if self.type == 'CSS':
        ext = '.css'
    
    sfile.active_operator.filename_ext = ext

class NXPICKER_OT_palette_export(bpy.types.Operator, ExportHelper):
    bl_idname = 'nxpicker.palette_export'
    bl_label = 'Export palette'
    bl_options = {'INTERNAL'}

    filename_ext = '.json'
    
    filepath: bpy.props.StringProperty(default='palette')
    type: bpy.props.EnumProperty(
        name="Output Format",
        description="Choose a format",
        items=(
            ('JSON', "JSON", "Export in JSON"),
            ('GPL', "GPL", "Export in GPL, the Gimp palette format"),
            ('CSS', "CSS", "Export in CSS for compatibility with Photoshop"),
        ),
        default='JSON',
        update=update_format
    )

    filter_glob: bpy.props.StringProperty(
        default="*.json;*.gpl;*.css",
        options={'HIDDEN'}
    )

    @classmethod
    def poll(cls, context):
        pal = bpy.data.palettes.get(PALETTE_NAME)
        return pal and len(pal.colors) > 0 

    def execute(self, context):
        pal = bpy.data.palettes.get(PALETTE_NAME)
        file_name = bpy.data.filepath if bpy.data.is_saved else 'Not available'
        if self.type == 'JSON':
            export_colors_to_json(self.filepath, [color.color for color in pal.colors], file_name)
        if self.type == 'GPL':
            export_colors_to_gpl(self.filepath, [color.color for color in pal.colors], file_name)
        if self.type == 'CSS':
            export_colors_to_css(self.filepath, [color.color for color in pal.colors], file_name)

        return {'FINISHED'}
    
    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.label(text="Format")
        row.prop(self, 'type', text='Select Format', expand=True)
        

class NXPICKER_OT_add_color_to_palette(bpy.types.Operator):
    bl_idname = 'nxpicker.add_color_to_palette'
    bl_label = 'Add to Palette'
    bl_description = 'Add selected color to palette'
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context):
        return bpy.data.palettes.get(PALETTE_NAME)

    def execute(self, context):
        color = context.window_manager.nxpicker.color

        pal = bpy.data.palettes.get(PALETTE_NAME)
        col = pal.colors.new()
        col.color = (color[0], color[1], color[2])
        pal.colors.active = col

        return {"FINISHED"}
    
    def invoke(self, context, event):
        pal = bpy.data.palettes.get(PALETTE_NAME)
        if pal is None:
            pal = bpy.data.palettes.new(PALETTE_NAME)
        pal.use_fake_user = False
        ts = bpy.context.tool_settings   
        ts.image_paint.palette = pal

        return self.execute(context)


class NXPICKER_OT_picker(bpy.types.Operator):
    bl_idname = 'nxpicker.picker'
    bl_label = 'Color Picker'
    bl_description = 'Extract color information from multiple adjacent pixels'
    bl_options = {'INTERNAL'}

    mouse_x: bpy.props.IntProperty()
    mouse_y: bpy.props.IntProperty()
    shift: bpy.props.BoolProperty(default=False)
    ctrl: bpy.props.BoolProperty(default=False)

    def execute(self, context):
        context.area.tag_redraw()
        wm = context.window_manager
        
        fb = gpu.state.active_framebuffer_get()
        screen_buffer = fb.read_color(self.mouse_x, self.mouse_y, wm.nxpicker.sample_size, wm.nxpicker.sample_size, 3, 0, 'FLOAT')

        pix = np.array(screen_buffer.to_list())
        pix_size = wm.nxpicker.sample_size * wm.nxpicker.sample_size
        sum_by_channel = pix.reshape(pix_size, 3).sum(axis=0)
        average_by_channel = sum_by_channel / pix_size

        red, green, blue = average_by_channel
        wm.nxpicker.color = (red, green, blue, 1.0)

        pal = bpy.data.palettes.get(PALETTE_NAME)
        if self.shift:
            col = pal.colors.new()
            col.color = (red, green, blue)
            pal.colors.active = col
            
        wm.nxpicker.selected = True

        r, g, b = convert_color(wm.nxpicker.color, '8')        
        self.report({'INFO'}, f"Red: {r}, Green: {g}, Blue: {b}")

        return {'FINISHED'}

    def invoke(self, context, event):
        pal = bpy.data.palettes.get(PALETTE_NAME)
        if pal is None:
            pal = bpy.data.palettes.new(PALETTE_NAME)
        pal.use_fake_user = False
        ts = bpy.context.tool_settings   
        ts.image_paint.palette = pal

        self.mouse_x = event.mouse_x
        self.mouse_y = event.mouse_y
        return self.execute(context)


class PanelBase:
    bl_label = 'Picker'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        layout.use_property_decorate = False
        layout.use_property_split = False
        wm = context.window_manager

        if wm.nxpicker.selected:
            red, green, blue, _ = wm.nxpicker.color
            r, g, b = convert_color(wm.nxpicker.color, wm.nxpicker.display_mode)

            box = layout.column().box()
            row = box.row()
            row.template_node_socket(color=(red, green, blue, 1.0))
            row.label(text=rgb_to_hex((red, green, blue)))
            row.prop(wm.nxpicker, 'display_mode', expand=True)
            row.operator('nxpicker.add_color_to_palette', text='', icon='ADD')
            row = box.row()
            row.label(text=f"R: {r}")
            row.label(text=f"G: {g}")
            row.label(text=f"B: {b}")
        else:
            row = layout.row()
            row.label(text="Pick Color")
            
            row = layout.row()
        ts = context.tool_settings
        if ts.image_paint.palette:
            if ts.image_paint.palette.name == PALETTE_NAME:                
                if ts.image_paint.palette.colors:
                    col = layout.column()
                    row_base = col.row()
                    col1 = row_base.column()
                    box = col1.box()
                    box.template_palette(ts.image_paint, "palette", color=True)
                    if ts.image_paint.palette.colors.active:
                        color = ts.image_paint.palette.colors.active.color
                        r, g, b = convert_color(color, wm.nxpicker.display_mode)
                        row = col1.row()
                        row.label(text=rgb_to_hex((color.r, color.g, color.b)))
                        row.label(text=f"R: {r}")
                        row.label(text=f"G: {g}")
                        row.label(text=f"B: {b}")
                    row = col1.row()
                    
                    col2 = row_base.column()
                    
                    col2.operator('nxpicker.palette_save', text="", icon="CURRENT_FILE")
                    col2.operator('nxpicker.palette_export', text="", icon="EXPORT")
                    col2.operator('nxpicker.palette_clean', text="", icon="FILE_REFRESH")


class NXPICKER_PT_node_editor(bpy.types.Panel, PanelBase):
    bl_idname = 'NXPICKER_PT_node_editor'
    bl_space_type = 'NODE_EDITOR'

    @classmethod
    def poll(cls, context):
        return context.area.ui_type == 'CompositorNodeTree'


class NXPICKER_PT_image_editor(bpy.types.Panel, PanelBase):
    bl_idname = 'NXPICKER_PT_image_editor'
    bl_space_type = 'IMAGE_EDITOR'

    @classmethod
    def poll(cls, context):
        return True


class ToolBase:
    bl_label = "Picker"
    bl_description = ("Pick a color")
    bl_icon = "ops.paint.weight_sample"
    bl_cursor = "EYEDROPPER"
    bl_widget = None
    bl_keymap = (
        ("nxpicker.picker", {"type": 'LEFTMOUSE', "value": 'PRESS'}, None),
        ("nxpicker.picker", {"type": 'LEFTMOUSE', "value": 'PRESS', "shift": True}, 
            {"properties": [("shift", True)]}),
    )

    def draw_settings(context, layout, tool):
        tool.operator_properties("nxpicker.picker")
        wm = context.window_manager

        row = layout.row()
        row.prop(wm.nxpicker, 'sample_size')


class NXPickerNodeEditor(bpy.types.WorkSpaceTool, ToolBase):
    bl_space_type='NODE_EDITOR'
    bl_context_mode=None
    bl_idname = "NXPicker.node_editor"


class NXPickerImageEditor(bpy.types.WorkSpaceTool, ToolBase):
    bl_space_type='IMAGE_EDITOR'
    bl_context_mode='VIEW'
    bl_idname = "NXPicker.image_editor"
    

class NXPickerPropertyGroup(bpy.types.PropertyGroup):
    color: bpy.props.FloatVectorProperty(
        name = "Color",
        subtype = "COLOR",
        size = 4,
        min = 0.0,
        max = 1.0,
        default = (0.0,0.0,0.0,1.0)
    )
    selected: bpy.props.BoolProperty(default=False)
    sample_size: bpy.props.IntProperty(default=1, min=1, max=25)
    display_mode: bpy.props.EnumProperty(
        name = 'Display Mode',
        items = [
            ('R', 'R', 'RVB', '', 1),
            ('H', 'H', 'HSV', '', 2),
            ('8', '8', '8bits', '', 3),
        ]
    )


classes = (
    NXPickerPropertyGroup,
    NXPICKER_OT_palette_save,
    NXPICKER_OT_palette_export,
    NXPICKER_OT_palette_clean,
    NXPICKER_OT_add_color_to_palette,
    NXPICKER_OT_picker,
    NXPICKER_PT_node_editor,
    NXPICKER_PT_image_editor,
)

tool_classes = (
    NXPickerNodeEditor,
    NXPickerImageEditor,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    for cls in tool_classes:
        bpy.utils.register_tool(cls, after=None, separator=True, group=False)
    
    bpy.types.WindowManager.nxpicker = bpy.props.PointerProperty(type=NXPickerPropertyGroup)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    for cls in tool_classes:
        bpy.utils.unregister_tool(cls)

    del bpy.types.WindowManager.nxpicker