# RAG 思路与开发实践

我在自己搭本地 RAG，这个仓库记录过程中想到的东西、踩过的坑、做过的选择。

核心问题就一个：**不用任何云服务，纯靠本地机器，能不能搞出一个靠谱的 RAG 系统？**

---

## 仓库里有什么

```
.
├── README.md              ← 你正在看的
├── thoughts/              ← 零散想法，不一定对
├── decisions/             ← 选了 A 没选 B，为什么
├── pitfalls/              ← 踩坑记录，Google 不到的那种
├── drafts/                ← 写到一半的文档
└── code/                  ← 实验代码，别当生产级的用
```

---

## 当前进展

**已完成：**
- RAGFlow v0.26.1 Docker 部署（Docker Desktop WSL2）
- 研发中心知识库搭建（19 个知识库，按组分类：研发/技服/实验室）
- 标准资料整理（ISO 6743 全套 + DIN/API/AGMA/ASTM/GB 清单）
- 定时同步脚本（每天 02:00 自动扫描共享文件夹）
- Embedding 模型选型完成 → **Qwen3-Embedding-0.6B**（具体看 `decisions/embedding-model-selection.md`）

**待做：**
- 切默认 embedding 到 Qwen3-0.6B（本地，替代 ZHIPU 云端 API）
- 生产中心 / 运营中心 / 行政财务 的知识库搭建
- 多部门权限隔离的入口页面
- 服务器部署迁移
- 钉钉 / 其他渠道集成

---

## 技术栈

| 环节 | 当前方案 |
|------|---------|
| RAG 引擎 | RAGFlow v0.26.1 |
| LLM | DeepSeek v4（API，问复杂问题用） |
| Embedding | **Qwen3-Embedding-0.6B**（决定切，目前在 ZHIPU） |
| 搜索引擎 | SearXNG（自建，内网隔离） |
| 入口 | QQ 机器人（测试中）+ Web 页面（规划中） |
| 同步 | Python 脚本 + Windows 任务计划 |
| 数据安全 | 全本地，配方数据不出服务器 |

---

## 参考

- [RAGFlow](https://github.com/infiniflow/ragflow)
- [SearXNG](https://docs.searxng.org/)
- [Qwen3-Embedding](https://github.com/QwenLM/Qwen3-Embedding)
