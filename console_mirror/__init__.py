# SPDX-License-Identifier: GPL-3.0-or-later

import os
import sys
import traceback

import bpy

original_stdout = sys.stdout
original_stderr = sys.stderr
original_excepthook = sys.excepthook
is_logging_active = False
active_text_name = "Log.txt"
addon_keymaps = []


class MirrorLogger:
    """Catches stdout/stderr and writes to both terminal and Blender Text Block."""

    def __init__(self, original_stream, text_name, is_error=False):
        self.terminal = original_stream
        self.text_name = text_name
        self.is_error = is_error
        self.at_line_start = True

    def get_target_text(self):
        if self.text_name not in bpy.data.texts:
            return bpy.data.texts.new(self.text_name)
        return bpy.data.texts[self.text_name]

    def _write_to_block(self, message, text_block):
        """Write lines to text block with [ERR] prefix logic."""
        lines = message.splitlines(keepends=True)
        output = []

        for line in lines:
            if self.at_line_start and self.is_error:
                output.append("[ERR] " + line)
            else:
                output.append(line)

            if line.endswith('\n'):
                self.at_line_start = True
            else:
                self.at_line_start = False

        text_block.write("".join(output))

    def write(self, message):
        # Write to original stream first
        try:
            if self.terminal:
                self.terminal.write(message)
                self.terminal.flush()
        except Exception:
            pass

        # Write to Blender Text Block
        try:
            text_block = self.get_target_text()
            if not message:
                return
            self._write_to_block(message, text_block)

        except Exception as e:
            # If Blender internal write fails, try to log to terminal
            try:
                if self.terminal:
                    self.terminal.write(f"\n[Console Mirror Internal Error]: {e}\n")
            except:
                pass

    def write_to_text(self, message):
        """Write only to Blender Text Block."""
        try:
            text_block = self.get_target_text()
            if not message:
                return
            self._write_to_block(message, text_block)
        except Exception:
            pass

    def flush(self):
        try:
            if self.terminal:
                self.terminal.flush()
        except Exception:
            pass


def mirror_excepthook(exctype, value, tb):
    """Custom exception hook to capture Python errors."""
    if issubclass(exctype, KeyboardInterrupt):
        original_excepthook(exctype, value, tb)
        return

    # Format the traceback
    lines = traceback.format_exception(exctype, value, tb)
    msg = "".join(lines)

    # Write to stderr (which should be our MirrorLogger)
    sys.stderr.write(msg)


def ensure_mirror():
    """Periodically re-wrap sys.stdout/stderr if stolen."""
    if not is_logging_active:
        return None

    # Re-wrap stolen streams, preserving chaining.
    if not isinstance(sys.stdout, MirrorLogger):
        sys.stdout = MirrorLogger(sys.stdout, active_text_name, is_error=False)

    if not isinstance(sys.stderr, MirrorLogger):
        sys.stderr = MirrorLogger(sys.stderr, active_text_name, is_error=True)

    if sys.excepthook != mirror_excepthook:
        sys.excepthook = mirror_excepthook

    return 0.1  # Check every 0.1 second


def start_mirror():
    global is_logging_active, active_text_name
    if is_logging_active: return

    # Get log name
    ctx = bpy.context
    if ctx and hasattr(ctx, "scene") and ctx.scene:
        active_text_name = ctx.scene.console_mirror_props.text_name
    else:
        active_text_name = "Log.txt"

    # Wrap streams, respecting current configuration
    if not isinstance(sys.stdout, MirrorLogger):
        sys.stdout = MirrorLogger(sys.stdout, active_text_name, is_error=False)
    if not isinstance(sys.stderr, MirrorLogger):
        sys.stderr = MirrorLogger(sys.stderr, active_text_name, is_error=True)

    sys.excepthook = mirror_excepthook
    is_logging_active = True

    if hasattr(bpy.app, "timers"):
        bpy.app.timers.register(ensure_mirror)

    # Register Keymap for Safe Run (Alt+P)
    try:
        wm = bpy.context.window_manager
        kc = wm.keyconfigs.addon
        if kc:
            km = kc.keymaps.new(name='Text', space_type='TEXT_EDITOR')
            kmi = km.keymap_items.new("console_mirror.run_script_safe", 'P', 'PRESS', alt=True)
            addon_keymaps.append((km, kmi))
    except Exception as e:
        print(f"Console Mirror: Failed to register keymap: {e}")

    print("--- Console Mirror Started ---")


def stop_mirror():
    global is_logging_active

    if isinstance(sys.stdout, MirrorLogger):
        sys.stdout = original_stdout
    if isinstance(sys.stderr, MirrorLogger):
        sys.stderr = original_stderr

    sys.excepthook = original_excepthook

    if hasattr(bpy.app, "timers") and bpy.app.timers.is_registered(ensure_mirror):
        bpy.app.timers.unregister(ensure_mirror)

    # Unregister Keymaps
    for km, kmi in addon_keymaps:
        try:
            km.keymap_items.remove(kmi)
        except:
            pass
    addon_keymaps.clear()

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


class CM_OT_RunScriptSafe(bpy.types.Operator):
    bl_idname = "console_mirror.run_script_safe"
    bl_label = "Run Script (Safe)"
    bl_description = "Run the active script with error catching enabled. Replaces standard run for better logging."

    def execute(self, context):
        text = None
        if hasattr(context, "edit_text") and context.edit_text:
            text = context.edit_text
        elif hasattr(context, "space_data") and hasattr(context.space_data, "text"):
            text = context.space_data.text

        if not text:
            self.report({'WARNING'}, "No active text block found to run.")
            return {'CANCELLED'}

        # Prevent executing the log file itself
        log_name = "Log.txt"
        if context and hasattr(context, "scene") and hasattr(context.scene, "console_mirror_props"):
            log_name = context.scene.console_mirror_props.text_name

        if text.name == log_name:
            self.report({'WARNING'}, f"Cannot run the log file '{text.name}' as a script.")
            return {'CANCELLED'}

        # Prepare namespace
        namespace = {
            "__name__": "__main__",
            "__file__": text.filepath if text.filepath else "Text",
            "bpy": bpy,
        }

        if text.filepath:
            script_dir = os.path.dirname(text.filepath)
            if script_dir not in sys.path:
                sys.path.append(script_dir)

        try:
            # Use compile to set correct filename in traceback
            filename = text.filepath if text.filepath else text.name
            code = compile(text.as_string(), filename, 'exec')
            exec(code, namespace)
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()

            # Strip addon internal frames for clean traceback.
            tb = exc_traceback
            while tb and tb.tb_frame.f_code.co_filename == __file__:
                tb = tb.tb_next

            # Format the clean traceback.
            lines = traceback.format_exception(exc_type, exc_value, tb)
            msg = "".join(lines)

            # Write to sys.stderr (handles both console and log file).
            sys.stderr.write(msg)

            # Report error to UI (Info/Status bar)
            self.report({'ERROR'}, f"{exc_type.__name__}: {exc_value}")

            # Return CANCELLED to suppress Blender's native error reporting.
            return {'CANCELLED'}


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

        # Run Button (Safe)
        layout.separator()
        layout.operator("console_mirror.run_script_safe", icon='PLAY', text="Run Script (Safe)")
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
    CM_OT_RunScriptSafe,
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
