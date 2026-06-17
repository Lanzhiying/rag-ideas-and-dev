# RAG 思路与开发实践

> 本地化 RAG 搭建过程中的想法、踩坑与思考记录。

---

## 🎯 项目定位

这个仓库不是教程，也不是轮子——是我在**自己搭建本地 RAG 系统**过程中遇到的实际问题、产生的想法、做出的选择以及背后的思考。

核心问题：**如何在本地环境（无云服务依赖）下，搭建一个可靠、好用的 RAG 系统？**

---

## 📂 仓库结构

```
.
├── README.md              ← 项目总览
├── thoughts/              ← 零散想法与灵感
├── decisions/             ← 关键决策记录（为什么选A不选B）
├── pitfalls/              ← 踩坑记录（问题 + 原因 + 解法）
├── drafts/                ← 草稿 / 半成品设计文档
└── code/                  ← 实验代码（非生产级）
```

---

## 🧩 待探索的本地 RAG 问题

- [ ] **文档分块** — 中文文档怎么切？按段落、语义、还是固定长度？
- [ ] **本地 Embedding** — 哪种模型在中文上好用？BGE、m3e、text2vec？
- [ ] **本地向量库** — Chroma vs Qdrant vs FAISS？资源占用与查询速度
- [ ] **检索策略** — 关键词 + 向量混合检索、重排序（本地 reranker）
- [ ] **本地 LLM** — Ollama / llama.cpp / vLLM 的选择与调优
- [ ] **上下文窗口** — 怎么分配检索结果和提示词的 token 预算？
- [ ] **评估** — 没有标注数据的情况下，怎么判断 RAG 回答好不好？

---

## 📝 想法日志

*记录搭建过程中冒出的想法，无论是否可行。*

---

## ⚠️ 踩坑记录

*那些 Google 不到、只能靠 debug 发现的问题。*

---

## 🔧 本地技术栈（演进中）

| 环节 | 当前选择 | 备选 | 备注 |
|------|----------|------|------|
| LLM 推理 | - | Ollama / llama.cpp | |
| Embedding | - | BGE-M3 / m3e-base | |
| 向量库 | - | Chroma / Qdrant | |
| 文档解析 | - | Unstructured / PyMuPDF | |
| RAG 框架 | - | 自研 / LangChain | |

---

## 📖 参考

- [BGE Embedding](https://huggingface.co/BAAI/bge-m3)
- [Ollama](https://ollama.com/)
- [Chroma](https://www.trychroma.com/)

---

*持续记录中，欢迎讨论。*
