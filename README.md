# Directory Size Analyzer

A graphical tool to visualize and analyze directory sizes on your system.

## Features

- Interactive GUI for directory selection and analysis
- Visual representation of subdirectory sizes using pie charts
- Real-time progress tracking during directory scanning
- Ability to analyze multiple directories in a single session
- Automatic sorting of directories by size
- Colorful visualization with size labels

## Requirements

- Python 3.6+
- Required packages:
  - matplotlib
  - tkinter (usually comes with Python)

## Installation

1. Ensure Python 3.6+ is installed on your system
2. Install required packages:
   ```
   pip install matplotlib
   ```

## Usage

1. Run the script:
   ```
   python get-directory-gui.py
   ```
2. Click the "Select Directory" button
3. Choose a directory to analyze
4. View the pie chart showing subdirectory sizes
5. Click "Select Directory" again to analyze a different directory

## How It Works

The application recursively scans the selected directory and calculates the size of each subdirectory. It then displays the results in a pie chart, with each slice representing a subdirectory. The size of each slice is proportional to the size of the corresponding subdirectory.

## Limitations

- Very large directories may take time to scan
- Permission errors may prevent scanning some directories
- Files directly in the selected directory are not included in the analysis