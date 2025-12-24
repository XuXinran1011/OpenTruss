# Memgraph 服务启动指南

## 问题诊断

当前测试显示 Memgraph 连接失败，原因是 Docker Desktop 服务未运行。

错误信息：
```
open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.
```

## 解决方案

### 方式 1: 启动 Docker Desktop（推荐）

1. **启动 Docker Desktop 应用程序**
   - 在 Windows 开始菜单中搜索 "Docker Desktop"
   - 点击启动，等待 Docker Desktop 完全启动（图标变为绿色）

2. **验证 Docker Desktop 运行状态**
   ```powershell
   docker ps
   ```
   如果命令成功执行（即使没有容器运行），说明 Docker Desktop 已启动

3. **启动 Memgraph 服务**
   ```powershell
   cd D:\MyPrograms\OpenTruss(beta)
   docker-compose up -d memgraph
   ```

4. **验证 Memgraph 运行**
   ```powershell
   # 检查容器状态
   docker ps | Select-String memgraph
   
   # 检查健康状态（需要等待几秒让服务完全启动）
   Start-Sleep -Seconds 3
   Invoke-WebRequest -Uri http://localhost:7444/healthz -UseBasicParsing
   ```

5. **重新运行测试**
   ```powershell
   cd backend
   python tests/test_manual_verification.py
   ```

### 方式 2: 直接使用 Docker 命令（如果 Docker Desktop 已启动）

如果 Docker Desktop 已启动但 docker-compose 有问题，可以直接使用 docker 命令：

```powershell
# 停止可能存在的旧容器
docker stop opentruss-memgraph 2>$null
docker rm opentruss-memgraph 2>$null

# 启动 Memgraph 容器
docker run -d `
  --name opentruss-memgraph `
  -p 7687:7687 `
  -p 7444:7444 `
  memgraph/memgraph:latest

# 等待服务启动
Start-Sleep -Seconds 5

# 验证运行状态
docker ps | Select-String memgraph
```

## 验证步骤

执行以下命令验证 Memgraph 是否正常运行：

```powershell
# 1. 检查容器状态
docker ps --filter "name=opentruss-memgraph"

# 2. 检查日志（查看是否有错误）
docker logs opentruss-memgraph --tail 20

# 3. 测试连接（使用 Python）
cd backend
python -c "from app.utils.memgraph import MemgraphClient; client = MemgraphClient(); print('连接成功！'); result = client.execute_query('RETURN 1 as test'); print(f'查询结果: {result}')"
```

## 常见问题

### Q: Docker Desktop 启动很慢或卡住？
A: 
- 检查系统资源（CPU、内存）是否充足
- 尝试重启 Docker Desktop
- 检查是否有防火墙或安全软件阻止

### Q: 端口 7687 已被占用？
A:
```powershell
# 查看端口占用
netstat -ano | findstr :7687

# 如果被占用，可以修改 docker-compose.yml 中的端口映射
# 或者停止占用端口的进程
```

### Q: 容器启动后立即退出？
A:
```powershell
# 查看容器日志
docker logs opentruss-memgraph

# 检查是否有错误信息
```

## 完成后

Memgraph 服务成功启动后，重新运行测试：

```powershell
cd D:\MyPrograms\OpenTruss(beta)\backend
python tests/test_manual_verification.py
```

预期结果：
- ✅ 模块导入测试通过
- ✅ Memgraph 连接测试通过
- ✅ Schema 初始化测试通过
- ✅ 数据摄入测试通过

