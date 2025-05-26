# SpaceSaver

A directory size analysis tool with GUI that helps you visualize disk space usage.

## Features

- Analyze directory sizes with an interactive GUI
- Visualize directory sizes with pie charts
- Easy-to-use interface

## Installation

### Option 1: Install from source

```bash
# Clone the repository
git clone https://github.com/yourusername/SpaceSaver.git
cd SpaceSaver

# Install the package
pip install -e .
```

### Option 2: Run directly

```bash
# Clone the repository
git clone https://github.com/yourusername/SpaceSaver.git
cd SpaceSaver

# Run the application
python -m spacesaver
```

## Usage

After installation, you can run the application in two ways:

1. From the command line:
   ```
   spacesaver
   ```

2. As a Python module:
   ```python
   from spacesaver import DirectoryAnalyzer
   import tkinter as tk
   
   root = tk.Tk()
   app = DirectoryAnalyzer(root)
   root.mainloop()
   ```

## Requirements

- Python 3.6+
- matplotlib
- tkinter (usually comes with Python)

### Linux-specific Requirements

On Linux, you may need to install tkinter separately:

```bash
# For Debian/Ubuntu
sudo apt-get install python3-tk

# For Fedora
sudo dnf install python3-tkinter

# For Arch Linux
sudo pacman -S tk
```

## License

This project is licensed under the terms of the MIT license.