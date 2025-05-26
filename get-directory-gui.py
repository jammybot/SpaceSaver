import os
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog, messagebox
from matplotlib.colors import to_rgba
import random
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def get_size_format(b, factor=1024, suffix="B"):
    """
    Scale bytes to its proper byte format
    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
    """
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if b < factor:
            return f"{b:.2f}{unit}{suffix}"
        b /= factor
    return f"{b:.2f}Y{suffix}"


def get_directory_size(directory):
    """Returns the `directory` size in bytes."""
    total = 0
    try:
        for entry in os.scandir(directory):
            if entry.is_file():
                # if it's a file, use stat() function
                total += entry.stat().st_size
            elif entry.is_dir():
                # if it's a directory, recursively call this function
                try:
                    total += get_directory_size(entry.path)
                except (FileNotFoundError, PermissionError):
                    pass
    except NotADirectoryError:
        # if `directory` isn't a directory, get the file size then
        return os.path.getsize(directory)
    except PermissionError:
        # if for whatever reason we can't open the folder, return 0
        return 0
    except Exception as e:
        print(f"Error accessing {directory}: {e}")
        return 0
    return total


def generate_colors(n):
    """Generate n distinct colors for the pie chart"""
    colors = []
    for i in range(n):
        # Generate a random color with some transparency
        color = (random.random(), random.random(), random.random(), 0.8)
        colors.append(color)
    return colors


class DirectoryAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("Directory Size Analyzer")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Create main frame
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create button frame
        self.button_frame = tk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X, pady=10)
        
        # Create select directory button
        self.select_btn = tk.Button(self.button_frame, text="Select Directory", 
                                   command=self.analyze_directory, bg="#4CAF50", fg="white",
                                   font=("Arial", 12), padx=10, pady=5)
        self.select_btn.pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_label = tk.Label(self.button_frame, text="Select a directory to analyze", 
                                    font=("Arial", 10), fg="#555555")
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # Create plot frame
        self.plot_frame = tk.Frame(self.main_frame)
        self.plot_frame.pack(fill=tk.BOTH, expand=True)
        
        # Initialize plot canvas as None
        self.canvas = None
        
    def analyze_directory(self):
        folder_path = filedialog.askdirectory(title="Select Directory to Analyze")
        
        if not folder_path:  # User canceled
            return
        
        self.status_label.config(text=f"Analyzing: {os.path.basename(folder_path)}")
        self.root.update()
        
        try:
            directory_sizes = []
            names = []
            
            # Show progress
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Analyzing Directory")
            progress_window.geometry("300x100")
            progress_window.transient(self.root)
            progress_window.grab_set()
            
            progress_label = tk.Label(progress_window, text="Scanning directories...\nThis may take a while for large directories.")
            progress_label.pack(pady=20)
            progress_window.update()
            
            # iterate over all the directories inside this path
            for directory in os.listdir(folder_path):
                full_path = os.path.join(folder_path, directory)
                if os.path.isdir(full_path):
                    # Update progress label
                    progress_label.config(text=f"Scanning: {directory}")
                    progress_window.update()
                    
                    # get the size of this directory (folder)
                    directory_size = get_directory_size(full_path)
                    if directory_size == 0:
                        continue
                    directory_sizes.append(directory_size)
                    names.append(f"{directory}\n{get_size_format(directory_size)}")
            
            progress_window.destroy()
            
            if not directory_sizes:
                messagebox.showinfo("Result", "No directories with size > 0 found.")
                self.status_label.config(text="No directories with size > 0 found")
                return
                
            total_size = sum(directory_sizes)
            self.status_label.config(text=f"Total size: {get_size_format(total_size)} - {os.path.basename(folder_path)}")
            
            # Clear previous plot if exists
            if self.canvas:
                self.canvas.get_tk_widget().destroy()
            
            # Create new plot
            self.plot_directory_sizes(directory_sizes, names, folder_path)
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.status_label.config(text=f"Error: {str(e)}")
    
    def plot_directory_sizes(self, sizes, names, folder_path):
        # Sort by size (largest first)
        sorted_data = sorted(zip(sizes, names), reverse=True)
        sizes = [s[0] for s in sorted_data]
        names = [s[1] for s in sorted_data]
        
        # Generate colors
        colors = generate_colors(len(sizes))
        
        # Create figure
        fig = plt.Figure(figsize=(8, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        wedges, texts, autotexts = ax.pie(
            sizes, 
            labels=names, 
            autopct=lambda pct: f"{pct:.1f}%" if pct > 3 else "",
            colors=colors,
            shadow=True,
            startangle=90
        )
        
        # Make labels more readable
        plt.setp(texts, fontsize=9)
        plt.setp(autotexts, fontsize=9, weight="bold")
        
        ax.set_title(f"Directory Size Analysis: {os.path.basename(folder_path)}")
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


if __name__ == "__main__":
    root = tk.Tk()
    app = DirectoryAnalyzer(root)
    root.mainloop()