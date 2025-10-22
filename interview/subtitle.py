import os
import sys
import re

# srt字幕文件台词提取，并保存为txt文件

def extract_srt_dialogue(srt_path):
    txt_path = os.path.splitext(srt_path)[0] + '.txt'
    with open(srt_path, 'r', encoding='utf-8') as srt_file, \
         open(txt_path, 'w', encoding='utf-8') as txt_file:
        buffer = []
        for line in srt_file:
            line = line.strip()
            # 跳过序号行
            if line.isdigit():
                continue
            # 跳过时间轴行
            if re.match(r"^\d{2}:\d{2}:\d{2},\d{3} --> ", line):
                continue
            # 跳过空行
            if not line:
                continue
            # 其余为台词
            buffer.append(line)
        # 将台词逐行写入txt
        for dialogue in buffer:
            txt_file.write(dialogue + '\n')
    print(f"已提取台词到: {txt_path}")

if __name__ == "__main__":
    # 获取路径输入
    srt_path = input("请输入srt文件路径: ")
    # 如果有去除左右双引号
    srt_path = srt_path.strip('"')
    extract_srt_dialogue(srt_path)

