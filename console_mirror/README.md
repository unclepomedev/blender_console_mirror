# Console Mirror

Redirects system console output (`stdout`/`stderr`) to a Blender Text Block for easy debugging without opening the system console window.

## Features

*   **Live Mirroring**: Instantly mirrors `print()` and error outputs to a text block named `Log.txt` inside Blender.
*   **Safe Script Execution**: Runs scripts with advanced error catching. Even if your script causes a crash-like error that usually vanishes, this addon captures the traceback and logs it.
*   **Clean Tracebacks**: Automatically filters out internal addon frames from error logs, showing you only the relevant lines in your code—just like Blender's native error reporting.
*   **Dual Logging**: Output is sent to both the internal `Log.txt` and the system terminal/console.

## Installation

1.  Download the `.zip` file.
2.  Open Blender 4.2 or later.
3.  Go to **Edit > Preferences > Get Extensions**.
4.  Click the arrow icon (**∨**) in the top right and select **Install from Disk...**.
5.  Select the downloaded zip file.

## Usage

1.  Switch to the **Text Editor** workspace.
2.  Open the Sidebar (Press **N**) and click the **Dev** tab.
3.  Click **Start Mirroring**.
4.  Run your script:
    *   **Recommended:** Press **`Alt+P`** or click the **Run Script (Safe)** button in the panel.
    *   *Note: Using the standard "Run Script" button (Play icon) in the header may not capture all crash logs.*
5.  Output will appear in the `Log.txt` text block.

## License

SPDX:GPL-3.0-or-later
