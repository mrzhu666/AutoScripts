"""
字幕文件重命名工具。

通过选择序号进入对应文件夹，并遍历文件夹下的所有文件夹，选择序号再进入某一剧集或电影的文件。
检查文件夹字幕文件，自动把字幕文件重命名为视频文件的名字，并且添加.chi后缀。
把字幕文件复制一份到subs文件夹中，用于备份应对sonarr和radarr的删除所有文件问题。
"""

import logging
import os
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

import yaml
from pydantic import BaseModel, Field, validator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# 视频文件扩展名
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov'}
# 字幕文件扩展名
SUBTITLE_EXTENSIONS = {'.srt', '.ass', '.ssa', '.sub'}
# 支持的类别
SUPPORTED_CATEGORIES = {'movie', 'tv', 'anime'}


class WindowConfig(BaseModel):
    """窗口配置模型。"""

    path: str = Field(..., description="根路径")

    @validator('path')
    def validate_path(cls, v: str) -> str:
        """验证路径是否存在。"""
        if not os.path.exists(v):
            raise ValueError(f"路径不存在: {v}")
        if not os.path.isdir(v):
            raise ValueError(f"路径不是目录: {v}")
        return v


class Config(BaseModel):
    """应用配置模型。"""

    window: WindowConfig = Field(..., description="窗口配置")


@dataclass
class FileInfo:
    """文件信息数据类。

    Attributes:
        name: 文件名（包含扩展名）
        path: 文件的完整路径对象
        extension: 文件扩展名（包含点号，如 '.mp4', '.srt'）
    """

    name: str = field(metadata={"description": "文件名（包含扩展名）"})
    path: Path = field(metadata={"description": "文件的完整路径对象"})
    extension: str = field(metadata={"description": "文件扩展名（包含点号，如 '.mp4', '.srt'）"})

    @property
    def is_video(self) -> bool:
        """检查是否为视频文件。"""
        return self.extension.lower() in VIDEO_EXTENSIONS

    @property
    def is_subtitle(self) -> bool:
        """检查是否为字幕文件。"""
        return self.extension.lower() in SUBTITLE_EXTENSIONS


