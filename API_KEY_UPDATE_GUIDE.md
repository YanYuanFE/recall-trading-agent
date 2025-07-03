# API密钥更新指南

## 问题诊断

当你运行项目时看到以下错误，说明API密钥需要更新：

```
API Key validation failed: Invalid API key. This key may have been reset or is no longer associated with an active account.
```

## 更新步骤

### 1. 获取新的API密钥

访问 [Recall Network 注册页面](https://register.recall.network) 获取新的API密钥。

### 2. 更新 .env 文件

编辑项目根目录下的 `.env` 文件：

```bash
# 当前配置
TRADING_SIM_API_KEY=602c0238f253cacb_83c246f4bc5a6ebe  # 旧密钥

# 更新为新密钥
TRADING_SIM_API_KEY=你的新API密钥
```

### 3. 验证API密钥

运行以下命令验证新密钥是否有效：

```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行API调试脚本
python3 debug_api.py
```

如果看到类似以下输出，说明密钥有效：
```
API Key validation successful on /account/portfolio
```

### 4. 重新运行项目

```bash
# 检查投资组合状态
./run.sh 2

# 生成日报
./run.sh 3

# 干运行模式
./run.sh 4
```

## API端点更新说明

基于最新的API文档，我们已经更新了以下端点支持：

### 新增端点
- `/account/positions` - 获取当前持仓（优先使用）
- `/account/history` - 获取账户历史记录

### 端点优先级
1. **投资组合数据**：
   - 首选：`/account/positions`
   - 备用：`/account/balances`
   - 回退：模拟数据

2. **交易历史**：
   - 首选：`/account/history`
   - 备用：`/account/trades`
   - 回退：模拟数据

### API认证增强

现在系统会测试多个端点来验证API密钥的有效性：
- `/account/portfolio`
- `/account/balances`
- `/account/positions`
- `/competition/status`

## 常见问题

### Q: 为什么我的API密钥失效了？
A: API密钥可能因为以下原因失效：
- 账户被重置
- 密钥过期
- 账户状态变更

### Q: 如何确认API密钥是否有效？
A: 运行 `python3 debug_api.py` 可以全面测试所有端点的可用性。

### Q: 项目是否能在没有有效API密钥的情况下运行？
A: 是的，项目会自动切换到演示模式，使用模拟数据展示所有功能。

## 技术支持

如果在更新API密钥过程中遇到问题，请：
1. 检查网络连接
2. 确认API密钥格式正确
3. 查看项目日志文件：`logs/trading_agent_*.log`
4. 联系Recall Network技术支持

---

## 最新更新 (2025-07-03)

### API端点修复
基于最新的Recall Network文档，已完成以下更新：

1. **修复了404错误**:
   - 更新了base URL从 `/sandbox/api` 到 `/api`
   - 修复了价格查询端点的错误处理

2. **代码更新**:
   - `config.py`: 更新了 `TRADING_SIM_API_URL` 
   - `trading_client.py`: 改进了 `get_token_price()` 方法，支持多个价格端点重试

3. **端点状态确认**:
   - ✅ 工作正常的端点：`/account/*`, `/competition/*`, `/trade/*`
   - ❌ 不存在的端点：`/market/tokens`, `/market/price` (已优雅处理)

### 最新发现 (2025-07-03 21:40)

**重要发现：端点环境差异**
1. **Sandbox环境**: 使用 `/account/*` 端点 ✅
2. **生产环境**: 使用 `/agent/*` 端点 ✅
3. **当前配置**: 已正确设置为sandbox + account端点

**代码状态**: 
- ✅ 已恢复使用 `/account/*` 端点 (适用于sandbox)
- ✅ API验证通过: `client.validate_api_key()` 返回 `True`
- ⚠️ 仍需更新API密钥解决401错误

### 下一步操作
1. **更新API密钥** (主要问题)
2. **运行测试**: `python3 debug_api.py`
3. **启动交易代理**验证修复

### 🎉 SANDBOX API更新完成 (2025-07-03 22:00)

**✅ 重大进展：Sandbox端点已更新**

1. **新的Sandbox URL**: `https://api.sandbox.competitions.recall.network/api`
2. **Agent端点支持**: `/agent/portfolio` 已正常工作 ✅
3. **API端点状态**:
   - ✅ `/agent/portfolio` - 200 OK (Total value: $31,500.1)
   - ✅ `/agent/balances` - 200 OK (7 tokens: USDC, USDbC, SOL)
   - ✅ `/agent/trades` - 200 OK (2 recent trades found)
   - ✅ `/agent/history` - 可用
   - ✅ API密钥验证通过

**代码更新完成**:
- ✅ 更新为使用 `/agent/*` 端点
- ✅ Base URL已正确配置: `https://api.sandbox.competitions.recall.network/api`
- ✅ 更新了 `/agent/balances` 数据解析适配新结构
- ✅ 移除了fallback机制，直接使用agent端点

**🎉 当前状态**: Sandbox环境的主要功能已完全正常工作！
- Portfolio查询 ✅
- 余额查询 ✅  
- 交易历史 ✅
- 实际交易执行 ✅

### 🧹 代码清理完成 (2025-07-03 22:16)

**✅ 移除不存在的端点**:
- ❌ 删除了 `/agent/positions` 相关代码（该端点不存在）
- ✅ 简化了portfolio管理逻辑，直接使用 `/agent/portfolio` 
- ✅ 更新了API验证函数
- ✅ 清理了debug脚本

**测试结果**: 程序运行无错误，portfolio数据正常显示，交易功能完全可用。

*更新日期：2025-07-03*