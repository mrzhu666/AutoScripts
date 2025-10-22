import os
import subprocess

# ffmpeg -i test.mp4 -vcodec copy -acodec copy -ss 00:00:00 -to 00:39:00 test_cut.mp4 -y
# 根据该命令，写一个python脚本，input输入三个参数，分别是：
# 1. 输入文件路径
# 2. 开始时间
# 3. 结束时间
# 输出文件路径为输入文件同一文件夹，名字为输入文件后面加_cut

def cut_video(input_path, start_time, end_time):
    base, ext = os.path.splitext(input_path)
    output_path = base + '_cut' + ext
    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-vcodec', 'copy',
        '-acodec', 'copy',
        '-ss', start_time,
        '-to', end_time,
        output_path,
        '-y'
    ]
    print('运行命令:', ' '.join(cmd))
    subprocess.run(cmd, check=True)
    print(f'裁剪完成，输出文件: {output_path}')

if __name__ == "__main__":
    input_path = input('请输入视频文件路径: ').strip('"')
    start_time = input('请输入开始时间(格式如00:00:00): ').strip()
    end_time = input('请输入结束时间(格式如00:39:00): ').strip()
    cut_video(input_path, start_time, end_time)
