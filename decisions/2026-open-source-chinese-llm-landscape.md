# 2026年6月 开源中文大模型全景报告

> 数据来源：HuggingFace API + 官方 GitHub README + 中文社区评测（Zhihu/掘金/腾讯云/CSDN/V2EX）
> 更新日期：2026-06-18
> 总预算：50万 RMB（约 S$9.3万），新加坡采购

---

## 一、市场份额总览

HuggingFace 中文模型下载量 TOP 10（2026.06）：

| 排名 | 模型 | 下载量 | 日期 |
|------|------|--------|------|
| 1 | Qwen3-0.6B | 2,096万 | 2025.04 |
| 2 | Qwen3-4B | 1,161万 | 2025.04 |
| 3 | Qwen3-8B | 1,004万 | 2025.04 |
| 4 | Qwen2.5-7B-Instruct | 973万 | 2024.09 |
| 5 | DeepSeek-R1-0528 | 562万 | 2025.05 |
| 6 | DeepSeek-R1 | 512万 | 2025.01 |
| 7 | Qwen3-1.7B | 426万 | 2025.04 |
| 8 | Qwen3-4B-Instruct-2507 | 365万 | 2025.08 |
| 9 | Qwen3-32B | 284万 | 2025.04 |
| 10 | DeepSeek-V4-Pro | 280万 | 2026.04 |

> Qwen 系列占据 6/10 席位。DeepSeek 紧随其后。

---

## 二、对话模型完整参数表

### 2.1 第一梯队（旗舰模型，需多卡部署）

| 模型 | 总参数 | 激活 | 架构 | 许可 | 发布日期 | 下载量 | Q4显存 |
|------|--------|------|------|------|----------|--------|--------|
| Xiaomi MiMo-V2.5-Pro | 1,023B | MoE(FP8) | MiMoV2 | MIT | 2026.04 | 6.6万 | ~560G |
| DeepSeek V4-Pro | 862B | MoE | DeepSeekV4 | MIT | 2026.04 | 280万 | ~474G |
| Qwen3.5-397B-A17B | 397B | 17B | MoE | Apache 2.0 | 2026.02 | 49万(NVFP4) | ~218G |
| Tencent Hy3-preview | 299B | 稠密 | HYV3 | other | 2026.04 | 6.5万 | ~164G |
| Kimi K2.6 | 1T | 32B | MoE | other | 2026.04 | 210万 | ~550G |
| DeepSeek V3.2 | 671B | 37B | MoE | MIT | 2025.12 | 276万 | ~243G |
| MiniMax M3 | ~428B | ~23B | MoE | other | 2026.06 | — | ~235G |
| GLM-5.2-FP8 | MoE | MoE | GLM-MoE-DSA | MIT | 2026.06.16 | 0.37万 | 待确认 |

### 2.2 第二梯队（双 A100 80GB 可跑）

| 模型 | 总参数 | 激活 | 架构 | 许可 | 发布日期 | 下载量 | Q4显存 |
|------|--------|------|------|------|----------|--------|--------|
| Step-3.5-Flash | 199B | 稠密 | Step3p5 | Apache 2.0 | 2026.02 | 25万 | ~110G |
| DeepSeek V4-Flash | 158B | MoE(FP8) | DeepSeekV4 | MIT | 2026.04 | 222万 | ~87G |
| Qwen3.5-122B-A10B | 122B | 10B | MoE | Apache 2.0 | 2026.02 | 76万 | ~67G |
| MiniMax M2.7 | ~230B | ~10B | MoE | other | 2026.04 | 213万 | ~127G |

### 2.3 第三梯队（单卡可跑，中文质量优秀）

| 模型 | 参数量 | 架构 | 许可 | 发布日期 | 下载量 | FP16显存 | Q4显存 |
|------|--------|------|------|----------|--------|----------|--------|
| ByteDance Seed-OSS-36B | 36B | 稠密 | Apache 2.0 | 2025.08 | 3万 | ~72G | ~20G |
| Qwen3.5-35B-A3B | 35B | MoE(3B激活) | Apache 2.0 | 2026.02 | 179万 | ~6G | ~19G |
| Qwen3.5-27B | 27B | 稠密 | Apache 2.0 | 2026.02 | 191万 | ~54G | ~15G |
| Baidu ERNIE-4.5-21B-A3B | 22B | MoE | Apache 2.0 | 2025.06 | 5万 | ~6G* | ~12G |
| Qwen3.5-9B | 9B | 稠密 | Apache 2.0 | 2026.02 | 671万 | ~18G | ~5G |
| Qwen3.5-4B | 4B | 稠密 | Apache 2.0 | 2026.02 | 706万 | ~8G | ~2.2G |
| Xiaomi MiMo-7B | 7.8B | 稠密 | MIT | 2025.04 | 12万 | ~16G | ~4.3G |
| ByteDance Ouro-2.6B-Thinking | 2.7B | 稠密 | Apache 2.0 | 2025.10 | 1.5万 | ~5.4G | ~1.5G |
| Qwen3.5-0.8B | 0.8B | 稠密 | Apache 2.0 | 2026.02 | 186万 | ~1.6G | ~0.4G |

