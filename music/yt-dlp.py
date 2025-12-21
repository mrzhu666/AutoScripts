# 利用yt-dlp下载youtube音乐。码率大概400kbs左右。
# https://music.youtube.com/ 
# 需要cookie下载的歌曲才能到达400kbps+

import os
import yaml


URL=input("Enter the URL of the music: ")

with open('./music/config.yaml', 'r') as file:
    config = yaml.safe_load(file)
    save_path = config['save_path']
    print(save_path)

# get current directory
current_dir = os.getcwd()
print(current_dir)

run_command = f"yt-dlp -x --audio-format mp3 --cookies {current_dir}\\music.youtube.com_cookies.txt --audio-quality 0 -P {save_path} {URL}"

# run command `yt-dlp -x --audio-format m4a --audio-quality 0 URL`
print(run_command)
os.system(run_command)





