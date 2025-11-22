# blender_console_mirror

Redirects system console output (`stdout`/`stderr`) to a Blender Text Block for easy debugging without an external
terminal.

## Features

* **Dual Logging:** Mirrors output to Blender while keeping the system terminal active.
* **Simple UI:** Control via the Text Editor sidebar (Start/Stop/Clear).
* **Safe:** Non-destructive mirroring prevents data loss on crashes.

## Installation

1. Download the `.zip` file.
2. Open Blender 4.2 or later.
3. Go to **Edit > Preferences > Get Extensions**.
4. Click the arrow icon (**∨**) in the top right and select **Install from Disk...**.
5. Select the downloaded zip file.

## Usage

1. Switch to the **Text Editor** workspace.
2. Open the Sidebar (Press **N**) and click the **Dev** tab.
3. Click **Start Mirroring**.
4. Run your scripts.
5. Output will appear in a text block named `Log.txt`.

## License

SPDX:GPL-3.0-or-later