### 2.4 垂直领域 / 专用模型

| 模型 | 领域 | 参数量 | 许可 | 发布日期 |
|------|------|--------|------|----------|
| Qwen3-Coder-Next | 代码 | MoE(FP8) | Apache 2.0 | 2026.01 |
| Qwen3-Coder-30B-A3B | 代码 | 30B/3B MoE | Apache 2.0 | 2025.07 |
| HuatuoGPT-Vision-7B | 医疗视觉 | 7B | ? | 2025.05 |
| HuatuoGPT-o1-8B | 医疗推理 | 8B | ? | 2024.12 |
| ChatTS-14B | 时序预测 | 14B | Apache 2.0 | 2024.12 |
| BAAI/OpenSeek-Mid-v1 | 研究 | Qwen3架构 | ? | 2026.04 |

---

## 三、按厂商分类

| 厂商 | 最新旗舰 | 参数量 | 许可 | 独有优势 |
|------|----------|--------|------|----------|
| **阿里(Qwen)** | Qwen3.5-397B-A17B | 397B/17B MoE | Apache 2.0 | 尺寸覆盖最全(0.8B→397B)、原生多模态、201语言、下载量碾压 |
| **DeepSeek** | DeepSeek V4-Pro | 862B MoE | MIT | V4-Flash(158B)性价比高、社区最活跃、GGUF现成、MIT无限制 |
| **智谱(GLM)** | GLM-5.2-FP8 | MoE | MIT | 1M上下文稳定、SWE-bench Pro 62.1编程最强、但服务稳定性差 |
| **月之暗面(Kimi)** | Kimi K2.6 | 1T/32B MoE | other | Agent Swarm(100子Agent)、长程编程12h持续执行 |
| **MiniMax** | MiniMax M3 | ~428B/23B | other | MSA稀疏注意力、1M上下文decode 15×加速、M2仅10B激活 |
| **小米** | MiMo-V2.5-Pro | 1,023B MoE | MIT | 1T参数+MIT许可，2026年最大开源模型之一 |
| **字节跳动** | Seed-OSS-36B | 36B稠密 | Apache 2.0 | 36B纯稠密、Apache 2.0 |
| **百度** | ERNIE-4.5-21B-A3B | 22B MoE | Apache 2.0 | 百度首个真正开源、21B MoE |
| **腾讯** | Hy3-preview | 299B稠密 | other | 299B纯稠密、腾讯混元 |
| **阶跃星辰(StepFun)** | Step-3.5-Flash | 199B稠密 | Apache 2.0 | 199B稠密+Apache 2.0 |

---

## 四、社区评测综合排名

来源：SuperCLUE、SWE-bench、GitHub README、社区评测文章

### 编程能力
1. **GLM-5.1** — SWE-bench Pro 58.4%（国产第一），Terminal-Bench 81.0
2. **DeepSeek V4** — SWE-bench Verified 57.8%
3. **Qwen3.5** — SWE-bench Verified 53.2%（编程是弱项）

### 中文质量
1. **DeepSeek V4-Pro** — SuperCLUE 70.98（国内第一）
2. **Qwen3.5-Plus** — CMMLU 90.2%，垂直领域语料丰富
3. **GLM-5.1** — 学术严谨性最佳、法律文书最规范

### 通识推理
1. **DeepSeek V4-Pro** — GPQA-Diamond 90.1%
2. **Qwen3.5-Plus** — MMLU-Pro 87.8%, GPQA-Diamond 88.4%
3. **GLM-5.2** — HLE 40.5, AIME 2026 99.2

### 多模态
1. **Qwen3.5** — 文本+图像+音频+视频四合一新时代
2. **Kimi K2.6** — 原生多模态
3. **MiniMax M3** — 原生多模态

---

## 五、社区踩坑记录

### GLM-5 系列（问题最多）
- 智谱官方致歉：算力不足、灰度慢、规则不透明、推出全额退款
- 乱码/复读/生僻字 bug（官方确认）
- Token 消耗黑洞（一个问题 100 万 token）
- 高峰期 429 错误频繁

### DeepSeek V4
- thinking+tools 协议陷阱：tool_call 后必须携带 reasoning_content
- AI 痕迹极重（知网 AIGC 3.0 检测率 55-78%）
- 1M 上下文实际上限约 256K-400K

