"""
Embedding 模型评估工具（纯 CPU 版）

用法：
    python evaluate_embedding.py --model BAAI/bge-small-zh-v1.5
    python evaluate_embedding.py --model all           # 全部模型
    python evaluate_embedding.py --model tier1         # 只测轻量级
"""

import time
import json
import subprocess
import platform
from pathlib import Path


# ============================================================
# 硬件检测
# ============================================================

def detect_hardware():
    """检测 CPU/内存信息（Linux / WSL）。"""
    info = {"platform": platform.platform(), "cpu_count": 1, "ram_gb": "?"}

    try:
        info["cpu_count"] = int(
            subprocess.check_output("nproc", shell=True).decode().strip()
        )
    except Exception:
        pass

    try:
        mem_bytes = int(
            subprocess.check_output(
                "free -b | grep Mem | awk '{print $2}'", shell=True
            ).decode().strip()
        )
        info["ram_gb"] = round(mem_bytes / (1024**3), 1)
    except Exception:
        pass

    try:
        info["cpu_model"] = subprocess.check_output(
            "lscpu | grep 'Model name' | cut -d: -f2", shell=True
        ).decode().strip()
    except Exception:
        pass

    return info


# ============================================================
# 模型分组
# ============================================================

TIER1_MODELS = [
    "BAAI/bge-small-zh-v1.5",
    "thenlper/gte-small",
    "sentence-transformers/all-MiniLM-L6-v2",
]

TIER2_MODELS = [
    "BAAI/bge-base-zh-v1.5",
    "moka-ai/m3e-base",
]

ALL_MODELS = TIER1_MODELS + TIER2_MODELS + [
    "BAAI/bge-large-zh-v1.5",
    "BAAI/bge-m3",
]


# ============================================================
# 测试文本
# ============================================================

TEST_TEXTS = [
    # 中文（短）
    "检索增强生成（RAG）是一种结合信息检索与文本生成的技术。",
    "Embedding 模型将文本转换为高维向量，用于语义相似度计算。",
    "本地部署大语言模型需要考虑显存、推理速度和并发能力。",
    "RAGFlow 是一个开源的 RAG 引擎，支持多种文档格式的解析。",
    "中文自然语言处理面临分词、语义理解和上下文建模等挑战。",
    # 中文（中长）
    "向量数据库如 Milvus、Qdrant 和 Chroma 常用于 RAG 系统的存储层，"
    "它们提供高效的向量相似度搜索能力，支持 ANN 近似最近邻算法。",
    "文档分块策略直接影响检索的粒度和召回质量。分块太大则语义噪声增加，"
    "分块太小则上下文信息丢失，需要在两者之间找到平衡。",
    "混合检索结合关键词匹配和语义搜索，兼顾精确性和泛化性。"
    "BM25 适合精确匹配场景，而向量检索擅长捕获语义相似性。",
    "模型量化（Quantization）可以在精度损失可控的前提下大幅降低资源消耗。"
    "INT8 量化通常可以将模型体积减少 50%，推理速度提升 2-3 倍。",
    "提示工程（Prompt Engineering）是优化 LLM 输出的关键技术。"
    "通过精心设计的提示模板，可以引导模型产生更准确、更格式化的回答。",
    # 英文
    "Retrieval-Augmented Generation combines information retrieval with text generation.",
    "Embedding models convert text into dense vector representations for semantic search.",
    "Local LLM deployment requires careful consideration of VRAM and throughput constraints.",
    "Vector databases store embeddings for efficient similarity search using ANN algorithms.",
    "Document chunking strategy significantly impacts retrieval quality and token efficiency.",
]


# ============================================================
# 1. 速度 + 内存测试
# ============================================================

