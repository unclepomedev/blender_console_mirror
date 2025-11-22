# SPDX-License-Identifier: GPL-3.0-or-later

import sys

import bpy

original_stdout = sys.stdout
original_stderr = sys.stderr
is_logging_active = False


class MirrorLogger:
    """
    Catches stdout/stderr and writes to both:
    1. The original system terminal.
    2. A specified Text Block within Blender.
    """

    def __init__(self, original_stream, is_error=False):
        self.terminal = original_stream
        self.is_error = is_error

    def get_target_text(self):
        scn = bpy.context.scene
        name = scn.console_mirror_props.text_name

        if name not in bpy.data.texts:
            return bpy.data.texts.new(name)
        return bpy.data.texts[name]

    def write(self, message):
        self.terminal.write(message)
        self.terminal.flush()

        try:
            text_block = self.get_target_text()

            prefix = "[ERR] " if self.is_error and message.strip() else ""
            text_block.write(prefix + message)

        except Exception:
            # If Blender internal write fails, ignore it to keep the script running
            pass

    def flush(self):
        self.terminal.flush()


def start_mirror():
    global is_logging_active
    if is_logging_active: return

    sys.stdout = MirrorLogger(original_stdout, is_error=False)
    sys.stderr = MirrorLogger(original_stderr, is_error=True)
    is_logging_active = True
    print("--- Console Mirror Started ---")


def stop_mirror():
    global is_logging_active

    if isinstance(sys.stdout, MirrorLogger):
        sys.stdout = original_stdout
    if isinstance(sys.stderr, MirrorLogger):
        sys.stderr = original_stderr

    is_logging_active = False
    print("--- Console Mirror Stopped ---")


class CM_Properties(bpy.types.PropertyGroup):
    text_name: bpy.props.StringProperty(
        name="Log File Name",
        default="Log.txt",
        description="Name of the text block to output logs"
    )


class CM_OT_Start(bpy.types.Operator):
    bl_idname = "console_mirror.start"
    bl_label = "Start Mirroring"
    bl_description = "Start redirecting console output to text editor"

    def execute(self, _):
        start_mirror()
        return {'FINISHED'}


class CM_OT_Stop(bpy.types.Operator):
    bl_idname = "console_mirror.stop"
    bl_label = "Stop Mirroring"
    bl_description = "Stop redirection and restore original console"

    def execute(self, _):
        stop_mirror()
        return {'FINISHED'}


class CM_OT_Clear(bpy.types.Operator):
    bl_idname = "console_mirror.clear"
    bl_label = "Clear Log"
    bl_description = "Clear the content of the log file"

    def execute(self, context):
        name = context.scene.console_mirror_props.text_name
        if name in bpy.data.texts:
            bpy.data.texts[name].clear()
        return {'FINISHED'}


class CM_PT_Panel(bpy.types.Panel):
    bl_label = "Console Mirror"
    bl_idname = "CM_PT_Panel"
    bl_space_type = 'TEXT_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Dev"

    def draw(self, context):
        layout = self.layout
        props = context.scene.console_mirror_props

        layout.prop(props, "text_name")

        row = layout.row(align=True)
        if is_logging_active:
            row.operator("console_mirror.stop", icon='PAUSE', text="Stop Mirroring")
            row.alert = True
        else:
            row.operator("console_mirror.start", icon='PLAY', text="Start Mirroring")

        layout.separator()
        layout.operator("console_mirror.clear", icon='TRASH')

        if is_logging_active:
            layout.label(text="Status: Active", icon='CHECKMARK')
        else:
            layout.label(text="Status: Inactive", icon='X')


classes = (
    CM_Properties,
    CM_OT_Start,
    CM_OT_Stop,
    CM_OT_Clear,
    CM_PT_Panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.console_mirror_props = bpy.props.PointerProperty(type=CM_Properties)


def unregister():
    stop_mirror()
    del bpy.types.Scene.console_mirror_props
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
