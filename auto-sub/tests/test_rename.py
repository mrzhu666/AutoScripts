"""单元测试：auto-sub/rename.py."""

from pathlib import Path
from typing import List

import sys

import pytest

# 将 auto-sub 目录加入 sys.path，便于导入 rename 模块
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import rename  # noqa: E402  pylint: disable=C0413


@pytest.fixture
def temp_root(tmp_path: Path) -> Path:
    """创建临时根目录。"""
    return tmp_path


def _create_file(path: Path, name: str) -> Path:
    """在指定路径创建一个空文件并返回路径。"""
    file_path = path / name
    file_path.write_text("", encoding="utf-8")
    return file_path


def test_get_sorted_files_returns_alphabetical(temp_root: Path) -> None:
    """验证 _get_sorted_files 返回的文件列表按文件名字典序排序。"""
    # 创建无序文件
    names: List[str] = ["z.txt", "b.txt", "a.txt"]
    for name in names:
        _create_file(temp_root, name)

    result = rename.SubtitleRenamer._get_sorted_files(temp_root)  # pylint: disable=protected-access
    result_names = [f.name for f in result]

    assert result_names == sorted(names), "文件列表应按字典序排序"


def test_process_movie_subtitle_renames_and_copies(temp_root: Path) -> None:
    """验证电影字幕处理：重命名并复制到 subs。"""
    category = "movie"
    work = "demo"
    work_dir = temp_root / category / work
    work_dir.mkdir(parents=True, exist_ok=True)

    video_path = work_dir / "demo_video.mkv"
    subtitle_path = work_dir / "sub.srt"
    video_path.write_text("video", encoding="utf-8")
    subtitle_path.write_text("subtitle", encoding="utf-8")

    renamer = rename.SubtitleRenamer(str(temp_root))
    success = renamer.process_movie_subtitle(category, work)

    new_subtitle = work_dir / "demo_video.chi.srt"
    copied_subtitle = work_dir / "subs" / "demo_video.chi.srt"

    assert success is True, "处理应成功"
    assert new_subtitle.exists(), "字幕文件应被重命名"
    assert copied_subtitle.exists(), "字幕文件应被复制到 subs 目录"

