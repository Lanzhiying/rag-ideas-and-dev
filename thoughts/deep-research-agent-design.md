# Deep Research Agent — 画布设计与 Prompt 讨论

> 2026-06-18 讨论记录

---

## 背景

在 RAGFlow 多 Agent 复审脚本跑通之后，下一个目标是构建一个 **Depth Research Agent**——能从多个外部学术来源搜索、提取、综合信息并生成研究报告的 RAGFlow 画布。

---

## 现有画布结构（Deep Research Test.json）

从导出的 JSON 中，当前架构：

```
Begin
  │
  ▼
Agent: NewPumasLick (Director — 战略研究总监)
  │  deepseek-v4-pro, 18625字符系统提示
  │
  ├──→ Agent: FreeDucksObey (Web Search — TavilySearch)
  ├──→ Agent: WeakBoatsServe (Content Reader — TavilyExtract)
  ├──→ Agent: SwiftToysTell (Synthesizer)
  └──→ Agent: PrettyIslandsRush (Academic Search)
         ├── 工具: Wikipedia
         ├── 工具: GoogleScholar
         ├── 工具: PubMed
         └── 工具: ArXiv
```

### 已知问题

1. **Message 节点直接连 Director（start→end）**——Director 跑完就触发 Message，但此时四个子 Agent 还没跑完。Message 输出的是 Director 的规划结果而不是最终报告。
2. **PrettyIslandsRush 的提示词只有 536 字符**，基本是个通用助手的提示，没有利用好 4 个学术搜索工具。
3. **Director → Message 的直连**和之前"Begin→下游Agent"的并行 bug 类似。

---

## 学术搜索工具行为（源码验证）

从 `agent/tools/` 目录下读取各工具实现：

| 工具 | 实现方式 | 关键行为 |
|---|---|---|
| **ArXiv** | `python arxiv` 库 | 搜标题+摘要，默认按提交日期排序，TopN=12，timeout=12s |
| **GoogleScholar** | `scholarly` 库 | 搜学术文献，可设年份/专利/排序，TopN=12，但爬取不稳定有 CAPTCHA 风险 |
| **Wikipedia** | `wikipedia` 库 | 先搜标题匹配，再抓页面摘要。支持 `zh` 中文，timeout=60s |
| **PubMed** | `pymed` 或类似 | 生物医学文献搜索 |
| **DuckDuckGo** | `duckduckgo_search` | 普通网页搜索，text/news 两个频道，TopN=10 |

### 搜索词技巧

- **Wikipedia**：查询词要像条目名，不是自然语言问题
- **ArXiv**：技术关键词组合效果最好
- **GoogleScholar**：自然语言 + 关键词，可设年份范围

---

## Prompt 设计讨论

### 合并 vs 拆分

| 方式 | 优点 | 缺点 |
|---|---|---|
| **4个工具放一个Agent** | 搜索之间可串联（Schalar 搜到 FTIR → 立刻调 PubMed 查） | 串行慢，需要多轮（max_rounds 设 8-10） |
| **拆成 4 个 Agent 并行** | 同时跑，总时间 = 最慢的那个（12-60s） | 无法动态串联，Google Scholar 找到的线索不能实时喂给 PubMed |

### 折中方案

拆成两组：

- **Round 1（并行）：** GoogleScholar Agent + ArXiv Agent
- **Round 2（拿到结果后）：** 补充解析 Agent（Wikipedia + PubMed），基于 Round 1 的发现查定义和方法

### Prompt 设计建议

学术搜索 Agent 的 prompt 应包含：

1. **角色定义**：绑定领域（润滑油脂/摩擦学），让 LLM 的搜索词更精准
2. **工具使用指南**：每个工具什么场景用、搜索词怎么写
3. **搜索流程**：先搜什么、后搜什么、什么情况下触发什么工具
4. **查询词技巧**：不同工具的查询词风格差异
5. **输出格式**：结构化输出，方便下游 Synthesizer 处理

**max_rounds 建议**：合并方案 8-10 轮，拆分方案 3-5 轮。

**temperature 建议**：0.3-0.5（搜索词生成需要精确，不要 Creative 模式）。
