#!/usr/bin/env python3
"""
制裁名单同步脚本（OpenSanctions 数据源）
=====================================
数据来源：OpenSanctions（聚合 OFAC、EU、UN 等制裁名单）
支持 OFAC SDN 和 EU 制裁的自动同步 → RAGFlow 入库

用法：
  python3 sanctions_sync.py --sync ofac        # 同步 OFAC SDN
  python3 sanctions_sync.py --sync eu          # 同步 EU 制裁
  python3 sanctions_sync.py --sync all         # 同步所有
  python3 sanctions_sync.py --cron             # 定时模式（每日）
  python3 sanctions_sync.py --list-sources     # 列出可用制裁数据源

数据源：
  - us_ofac_sdn:     US OFAC SDN List (70,780 实体)
  - us_ofac_cons:    US OFAC 合并非SDN名单 (1,920 实体)
  - eu_sanctions:    EU 制裁合集 (41,149 实体)
  - eu_sanctions_map: EU 制裁地图 (2,069 实体)
  - ext_us_ofac_press_releases: OFAC 新闻稿 (21,130 条)

RAGFlow API 配置（在运行目录创建 .env）：
  RAGFLOW_URL=http://ragflow:9380
  RAGFLOW_API_KEY=your_api_key_here
"""

import argparse
import csv
import io
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import quote
from zipfile import ZipFile

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# === 配置 ===
DATA_DIR = Path(__file__).parent / "sanctions_data"
DATA_DIR.mkdir(exist_ok=True)

# OpenSanctions 数据源
OS_BASE = "https://data.opensanctions.org/datasets/latest"

# 制裁数据源配置
SOURCES = {
    "us_ofac_sdn": {
        "title": "US OFAC SDN List",
        "entity_count": 70780,
        "kb_name": "ofac_sanctions",
        "parser_id": "laws",
        "description": "OFAC 特别指定国民名单",
    },
    "us_ofac_cons": {
        "title": "US OFAC Consolidated (non-SDN)",
        "entity_count": 1920,
        "kb_name": "ofac_sanctions",
        "parser_id": "laws",
        "description": "OFAC 合并非 SDN 名单",
    },
    "eu_sanctions": {
        "title": "EU Sanctions",
        "entity_count": 41149,
        "kb_name": "eu_sanctions",
        "parser_id": "laws",
        "description": "欧盟制裁实体合集",
    },
    "eu_sanctions_map": {
        "title": "EU Sanctions Map",
        "entity_count": 2069,
        "kb_name": "eu_sanctions",
        "parser_id": "laws",
        "description": "欧盟制裁地图数据",
    },
}


def load_env():
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ.setdefault(k, v)


def fetch_sanctions(source_id: str) -> list[dict]:
    """
    从 OpenSanctions 下载并解析制裁数据
    返回实体的结构化列表
    """
    logger.info(f"正在拉取 [{source_id}]: {SOURCES[source_id]['title']}")

    # 先获取 dataset index 找到数据文件
    index_url = f"{OS_BASE}/{source_id}/index.json"
    try:
        resp = requests.get(index_url, timeout=30)
        resp.raise_for_status()
        index = resp.json()
    except Exception as e:
        logger.error(f"获取 dataset index 失败: {e}")
        return []

    # 查找数据文件（优先 FTM JSON，其次 CSV）
    data_url = None
    data_format = None
    for resource in index.get("resources", []):
        path = resource.get("path", "")
        if path.endswith(".ftm.json"):
            data_url = f"{OS_BASE}/{source_id}/{path}"
            data_format = "ftm_json"
            break
    if not data_url:
        for resource in index.get("resources", []):
            path = resource.get("path", "")
            if path.endswith(".simple.csv"):
                data_url = f"{OS_BASE}/{source_id}/{path}"
                data_format = "csv"
                break

    if not data_url:
        logger.error(f"未找到数据文件")
        return []

    logger.info(f"下载数据: {data_url}")
    try:
        resp = requests.get(data_url, timeout=120, stream=True)
        resp.raise_for_status()

        if data_format == "csv":
            # CSV 格式 — 每行一条记录
            reader = csv.DictReader(resp.iter_lines(decode_unicode=True))
            entities = []
            for row in reader:
                entities.append({"properties": dict(row), "schema": source_id})
            logger.info(f"下载完成: {len(entities)} 条实体 (CSV)")
            return entities

        # JSON 格式 — FTM JSON lines
        entities = []
        for line in resp.iter_lines(decode_unicode=True):
            if not line or line.startswith("#"):
                continue
            try:
                entity = json.loads(line)
                entities.append(entity)
            except json.JSONDecodeError:
                continue

        logger.info(f"下载完成: {len(entities)} 条实体")
        return entities

    except Exception as e:
        logger.error(f"下载失败: {e}")
        return []


