import yaml
import os
import shutil

# 通过选择序号进入对应文件夹，并遍历文件夹下的所有文夹，选择序号再进入某一剧集或电影的文件
# 检查文件夹字幕文件，自动把字幕文件重命名为视频文件的名字，并且添加.chi后缀
# 把字幕文件复制一份到subs文件夹中，用于备份应对sonarr和radarr的删除所有文件问题


def show_list(folder_list: list):
    for index, folder in enumerate(folder_list):
        print(f"{index+1}. {folder}")


with open('./auto-sub/config.yaml', 'r') as file:
    config = yaml.safe_load(file)
    root_path = config['window']['path']
    print(root_path)

# 遍历root_path下的所有文件夹，根据修改时间进行排序
folder_list=[]
for folder in sorted(os.listdir(root_path), 
                    key=lambda x: os.path.getmtime(os.path.join(root_path, x)),
                    reverse=True):
    if os.path.isdir(os.path.join(root_path, folder)):
        folder_list.append(folder)
        print(folder)
print("=========================================================")
show_list(folder_list)
input_index = int(input("请输入一个序号\n"))
selected_category = folder_list[input_index-1]


# 遍历二级文件夹，根据修改时间进行排序
print("=========================================================")
folder_list=[]
for folder in sorted(os.listdir(os.path.join(root_path, selected_category)), 
                    key=lambda x: os.path.getmtime(os.path.join(root_path, selected_category, x)),
                    reverse=True):
    if os.path.isdir(os.path.join(root_path, selected_category, folder)):
        folder_list.append(folder)
show_list(folder_list)
input_index = int(input("请输入一个序号\n"))
selected_work = folder_list[input_index-1]
print("=========================================================")


def movie_subtitle(selected_work):
    # 遍历selected_work下的所有文件，分别分类出视频文件和字幕文件
    video_list = []
    subtitle_list = []
    for file in os.listdir(os.path.join(root_path, selected_category, selected_work)):
        if file.endswith('.mp4') or file.endswith('.mkv') or file.endswith('.avi') or file.endswith('.mov'):
            video_list.append(file)
        elif file.endswith('.srt') or file.endswith('.ass') or file.endswith('.ssa') or file.endswith('.sub'):
            subtitle_list.append(file)
    print("视频文件：")
    show_list(video_list)
    print("字幕文件：")
    show_list(subtitle_list)
    if(len(video_list) != 1 or len(subtitle_list) != 1):
        print("视频文件和字幕文件数量不正确")
        return
    video_name=video_list[0]
    subtitle_name=subtitle_list[0]

    # 视频文件名去除后缀
    video_name=os.path.splitext(video_name)[0]
    # 修改字幕文件名,后缀为.chi+原后缀
    subtitle_new_name=video_name+'.chi'+os.path.splitext(subtitle_name)[-1]
    print(r'原字幕文件名：',subtitle_name,'\n',r'新字幕文件名：',subtitle_new_name)
    os.rename(os.path.join(root_path, selected_category, selected_work, subtitle_name),
              os.path.join(root_path, selected_category, selected_work, subtitle_new_name))
    sub_folder=os.path.join(root_path,selected_category, selected_work,"subs")
    # 判断字幕文件夹是否存在，不存在则创建
    if not os.path.exists(sub_folder):
        os.makedirs(sub_folder)

    # 将字幕文件复制到sub文件夹中
    shutil.copy(
        os.path.join(root_path, selected_category, selected_work, subtitle_new_name),
        os.path.join(sub_folder, subtitle_new_name)
    )
    


# 如果类别电影，则调用movie_subtitle函数
if(selected_category == 'movie'):
    movie_subtitle(selected_work)
# 如果类别剧集，则调用tv_subtitle函数
elif(selected_category == 'tv'):
    tv_subtitle(selected_work)
# 如果类别番剧，则调用anime_subtitle函数
elif(selected_category == 'anime'):
    anime_subtitle(selected_work)



