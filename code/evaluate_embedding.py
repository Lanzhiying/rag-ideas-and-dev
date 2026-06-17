"""
Embedding 模型评估工具

用法：
    python evaluate.py --model BAAI/bge-base-zh --task speed
    python evaluate.py --model BAAI/bge-small-zh --task recall --testset data/test_queries.json
"""

import time
import argparse
import json
import numpy as np
from pathlib import Path


# ============================================================
# 1. 速度测试
# ============================================================

def benchmark_speed(model_name: str, texts: list[str], device: str = "cpu"):
    """
    测试模型的推理速度。

    Returns:
        dict: {
            "model": str,
            "device": str,
            "num_texts": int,
            "total_time_sec": float,
            "tokens_per_sec": float,
            "texts_per_sec": float,
        }
    """
    import time
    from sentence_transformers import SentenceTransformer

    print(f"加载模型: {model_name} (device={device}) ...")
    t0 = time.time()
    model = SentenceTransformer(model_name, device=device)
    load_time = time.time() - t0
    print(f"  加载耗时: {load_time:.1f}s")

    # Warm-up
    _ = model.encode(["预热"], show_progress_bar=False)

    # 正式测试
    print(f"编码 {len(texts)} 条文本 ...")
    t0 = time.time()
    embeddings = model.encode(texts, show_progress_bar=True)
    encode_time = time.time() - t0

    total_chars = sum(len(t) for t in texts)
    result = {
        "model": model_name,
        "device": device,
        "num_texts": len(texts),
        "total_chars": total_chars,
        "load_time_sec": round(load_time, 2),
        "encode_time_sec": round(encode_time, 2),
        "texts_per_sec": round(len(texts) / encode_time, 2),
        "chars_per_sec": round(total_chars / encode_time, 2),
        "embedding_dim": embeddings.shape[1],
    }
    return result


# ============================================================
# 2. 检索精度测试（简化版）
# ============================================================

def benchmark_recall(
    model_name: str,
    testset: list[dict],
    device: str = "cpu",
    top_k: int = 5,
):
    """
    简化版召回率测试：
    testset = [
        {"query": "...", "relevant_chunks": [0, 3, 7]},
        ...
    ]

    对每个 query，计算其 embedding 后与所有 chunks 的余弦相似度，
    取 top_k，看在 relevant_chunks 中的命中率。
    """
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity

    # 收集所有 unique chunks
    all_chunks = []
    queries = []
    relevance_map = []  # list of (query_idx, relevant_chunk_indices)

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

    print(f"加载模型: {model_name} (device={device}) ...")
    model = SentenceTransformer(model_name, device=device)

    print(f"编码 {len(queries)} 条 query ...")
    query_embs = model.encode(queries, show_progress_bar=True)

    print(f"编码 {len(all_chunks)} 条 chunk ...")
    chunk_embs = model.encode(all_chunks, show_progress_bar=True)

    # 计算相似度 & Recall
    sim_matrix = cosine_similarity(query_embs, chunk_embs)

    recalls = []
    for i, rel_ids in enumerate(relevance_map):
        ranked = np.argsort(sim_matrix[i])[::-1][:top_k]
        hits = len(set(ranked) & set(rel_ids))
        recall = hits / len(rel_ids) if rel_ids else 0
        recalls.append(recall)

    result = {
        "model": model_name,
        "num_queries": len(queries),
        "num_chunks": len(all_chunks),
        "top_k": top_k,
        "mean_recall": round(np.mean(recalls), 4),
        "recall_std": round(np.std(recalls), 4),
    }
    return result


# ============================================================
# 3. 内存占用
# ============================================================

def benchmark_memory(model_name: str, device: str = "cpu"):
    """估算模型内存占用。"""
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name, device=device)
    total_params = sum(p.numel() for p in model.parameters())
    # 粗略估算：float32 = 4 bytes per param
    estimated_mb = (total_params * 4) / (1024 * 1024)

    return {
        "model": model_name,
        "total_params": total_params,
        "estimated_size_mb": round(estimated_mb, 1),
    }


