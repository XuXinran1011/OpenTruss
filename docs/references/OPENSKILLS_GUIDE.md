# OpenSkills 使用指南

本指南介绍如何在 OpenTruss 项目中使用 OpenSkills 获取和管理技能。

## 获取 Skills 的方式

### 1. 安装 Anthropic 官方技能集（推荐）

Anthropic 官方提供了多个实用的技能：

```bash
# 安装所有官方技能（交互式选择）
openskills install anthropics/skills

# 安装到项目目录（默认，推荐用于团队共享）
openskills install anthropics/skills

# 安装到全局目录（所有项目共享）
openskills install anthropics/skills --global

# 安装到通用目录（适用于多个 AI 代理）
openskills install anthropics/skills --universal
```

**官方技能包括**:
- `pdf` - PDF 处理（提取文本、表格、合并、分割等）
- `docx` - Word 文档创建和编辑
- `xlsx` - Excel 表格创建、编辑、公式计算
- `pptx` - PowerPoint 演示文稿创建和编辑
- `canvas-design` - 创建海报和视觉设计
- `mcp-builder` - 构建 Model Context Protocol 服务器
- `skill-creator` - 详细的技能创建指南

### 2. 从 GitHub 安装单个技能

如果某个技能有独立的 GitHub 仓库：

```bash
# 安装特定用户的技能
openskills install username/skill-name

# 示例
openskills install john/my-custom-skill
```

### 3. 从本地路径安装

适用于本地开发或测试技能：

```bash
# 绝对路径
openskills install /path/to/my-skill

# 相对路径
openskills install ./local-skills/my-skill

# 主目录路径
openskills install ~/my-skills/custom-skill

# 安装目录中的所有技能
openskills install ./my-skills-folder
```

### 4. 从私有 Git 仓库安装

支持 SSH 或 HTTPS：

```bash
# SSH（使用 SSH 密钥）
openskills install git@github.com:your-org/private-skills.git

# HTTPS（可能需要输入凭据）
openskills install https://github.com/your-org/private-skills.git
```

## 安装选项

### 安装位置

OpenSkills 按优先级搜索以下位置：

1. `./.agent/skills/` - 项目级通用（使用 `--universal` 时）
2. `~/.agent/skills/` - 全局通用（使用 `--universal --global` 时）
3. `./.claude/skills/` - 项目级（默认，推荐）
4. `~/.claude/skills/` - 全局（使用 `--global` 时）

### 常用选项

```bash
# 项目安装（默认，推荐团队使用）
openskills install anthropics/skills

# 全局安装（所有项目共享）
openskills install anthropics/skills --global

# 通用模式（适用于多个 AI 代理，避免冲突）
openskills install anthropics/skills --universal

# 非交互式安装（用于脚本/CI）
openskills install anthropics/skills -y

# 自定义输出文件
openskills sync -o custom-rules.md
```

## 管理 Skills

### 查看已安装的技能

```bash
# 列出所有已安装的技能
openskills list
```

### 读取技能内容

```bash
# 查看技能内容（AI 代理使用）
openskills read pdf
openskills read opentruss-architecture
```

### 同步到 AGENTS.md

安装技能后，需要同步到 `AGENTS.md`：

```bash
# 交互式同步（推荐）
openskills sync

# 非交互式同步（用于脚本）
openskills sync -y

# 同步到自定义文件
openskills sync -o .ruler/AGENTS.md
```

### 删除技能

```bash
# 交互式删除（推荐）
openskills manage

# 删除特定技能
openskills remove pdf
openskills rm xlsx
```

## 推荐的工作流

### 1. 首次设置项目技能

```bash
# 1. 安装官方技能集（选择需要的）
openskills install anthropics/skills

# 2. 同步到 AGENTS.md
openskills sync

# 3. 查看已安装的技能
openskills list
```

### 2. 添加自定义技能

```bash
# 1. 在 .claude/skills/ 下创建技能目录
mkdir -p .claude/skills/my-custom-skill

# 2. 创建 SKILL.md 文件
# 编辑 .claude/skills/my-custom-skill/SKILL.md

# 3. 同步到 AGENTS.md
openskills sync
```

### 3. 使用符号链接进行本地开发

```bash
# 1. 克隆技能开发仓库
git clone git@github.com:your-org/my-skills.git ~/dev/my-skills

# 2. 创建符号链接
mkdir -p .claude/skills
ln -s ~/dev/my-skills/my-skill .claude/skills/my-skill

# 3. 验证
openskills list  # 应该显示 my-skill
openskills sync  # 同步到 AGENTS.md
```

## 查找可用的 Skills

### 1. Anthropic 官方技能集

访问: https://github.com/anthropics/skills

### 2. 社区技能

- 在 GitHub 上搜索 `SKILL.md` 文件
- 查找标记为 `claude-skills` 的仓库
- 查看 OpenSkills 相关的讨论和示例

### 3. 创建自己的技能

参考官方 `skill-creator` 技能：

```bash
# 安装技能创建指南
openskills install anthropics/skills
openskills read skill-creator
```

## 在 OpenTruss 项目中的最佳实践

### 推荐安装的技能

对于 OpenTruss 这样的 BIM 项目，以下技能可能很有用：

1. **pdf** - 处理 GB50300 标准文档、施工图纸等
2. **docx** - 生成项目报告、文档
3. **xlsx** - 处理检验批数据、导出表格

### 安装建议

```bash
# 1. 安装官方技能集（选择需要的）
openskills install anthropics/skills

# 2. 同步到 AGENTS.md
openskills sync

# 3. 提交到版本控制（包括项目特定技能和 AGENTS.md）
git add .claude/skills/ AGENTS.md
git commit -m "feat: add OpenSkills integration"
```

### 团队协作

- **项目技能**（`.claude/skills/`）：提交到版本控制，团队共享
- **全局技能**（`~/.claude/skills/`）：个人偏好，不提交到版本控制
- **AGENTS.md**：提交到版本控制，记录项目使用的技能

## 故障排查

### 技能未显示

```bash
# 1. 检查技能是否正确安装
openskills list

# 2. 检查目录结构
ls -la .claude/skills/

# 3. 验证 SKILL.md 格式
cat .claude/skills/skill-name/SKILL.md | head -5
```

### 同步失败

```bash
# 1. 确保在项目根目录
pwd

# 2. 手动检查 AGENTS.md 格式
cat AGENTS.md

# 3. 尝试强制同步
openskills sync -y
```

## 相关资源

- OpenSkills 项目: https://github.com/numman-ali/openskills
- Anthropic 官方技能: https://github.com/anthropics/skills
- OpenSkills 文档: 查看项目 README.md

## 示例：完整安装流程

```bash
# 1. 查看当前技能
openskills list

# 2. 安装官方 PDF 技能（如果只想安装特定技能，需要先克隆仓库）
# 或者安装整个官方技能集
openskills install anthropics/skills

# 3. 同步到 AGENTS.md（交互式选择需要的技能）
openskills sync

# 4. 验证安装
openskills list

# 5. 查看技能内容（测试）
openskills read pdf

# 6. 提交到版本控制
git add .claude/skills/ AGENTS.md
git status
```

---

**最后更新**：2025-12-28  
**文档版本**：1.0  
**维护者**：OpenTruss 开发团队