class SubtitleRenamer:
    """字幕文件重命名器。"""

    def __init__(self, root_path: str) -> None:
        """初始化字幕重命名器。

        Args:
            root_path: 根路径

        Raises:
            ValueError: 如果根路径无效
        """
        self.root_path = Path(root_path)
        if not self.root_path.exists():
            raise ValueError(f"根路径不存在: {root_path}")
        if not self.root_path.is_dir():
            raise ValueError(f"根路径不是目录: {root_path}")

    @staticmethod
    def _get_sorted_folders(path: Path) -> List[str]:
        """根据文件夹路径，获取按修改时间排序的文件夹列表。

        Args:
            path: 要遍历的路径

        Returns:
            文件夹名称列表，按修改时间降序排列
        """
        try:
            folders = [
                folder.name
                for folder in path.iterdir()
                if folder.is_dir()
            ]
            return sorted(
                folders,
                key=lambda x: os.path.getmtime(path / x),
                reverse=True
            )
        except OSError as e:
            logger.error(f"读取文件夹失败: {path}, 错误: {e}")
            return []

    @staticmethod
    def _get_sorted_files(path: Path) -> List[FileInfo]:
        """获取路径下的文件信息列表。

        Args:
            path: 要遍历的路径

        Returns:
            文件信息列表，按文件名字典顺序排序
        """
        try:
            files = [
                FileInfo(
                    name=file.name,
                    path=file,
                    extension=file.suffix
                )
                for file in path.iterdir()
                if file.is_file()
            ]
            return sorted(files, key=lambda f: f.name)
        except OSError as e:
            logger.error(f"读取文件失败: {path}, 错误: {e}")
            return []

    @staticmethod
    def _show_list(items: List[str], title: Optional[str] = None) -> None:
        """显示列表供用户选择。

        Args:
            items: 要显示的项列表
            title: 可选的标题
        """
        if title:
            logger.info(title)
        for index, item in enumerate(items, start=1):
            print(f"{index}. {item}")

    @staticmethod
    def _get_user_selection(items: List[str], prompt: str) -> Optional[str]:
        """获取用户选择的项。

        Args:
            items: 可选项列表
            prompt: 提示信息

        Returns:
            选中的项，如果选择无效则返回None
        """
        if not items:
            logger.warning("列表为空，无法选择")
            return None

        try:
            user_input = input(f"{prompt}\n")
            index = int(user_input) - 1
            if 0 <= index < len(items):
                return items[index]
            else:
                logger.error(f"无效的序号: {user_input}")
                return None
        except ValueError as e:
            logger.error(f"输入无效: {e}")
            return None

    def select_category(self) -> Optional[str]:
        """选择类别文件夹。

        Returns:
            选中的类别名称，如果选择失败则返回None
        """
        logger.info("=" * 60)
        folders = self._get_sorted_folders(self.root_path)
        if not folders:
            logger.error("根路径下没有找到文件夹")
            return None

        self._show_list(folders, "类别列表:")
        selected = self._get_user_selection(folders, "请输入一个序号")
        if selected and selected in SUPPORTED_CATEGORIES:
            logger.info(f"已选择类别: {selected}")
            return selected
        elif selected:
            logger.warning(f"不支持的类别: {selected}")
            return selected
        return None

    def select_work(self, category: str) -> Optional[str]:
        """选择作品文件夹。

        Args:
            category: 类别名称

        Returns:
            选中的作品名称，如果选择失败则返回None
        """
        logger.info("=" * 60)
        category_path = self.root_path / category
        if not category_path.exists():
            logger.error(f"类别路径不存在: {category_path}")
            return None

        folders = self._get_sorted_folders(category_path)
        if not folders:
            logger.error(f"类别 {category} 下没有找到文件夹")
            return None

        self._show_list(folders, "作品列表:")
        selected_work = self._get_user_selection(folders, "请输入一个序号")
        if selected_work:
            logger.info(f"已选择作品: {selected_work}")
        return selected_work

    def select_season(self, category: str, work: str) -> Optional[str]:
        """选择季度文件夹。

        Args:
            category: 类别名称
            work: 作品名称

        Returns:
            选中的季度名称，如果选择失败则返回None
        """
        logger.info("=" * 60)
        work_path = self.root_path / category / work
        if not work_path.exists():
            logger.error(f"作品路径不存在: {work_path}")
            return None

        folders = self._get_sorted_folders(work_path)
        if not folders:
            logger.error(f"作品 {work} 下没有找到季度文件夹")
            return None

        self._show_list(folders, "季度列表:")
        selected = self._get_user_selection(folders, "请输入一个序号")
        if selected:
            logger.info(f"已选择季度: {selected}")
        return selected

    def process_movie_subtitle(self, category: str, work: str) -> bool:
        """处理电影字幕文件。

        Args:
            category: 类别名称
            work: 作品名称

        Returns:
            处理是否成功
        """
        work_path = self.root_path / category / work
        if not work_path.exists():
            logger.error(f"作品路径不存在: {work_path}")
            return False

        files = self._get_sorted_files(work_path)
        video_files = [f for f in files if f.is_video]
        subtitle_files = [f for f in files if f.is_subtitle]

        logger.info("视频文件:")
        self._show_list([f.name for f in video_files])
        logger.info("字幕文件:")
        self._show_list([f.name for f in subtitle_files])

        if len(video_files) != 1 or len(subtitle_files) != 1:
            logger.error("视频文件和字幕文件数量不正确，需要各一个")
            return False

        video_file = video_files[0]
        subtitle_file = subtitle_files[0]

        # 生成新的字幕文件名
        video_name_without_ext = video_file.path.stem
        subtitle_new_name = f"{video_name_without_ext}.chi{subtitle_file.extension}"
        subtitle_new_path = work_path / subtitle_new_name

        logger.info(f"原字幕文件名: {subtitle_file.name}")
        logger.info(f"新字幕文件名: {subtitle_new_name}")

        try:
            # 重命名字幕文件
            subtitle_file.path.rename(subtitle_new_path)
            logger.info(f"字幕文件已重命名: {subtitle_new_path}")

            # 创建subs文件夹并复制字幕文件
            subs_folder = work_path / "subs"
            subs_folder.mkdir(exist_ok=True)
            shutil.copy(subtitle_new_path, subs_folder / subtitle_new_name)
            logger.info(f"字幕文件已复制到: {subs_folder / subtitle_new_name}")

            return True
        except (OSError, shutil.Error) as e:
            logger.error(f"处理字幕文件失败: {e}")
            return False

    def _extract_season_number(self, season_name: str) -> Optional[int]:
        """从季度名称中提取季度序号。

        Args:
            season_name: 季度名称

        Returns:
            季度序号，如果提取失败则返回None
        """
        match = re.search(r'\d+', season_name)
        if match:
            try:
                return int(match.group())
            except ValueError:
                logger.warning(f"无法将季度序号转换为整数: {match.group()}")
                return None
        logger.warning(f"无法从季度名称中提取序号: {season_name}")
        return None

    def process_tv_subtitle(self, category: str, work: str, season: str) -> bool:
        """处理电视剧字幕文件。

        Args:
            category: 类别名称
            work: 作品名称
            season: 季度名称

        Returns:
            处理是否成功
        """
        season_path = self.root_path / category / work / season
        if not season_path.exists():
            logger.error(f"季度路径不存在: {season_path}")
            return False

        files = self._get_sorted_files(season_path)
        subtitle_files = [f for f in files if f.is_subtitle]

        if not subtitle_files:
            logger.warning("未找到字幕文件")
            return False

        logger.info("字幕文件:")
        self._show_list([f.name for f in subtitle_files])

        season_num = self._extract_season_number(season)
        if season_num is None:
            logger.error(f"无法提取季度序号: {season}")
            return False

        logger.info(f"季度序号: {season_num}")

        success_count = 0
        for episode_index, subtitle_file in enumerate(subtitle_files, start=1):
            subtitle_new_name = (
                f"{work} - S{season_num:02d}E{episode_index:02d}"
                f".chi{subtitle_file.extension}"
            )
            subtitle_new_path = season_path / subtitle_new_name

            logger.info(f"原字幕文件名: {subtitle_file.name}")
            logger.info(f"新字幕文件名: {subtitle_new_name}")

            try:
                subtitle_file.path.rename(subtitle_new_path)
                logger.info(f"字幕文件已重命名: {subtitle_new_path}")
                success_count += 1
            except OSError as e:
                logger.error(f"重命名字幕文件失败: {subtitle_file.name}, 错误: {e}")

        logger.info(f"成功处理 {success_count}/{len(subtitle_files)} 个字幕文件")
        return success_count == len(subtitle_files)

    def process_anime_subtitle(self, category: str, work: str, season: str) -> bool:
        """处理番剧字幕文件。

        Args:
            category: 类别名称
            work: 作品名称
            season: 季度名称

        Returns:
            处理是否成功
        """
        # 番剧和电视剧的处理逻辑相同
        return self.process_tv_subtitle(category, work, season)

    def run(self) -> None:
        """运行字幕重命名流程。"""
        try:
            # 选择类别
            category = self.select_category()
            if not category:
                logger.error("未选择类别，退出")
                return

            # 选择作品
            work = self.select_work(category)
            if not work:
                logger.error("未选择作品，退出")
                return

            # 如果是电视剧或番剧，需要选择季度
            if category in {'tv', 'anime'}:
                season = self.select_season(category, work)
                if not season:
                    logger.error("未选择季度，退出")
                    return

                # 处理字幕
                if category == 'tv':
                    self.process_tv_subtitle(category, work, season)
                elif category == 'anime':
                    self.process_anime_subtitle(category, work, season)
            elif category == 'movie':
                # 处理电影字幕
                self.process_movie_subtitle(category, work)
            else:
                logger.warning(f"不支持的类别: {category}")

        except Exception as e:
            logger.exception(f"运行过程中发生错误: {e}")


def load_config(config_path: str = 'config.yaml') -> Config:
    """加载配置文件。

    Args:
        config_path: 配置文件路径

    Returns:
        配置对象

    Raises:
        FileNotFoundError: 如果配置文件不存在
        ValueError: 如果配置无效
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config_data = yaml.safe_load(file)
            if not config_data:
                raise ValueError("配置文件为空")
            return Config(**config_data)
    except FileNotFoundError:
        logger.error(f"配置文件不存在: {config_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"解析YAML文件失败: {e}")
        raise ValueError(f"配置文件格式错误: {e}") from e
    except Exception as e:
        logger.error(f"加载配置失败: {e}")
        raise ValueError(f"配置无效: {e}") from e


def main() -> None:
    """主函数。"""
    try:
        config = load_config("./auto-sub/config.yaml")
        root_path = config.window.path
        logger.info(f"根路径: {root_path}")

        renamer = SubtitleRenamer(root_path)
        renamer.run()
    except Exception as e:
        logger.exception(f"程序执行失败: {e}")
        raise


if __name__ == "__main__":
    main()
