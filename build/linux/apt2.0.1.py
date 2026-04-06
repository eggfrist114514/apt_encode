import numpy as np
from PIL import Image
import sys
import wave
import math
import struct
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

SYNCA = "000011001100110011001100110011000000000"
SYNCB = "000011100111001110011100111001110011100"

def process_image_path(path):
    return path.strip('"').strip("'")

def convert_to_8bit(image):
    if image.mode == 'I;16':
        array = np.array(image, dtype=np.uint16)
        array = (array >> 8).astype(np.uint8)
        return Image.fromarray(array, 'L')
    else:
        return image.convert('L')

def generate_image():
    img1_path = input("请输入a图:\n")
    img2_path = input("请输入b图:\n")
    files = os.path.join(SCRIPT_DIR, 'apt.wav')
    
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
    
    apt_a_format = str(input("APT-A传输格式\n1,2,3b,4,5,默认选项:3b\n").strip() or "3b")
    apt_b_format = str(input("APT-B传输格式\n1,2,3b,4,5,默认选项:4\n").strip() or "4")
    
    t_val_list = APT_A_CONFIGS.get(apt_a_format, APT_A_CONFIGS["5"])
    t_val1_list = APT_B_CONFIGS.get(apt_b_format, APT_B_CONFIGS["5"])
    
    print(f"已选择 APT-A: {apt_a_format}, APT-B: {apt_b_format}")
    
    switch_sensor = input("切换传感器?N/Y\n").strip() or None
    cs = 0
    if switch_sensor in ["Y","y"]:
        switch_line = int(input("第几次遥测切换?\n"))
        switch_a_format = input("切换A图格式")
        switch_b_format = input("切换b图格式")
        t_val_list_switch = APT_A_CONFIGS.get(switch_a_format, APT_A_CONFIGS["5"])
        t_val1_list_switch = APT_B_CONFIGS.get(switch_b_format, APT_B_CONFIGS["5"])
    else:
        switch_line = -1
    
    fault_flag = int(input("红外状态\n0:正常,1:禁用,默认选项0 ") or 0)
    fault_flag = int(fault_flag)
    
    img1 = Image.open(img1_path)
    img2 = Image.open(img2_path)
    
    img1 = convert_to_8bit(img1)
    img2 = convert_to_8bit(img2)
    
    w1, h1 = img1.size
    new_height = int(909 * h1 / w1)
    imgA = img1.resize((909, new_height), Image.NEAREST)
    imgB = img2.resize((909, new_height), Image.NEAREST)
    
    arrA = np.array(imgA)
    arrB = np.array(imgB)
    
    conn =114514
    black_mode = 1
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
    
    is_a_format_high = apt_a_format in ["3b", "4", "5"]
    is_b_format_high = apt_b_format in ["3b", "4", "5"]
    
    for y in range(new_height):
        current_a_format = apt_a_format
        current_b_format = apt_b_format
        current_t_val_list = t_val_list
        current_t_val1_list = t_val1_list
        
        if conn ==1 or cs // 128 == switch_line and switch_sensor in ["Y","y"]:
            current_a_format = switch_a_format
            current_b_format = switch_b_format
            current_t_val_list = t_val_list_switch
            current_t_val1_list = t_val1_list_switch
            conn = 1
        
        is_current_a_high = current_a_format in ["3b", "4", "5"]
        is_current_b_high = current_b_format in ["3b", "4", "5"]
        
        line = []
        line.extend(syncA_arr.tolist())
        
        if fault_flag == 0:
            if is_current_a_high:
                spaceA = 0 if (y % 120 == 0 or y % 120 == 1) else 255
            else:
                spaceA = 255 if (y % 120 == 0 or y % 120 == 1) else 0
        else:
            if black_mode == 1:
                spaceA = 255 if (y % 120 == 0 or y % 120 == 1) else 0
            else:
                spaceA = 0
        line.extend([spaceA] * len_space)
        
        if fault_flag == 0:
            line.extend(arrA[y].tolist())
        else:
            if black_mode == 1:
                line.extend([10] * len_image)
            else:
                line.extend([255] * len_image)
        
        t_val = current_t_val_list[(avhrr//8)]
        if black_mode == 0 and fault_flag == 1:
            avhrr = 0
            t_val = 25
        line.extend([t_val] * len_telemetry)
        
        line.extend(syncB_arr.tolist())
        
        if fault_flag == 0:
            if is_current_b_high:
                spaceB = 0 if (y % 120 == 0 or y % 120 == 1) else 255
            else:
                spaceB = 255 if (y % 120 == 0 or y % 120 == 1) else 0
        else:
            if black_mode == 1:
                spaceB = 255 if (y % 120 == 0 or y % 120 == 1) else 0
            else:
                spaceB = 0
        line.extend([spaceB] * len_space)
        
        if fault_flag == 0:
            line.extend(arrB[y].tolist())
        else:
            if black_mode == 1:
                line.extend([10] * len_image)
            else:
                line.extend([255] * len_image)
        
        t_val1 = current_t_val1_list[(avhrr1//8)]
        if black_mode == 0 and fault_flag == 1:
            avhrr1 = 0
            t_val1 = 20
        line.extend([t_val1] * len_telemetry)
        
        output[y] = np.array(line, dtype=np.uint8)
        
        avhrr = 0 if avhrr >= 127 else avhrr + 1
        avhrr1 = 0 if avhrr1 >= 127 else avhrr1 + 1
        cs += 1
    
    output_path = os.path.join(SCRIPT_DIR, 'APT.png')
    Image.fromarray(output).save(output_path)
    print(f"图像已保存至: {output_path}")
    return (new_height, total_width, files)

def generate_audio(height, width, files):
    img_path = os.path.join(SCRIPT_DIR, 'APT.png')
    if not os.path.exists(img_path):
        print("没有可用的图片文件,退出")
        return
    
    img = Image.open(img_path)
    if img.mode != 'L':
        img = convert_to_8bit(img)
    arr = np.array(img)
    
    sample_rate = 12480
    frequency = 2400
    samples_per_pixel = sample_rate // (2 * width)
    
    if os.path.exists(files):
        os.remove(files)
    
    wav_file = wave.open(files, 'wb')
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(sample_rate)
    
    phase = 0.0
    angle_increment = 2 * math.pi * frequency / sample_rate
    
    total_pixels = height * width
    processed_pixels = 0
    
    for y in range(height):
        for x in range(width):
            pixel = arr[y, x]
            amplitude = pixel / 255.0
            
            for _ in range(samples_per_pixel):
                sample = amplitude * math.sin(phase)
                normalized = int(sample * 32767)
                wav_file.writeframes(struct.pack('<h', normalized))
                phase += angle_increment
            processed_pixels += 1
        
        percentage = (processed_pixels / total_pixels) * 100
        sys.stdout.write(f"\r\x1b[34mProgress\x1b[0m: {percentage:.2f}%")
        sys.stdout.flush()
    
    wav_file.close()
    print(f"\nAPT音频已保存至: {os.path.abspath(files)}")

if __name__ == "__main__":
    print("apt_encode v2.0.1")
    height, width, files = generate_image()
    generate_audio(height, width, files)
