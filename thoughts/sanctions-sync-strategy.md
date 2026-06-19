# 制裁名单自动同步方案

> 2026-06-19 更新：数据源改为 OpenSanctions

---

## 整体思路

制裁名单不适合用 RSS 订阅，因为：

- OFAC SDN List 和 EU Consolidated List 是结构化数据（XML/CSV），不是 RSS 格式
- OFAC 官方 CDN（Akamai）会拦截非美国 IP 的下载请求
- 制裁原因（为什么被制裁）在新闻稿/法规正文里，不在名单本身
- 需要定时轮询 + 数据清洗 + 关联匹配

所以方案是：

```
cron (每日) → sanctions_sync.py → OpenSanctions API
    ├── 下载 FTM JSON → 解析五列表格
    ├── 匹配 OFAC 新闻稿（如可用）
    └── 结果 → RAGFlow API → 入库 (laws pipeline)
```

## 五列结构

| 实体名称 | 实体类型 | 制裁项目 | 依据法规 | 制裁原因 |
|---|---|---|---|---|
| → 来自 SDN List | → 来自 SDN List | → 来自 SDN List | → 来自 SDN List Program 字段 | → 从新闻稿匹配提取 |

## 脚本

`code/sanctions_sync.py`

| 命令 | 作用 |
|---|---|
| `--list-sources` | 列出可用数据源 |
| `--sync ofac` | 同步 OFAC SDN + 合并非SDN名单 |
| `--sync eu` | 同步 EU 制裁 |
| `--sync all` | 同步所有 |
| `--cron` | 定时模式（每日全量同步，凌晨3点） |

### 数据源

| 源 ID | 内容 | 实体数 |
|---|---|---|
| `us_ofac_sdn` | OFAC 特别指定国民名单 | 70,780 |
| `us_ofac_cons` | OFAC 合并非 SDN 名单 | 1,920 |
| `eu_sanctions` | 欧盟制裁合集 | 41,149 |
| `eu_sanctions_map` | 欧盟制裁地图 | 2,069 |

数据来源：OpenSanctions（`https://data.opensanctions.org/`），聚合 OFAC、EU、UN、UK 等制裁机构的公开数据。

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
