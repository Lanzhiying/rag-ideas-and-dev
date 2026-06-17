# RAG 思路与开发实践

> Retrieval-Augmented Generation — 从想法到落地，记录我的 RAG 探索历程。

---

## 📂 仓库结构

```
.
├── README.md              ← 项目总览（本文件）
├── docs/                  ← 文档与笔记
│   ├── concepts/          ← RAG 核心概念理解
│   ├── pipeline/          ← 流水线设计思路
│   └── experiments/       ← 实验记录
├── code/                  ← 代码实现
│   ├── ingestion/         ← 文档摄取 / 分块
│   ├── embedding/         ← 向量化 / 索引
│   ├── retrieval/         ← 检索策略
│   └── generation/        ← 生成 / 后处理
└── assets/                ← 图片、架构图
```

---

## 🧭 思路路线图

- [ ] **Phase 1** — RAG 基础 pipeline 搭建（Naive RAG）
  - 文档摄取 & 分块策略
  - Embedding & 向量数据库选型
  - 基础检索 + LLM 生成
- [ ] **Phase 2** — 检索质量优化（Advanced RAG）
  - 查询重写 / HyDE
  - 多路召回 & 融合排序
  - Chunk 大小与重叠实验
- [ ] **Phase 3** — 进阶方向探索
  - Agentic RAG（工具调用 / 路由）
  - Graph RAG（知识图谱增强）
  - Multi-modal RAG

---

## 📝 核心想法记录

*等待填充 —— 我会持续在这里记录对 RAG 的理解、灵感与踩坑经验。*

---

## ⚙️ 技术栈记录

| 组件 | 选项 | 选择 | 原因 |
|------|------|------|------|
| LLM | OpenAI / Claude / 本地模型 | - | - |
| Embedding | text-embedding-3 / bge / mxbai | - | - |
| 向量库 | Chroma / Milvus / Qdrant / FAISS | - | - |
| 框架 | LangChain / LlamaIndex / 自研 | - | - |

---

## 📖 参考资源

- [RAG Survey (Gao et al.)](https://arxiv.org/abs/2312.10997)
- [LangChain RAG Docs](https://python.langchain.com/docs/tutorials/rag/)
- [LlamaIndex RAG Guide](https://docs.llamaindex.ai/en/stable/understanding/rag/)

---

*持续更新中…*
