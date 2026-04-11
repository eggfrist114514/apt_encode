import sys
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
from PIL import Image, ImageTk
import wave
import math
import struct

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

SYNCA = "000011001100110011001100110011000000000"
SYNCB = "000011100111001110011100111001110011100"

APT_A_CONFIGS = {
    "1": [27,60,95,124,160,190,223,255,0,55,55,55,55,0,0,60],
    "2": [27,60,95,124,160,190,223,255,0,55,55,55,55,0,0,60],
    "3b": [27,60,95,124,160,190,223,255,0,55,55,55,55,90,120,95],
    "4": [27,60,95,124,160,190,223,255,0,55,55,55,55,120,160,124],
    "5": [27,60,95,124,160,190,223,255,0,55,55,55,55,120,160,160]
}

APT_B_CONFIGS = {
    "1": [27,60,95,126,160,190,222,255,0,106,106,106,106,0,0,27],
    "2": [27,60,95,126,160,190,222,255,0,106,106,106,106,0,0,60],
    "3b": [27,60,95,126,160,190,222,255,0,106,106,106,106,90,120,95],
    "4": [27,60,95,126,160,190,222,255,0,106,106,106,106,90,120,126],
    "5": [27,60,95,126,160,190,222,255,0,106,106,106,106,90,120,160]
}

def convert_to_8bit(image):
    if image.mode == 'I;16':
        array = np.array(image, dtype=np.uint16)
        array = (array >> 8).astype(np.uint8)
        return Image.fromarray(array, 'L')
    else:
        return image.convert('L')

