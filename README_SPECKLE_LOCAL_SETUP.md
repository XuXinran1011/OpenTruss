# 使用本地 Speckle 文件进行转换

## 设置步骤

如果您有 Speckle BuiltElements 的 .cs 文件，可以按以下步骤进行转换：

### 1. 准备文件

将 Speckle BuiltElements 的 .cs 文件放在项目根目录下的 `SpeckleBuiltElements/` 目录中：

```
OpenTruss/
├── SpeckleBuiltElements/          # 新建此目录
│   ├── Wall.cs
│   ├── Beam.cs
│   ├── Column.cs
│   ├── Floor.cs
│   ├── Ceiling.cs
│   ├── Roof.cs
│   ├── Duct.cs
│   ├── Pipe.cs
│   ├── ... (其他 .cs 文件)
│   └── ...
├── scripts/
│   └── convert_speckle_to_pydantic.py
└── backend/
    └── app/
        └── models/
            └── speckle/
```

### 2. 运行转换脚本

```bash
# 从项目根目录运行
python scripts/convert_speckle_to_pydantic.py
```

脚本会：
1. 自动检测 `./SpeckleBuiltElements/` 目录
2. 解析所有 .cs 文件
3. 提取类定义和属性
4. 生成 Python Pydantic 模型到 `backend/app/models/speckle/`

### 3. 查看生成结果

转换完成后，检查生成的文件：

```bash
# 查看生成的文件
ls backend/app/models/speckle/

# 查看特定类别
cat backend/app/models/speckle/architectural.py
cat backend/app/models/speckle/mep.py
```

### 4. 验证模型

启动 FastAPI 服务验证模型是否正确：

```bash
cd backend
uvicorn app.main:app --reload

# 在另一个终端验证 OpenAPI schema
python scripts/verify_openapi_schema.py
```

## 注意事项

1. **文件命名**：确保 .cs 文件名与类名匹配（如 `Wall.cs` 包含 `Wall` 类）

2. **字段覆盖**：转换脚本会覆盖现有的模型文件。建议：
   - 先备份现有模型（如果需要）
   - 或使用 Git 版本控制

3. **手动调整**：自动生成的模型可能需要手动调整：
   - 某些特殊字段的默认值
   - 字段描述信息
   - 业务逻辑相关的验证规则

4. **保留现有更新**：如果之前手动更新过某些模型（如 Duct, Pipe 的完整属性），转换后可能需要：
   - 检查是否有属性丢失
   - 重新应用手动修改

## 获取 Speckle 文件

如果还没有文件，可以从 GitHub 获取：

```bash
# 方法 1: 使用脚本（需要网络）
python scripts/fetch_speckle_built_elements.py

# 方法 2: 手动下载
# 访问 https://github.com/specklesystems/speckle-sharp/tree/main/Objects/Objects/BuiltElements
# 逐个下载 .cs 文件到 SpeckleBuiltElements/ 目录
```

## 转换规则说明

脚本会自动处理以下转换：

1. **类型映射**：
   - `ICurve` → `Geometry2D`
   - `Level` → `level_id: Optional[str]`
   - `Point` → `List[float]` (坐标列表)
   - `double?` → `Optional[float]`
   - `List<ICurve>` → `List[Geometry2D]`

2. **字段映射**：
   - `baseLine` / `baseCurve` → `geometry_2d`
   - `outline` → `geometry_2d`
   - `level` → `level_id`
   - `basePoint` → `base_point`

3. **命名转换**：
   - camelCase → snake_case（如 `basePoint` → `base_point`）
   - 保持别名以支持原始命名