def extract_fields(entity: dict, source_id: str) -> dict:
    """
    从 OpenSanctions 实体中提取五列所需的字段
    """
    props = entity.get("properties", {})

    # 实体名称
    name = ""
    for n in props.get("name", []):
        name = n
        break
    if not name:
        for alias in props.get("alias", []):
            name = alias
            break

    # 实体类型 / 分类
    entity_type = entity.get("schema", "")
    type_labels = {
        "Person": "个人",
        "Organization": "组织",
        "LegalEntity": "法人",
        "Vessel": "船只",
        "Aircraft": "飞行器",
    }
    entity_type_label = type_labels.get(entity_type, entity_type)

    # 制裁项目（Program/Executive Order）
    program_ids = props.get("programId", [])
    program = "; ".join(program_ids) if program_ids else ""

    # 依据法规（从 topics 提取）
    topics = props.get("topics", [])
    topic_labels = {
        "sanction": "制裁",
        "sanction.entity": "制裁实体",
        "sanction.program": "制裁项目",
        "poe": "政治公众人物",
        "crime.financial": "金融犯罪",
        "crime.fraud": "欺诈",
        "crime.terror": "恐怖主义",
        "crime.cyber": "网络犯罪",
        "crime.drugs": "毒品",
        "crime.human-rights": "人权",
        "crime.evasion": "逃避制裁",
        "crime.money-laundering": "洗钱",
    }
    regulations = "; ".join(topic_labels.get(t, t) for t in topics) if topics else program

    # 行业/领域
    sectors = props.get("sector", [])
    sector = "; ".join(sectors) if sectors else ""

    # 制裁原因（从 summary, notes 提取 — FTM 可能没有）
    # 改为：从 URN/别名中推断
    reason = ""
    aliases = props.get("alias", [])
    if aliases:
        reason = f"别名: {'; '.join(aliases[:3])}"

    # 国家
    countries = props.get("country", [])
    country = "; ".join(countries) if countries else ""

    # 来源链接
    url = ""
    for u in props.get("sourceUrl", []):
        url = u
        break

    return {
        "实体名称": name,
        "实体类型": entity_type_label,
        "制裁项目": program,
        "依据法规": regulations,
        "制裁原因": reason,
        "国家": country,
        "行业": sector,
        "来源": url,
        "数据源": source_id,
        "同步日期": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }


