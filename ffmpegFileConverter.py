import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import subprocess
import threading
import os
import re

IMAGE_FORMATS = ["png", "jpg", "jpeg", "webp", "bmp", "gif", "tiff"]
AUDIO_FORMATS = ["mp3", "wav", "ogg", "flac", "aac", "m4a"]
VIDEO_FORMATS = ["mp4", "avi", "mkv", "mov", "webm", "flv"]

ffmpeg_process = None


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

    update_output_name()


def update_output_name(*args):
    input_path = input_entry.get().strip()
    output_format = format_var.get().strip().lower()
    if input_path and output_format:
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        name_entry.delete(0, tk.END)
        name_entry.insert(0, base_name)


def select_file():
    file_path = filedialog.askopenfilename()
    if file_path:
        clean_path = file_path.strip('"')
        input_entry.delete(0, tk.END)
        input_entry.insert(0, clean_path)
        update_format_options(clean_path)


def drop_file(event):
    clean_path = event.data.strip('"')
    input_entry.delete(0, tk.END)
    input_entry.insert(0, clean_path)
    update_format_options(clean_path)


def cancel_conversion():
    global ffmpeg_process
    if ffmpeg_process and ffmpeg_process.poll() is None:
        ffmpeg_process.terminate()
        progress_label.config(text="Conversion canceled.")
        progress_bar["value"] = 0
        convert_button["state"] = "normal"
        cancel_button["state"] = "disabled"


def get_duration(path):
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
             path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return float(result.stdout.strip())
    except:
        return None


def format_duration(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:05.2f}"


def convert_file():
    global ffmpeg_process

    input_path = input_entry.get()
    output_format = format_var.get().lower().strip()
    custom_name = name_entry.get().strip()
    open_folder = open_var.get()

    if not input_path or not output_format:
        messagebox.showerror("Error", "Please select a file and output format.")
        return

    input_dir = os.path.dirname(input_path)
    output_path = os.path.join(input_dir, f"{custom_name}.{output_format}")

    if os.path.exists(output_path):
        overwrite = messagebox.askyesno(
            "File Exists",
            f"The file:\n{output_path}\nalready exists.\nDo you want to overwrite it?"
        )
        if not overwrite:
            return

    duration = get_duration(input_path)
    if not duration:
        duration = 0

    def run_ffmpeg():
        global ffmpeg_process
        progress_bar["value"] = 0
        progress_label.config(text="Converting...")

        # Show progress UI
        progress_bar.grid(row=5, column=1, pady=10)
        progress_label.grid(row=6, column=1)

        convert_button["state"] = "disabled"
        cancel_button["state"] = "normal"

        cmd = ["ffmpeg", "-y", "-i", input_path]

        if output_format in AUDIO_FORMATS:
            cmd += ["-vn"]

        cmd.append(output_path)
        ffmpeg_process = subprocess.Popen(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            universal_newlines=True,
            bufsize=1
        )

        time_pattern = re.compile(r"time=(\d{2}:\d{2}:\d{2}\.\d{2})")
        speed_pattern = re.compile(r"speed=\s*([\d.]+)x")

        def read_progress():
            while True:
                line = ffmpeg_process.stderr.readline()
                if not line:
                    break

                # Sometimes ffmpeg outputs progress on same line with \r
                if '\r' in line:
                    line = line.split('\r')[-1]

                time_match = time_pattern.search(line)
                speed_match = speed_pattern.search(line)

                current_time_str = time_match.group(1) if time_match else ""
                speed_str = speed_match.group(1) if speed_match else ""

                if current_time_str and duration:
                    h, m, s = current_time_str.split(":")
                    current_secs = int(h) * 3600 + int(m) * 60 + float(s)
                    percent = (current_secs / duration) * 100
                    progress_bar["value"] = percent

                if current_time_str:
                    label = f"Converting... {current_time_str} / {format_duration(duration)}"
                    if speed_str:
                        label += f"  |  speed: {speed_str}x"
                    else:
                        label += "  |  speed: N/A"
                    progress_label.config(text=label)

            ffmpeg_process.wait()
            if ffmpeg_process.returncode == 0:
                progress_bar["value"] = 100
                progress_label.config(text="Conversion complete.")
                if open_folder:
                    os.startfile(input_dir)
            elif ffmpeg_process.returncode == -15:
                progress_label.config(text="Conversion canceled.")
            else:
                progress_label.config(text="Conversion failed.")
                messagebox.showerror("FFmpeg Error", "Conversion failed.")

            # Hide progress UI
            progress_bar.grid_remove()
            progress_label.grid_remove()
            convert_button["state"] = "normal"
            cancel_button["state"] = "disabled"

        threading.Thread(target=read_progress).start()

    threading.Thread(target=run_ffmpeg).start()


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
format_var.trace_add("write", update_output_name)
format_menu = ttk.Combobox(frame, textvariable=format_var)
format_menu.grid(row=1, column=1, pady=10)

tk.Label(frame, text="New file name (optional):").grid(row=2, column=0, sticky="w")
name_entry = tk.Entry(frame, width=50)
name_entry.grid(row=2, column=1, padx=5)

open_var = tk.BooleanVar(value=True)
open_checkbox = tk.Checkbutton(frame, text="Open folder after conversion", variable=open_var)
open_checkbox.grid(row=3, column=1, sticky="w", pady=(5, 10))

convert_button = tk.Button(frame, text="Convert", command=convert_file)
convert_button.grid(row=4, column=1, pady=5)

cancel_button = tk.Button(frame, text="Cancel", command=cancel_conversion, state="disabled")
cancel_button.grid(row=4, column=2, pady=5)

progress_bar = ttk.Progressbar(frame, orient="horizontal", length=400, mode="determinate")
# progress_bar.grid(row=5, column=1, pady=10)

progress_label = tk.Label(frame, text="")
# progress_label.grid(row=6, column=1)

root.mainloop()
