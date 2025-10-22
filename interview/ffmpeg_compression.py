import os
import subprocess

# ffmpeg -i input.mp4 -vcodec libx264 -b:v 1000k -acodec copy -y output.mp4
# 根据该命令，写一个python脚本，input输入两个参数，分别是：
# 1. 输入文件路径
# 2. 码率
# 输出文件路径为输入文件同一文件夹，名字为输入文件后面加_Compression

def compress_video(input_path, bitrate):
    if bitrate == '':
        bitrate = '400k'
    base, ext = os.path.splitext(input_path)
    output_path = base + '_compression' + ext
    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-vcodec', 'h264_nvenc', # GPU加速，CPU为libx264
        '-b:v', bitrate,
        '-acodec', 'copy',
        output_path,
        '-y'
    ]
    print('运行命令:', ' '.join(cmd))
    subprocess.run(cmd, check=True)
    print(f'压缩完成，输出文件: {output_path}')

if __name__ == "__main__":
    input_path = input('请输入视频文件路径: ').strip('"')
    bitrate = input('请输入视频码率(默认800k): ').strip()
    compress_video(input_path, bitrate)