class APTEncoderApp:
    def __init__(self, root):
        self.root = root
        root.title("APT Encoder v2.0 UI (Linux)")
        root.geometry("1200x800")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=2)
        main_frame.rowconfigure(0, weight=1)

        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=(0, 10))
        left_frame.columnconfigure(1, weight=1)

        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=2, sticky="nsew")
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)

        row = 0
        ttk.Label(left_frame, text="输入图片A路径:").grid(row=row, column=0, sticky="w", pady=5)
        self.entry_img_a = ttk.Entry(left_frame)
        self.entry_img_a.grid(row=row, column=1, sticky="ew", padx=5)
        btn_a = ttk.Button(left_frame, text="打开", command=self.browse_image_a)
        btn_a.grid(row=row, column=2, padx=5)
        row += 1

        ttk.Label(left_frame, text="输入图片B路径:").grid(row=row, column=0, sticky="w", pady=5)
        self.entry_img_b = ttk.Entry(left_frame)
        self.entry_img_b.grid(row=row, column=1, sticky="ew", padx=5)
        btn_b = ttk.Button(left_frame, text="打开", command=self.browse_image_b)
        btn_b.grid(row=row, column=2, padx=5)
        row += 1

        ttk.Label(left_frame, text="AVHRR A图格式:").grid(row=row, column=0, sticky="w", pady=5)
        self.a_format_var = tk.StringVar(value="3b")
        a_frame = ttk.Frame(left_frame)
        a_frame.grid(row=row, column=1, columnspan=2, sticky="w")
        ttk.Radiobutton(a_frame, text="可见光 1", variable=self.a_format_var, value="1").pack(side="left")
        ttk.Radiobutton(a_frame, text="可见光 2", variable=self.a_format_var, value="2").pack(side="left")
        ttk.Radiobutton(a_frame, text="红外 3b", variable=self.a_format_var, value="3b").pack(side="left")
        ttk.Radiobutton(a_frame, text="红外 4", variable=self.a_format_var, value="4").pack(side="left")
        ttk.Radiobutton(a_frame, text="红外 5", variable=self.a_format_var, value="5").pack(side="left")
        row += 1

        ttk.Label(left_frame, text="AVHRR B图格式:").grid(row=row, column=0, sticky="w", pady=5)
        self.b_format_var = tk.StringVar(value="4")
        b_frame = ttk.Frame(left_frame)
        b_frame.grid(row=row, column=1, columnspan=2, sticky="w")
        ttk.Radiobutton(b_frame, text="可见光 1", variable=self.b_format_var, value="1").pack(side="left")
        ttk.Radiobutton(b_frame, text="可见光 2", variable=self.b_format_var, value="2").pack(side="left")
        ttk.Radiobutton(b_frame, text="红外 3b", variable=self.b_format_var, value="3b").pack(side="left")
        ttk.Radiobutton(b_frame, text="红外 4", variable=self.b_format_var, value="4").pack(side="left")
        ttk.Radiobutton(b_frame, text="红外 5", variable=self.b_format_var, value="5").pack(side="left")
        row += 1

        self.switch_var = tk.BooleanVar(value=False)
        self.switch_check = ttk.Checkbutton(left_frame, text="切换传感器", variable=self.switch_var, command=self.toggle_switch_options)
        self.switch_check.grid(row=row, column=0, sticky="w", pady=5)
        row += 1

        self.switch_frame = ttk.Frame(left_frame)
        self.switch_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=5)
        self.switch_frame.columnconfigure(1, weight=1)
        self.switch_frame.grid_remove()

        ttk.Label(self.switch_frame, text="传感器切换的遥测次数(128行一次):").grid(row=0, column=0, sticky="w")
        self.switch_line_var = tk.StringVar()
        self.switch_line_entry = ttk.Entry(self.switch_frame, textvariable=self.switch_line_var, width=10)
        self.switch_line_entry.grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(self.switch_frame, text="切换A图格式:").grid(row=1, column=0, sticky="w", pady=5)
        self.switch_a_var = tk.StringVar(value="3b")
        sw_a_frame = ttk.Frame(self.switch_frame)
        sw_a_frame.grid(row=1, column=1, sticky="w")
        ttk.Radiobutton(sw_a_frame, text="可见光 1", variable=self.switch_a_var, value="1").pack(side="left")
        ttk.Radiobutton(sw_a_frame, text="可见光 2", variable=self.switch_a_var, value="2").pack(side="left")
        ttk.Radiobutton(sw_a_frame, text="红外 3b", variable=self.switch_a_var, value="3b").pack(side="left")
        ttk.Radiobutton(sw_a_frame, text="红外 4", variable=self.switch_a_var, value="4").pack(side="left")
        ttk.Radiobutton(sw_a_frame, text="红外 5", variable=self.switch_a_var, value="5").pack(side="left")

        ttk.Label(self.switch_frame, text="切换B图格式:").grid(row=2, column=0, sticky="w", pady=5)
        self.switch_b_var = tk.StringVar(value="4")
        sw_b_frame = ttk.Frame(self.switch_frame)
        sw_b_frame.grid(row=2, column=1, sticky="w")
        ttk.Radiobutton(sw_b_frame, text="可见光 1", variable=self.switch_b_var, value="1").pack(side="left")
        ttk.Radiobutton(sw_b_frame, text="可见光 2", variable=self.switch_b_var, value="2").pack(side="left")
        ttk.Radiobutton(sw_b_frame, text="红外 3b", variable=self.switch_b_var, value="3b").pack(side="left")
        ttk.Radiobutton(sw_b_frame, text="红外 4", variable=self.switch_b_var, value="4").pack(side="left")
        ttk.Radiobutton(sw_b_frame, text="红外 5", variable=self.switch_b_var, value="5").pack(side="left")

        row += 1

        self.fault_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(left_frame, text="禁用红外", variable=self.fault_var).grid(row=row, column=0, sticky="w", pady=5)
        row += 1

        ttk.Label(left_frame, text="输出文件夹:").grid(row=row, column=0, sticky="w", pady=5)
        self.output_dir_var = tk.StringVar()
        self.output_dir_entry = ttk.Entry(left_frame, textvariable=self.output_dir_var)
        self.output_dir_entry.grid(row=row, column=1, sticky="ew", padx=5)
        btn_out = ttk.Button(left_frame, text="打开", command=self.browse_output_dir)
        btn_out.grid(row=row, column=2, padx=5)
        row += 1

        ttk.Label(left_frame, text="图片生成进度:").grid(row=row, column=0, sticky="w", pady=5)
        self.progress_img = ttk.Progressbar(left_frame, orient="horizontal", mode="determinate")
        self.progress_img.grid(row=row, column=1, columnspan=2, sticky="ew", padx=5)
        row += 1

        ttk.Label(left_frame, text="音频生成进度:").grid(row=row, column=0, sticky="w", pady=5)
        self.progress_audio = ttk.Progressbar(left_frame, orient="horizontal", mode="determinate")
        self.progress_audio.grid(row=row, column=1, columnspan=2, sticky="ew", padx=5)
        row += 1

        self.btn_generate = ttk.Button(left_frame, text="开始生成", command=self.toggle_generation)
        self.btn_generate.grid(row=row, column=0, columnspan=3, pady=20)
        row += 1

        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(left_frame, textvariable=self.status_var, foreground="blue")
        self.status_label.grid(row=row, column=0, columnspan=3, sticky="w")

        ttk.Label(right_frame, text="APT图像预览:").grid(row=0, column=0, sticky="nw", pady=(0, 5))
        
        self.preview_frame = ttk.Frame(right_frame)
        self.preview_frame.grid(row=1, column=0, sticky="nsew")
        self.preview_frame.columnconfigure(0, weight=1)
        self.preview_frame.rowconfigure(0, weight=1)
        
        self.preview_canvas = tk.Canvas(self.preview_frame, bg='black', width=600, height=400)
        self.preview_canvas.grid(row=0, column=0, sticky="nsew")
        
        v_scrollbar = ttk.Scrollbar(self.preview_frame, orient="vertical", command=self.preview_canvas.yview)
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar = ttk.Scrollbar(self.preview_frame, orient="horizontal", command=self.preview_canvas.xview)
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        self.preview_canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.preview_label = ttk.Label(right_frame, text="等待生成...", anchor="center")
        self.preview_label.grid(row=2, column=0, pady=5)
        
        self.preview_image = None
        self.preview_photo = None

        self.running = False
        self.stop_event = threading.Event()
        self.worker_thread = None
        self.current_output_array = None

        root.bind('<Configure>', self.on_window_resize)

    def on_window_resize(self, event):
        if self.current_output_array is not None:
            self.update_preview()

    def toggle_switch_options(self):
        if self.switch_var.get():
            self.switch_frame.grid()
        else:
            self.switch_frame.grid_remove()

    def browse_image_a(self):
        path = filedialog.askopenfilename(title="选择图片A", filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.tif")])
        if path:
            self.entry_img_a.delete(0, tk.END)
            self.entry_img_a.insert(0, path)

    def browse_image_b(self):
        path = filedialog.askopenfilename(title="选择图片B", filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.tif")])
        if path:
            self.entry_img_b.delete(0, tk.END)
            self.entry_img_b.insert(0, path)

    def browse_output_dir(self):
        path = filedialog.askdirectory(title="选择输出文件夹")
        if path:
            self.output_dir_var.set(path)

    def toggle_generation(self):
        if self.running:
            self.stop_event.set()
            self.btn_generate.config(state="disabled")
            self.status_var.set("正在停止...")
        else:
            self.start_generation()

    def start_generation(self):
        img_a_path = self.entry_img_a.get().strip()
        img_b_path = self.entry_img_b.get().strip()
        if not img_a_path or not img_b_path:
            messagebox.showerror("错误", "请选择两张图片")
            return
        if not os.path.exists(img_a_path) or not os.path.exists(img_b_path):
            messagebox.showerror("错误", "图片文件不存在")
            return
        output_dir = self.output_dir_var.get().strip()
        if not output_dir:
            output_dir = SCRIPT_DIR
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except:
                messagebox.showerror("错误", "无法创建输出文件夹")
                return
        self.running = True
        self.stop_event.clear()
        self.btn_generate.config(text="停止生成")
        self.progress_img["value"] = 0
        self.progress_audio["value"] = 0
        self.status_var.set("正在生成图片...")
        self.worker_thread = threading.Thread(target=self.generate_apt, args=(img_a_path, img_b_path, output_dir), daemon=True)
        self.worker_thread.start()

    def generate_apt(self, img_a_path, img_b_path, output_dir):
        try:
            apt_a_format = self.a_format_var.get()
            apt_b_format = self.b_format_var.get()
            t_val_list = APT_A_CONFIGS.get(apt_a_format, APT_A_CONFIGS["5"])
            t_val1_list = APT_B_CONFIGS.get(apt_b_format, APT_B_CONFIGS["5"])

            switch_enabled = self.switch_var.get()
            switch_line = -1
            switch_a_format = apt_a_format
            switch_b_format = apt_b_format
            if switch_enabled:
                try:
                    switch_line = int(self.switch_line_var.get().strip())
                except:
                    self.root.after(0, lambda: messagebox.showerror("错误", "切换次数必须是整数"))
                    self.reset_ui()
                    return
                switch_a_format = self.switch_a_var.get()
                switch_b_format = self.switch_b_var.get()
            t_val_list_switch = APT_A_CONFIGS.get(switch_a_format, APT_A_CONFIGS["5"])
            t_val1_list_switch = APT_B_CONFIGS.get(switch_b_format, APT_B_CONFIGS["5"])

            fault_flag = 1 if self.fault_var.get() else 0

            img1 = Image.open(img_a_path)
            img2 = Image.open(img_b_path)
            img1 = convert_to_8bit(img1)
            img2 = convert_to_8bit(img2)
            w1, h1 = img1.size
            new_height = int(909 * h1 / w1)
            imgA = img1.resize((909, new_height), Image.NEAREST)
            imgB = img2.resize((909, new_height), Image.NEAREST)
            arrA = np.array(imgA)
            arrB = np.array(imgB)

            connt = 114514
            len_syncA = len(SYNCA)
            len_syncB = len(SYNCB)
            len_space = 47
            len_telemetry = 45
            len_image = 909
            total_width = len_syncA + len_space + len_image + len_telemetry + len_syncB + len_space + len_image + len_telemetry
            output = np.zeros((new_height, total_width), dtype=np.uint8)

            syncA_arr = np.array([255 if c == '1' else 0 for c in SYNCA], dtype=np.uint8)
            syncB_arr = np.array([255 if c == '1' else 0 for c in SYNCB], dtype=np.uint8)

            avhrr = 0
            avhrr1 = 0

            y_indices = np.arange(new_height)
            row_mod = y_indices % 120
            space_high_mask = (row_mod == 0) | (row_mod == 1)

            for y in range(new_height):
                if self.stop_event.is_set():
                    self.root.after(0, lambda: self.status_var.set("已停止"))
                    self.reset_ui()
                    return

                current_a_format = apt_a_format
                current_b_format = apt_b_format
                current_t_val_list = t_val_list
                current_t_val1_list = t_val1_list
                if connt == 1 or (switch_enabled and y // 128 == switch_line):
                    current_a_format = switch_a_format
                    current_b_format = switch_b_format
                    current_t_val_list = t_val_list_switch
                    current_t_val1_list = t_val1_list_switch
                    connt = 1

                is_current_a_high = current_a_format in ["3b", "4", "5"]
                is_current_b_high = current_b_format in ["3b", "4", "5"]

                line = np.zeros(total_width, dtype=np.uint8)
                pos = 0
                line[pos:pos+len_syncA] = syncA_arr
                pos += len_syncA

                if fault_flag == 0:
                    if is_current_a_high:
                        spaceA = np.where(space_high_mask[y], 0, 255)
                    else:
                        spaceA = np.where(space_high_mask[y], 255, 0)
                else:
                    spaceA = np.where(space_high_mask[y], 255, 0)
                line[pos:pos+len_space] = spaceA
                pos += len_space

                if fault_flag == 1 and is_current_a_high:
                    line[pos:pos+len_image] = 0
                else:
                    line[pos:pos+len_image] = arrA[y]
                pos += len_image

                t_val = current_t_val_list[(avhrr//8)]
                line[pos:pos+len_telemetry] = t_val
                pos += len_telemetry

                line[pos:pos+len_syncB] = syncB_arr
                pos += len_syncB

                if fault_flag == 0:
                    if is_current_b_high:
                        spaceB = np.where(space_high_mask[y], 0, 255)
                    else:
                        spaceB = np.where(space_high_mask[y], 255, 0)
                else:
                    spaceB = np.where(space_high_mask[y], 255, 0)
                line[pos:pos+len_space] = spaceB
                pos += len_space

                if fault_flag == 1 and is_current_b_high:
                    line[pos:pos+len_image] = 0
                else:
                    line[pos:pos+len_image] = arrB[y]
                pos += len_image

                t_val1 = current_t_val1_list[(avhrr1//8)]
                line[pos:pos+len_telemetry] = t_val1

                output[y] = line

                avhrr = 0 if avhrr >= 127 else avhrr + 1
                avhrr1 = 0 if avhrr1 >= 127 else avhrr1 + 1

                progress = (y+1) / new_height * 100
                self.root.after(0, lambda p=progress: self.update_img_progress(p))

            if self.stop_event.is_set():
                self.root.after(0, lambda: self.status_var.set("已停止"))
                self.reset_ui()
                return

            self.current_output_array = output
            self.root.after(0, lambda: self.update_preview())
            
            output_path = os.path.join(output_dir, 'APT.png')
            Image.fromarray(output).save(output_path)
            self.root.after(0, lambda: self.status_var.set("图片生成完成，正在生成音频..."))
            self.generate_audio(output, output_dir)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"生成失败: {str(e)}"))
            self.reset_ui()

    def update_preview(self):
        if self.current_output_array is not None:
            preview_img = Image.fromarray(self.current_output_array)
            
            canvas_width = self.preview_canvas.winfo_width()
            if canvas_width <= 1:
                canvas_width = 600
            
            scale_factor = canvas_width / preview_img.width
            preview_height = int(preview_img.height * scale_factor)
            
            preview_resized = preview_img.resize((canvas_width, preview_height), Image.NEAREST)
            
            self.preview_photo = ImageTk.PhotoImage(preview_resized)
            
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(0, 0, anchor="nw", image=self.preview_photo)
            self.preview_canvas.configure(scrollregion=(0, 0, preview_resized.width, preview_resized.height))
            
            self.preview_label.config(text=f"尺寸: {self.current_output_array.shape[1]} x {self.current_output_array.shape[0]}")

    def generate_audio(self, image_array, output_dir):
        try:
            if self.stop_event.is_set():
                self.root.after(0, lambda: self.status_var.set("已停止"))
                self.reset_ui()
                return

            height, width = image_array.shape
            sample_rate = 12480
            frequency = 2400
            samples_per_pixel = sample_rate // (2 * width)
            files = os.path.join(output_dir, 'apt.wav')
            if os.path.exists(files):
                os.remove(files)

            wav_file = wave.open(files, 'wb')
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)

            amplitudes = image_array.astype(np.float32) / 255.0
            flat_amps = np.repeat(amplitudes.ravel(), samples_per_pixel)

            chunk_size = 1024 * 64
            num_chunks = int(np.ceil(len(flat_amps) / chunk_size))
            angle_increment = 2 * math.pi * frequency / sample_rate
            phase = 0.0

            for i in range(num_chunks):
                if self.stop_event.is_set():
                    wav_file.close()
                    self.root.after(0, lambda: self.status_var.set("已停止"))
                    self.reset_ui()
                    return

                start = i * chunk_size
                end = min(start + chunk_size, len(flat_amps))
                chunk_amps = flat_amps[start:end]
                indices = np.arange(start, end, dtype=np.float64)
                angles = indices * angle_increment + phase
                samples = chunk_amps * np.sin(angles)
                samples_int = (samples * 32767).astype(np.int16)
                wav_file.writeframes(samples_int.tobytes())
                phase = (end * angle_increment + phase) % (2 * math.pi)

                progress = (end / len(flat_amps)) * 100
                self.root.after(0, lambda p=progress: self.update_audio_progress(p))

            wav_file.close()
            if not self.stop_event.is_set():
                self.root.after(0, lambda: self.status_var.set(f"完成！输出目录: {output_dir}"))
                self.root.after(0, lambda: messagebox.showinfo("完成", f"APT图片和音频已保存到:\n{output_dir}"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"音频生成失败: {str(e)}"))
        finally:
            self.reset_ui()

    def update_img_progress(self, value):
        self.progress_img["value"] = value
        self.root.update_idletasks()

    def update_audio_progress(self, value):
        self.progress_audio["value"] = value
        self.root.update_idletasks()

    def reset_ui(self):
        self.running = False
        self.btn_generate.config(text="开始生成", state="normal")
        self.progress_img["value"] = 0
        self.progress_audio["value"] = 0
        self.status_var.set("")

if __name__ == "__main__":
    root = tk.Tk()
    app = APTEncoderApp(root)
    root.mainloop()
