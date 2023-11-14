import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from threading import Thread
import queue
import sqlite3
from pathlib import Path
from PIL import Image, ImageTk
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
from datetime import datetime

class PNGtoJPEGConverter:
    def __init__(self, master):
        self.master = master
        master.title("PNG to JPEG Converter")

        self.source_folder_var = tk.StringVar()
        self.destination_folder_var = tk.StringVar()
        self.progress_var = tk.DoubleVar()
        self.error_log_var = tk.StringVar()

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.master, text="Source Folder:").grid(row=0, column=0, sticky=tk.E)
        tk.Entry(self.master, textvariable=self.source_folder_var, state="readonly").grid(row=0, column=1)
        tk.Button(self.master, text="Select Folder", command=self.select_source_folder).grid(row=0, column=2)

        tk.Label(self.master, text="Destination Folder:").grid(row=1, column=0, sticky=tk.E)
        tk.Entry(self.master, textvariable=self.destination_folder_var, state="readonly").grid(row=1, column=1)
        tk.Button(self.master, text="Select Folder", command=self.select_destination_folder).grid(row=1, column=2)

        tk.Label(self.master, text="Conversion Scale:").grid(row=2, column=0, sticky=tk.E)
        self.scale_var = tk.Scale(self.master, from_=0, to=100, orient=tk.HORIZONTAL)
        self.scale_var.set(50)
        self.scale_var.grid(row=2, column=1)

        self.start_button = tk.Button(self.master, text="Start Conversion", command=self.start_conversion)
        self.start_button.grid(row=3, column=0, columnspan=3)

        self.progressbar = ttk.Progressbar(self.master, variable=self.progress_var, maximum=100)
        self.progressbar.grid(row=4, column=0, columnspan=3, sticky=tk.EW)

        tk.Label(self.master, text="Error Log:").grid(row=5, column=0, sticky=tk.E)
        tk.Label(self.master, textvariable=self.error_log_var, wraplength=400, justify=tk.LEFT).grid(row=5, column=1, columnspan=2)

    def select_source_folder(self):
        folder = filedialog.askdirectory()
        self.source_folder_var.set(folder)

    def select_destination_folder(self):
        folder = filedialog.askdirectory()
        self.destination_folder_var.set(folder)

    def start_conversion(self):
        source_folder = Path(self.source_folder_var.get())
        destination_folder = Path(self.destination_folder_var.get())
        scale = self.scale_var.get() / 100.0

        self.progress_var.set(0)
        self.error_log_var.set("")

        # Start conversion in a separate thread
        conversion_thread = Thread(target=self.convert_images, args=(source_folder, destination_folder, scale))
        conversion_thread.start()

    def convert_images(self, source_folder, destination_folder, scale):
        # Add your image conversion logic here

        # Simulate conversion progress for demonstration
        for i in range(101):
            time.sleep(0.1)  # Simulate processing time
            self.progress_var.set(i)

        # Update error log (simulated error for demonstration)
        self.error_log_var.set("Simulated error occurred during conversion.")

if __name__ == "__main__":
    root = tk.Tk()
    app = PNGtoJPEGConverter(root)
    root.mainloop()
