# 利用yt-dlp下载youtube音乐。码率大概400kbs左右。
# https://music.youtube.com/ 
# 需要cookie下载的歌曲才能到达400kbps+

URL=input("Enter the URL of the music: ")



import os

# get current directory
current_dir = os.getcwd()
print(current_dir)

# run command `yt-dlp -x --audio-format m4a --audio-quality 0 URL`

print(f"yt-dlp -x --audio-format m4a --cookies {current_dir}\\music.youtube.com_cookies.txt --audio-quality 0 {URL}")
os.system(f"yt-dlp -x --audio-format m4a --cookies {current_dir}\\music.youtube.com_cookies.txt --audio-quality 0 {URL}")