### Qwen3.5
- 编程基准比 GLM/DS 低 5-7 分
- 长上下文 >64K 后质量下降
- Agent 工具调用偶有损坏

---

## 六、嵌入模型 (Embedding) 与重排序模型 (Reranker)

### 嵌入模型

| 型号 | 维度 | 参数量 | 许可 | 发布日期 | 下载量 |
|------|------|--------|------|----------|--------|
| Qwen3-Embedding-0.6B | ? | 0.6B | Apache 2.0 | 2025.06 | 778万 |
| Qwen3-Embedding-4B | ? | 4B | Apache 2.0 | 2025.06 | 174万 |
| Qwen3-Embedding-8B | ? | 8B | Apache 2.0 | 2025.06 | 180万 |
| BGE-M3 | 1024 | 568M | MIT | 2024.03 | 1,182万 |
| BGE-Large-ZH-v1.5 | 1024 | 326M | MIT | 2023.09 | 98万 |
| GTE-Qwen2-7B-Instruct | 4096 | 7B | Apache 2.0 | 2024 | — |
| Jina-Embeddings-v5 | ? | ? | ? | 2026.01 | 52万 |

### 重排序模型

| 型号 | 参数量 | 许可 | 发布日期 | 下载量 |
|------|--------|------|----------|--------|
| BGE-Reranker-V2-M3 | 568M | MIT | 2024.03 | 1,182万 |
| Qwen3-Reranker-0.6B | 0.6B | Apache 2.0 | 2025.06 | — |
| Qwen3-Reranker-4B | 4B | Apache 2.0 | 2025.06 | — |

> BGE-M3 + BGE-Reranker-V2-M3 仍是 RAG 社区标准方案，下载量碾压。

---

## 七、硬件选型矩阵（方案 B: A100 80GB ×2, 160GB NVLink）

### 能跑的模型

| 模型 | 精度 | 显存需求 | 方案B余量 | 并发能力 |
|------|------|----------|-----------|----------|
| **DeepSeek V4-Flash** | Q4 | ~87 GB | 73GB给KV Cache | 30+并发 |
| **Qwen3.5-122B-A10B** | FP8 | ~65 GB | 95GB给KV Cache | 40+并发 |
| **Qwen3.5-35B-A3B** | FP8全量 | ~22 GB | 138GB余量 | 60+并发 |
| **Step-3.5-Flash** | Q4 | ~110 GB | 50GB | 20+并发 |
| **MiniMax M2.7** | 激活(10B) | ~20 GB | 非常充裕 | 70+并发 |
| **ByteDance Seed-OSS-36B** | Q4 | ~20 GB | 非常充裕 | 70+并发 |
| **GLM-5.2-FP8** | FP8 | 待测 | 待定 | — |

### 不能跑的模型（需更多GPU）

| 模型 | 原因 | 最低需求 |
|------|------|----------|
| Xiaomi MiMo-V2.5-Pro | 1,023B, Q4 ~560GB | H100×8 |
| DeepSeek V4-Pro | 862B, Q4 ~474GB | H100×6 |
| Tencent Hy3-preview | 299B稠密, Q4 ~164GB | A100 80G×3 |
| Kimi K2.6 | 1T, Q4 ~550GB | H100×8 |
| DeepSeek V3.2 | 671B, Q4 ~243GB | H100×4 |

---

## 八、最终建议（方案B: A100 80GB ×2, 34万RMB）

**主力模型**：DeepSeek V4-Flash (Q4) 或 Qwen3.5-122B-A10B (FP8)

| 对比维度 | DeepSeek V4-Flash | Qwen3.5-122B-A10B |
|----------|-------------------|---------------------|
| 参数规模 | 158B MoE | 122B/10B MoE |
| 所有权 | MIT（最自由） | Apache 2.0 |
| 社区生态 | GGUF现成、下载249万 | FP8版本现成、下载76万 |
| 中文质量 | SuperCLUE 第一 | CMMLU 90.2% |
| 编程能力 | 强 | 偏弱 |
| 多模态 | 纯文本 | 原生多模态（图+文+音+视） |
| 单卡Q4 | ~87GB | ~67GB |
| 双卡余量 | 73GB | 95GB |

**建议**：主力用 DeepSeek V4-Flash（MIT 许可+社区最活跃），备选 Qwen3.5-122B 覆盖多模态场景。Embedding 和 Reranker 用 BGE-M3 + BGE-Reranker-V2-M3（MIT，社区标准）。

剩余预算约 16 万：投入高速 NVMe 存储阵列（4TB U.2 ×4 RAID 0），对 RAG 文档检索速度提升最显著。
