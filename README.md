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

## 我现在在纠结什么

- 中文文档怎么切？按段落、按语义、还是固定长度——试了几种都不太满意
- 本地 Embedding 模型到底选哪个？CPU 上跑得太慢了，bge-small 凑合但不知道精度差了多少
- 向量库 Chroma、Qdrant、FAISS 三个都摸了一遍，各有各的烦人之处
- 检索策略要不要上混合？加了关键词匹配会不会反而把结果搞乱了
- 本地 LLM 用 Ollama 还是 llama.cpp？7B 模型在我的 CPU 上回答一个问题要半分钟，能忍吗
- 怎么评估 RAG 输出好不好——没有标注数据，总不能全靠感觉

---

## 技术栈（还在试）

| 环节 | 当前在用的 | 也试过的 |
|------|-----------|---------|
| LLM 推理 | Ollama (qwen2:7b) | llama.cpp |
| Embedding | 待定，正在测 | BGE 全家桶、m3e、gte-small |
| 向量库 | Chroma（因为简单） | Qdrant、FAISS |
| 文档解析 | PyMuPDF | Unstructured |
| RAG 框架 | RAGFlow | 自己拼 |

---

## 参考

- [BGE Embedding](https://huggingface.co/BAAI/bge-m3)
- [Ollama](https://ollama.com/)
- [Chroma](https://www.trychroma.com/)
