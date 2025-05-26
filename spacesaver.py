"""
SpaceSaver - A directory size analysis tool.
This module provides a portable way to analyze directory sizes with a GUI.
"""

import os
import matplotlib.pyplot as plt
# Import specific classes from tkinter instead of the entire module
from tkinter import Tk, filedialog, messagebox, ttk  # Tk for main window, other classes for specific functionalities
import random
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import threading
from datetime import datetime
from functools import lru_cache
from hashlib import md5  # Import only the md5 function from hashlib
from pathlib import Path
import time


@lru_cache(maxsize=1024)
# Import statements for input validation
import math

def get_size_format(b, factor=1024, suffix="B"):
    """
    Scale bytes to its proper byte format
    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
    """
    if not isinstance(b, (int, float)) or b < 0:
        raise ValueError("Input 'b' must be a non-negative number")
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if b < factor:
            return f"{b:.2f}{unit}{suffix}"
        b /= factor
    return f"{b:.2f}Y{suffix}"


class DirectorySizeCache:
    """Cache for directory sizes with modification time tracking"""
    def __init__(self):
        self._cache = {}
        self._mod_times = {}
        
    def get(self, path):
        """Get cached size if path hasn't been modified"""
        path_str = str(path)
        try:
            mtime = os.path.getmtime(path_str)
            if path_str in self._cache and self._mod_times[path_str] == mtime:
                return self._cache[path_str]
        except (OSError, KeyError):
            pass
        return None
        
    def set(self, path, size):
        """Cache directory size and modification time"""
        path_str = str(path)
        try:
            self._cache[path_str] = size
            self._mod_times[path_str] = os.path.getmtime(path_str)
        except OSError:
            pass

# Global cache instance
_dir_size_cache = DirectorySizeCache()

def get_directory_size(directory, batch_size=100):
    """Returns the `directory` size in bytes with caching and batch processing."""
    directory = Path(directory)
    
    # Check cache first
    cached_size = _dir_size_cache.get(directory)
    if cached_size is not None:
        return cached_size
        
    total = 0
    try:
        # Process files in batches
        entries = list(os.scandir(directory))
        stack = [(directory, entries)]
        
        while stack:
            current_dir, dir_entries = stack.pop()
            for i in range(0, len(dir_entries), batch_size):
                batch = dir_entries[i:i + batch_size]
                for entry in batch:
                    try:
                        if entry.is_file():
                            total += entry.stat().st_size
                        elif entry.is_dir():
                            sub_entries = list(os.scandir(entry.path))
                            stack.append((entry.path, sub_entries))
                    except (FileNotFoundError, PermissionError):
                        continue
                    
    except NotADirectoryError:
        try:
            total = os.path.getsize(directory)
        except (FileNotFoundError, PermissionError):
            return 0
    except PermissionError:
        return 0
    except Exception as e:
        print(f"Error accessing {directory}: {e}")
        return 0
        
    # Cache the result
    _dir_size_cache.set(directory, total)
    return total


class ColorCache:
    """Cache for generated colors to avoid regeneration"""
    def __init__(self):
        self._colors = {}
        
    def get_colors(self, n):
        """Get n distinct colors, generating new ones if needed"""
        if n in self._colors:
            return self._colors[n]
            
        # Generate new colors with golden ratio to ensure good distribution
        colors = []
        golden_ratio = 0.618033988749895
        hue = random.random()
        for i in range(n):
            hue = (hue + golden_ratio) % 1.0
            # Use HSV color space for more visually pleasing colors
            rgb = plt.cm.hsv(hue)
            colors.append((rgb[0], rgb[1], rgb[2], 0.8))  # Add alpha=0.8
            
        self._colors[n] = colors
        return colors

# Global color cache instance
_color_cache = ColorCache()

def generate_colors(n):
    """Generate n distinct colors for the pie chart using cached values"""
    return _color_cache.get_colors(n)