def fetch_press_releases() -> dict[str, str]:
    """
    拉取 OFAC 新闻稿，建立 实体名 → 制裁原因 的映射
    """
    logger.info("正在拉取 OFAC 新闻稿（OpenSanctions）...")
    try:
        resp = requests.get(
            f"{OS_BASE}/ext_us_ofac_press_releases/index.json",
            timeout=30,
        )
        resp.raise_for_status()
        index = resp.json()

        data_url = None
        for r in index.get("resources", []):
            if r.get("path", "").endswith(".ijson"):
                data_url = f"{OS_BASE}/ext_us_ofac_press_releases/{r['path']}"
                break

        if not data_url:
            logger.warning("未找到新闻稿数据文件")
            return {}

        resp = requests.get(data_url, timeout=120, stream=True)
        resp.raise_for_status()

        # 建立 实体名 → 制裁原因 映射
        name_to_reason = {}
        for line in resp.iter_lines(decode_unicode=True):
            if not line or line.startswith("#"):
                continue
            try:
                article = json.loads(line)
                props = article.get("properties", {})
                title = " ".join(props.get("title", [""]))
                summary = " ".join(props.get("summary", [""]))
                text = f"{title} {summary}"

                # 从新闻正文提取被制裁的实体名
                mentioned = props.get("mentions", []) + props.get("entities", [])
                for m in mentioned:
                    if isinstance(m, str) and len(m) > 2:
                        if m not in name_to_reason or len(text) > len(name_to_reason[m]):
                            name_to_reason[m] = text[:500]
            except json.JSONDecodeError:
                continue

        logger.info(f"新闻稿处理完成: {len(name_to_reason)} 条实体提及")
        return name_to_reason

    except Exception as e:
        logger.warning(f"新闻稿拉取失败: {e}")
        return {}


def match_reasons(entities: list[dict], press_map: dict[str, str]) -> list[dict]:
    """将新闻稿中的制裁原因匹配到实体"""
    matched = 0
    for e in entities:
        name = e.get("实体名称", "")
        if not name:
            continue

        # 精确匹配
        if name in press_map:
            e["制裁原因"] = press_map[name]
            matched += 1
            continue

        # 模糊匹配：名称作为关键词出现在新闻稿中
        name_lower = name.lower()
        for key, val in press_map.items():
            if name_lower in key.lower() or key.lower() in name_lower:
                e["制裁原因"] = val
                matched += 1
                break

    logger.info(f"已匹配制裁原因: {matched}/{len(entities)} 条")
    return entities


