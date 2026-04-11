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
    switch_enabled = switch_sensor in ["Y","y"]
    if switch_enabled:
        switch_line = int(input("第几次遥测切换?\n"))
        switch_a_format = input("切换A图格式")
        switch_b_format = input("切换b图格式")
        t_val_list_switch = APT_A_CONFIGS.get(switch_a_format, APT_A_CONFIGS["5"])
        t_val1_list_switch = APT_B_CONFIGS.get(switch_b_format, APT_B_CONFIGS["5"])
    else:
        switch_line = -1
        switch_a_format = apt_a_format
        switch_b_format = apt_b_format
        t_val_list_switch = t_val_list
        t_val1_list_switch = t_val1_list
    
    fault_flag = int(input("红外状态\n0:正常,1:禁用,默认选项0 ") or 0)
    
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
        
        if y % 10 == 0 or y == new_height - 1:
            percentage = (y + 1) / new_height * 100
            sys.stdout.write(f"\r\x1b[34m图像生成进度\x1b[0m: {percentage:.2f}%")
            sys.stdout.flush()
    
    print()
    output_path = os.path.join(SCRIPT_DIR, 'APT.png')
    Image.fromarray(output).save(output_path)
    print(f"图像已保存至: {output_path}")
    return (new_height, total_width, files, output)

def generate_audio(height, width, files, image_array=None):
    if image_array is None:
        img_path = os.path.join(SCRIPT_DIR, 'APT.png')
        if not os.path.exists(img_path):
            print("没有可用的图片文件,退出")
            return
        
        img = Image.open(img_path)
        if img.mode != 'L':
            img = convert_to_8bit(img)
        arr = np.array(img)
    else:
        arr = image_array
    
    sample_rate = 12480
    frequency = 2400
    samples_per_pixel = sample_rate // (2 * width)
    
    if os.path.exists(files):
        os.remove(files)
    
    wav_file = wave.open(files, 'wb')
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(sample_rate)
    
    amplitudes = arr.astype(np.float32) / 255.0
    flat_amps = np.repeat(amplitudes.ravel(), samples_per_pixel)
    
    chunk_size = 1024 * 64
    num_chunks = int(np.ceil(len(flat_amps) / chunk_size))
    angle_increment = 2 * math.pi * frequency / sample_rate
    phase = 0.0
    
    for i in range(num_chunks):
        start = i * chunk_size
        end = min(start + chunk_size, len(flat_amps))
        chunk_amps = flat_amps[start:end]
        indices = np.arange(start, end, dtype=np.float64)
        angles = indices * angle_increment + phase
        samples = chunk_amps * np.sin(angles)
        samples_int = (samples * 32767).astype(np.int16)
        wav_file.writeframes(samples_int.tobytes())
        phase = (end * angle_increment + phase) % (2 * math.pi)
        
        percentage = (end / len(flat_amps)) * 100
        sys.stdout.write(f"\r\x1b[34m音频生成进度\x1b[0m: {percentage:.2f}%")
        sys.stdout.flush()
    
    wav_file.close()
    print(f"\nAPT音频已保存至: {os.path.abspath(files)}")

if __name__ == "__main__":
    print("apt_encode v2.0.2")
    height, width, files, output_array = generate_image()
    generate_audio(height, width, files, output_array)