class DirectoryAnalyzer:
    def __init__(self, root=None):
        """
        Initialize the DirectoryAnalyzer.
        If root is None, a new Tk root window will be created.
        """
        if root is None:
            self.root = tk.Tk()
            self.should_run_mainloop = True
        else:
            self.root = root
            self.should_run_mainloop = False
            
        self.root.title("SpaceSaver - Directory Size Analyzer")
        self.root.geometry("1024x768")
        self.root.minsize(800, 600)
        
        # Set up the menu
        self.setup_menu()
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create toolbar
        self.setup_toolbar()
        
        # Create main content area with paned window
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tree view frame (left panel)
        self.tree_frame = ttk.Frame(self.paned_window)
        self.setup_tree_view()
        self.paned_window.add(self.tree_frame, weight=1)
        
        # Create visualization frame (right panel)
        self.viz_frame = ttk.Frame(self.paned_window)
        self.setup_visualization_panel()
        self.paned_window.add(self.viz_frame, weight=3)
        
        # Create status bar
        self.setup_status_bar()
        
        # Initialize variables
        self.canvas = None
        self.current_directory = None
        self.analysis_thread = None
        self.last_analysis_time = None
        
        # Cache for analysis results
        self._analysis_cache = {}
        self._figure_cache = {}
        
    def setup_menu(self):
        """Set up the application menu bar"""
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        
        # File menu
        file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Directory...", command=self.analyze_directory)
        file_menu.add_command(label="Refresh", command=self.refresh_analysis)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # View menu
        view_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Pie Chart", command=lambda: self.change_chart_type("pie"))
        view_menu.add_command(label="Bar Chart", command=lambda: self.change_chart_type("bar"))
        
        # Help menu
        help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
    def setup_toolbar(self):
        """Set up the toolbar with quick access buttons"""
        self.toolbar_frame = ttk.Frame(self.main_frame)
        self.toolbar_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Toolbar buttons
        ttk.Button(self.toolbar_frame, text="Open Directory", command=self.analyze_directory).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.toolbar_frame, text="Refresh", command=self.refresh_analysis).pack(side=tk.LEFT, padx=2)
        ttk.Separator(self.toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # Chart type selector
        ttk.Label(self.toolbar_frame, text="Chart Type:").pack(side=tk.LEFT, padx=5)
        self.chart_type = tk.StringVar(value="pie")
        chart_combo = ttk.Combobox(self.toolbar_frame, textvariable=self.chart_type, values=["Pie Chart", "Bar Chart"], state="readonly", width=10)
        chart_combo.pack(side=tk.LEFT, padx=2)
        chart_combo.bind('<<ComboboxSelected>>', lambda e: self.change_chart_type(self.chart_type.get().lower().split()[0]))
        
    def setup_tree_view(self):
        """Set up the directory tree view"""
        # Create a frame for the tree and its scrollbar
        tree_container = ttk.Frame(self.tree_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        # Create the tree view
        self.tree = ttk.Treeview(tree_container, selectmode="browse", show="tree")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        tree_scroll = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
    def setup_visualization_panel(self):
        """Set up the visualization panel"""
        # Create frame for visualization controls
        self.viz_controls = ttk.Frame(self.viz_frame)
        self.viz_controls.pack(fill=tk.X, padx=5, pady=5)
        
        # Add controls
        ttk.Label(self.viz_controls, text="Minimum slice size:").pack(side=tk.LEFT, padx=5)
        self.min_slice_var = tk.StringVar(value="3")
        min_slice_entry = ttk.Entry(self.viz_controls, textvariable=self.min_slice_var, width=5)
        min_slice_entry.pack(side=tk.LEFT, padx=2)
        ttk.Label(self.viz_controls, text="%").pack(side=tk.LEFT)
        
        # Create frame for the plot
        self.plot_frame = ttk.Frame(self.viz_frame)
        self.plot_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def setup_status_bar(self):
        """Set up the status bar"""
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=2)
        
        self.status_label = ttk.Label(self.status_frame, text="Ready", anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.status_frame, length=200, mode='determinate', variable=self.progress_var)
        self.progress_bar.pack(side=tk.RIGHT, padx=5)
        self.progress_bar.pack_forget()  # Hide initially
        
    def analyze_directory(self):
        """Open and analyze a directory"""
        try:
            folder_path = filedialog.askdirectory(title="Select Directory to Analyze")
            
            if not folder_path:  # User canceled
                return
                
            self.current_directory = folder_path
            self.refresh_analysis()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while selecting the directory: {str(e)}")
        
    def refresh_analysis(self):
        """Refresh the analysis of the current directory"""
        if not self.current_directory or not os.path.exists(self.current_directory):
            messagebox.showerror("Error", "No directory selected or directory no longer exists")
            return
            
        # Show progress bar
        self.progress_bar.pack(side=tk.RIGHT, padx=5)
        self.progress_var.set(0)
        self.status_label.config(text=f"Analyzing: {os.path.basename(self.current_directory)}")
        self.root.update()
        
        # Start analysis in a separate thread
        self.analysis_thread = threading.Thread(target=self._analyze_directory_thread)
        self.analysis_thread.start()
        
        # Schedule check for completion
        self.root.after(100, self._check_analysis_complete)
        
    def _analyze_directory_thread(self):
        """Perform directory analysis in a separate thread with caching"""
        try:
            # Check if we have a valid cached analysis
            cache_key = (self.current_directory, time.time() // 300)  # Cache key includes 5-min time bucket
            if cache_key in self._analysis_cache:
                self.last_analysis = self._analysis_cache[cache_key]
                self.last_analysis_time = datetime.now()
                return

            directory_sizes = []
            names = []
            
            # Get total items count for progress
            total_items = sum(1 for _ in os.scandir(self.current_directory) if _.is_dir())
            processed_items = 0
            
            # Clear tree view
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            # Add root directory
            root_size = get_directory_size(self.current_directory)
            root_name = os.path.basename(self.current_directory)
            root_id = self.tree.insert("", "end", text=f"{root_name} ({get_size_format(root_size)})")
            
            # Process directories in batches
            batch_size = 10
            entries = [entry for entry in os.scandir(self.current_directory) if entry.is_dir()]
            
            for i in range(0, len(entries), batch_size):
                batch = entries[i:i + batch_size]
                for entry in batch:
                    processed_items += 1
                    self.progress_var.set((processed_items / total_items) * 100)
                    
                    try:
                        # Get directory size with caching
                        directory_size = get_directory_size(entry.path)
                        if directory_size == 0:
                            continue
                            
                        # Add to lists for visualization
                        directory_sizes.append(directory_size)
                        names.append(f"{entry.name}\n{get_size_format(directory_size)}")
                        
                        # Add to tree view
                        self.tree.insert(root_id, "end", text=f"{entry.name} ({get_size_format(directory_size)})")
                    except Exception:
                        continue
            
            # Store results
            analysis_result = {
                'sizes': directory_sizes,
                'names': names,
                'total_size': sum(directory_sizes)
            }
            
            # Cache the analysis results
            self._analysis_cache[cache_key] = analysis_result
            self.last_analysis = analysis_result
            self.last_analysis_time = datetime.now()
            
        except Exception as e:
            self.last_analysis = None
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            
    def _check_analysis_complete(self):
        """Check if the analysis thread has completed"""
        if self.analysis_thread and self.analysis_thread.is_alive():
            # Still running, check again later
            self.root.after(100, self._check_analysis_complete)
            return
            
        # Analysis complete
        self.progress_bar.pack_forget()
        
        try:
            if not self.last_analysis:
                raise Exception("Analysis failed")
                
            if not self.last_analysis['sizes']:
                raise Exception("No directories with size > 0 found")
                
            # Update status
            self.status_label.config(
                text=(f"Total size: {get_size_format(self.last_analysis['total_size'])} - "
                      f"{os.path.basename(self.current_directory)} "
                      f"(analyzed at {self.last_analysis_time.strftime('%H:%M:%S')})")
            )
            
            # Update visualization
            self.update_visualization()
        except Exception as e:
            self.status_label.config(text=str(e))
        
    def update_visualization(self):
        """Update the visualization with current data using caching"""
        if not self.last_analysis:
            return
            
        # Generate cache key based on current data and chart type
        cache_key = (
            tuple(self.last_analysis['sizes']),
            tuple(self.last_analysis['names']),
            self.chart_type.get(),
            self.min_slice_var.get()
        )
        
        # Check if we have a cached figure
        if cache_key in self._figure_cache:
            if self.canvas:
                self.canvas.get_tk_widget().destroy()
            
            fig = self._figure_cache[cache_key]
            self.canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
            self.canvas.draw()
            
            # Add matplotlib toolbar
            toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
            toolbar.update()
            
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            return
            
        # Clear previous plot if exists
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            
        # Get current chart type
        chart_type = self.chart_type.get().lower().split()[0]
        
        # Create new plot
        if chart_type == "pie":
            fig = self.create_pie_chart()
        else:
            fig = self.create_bar_chart()
            
        # Cache the figure
        self._figure_cache[cache_key] = fig
            
    def create_pie_chart(self):
        """Create a pie chart visualization with caching"""
        sorted_data = self._prepare_chart_data()
        sizes, names = self._extract_sizes_and_names(sorted_data)
        min_pct = self._get_min_slice_size()
        colors = generate_colors(len(sizes))
        
        fig = self._create_pie_figure(sizes, names, min_pct, colors)
        return fig
        
    def _prepare_chart_data(self):
        return sorted(zip(self.last_analysis['sizes'], self.last_analysis['names']), reverse=True)
        
    def _extract_sizes_and_names(self, sorted_data):
        sizes = [s[0] for s in sorted_data]
        names = [s[1] for s in sorted_data]
        return sizes, names
        
    def _get_min_slice_size(self):
        try:
            return float(self.min_slice_var.get())
        except ValueError:
            return 3.0
        
        # Create figure
        fig = plt.Figure(figsize=(8, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        wedges, texts, autotexts = ax.pie(
            sizes, 
            labels=names,
            autopct=lambda pct: f"{pct:.1f}%" if pct > min_pct else "",
            colors=colors,
            shadow=True,
            startangle=90
        )
        
        # Make labels more readable
        plt.setp(texts, fontsize=9)
        plt.setp(autotexts, fontsize=9, weight="bold")
        
        ax.set_title(f"Directory Size Analysis: {os.path.basename(self.current_directory)}")
        
        # Create canvas with toolbar
        self.canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        self.canvas.draw()
        
        # Add matplotlib toolbar
        toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        toolbar.update()
        
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        return fig
        
    def create_bar_chart(self):
        """Create a bar chart visualization with caching"""
        # Sort by size (largest first)
        sorted_data = sorted(zip(self.last_analysis['sizes'], self.last_analysis['names']), reverse=True)
        sizes = [s[0] for s in sorted_data]
        names = [s[1].split('\n')[0] for s in sorted_data]  # Use only directory names
        
        # Create figure
        fig = plt.Figure(figsize=(8, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        # Create bars
        bars = ax.bar(range(len(sizes)), sizes)
        
        # Customize the plot
        ax.set_title(f"Directory Size Analysis: {os.path.basename(self.current_directory)}")
        ax.set_xlabel("Directories")
        ax.set_ylabel("Size (bytes)")
        
        # Set x-axis labels
        ax.set_xticks(range(len(names)))
        ax.set_xticklabels(names, rotation=45, ha='right')
        
        # Add size labels on top of bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{get_size_format(height)}',
                   ha='center', va='bottom', rotation=0)
        
        # Adjust layout to prevent label cutoff
        fig.tight_layout()
        
        # Create canvas with toolbar
        self.canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        self.canvas.draw()
        
        # Add matplotlib toolbar
        toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        toolbar.update()
        
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        return fig
        
    def change_chart_type(self, chart_type):
        """Change the visualization type"""
        if self.last_analysis:
            self.update_visualization()
            
    def show_about(self):
        """Show the about dialog"""
        about_text = """SpaceSaver - Directory Size Analyzer

A tool to help you visualize and manage disk space usage.

Features:
- Interactive directory analysis
- Multiple visualization types
- Directory tree view
- Real-time updates

Version: 1.0
"""
        messagebox.showinfo("About SpaceSaver", about_text)
    
    def run(self):
        """Run the application main loop if needed"""
        if self.should_run_mainloop:
            self.root.mainloop()


def main():
    """Entry point for the application"""
    app = DirectoryAnalyzer()
    app.run()


if __name__ == "__main__":
    main()