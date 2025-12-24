#!/usr/bin/env python3
"""
脚本：从 GitHub 批量获取 Speckle BuiltElements .cs 文件

功能：
- 从 Speckle 的 GitHub 仓库下载所有 BuiltElements .cs 文件
- 保存到临时目录供后续处理
"""

import os
import requests
from pathlib import Path
from typing import List

# Speckle GitHub 仓库信息
SPECKLE_REPO_BASE = "https://raw.githubusercontent.com/specklesystems/speckle-sharp/main/Objects/Objects/BuiltElements"

# BuiltElements 文件列表（从 GitHub 目录结构获取）
BUILT_ELEMENTS_FILES = [
    # 核心建筑元素
    "Wall.cs",
    "Beam.cs",
    "Column.cs",
    "Floor.cs",
    "Ceiling.cs",
    "Roof.cs",
    "Brace.cs",
    
    # MEP 元素
    "Duct.cs",
    "Pipe.cs",
    "CableTray.cs",
    "Conduit.cs",
    "Wire.cs",
    
    # 空间元素
    "Area.cs",
    "Level.cs",
    "Room.cs",
    "Space.cs",
    "Zone.cs",
    
    # 其他元素
    "Opening.cs",
    "Topography.cs",
    "GridLine.cs",
    "Profile.cs",
    "Rebar.cs",
    "Structure.cs",
    "Network.cs",
    "View.cs",
    "Alignment.cs",
    "Baseline.cs",
    "Featureline.cs",
    "Station.cs",
]


def download_file(url: str, output_path: Path) -> bool:
    """下载单个文件"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(response.text, encoding='utf-8')
        print(f"✓ 已下载: {output_path.name}")
        return True
    except Exception as e:
        print(f"✗ 下载失败 {output_path.name}: {e}")
        return False


def fetch_all_files(output_dir: Path) -> List[str]:
    """下载所有 BuiltElements 文件"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    downloaded = []
    failed = []
    
    for filename in BUILT_ELEMENTS_FILES:
        url = f"{SPECKLE_REPO_BASE}/{filename}"
        output_path = output_dir / filename
        
        if download_file(url, output_path):
            downloaded.append(filename)
        else:
            failed.append(filename)
    
    print(f"\n总计: {len(BUILT_ELEMENTS_FILES)} 个文件")
    print(f"成功: {len(downloaded)} 个")
    print(f"失败: {len(failed)} 个")
    
    if failed:
        print(f"\n失败的文件: {', '.join(failed)}")
    
    return downloaded


def main():
    """主函数"""
    # 输出目录：项目根目录下的临时目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    output_dir = project_root / "temp" / "speckle_built_elements"
    
    print(f"开始下载 Speckle BuiltElements 文件...")
    print(f"输出目录: {output_dir}")
    print(f"{'='*60}\n")
    
    downloaded = fetch_all_files(output_dir)
    
    print(f"\n{'='*60}")
    print(f"文件已保存到: {output_dir}")
    print(f"\n下一步: 运行 convert_speckle_to_pydantic.py 进行转换")


if __name__ == "__main__":
    main()