def export_csv(entities: list[dict], output: Path):
    """导出 CSV"""
    fields = [
        "实体名称", "实体类型", "制裁项目", "依据法规",
        "制裁原因", "国家", "来源", "数据源", "同步日期",
    ]
    with open(output, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(entities)
    logger.info(f"CSV 导出: {output} ({len(entities)} 条)")


def upload_to_ragflow(csv_path: Path, kb_name: str):
    """通过 RAGFlow API 上传到知识库"""
    ragflow_url = os.environ.get("RAGFLOW_URL", "http://ragflow:9380")
    api_key = os.environ.get("RAGFLOW_API_KEY", "")
    if not api_key:
        logger.warning("RAGFLOW_API_KEY 未配置，跳过入库")
        return

    logger.info(f"上传到 RAGFlow 知识库: {kb_name}")
    try:
        session = requests.Session()
        session.headers.update({"Authorization": f"Bearer {api_key}"})

        # 获取或创建知识库
        resp = session.get(f"{ragflow_url}/api/v1/datasets")
        datasets = resp.json().get("data", [])
        kb_id = None
        for ds in datasets:
            if ds.get("name") == kb_name:
                kb_id = ds.get("id")
                break
        if not kb_id:
            resp = session.post(f"{ragflow_url}/api/v1/datasets", json={
                "name": kb_name,
                "chunk_method": "laws",
            })
            kb_id = resp.json().get("data", {}).get("id")
        else:
            # 重建知识库：删除旧的重新创建（API不支持单文件删除）
            logger.info(f"重建知识库: {kb_name}")
            session.delete(f"{ragflow_url}/api/v1/datasets/{kb_id}")
            resp = session.post(f"{ragflow_url}/api/v1/datasets", json={
                "name": kb_name,
                "chunk_method": "laws",
            })
            kb_id = resp.json().get("data", {}).get("id")

        if not kb_id:
            logger.error("无法创建知识库")
            return

        # 上传
        with open(csv_path, "rb") as f:
            resp = session.post(
                f"{ragflow_url}/api/v1/datasets/{kb_id}/documents",
                files={"file": (csv_path.name, f, "text/csv")},
            )
        if resp.status_code in (200, 201):
            logger.info(f"✓ 上传成功: {csv_path.name}")
        else:
            logger.error(f"上传失败: {resp.status_code}")
    except Exception as e:
        logger.error(f"上传异常: {e}")


def list_sources():
    """列出可用的制裁数据源"""
    print("\n=== 可用制裁数据源 ===")
    for sid, info in SOURCES.items():
        print(f"  {sid:30s} | {info['title']:40s} | {info['entity_count']:>6} 实体")
    print()


def main():
    load_env()
    parser = argparse.ArgumentParser(description="制裁名单同步工具")
    parser.add_argument("--list-sources", action="store_true", help="列出可用数据源")
    parser.add_argument("--sync", choices=["ofac", "eu", "us", "all"], help="同步指定数据源")
    parser.add_argument("--cron", action="store_true", help="定时模式")
    args = parser.parse_args()

    if args.list_sources:
        list_sources()
        return

    # 确定要同步的数据源
    if args.sync == "ofac" or args.sync == "us":
        targets = ["us_ofac_sdn", "us_ofac_cons"]
    elif args.sync == "eu":
        targets = ["eu_sanctions", "eu_sanctions_map"]
    elif args.sync == "all":
        targets = list(SOURCES.keys())
    elif args.cron:
        targets = list(SOURCES.keys())
    else:
        parser.print_help()
        return

    # 拉取新闻稿（仅一次，所有数据源共享）
    press_map = fetch_press_releases()

    # 按知识库分组上传，避免重复重建
    kb_groups: dict[str, list[str]] = {}
    for source_id in targets:
        if source_id not in SOURCES:
            continue
        kb = SOURCES[source_id]["kb_name"]
        kb_groups.setdefault(kb, []).append(source_id)

    for kb_name, group in kb_groups.items():
        logger.info(f"\n{'='*60}")
        logger.info(f"知识库: {kb_name} ({', '.join(group)})")
        logger.info(f"{'='*60}")

        csv_paths = []
        for source_id in group:
            entities = fetch_sanctions(source_id)
            if not entities:
                logger.warning(f"{source_id}: 未获取到数据，跳过")
                continue

            records = [extract_fields(e, source_id) for e in entities]
            records = [r for r in records if r["实体名称"]]
            records = match_reasons(records, press_map)

            timestamp = datetime.now().strftime("%Y%m%d")
            csv_path = DATA_DIR / f"sanctions_{source_id}.csv"
            export_csv(records, csv_path)
            csv_paths.append((source_id, csv_path))

        if not csv_paths:
            continue

        # 查找知识库，不存在则创建
        ragflow_url = os.environ.get("RAGFLOW_URL", "http://ragflow:9380")
        api_key = os.environ.get("RAGFLOW_API_KEY", "")
        if not api_key:
            logger.warning("RAGFLOW_API_KEY 未配置，跳过入库")
            continue

        session = requests.Session()
        session.headers.update({"Authorization": f"Bearer {api_key}"})

        resp = session.get(f"{ragflow_url}/api/v1/datasets")
        kb_id = None
        for ds in resp.json().get("data", []):
            if ds.get("name") == kb_name:
                kb_id = ds.get("id")
                break
        if not kb_id:
            resp = session.post(f"{ragflow_url}/api/v1/datasets", json={
                "name": kb_name,
                "chunk_method": "laws",
            })
            kb_id = resp.json().get("data", {}).get("id")
            if not kb_id:
                logger.error(f"无法创建知识库: {kb_name}")
                continue

        # 上传所有文件
        for source_id, csv_path in csv_paths:
            with open(csv_path, "rb") as f:
                resp = session.post(
                    f"{ragflow_url}/api/v1/datasets/{kb_id}/documents",
                    files={"file": (csv_path.name, f, "text/csv")},
                )
            label = SOURCES[source_id]["title"]
            if resp.status_code in (200, 201):
                logger.info(f"✓ [{label}] 上传成功")
            else:
                logger.error(f"✗ [{label}] 上传失败: {resp.status_code}")

        time.sleep(1)


if __name__ == "__main__":
    main()
