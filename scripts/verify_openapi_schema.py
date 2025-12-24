#!/usr/bin/env python3
"""验证 OpenAPI schema 是否包含所有 Speckle 模型"""

import json
import requests
import sys
from pathlib import Path


def verify_openapi_schema(openapi_url: str = "http://localhost:8000/openapi.json"):
    """验证 OpenAPI schema"""
    try:
        response = requests.get(openapi_url, timeout=5)
        response.raise_for_status()
        schema = response.json()
    except requests.exceptions.RequestException as e:
        print(f"✗ 无法访问 OpenAPI schema: {e}")
        print("请确保 FastAPI 服务正在运行 (uvicorn app.main:app --reload)")
        return False
    
    # 检查 components/schemas 中是否包含 Speckle 模型
    schemas = schema.get("components", {}).get("schemas", {})
    
    expected_models = [
        # Base
        "Geometry2D",
        "SpeckleBuiltElementBase",
        # Architectural
        "Wall", "Floor", "Ceiling", "Roof", "Column",
        # Structural
        "Beam", "Brace", "Structure", "Rebar",
        # MEP
        "Duct", "Pipe", "CableTray", "Conduit", "Wire",
        # Spatial
        "Level", "Room", "Space", "Zone", "Area",
        # Other
        "Opening", "Topography", "GridLine", "Profile", "Network", "View",
        "Alignment", "Baseline", "Featureline", "Station",
    ]
    
    missing = []
    found = []
    
    for model in expected_models:
        if model in schemas:
            found.append(model)
            print(f"✓ 找到模型: {model}")
        else:
            missing.append(model)
            print(f"✗ 缺少模型: {model}")
    
    print(f"\n总计: {len(expected_models)} 个模型")
    print(f"找到: {len(found)} 个")
    print(f"缺少: {len(missing)} 个")
    
    if missing:
        print(f"\n缺少的模型: {', '.join(missing)}")
        return False
    
    # 保存 schema 到文件（用于 TypeScript 代码生成）
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    schema_file = project_root / "temp" / "openapi.json"
    schema_file.parent.mkdir(parents=True, exist_ok=True)
    schema_file.write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"\n✓ OpenAPI schema 已保存到: {schema_file}")
    
    return True


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000/openapi.json"
    success = verify_openapi_schema(url)
    sys.exit(0 if success else 1)