def benchmark_model(model_name: str, texts: list[str], device: str = "cpu"):
    """
    测试单模型的推理速度和内存占用。

    Returns:
        dict or None (如果加载失败)
    """
    import gc
    from sentence_transformers import SentenceTransformer

    print(f"\n{'='*60}")
    print(f"📦 {model_name}")
    print(f"{'='*60}")

    # --- 加载 ---
    print("  加载模型 ...", end=" ", flush=True)
    t0 = time.time()
    try:
        model = SentenceTransformer(model_name, device=device)
    except Exception as e:
        print(f"❌ 失败: {e}")
        return None
    load_time = time.time() - t0

    # 参数 & 内存
    total_params = sum(p.numel() for p in model.parameters())
    estimated_mb = (total_params * 4) / (1024 * 1024)

    print(f"✅ {load_time:.1f}s | {total_params:,} params | ~{estimated_mb:.0f} MB")

    # --- Warm-up ---
    _ = model.encode(["预热"], show_progress_bar=False)

    # --- 速度测试 ---
    print(f"  编码 {len(texts)} 条 ...", end=" ", flush=True)
    t0 = time.time()
    embeddings = model.encode(texts, show_progress_bar=False)
    encode_time = time.time() - t0

    total_chars = sum(len(t) for t in texts)

    result = {
        "model": model_name,
        "device": device,
        "load_time_sec": round(load_time, 2),
        "encode_time_sec": round(encode_time, 2),
        "total_time_sec": round(load_time + encode_time, 2),
        "num_texts": len(texts),
        "texts_per_sec": round(len(texts) / encode_time, 2) if encode_time > 0 else 0,
        "chars_per_sec": round(total_chars / encode_time, 2) if encode_time > 0 else 0,
        "embedding_dim": embeddings.shape[1],
        "total_params": total_params,
        "estimated_size_mb": round(estimated_mb, 1),
    }

    # 清理内存
    del model, embeddings
    gc.collect()

    return result


# ============================================================
# 2. 检索精度测试
# ============================================================

def benchmark_recall(model_name: str, testset: list[dict], device: str = "cpu", top_k: int = 5):
    """简化版 Recall@K 测试。"""
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np

    all_chunks = []
    queries = []
    relevance_map = []
    chunk_to_id = {}

    for item in testset:
        queries.append(item["query"])
        rel_ids = []
        for chunk_text in item["chunks"]:
            if chunk_text not in chunk_to_id:
                chunk_to_id[chunk_text] = len(all_chunks)
                all_chunks.append(chunk_text)
            rel_ids.append(chunk_to_id[chunk_text])
        relevance_map.append(rel_ids)

    model = SentenceTransformer(model_name, device=device)
    query_embs = model.encode(queries, show_progress_bar=False)
    chunk_embs = model.encode(all_chunks, show_progress_bar=False)

    sim_matrix = cosine_similarity(query_embs, chunk_embs)
    recalls = []
    for i, rel_ids in enumerate(relevance_map):
        ranked = np.argsort(sim_matrix[i])[::-1][:top_k]
        hits = len(set(ranked) & set(rel_ids))
        recalls.append(hits / len(rel_ids))

    return {
        "model": model_name,
        "num_queries": len(queries),
        "num_chunks": len(all_chunks),
        "top_k": top_k,
        "mean_recall": round(np.mean(recalls), 4),
    }


# ============================================================
# 批量对比
# ============================================================

def run_comparison(models: list[str], texts: list[str] = None, device: str = "cpu"):
    """运行多个模型的速度 + 内存对比。"""
    if texts is None:
        texts = TEST_TEXTS

    # 硬件信息
    hw = detect_hardware()
    print(f"🖥️  硬件: {hw.get('cpu_model', '?')} | {hw['cpu_count']} 核 | {hw['ram_gb']} GB RAM")
    print(f"📝 测试文本: {len(texts)} 条\n")

    results = []
    for i, m in enumerate(models):
        print(f"[{i+1}/{len(models)}]", end="")
        r = benchmark_model(m, texts, device)
        if r:
            results.append(r)

    if not results:
        print("\n❌ 没有成功测试的模型")
        return []

    # --- 打印对比表 ---
    print("\n" + "=" * 100)
    print(f"{'模型':<38} {'维度':>5} {'大小MB':>7} {'加载s':>6} {'编码s':>7} {'条/秒':>7} {'字/秒':>9}")
    print("-" * 100)

    sorted_results = sorted(results, key=lambda x: x["texts_per_sec"], reverse=True)
    for r in sorted_results:
        print(
            f"{r['model']:<38} {r['embedding_dim']:>5} {r['estimated_size_mb']:>7.1f} "
            f"{r['load_time_sec']:>6.1f} {r['encode_time_sec']:>7.2f} "
            f"{r['texts_per_sec']:>7.2f} {r['chars_per_sec']:>9.0f}"
        )

    print("=" * 100)

    return sorted_results


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Embedding 模型评估（纯 CPU）")
    parser.add_argument("--model", type=str, default="tier1",
                        help="模型名 / 'tier1' / 'tier2' / 'all'")
    parser.add_argument("--task", type=str, default="speed",
                        choices=["speed", "recall"])
    parser.add_argument("--output", type=str, help="保存 JSON 结果")
    args = parser.parse_args()

    # 选择模型列表
    model_map = {
        "tier1": TIER1_MODELS,
        "tier2": TIER2_MODELS,
        "all": ALL_MODELS,
    }
    selected = model_map.get(args.model, [args.model])

    results = run_comparison(selected)

    if args.output and results:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n📁 结果已保存: {args.output}")