# ============================================================
# 预置测试文本
# ============================================================

TEST_TEXTS_ZH = [
    "检索增强生成（RAG）是一种结合信息检索与文本生成的技术。",
    "Embedding 模型将文本转换为高维向量，用于语义相似度计算。",
    "本地部署大语言模型需要考虑显存、推理速度和并发能力。",
    "RAGFlow 是一个开源的 RAG 引擎，支持多种文档格式的解析。",
    "中文自然语言处理面临分词、语义理解和上下文建模等挑战。",
    "向量数据库如 Milvus、Qdrant 和 Chroma 常用于 RAG 系统的存储层。",
    "提示工程（Prompt Engineering）是优化 LLM 输出的关键技术。",
    "文档分块策略直接影响检索的粒度和召回质量。",
    "混合检索结合关键词匹配和语义搜索，兼顾精确性和泛化性。",
    "模型量化（Quantization）可以在精度损失可控的前提下大幅降低资源消耗。",
]

TEST_TEXTS_EN = [
    "Retrieval-Augmented Generation combines information retrieval with text generation.",
    "Embedding models convert text into dense vector representations.",
    "Local LLM deployment requires careful consideration of VRAM and throughput.",
    "Vector databases store embeddings for efficient similarity search.",
    "Document chunking strategy significantly impacts retrieval quality.",
]


# ============================================================
# 多模型对比入口
# ============================================================

MODEL_LIST = [
    "BAAI/bge-small-zh-v1.5",
    "BAAI/bge-base-zh-v1.5",
    "BAAI/bge-large-zh-v1.5",
    "BAAI/bge-m3",
    "moka-ai/m3e-base",
    "sentence-transformers/all-MiniLM-L6-v2",
    "thenlper/gte-small",
]


def run_full_benchmark(
    models: list[str] | None = None,
    device: str = "cpu",
    texts: list[str] | None = None,
):
    """运行全量速度 + 内存测试，输出对比表。"""
    if models is None:
        models = MODEL_LIST
    if texts is None:
        texts = TEST_TEXTS_ZH + TEST_TEXTS_EN

    results = []
    for m in models:
        try:
            speed = benchmark_speed(m, texts, device)
            mem = benchmark_memory(m, device)
            results.append({**speed, **mem})
            print(f"  ✅ {m}")
        except Exception as e:
            print(f"  ❌ {m}: {e}")

    # 打印对比表
    print("\n" + "=" * 90)
    print(f"{'模型':<35} {'维度':>5} {'大小MB':>8} {'条/秒':>8} {'字/秒':>10} {'参数':>10}")
    print("-" * 90)
    for r in sorted(results, key=lambda x: x.get("texts_per_sec", 0), reverse=True):
        print(
            f"{r['model']:<35} {r.get('embedding_dim', '?'):>5} "
            f"{r.get('estimated_size_mb', 0):>8.1f} {r['texts_per_sec']:>8.1f} "
            f"{r['chars_per_sec']:>10.1f} {r['total_params']:>10,}"
        )

    return results


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Embedding 模型评估")
    parser.add_argument("--model", type=str, help="单个模型名称或 'all'")
    parser.add_argument("--task", type=str, default="speed",
                        choices=["speed", "memory", "recall", "all"])
    parser.add_argument("--device", type=str, default="cpu",
                        help="cpu / cuda / mps")
    parser.add_argument("--output", type=str, help="输出 JSON 文件路径")
    args = parser.parse_args()

    if args.model == "all" or not args.model:
        run_full_benchmark(device=args.device)
    else:
        if args.task == "speed":
            result = benchmark_speed(args.model, TEST_TEXTS_ZH + TEST_TEXTS_EN, args.device)
        elif args.task == "memory":
            result = benchmark_memory(args.model, args.device)
        else:
            result = run_full_benchmark([args.model], device=args.device)

        print(json.dumps(result, indent=2, ensure_ascii=False))

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(result if isinstance(result, dict) else result, f, indent=2, ensure_ascii=False)
        print(f"\n结果已保存到 {args.output}")
