# RAGFlow 多 Agent 画布：下游 Agent 收到空输入

## 现象

画布结构：Begin → 两个 Docs QA Agent（并行查知识库） → Review Agent（比对结果）。

Review Agent 的运行日志显示上游输出变量为空：

```
Input
  sys.query: "L-CKD有哪些添加剂可用？"
  Agent:StalePandasDream@content: ""
  Agent:ThinCobrasDream@content: ""
```

Review Agent 以为还没收到数据，输出"等待AI助手A和AI助手B的回答"。

实际上两个 Docs QA Agent 各自都正常运行并有输出。

## 根因

画布里多了一条不该存在的线：**Begin → Review Agent**。

所有连线都是 `start→end`（控制流触发）。Begin 节点一启动，三个 Agent 同时开始执行。Review Agent 读到 `{Agent:StalePandasDream@content}` 时，StalePandasDream 还在调 Retrieval 工具、等 LLM 返回 — output 变量还没填充，自然拿到空字符串。

RAGFlow 画布上的 `start→end` 连线是「轮到你了」的信号，不传数据。数据靠 Prompt 里的变量引用 `{Agent:Name@variable}` 来传递 — 但这个引用拿的是上游 Agent **当时** 的 output 变量值，不是等它跑完再拿。

```
错误的连线：
  begin ──→ Docs QA Agent A   ✓
  begin ──→ Docs QA Agent B   ✓
  begin ──→ Review Agent      ✗ 这条导致并行启动
  Docs QA Agent A ──→ Review Agent
  Docs QA Agent B ──→ Review Agent
```

## 修复

**删掉 `begin → Review Agent` 那条连线。**

删掉后 Review Agent 只有两个入口：Docs QA Agent A 和 B 各一条。RAGFlow 会等两个上游都跑完才触发 Review Agent，此时 output 变量已填充完毕。

```
正确的连线：
  begin ──→ Docs QA Agent A
  begin ──→ Docs QA Agent B
  Docs QA Agent A ──→ Review Agent
  Docs QA Agent B ──→ Review Agent
```

## 诊断方法

从 RAGFlow 导出画布 JSON，看 edges 数组：

```json
// 如果看到这个，就是问题所在
{"source": "begin", "target": "Agent:ReviewAgentName", "sourceHandle": "start", "targetHandle": "end"}
```

用 `hermes` 的 ragflow skill inspect 脚本可以直接跑出来所有节点的入边/出边。

## 另一个发现的隐患

Review Agent 的 `max_tokens` 设成 256 太低。光思考过程（`<think>...</think>`）就吃掉一大半，真正输出会被截断。多轮比对审查需要充足的 token 预算，建议 2048 起步或直接关掉上限。
