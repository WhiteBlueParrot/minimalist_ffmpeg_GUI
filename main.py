import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import subprocess
import os

IMAGE_FORMATS = ["png", "jpg", "jpeg", "webp", "bmp", "gif", "tiff"]
AUDIO_FORMATS = ["mp3", "wav", "ogg", "flac", "aac", "m4a"]
VIDEO_FORMATS = ["mp4", "avi", "mkv", "mov", "webm", "flv"]


def get_file_category(ext):
    ext = ext.lower()
    if ext in IMAGE_FORMATS:
        return "image"
    elif ext in AUDIO_FORMATS:
        return "audio"
    elif ext in VIDEO_FORMATS:
        return "video"
    return None


def update_format_options(input_path):
    ext = os.path.splitext(input_path)[1][1:].lower()
    category = get_file_category(ext)

    if category == "image":
        format_menu['values'] = IMAGE_FORMATS
    elif category == "audio":
        format_menu['values'] = AUDIO_FORMATS
    elif category == "video":
        format_menu['values'] = VIDEO_FORMATS + AUDIO_FORMATS
    else:
        format_menu['values'] = []


def select_file():
    file_path = filedialog.askopenfilename()
    if file_path:
        input_entry.delete(0, tk.END)
        input_entry.insert(0, file_path)
        update_format_options(file_path)


def drop_file(event):
    path = event.data.strip('{}')
    input_entry.delete(0, tk.END)
    input_entry.insert(0, path)
    update_format_options(path)


def convert_file():
    input_path = input_entry.get()
    output_format = format_var.get()

    if not input_path or not output_format:
        messagebox.showerror("Error", "Please select a file and output format.")
        return

    base, _ = os.path.splitext(input_path)
    output_path = f"{base}.{output_format}"

    if os.path.exists(output_path):
        overwrite = messagebox.askyesno(
            "File Exists",
            f"The file:\n{output_path}\nalready exists.\nDo you want to overwrite it?"
        )
        if not overwrite:
            return

    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_path, output_path],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT
        )
        messagebox.showinfo("Success", f"Converted to:\n{output_path}")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("FFmpeg Error", str(e))


# GUI setup
root = TkinterDnD.Tk()
root.title("FFmpeg Converter")

frame = tk.Frame(root, padx=10, pady=10)
frame.pack()

tk.Label(frame, text="Input File:").grid(row=0, column=0, sticky="w")
input_entry = tk.Entry(frame, width=50)
input_entry.grid(row=0, column=1, padx=5)
input_entry.drop_target_register(DND_FILES)
input_entry.dnd_bind('<<Drop>>', drop_file)

tk.Button(frame, text="Browse", command=select_file).grid(row=0, column=2)

tk.Label(frame, text="Convert to:").grid(row=1, column=0, sticky="w", pady=10)
format_var = tk.StringVar()
format_menu = ttk.Combobox(frame, textvariable=format_var)
format_menu.grid(row=1, column=1, pady=10)

tk.Button(frame, text="Convert", command=convert_file).grid(row=2, column=1, pady=10)

root.mainloop()
