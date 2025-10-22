# 请你作为资深python开发者，帮我写一个脚本，实现以下功能，然后不需要运行只需要写即可：
# 1. 输入一个文件的全路径
# 2. 根据文件名进行改名
# 
# 文件名格式为：手机号码(手机号码)_日期.mp3
# 改名规则为：日期和手机号码对调。日期格式更改格式为：年份-月份-日期 时-分-秒。

# 以下为修文件名的案例：
# 案例1输入：18928275715(18928275715)_20251020153540.mp3
# 案例1输出：2025-10-20 15-35-40 18928275715.mp3
# 案例2输入：15338716280(15338716280)_20251019111812.mp3
# 案例2输出：2025-10-19 11-18-12 15338716280.mp3

import os
import re
import sys
from dataclasses import dataclass
from typing import Optional, Tuple


FILENAME_PATTERN = re.compile(
    r"^(?P<phone>\d{11})\((?P=phone)\)_(?P<timestamp>\d{14})\.(?P<ext>mp3)$",
    re.IGNORECASE,
)


@dataclass
class ParsedName:
    phone: str
    timestamp: str
    ext: str


def parse_filename(filename: str) -> Optional[ParsedName]:
    match = FILENAME_PATTERN.match(filename)
    if not match:
        return None
    return ParsedName(
        phone=match.group("phone"),
        timestamp=match.group("timestamp"),
        ext=match.group("ext").lower(),
    )


def format_timestamp(ts14: str) -> str:
    """将14位时间戳 yyyymmddHHMMSS 格式化为 YYYY-MM-DD HH-MM-SS"""
    year = ts14[0:4]
    month = ts14[4:6]
    day = ts14[6:8]
    hour = ts14[8:10]
    minute = ts14[10:12]
    second = ts14[12:14]
    return f"{year}-{month}-{day} {hour}-{minute}-{second}"


def build_new_name(parsed: ParsedName) -> str:
    date_str = format_timestamp(parsed.timestamp)
    return f"{date_str} {parsed.phone}.{parsed.ext}"


def compute_paths(input_path: str) -> Tuple[str, str]:
    directory = os.path.dirname(input_path)
    original_name = os.path.basename(input_path)
    parsed = parse_filename(original_name)
    if not parsed:
        raise ValueError(
            "文件名不符合规则，应为：手机号码(手机号码)_日期.mp3，例如 18900000000(18900000000)_20250101010203.mp3"
        )
    new_name = build_new_name(parsed)
    return os.path.join(directory, original_name), os.path.join(directory, new_name)


def rename_file(input_path: str) -> str:
    src, dst = compute_paths(input_path)

    if not os.path.exists(src):
        raise FileNotFoundError(f"源文件不存在：{src}")

    if os.path.abspath(src) == os.path.abspath(dst):
        return dst

    if os.path.exists(dst):
        raise FileExistsError(f"目标文件已存在：{dst}")

    os.rename(src, dst)
    return dst


def main(argv: Optional[list] = None) -> int:
    # 利用input输入文件全路径
    input_path = input("请输入文件全路径: ")
    # 如果有去除左右双引号
    input_path = input_path.strip('"')
    # 校验文件是否存在
    if not os.path.exists(input_path):
        print(f"文件不存在：{input_path}")
        return 1

    try:
        new_path = rename_file(input_path)
        print(f"重命名成功：{new_path}")
        return 0
    except Exception as exc:
        print(f"重命名失败：{exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())