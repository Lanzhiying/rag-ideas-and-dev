# 制裁名单自动同步方案

> 2026-06-18

---

## 整体思路

制裁名单不适合用 RSS 订阅，因为：

- OFAC SDN List 和 EU Consolidated List 是结构化数据（XML/CSV），不是 RSS 格式
- 制裁原因（为什么被制裁）在新闻稿/法规正文里，不在名单本身
- 需要定时轮询 + 数据清洗 + 关联匹配

所以方案是：

```
cron (每日) → Python 脚本
                ├── OFAC SDN List → 下载 → 解析 → 5 列表格
                ├── OFAC 新闻稿 → 拉取 → 匹配制裁原因
                └── 结果 → RAGFlow API → 入库 (laws pipeline)
```

## 五列结构

| 实体名称 | 实体类型 | 制裁项目 | 依据法规 | 制裁原因 |
|---|---|---|---|---|
| → 来自 SDN List | → 来自 SDN List | → 来自 SDN List | → 来自 SDN List Program 字段 | → 从新闻稿匹配提取 |

## 脚本

`code/ofac_sanctions_sync.py`

| 命令 | 作用 |
|---|---|
| `--download` | 下载最新 SDN List |
| `--parse` | 解析 → 导出 CSV |
| `--sync` | 全流程：下载→解析→匹配→入库 |
| `--cron` | 定时模式 |

### 配置

创建 `.env` 文件在 `code/` 目录下：

```
RAGFLOW_URL=http://ragflow:9380
RAGFLOW_API_KEY=your_api_key_here
KB_NAME=ofac_sanctions
```

### 定时任务

```bash
# 每日凌晨 3 点执行
0 3 * * * cd /path/to/code && python3 ofac_sanctions_sync.py --cron
```

## 待办

- [ ] EU Consolidated List 解析（数据结构不同，需单独写解析器）
- [ ] 去重逻辑（同一实体在不同更新批次中只保留最新版本）
- [ ] 增量更新（只处理新增/变更的条目）
