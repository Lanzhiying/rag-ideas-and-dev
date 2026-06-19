#!/usr/bin/env python3
"""
OFAC 制裁名单同步脚本
======================
定时拉取 OFAC SDN List → 解析结构化数据 + 匹配制裁理由 → RAGFlow 入库

用法：
  python3 ofac_sanctions_sync.py --download        # 拉取最新名单
  python3 ofac_sanctions_sync.py --parse            # 解析已下载的名单
  python3 ofac_sanctions_sync.py --sync             # 全流程：下载→解析→入库
  python3 ofac_sanctions_sync.py --cron             # 定时模式（每日检查更新）

RAGFlow API 配置：
  在运行目录创建 .env 文件：
    RAGFLOW_URL=http://ragflow:9380
    RAGFLOW_API_KEY=your_api_key_here
    KB_NAME=ofac_sanctions
"""

import argparse
import csv
import os
import re
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# === 配置 ===
DATA_DIR = Path(__file__).parent / "sanctions_data"
DATA_DIR.mkdir(exist_ok=True)

# OFAC SDN List 下载地址
# 美国政府官方地址（可能需要浏览器访问后获取真实直链）
OFAC_SDN_URL = "https://sanctionslist.ofac.treas.gov/sdnlist.txt"

# OFAC 新闻稿 RSS（用于提取制裁原因）
OFAC_PRESS_RSS = "https://home.treasury.gov/news/press-releases/rss"

# 字段映射 — OFAC SDN 固定宽度格式的字段
SDN_FIELDS = [
    "实体编号",      # ent_num
    "实体名称",      # sdn_name
    "实体类型",      # sdn_type (Individual, Entity, Vessel, etc.)
    "项目",          # program (制裁项目编号)
    "标题",          # title (头衔/职位)
    "呼叫信号",      # call_sign (船只)
    "吨位",          # tonnage (船只)
    "GRT",           # grt
    "船只类型",      # vessel_type
    "船籍国",        # vessel_flag
    "船籍国编号",    # vessel_owner_id
    "备注",          # remarks
]


def load_env():
    """从 .env 文件加载配置"""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ.setdefault(k, v)


def download_ofac_list():
    """下载 OFAC SDN List"""
    logger.info("正在下载 OFAC SDN List...")

    # 尝试官方地址
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/plain, text/csv, application/json, */*",
        "Accept-Language": "en-US,en;q=0.9",
    })

    # 官方下载地址列表（按优先级）
    urls = [
        OFAC_SDN_URL,
        "https://sanctionslist.ofac.treas.gov/sdnlist.txt",
        "https://sanctionslist.ofac.treas.gov/sdn_advanced.txt",
    ]

    for url in urls:
        try:
            resp = session.get(url, timeout=30)
            if resp.status_code == 200 and len(resp.text) > 1000:
                timestamp = datetime.now().strftime("%Y%m%d")
                filepath = DATA_DIR / f"ofac_sdn_{timestamp}.txt"
                filepath.write_text(resp.text)
                logger.info(f"✓ 下载成功: {filepath} ({len(resp.text)} bytes)")
                return filepath
            else:
                logger.warning(f"  {url} → {resp.status_code} (长度: {len(resp.text)})")
        except Exception as e:
            logger.warning(f"  {url} → 异常: {e}")

    # 如果官方地址都失败，提示用户手动下载
    logger.error(
        "✗ 自动下载失败。请手动从以下地址下载 SDN List：\n"
        "  1. 浏览器访问 https://ofac.treasury.gov/specially-designated-nationals-list-sdn-list\n"
        "  2. 找到 SDN List 的文本/CSV 下载链接\n"
        "  3. 下载后放入制裁列表到 sanctions_data/ 目录"
    )
    return None


def parse_ofac_list(filepath: Path) -> list[dict]:
    """
    解析 OFAC SDN List (固定宽度文本格式 → 结构化表格)
    """
    logger.info(f"正在解析: {filepath}")
    text = filepath.read_text(encoding="utf-8", errors="replace")

    # SDN 固定宽度格式解析
    # 每行是一条记录，字段按固定列位置分割
    # 格式参考: https://ofac.treasury.gov/ofac-license-application-faqs/sdn-list-data-format
    records = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("                  "):
            continue

        # 尝试用固定宽度解析
        # SDN 格式: 编号(10) + 名称(150) + 类型(12) + 项目(30) + 备注(...)
        try:
            record = {
                "实体编号": line[:10].strip(),
                "实体名称": line[10:160].strip() if len(line) > 10 else "",
                "实体类型": line[160:172].strip() if len(line) > 160 else "",
                "项目": line[172:202].strip() if len(line) > 172 else "",
                "备注": line[202:].strip() if len(line) > 202 else "",
                "下载日期": datetime.now(timezone.utc).isoformat(),
            }
            if record["实体编号"] and record["实体名称"]:
                records.append(record)
        except Exception:
            continue

    logger.info(f"解析完成: {len(records)} 条记录")
    return records


def fetch_press_releases() -> list[dict]:
    """
    拉取 OFAC 新闻稿，提取制裁公告和原因描述
    """
    logger.info("正在拉取 OFAC 新闻稿...")
    articles = []

    try:
        resp = requests.get(
            "https://home.treasury.gov/news/press-releases/rss",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15,
        )
        if resp.status_code == 200 and "rss" in resp.text.lower():
            import xml.etree.ElementTree as ET
            root = ET.fromstring(resp.content)
            for item in root.iter("item"):
                title = item.findtext("title", "")
                desc = item.findtext("description", "")
                link = item.findtext("link", "")
                pub_date = item.findtext("pubDate", "")

                # 只保留制裁相关的新闻
                if re.search(r"sanction|ofac|designat|blocked|executive.?order", title, re.I):
                    articles.append({
                        "标题": title,
                        "原因描述": desc,
                        "链接": link,
                        "发布日期": pub_date,
                    })
    except Exception as e:
        logger.warning(f"拉取新闻稿失败: {e}")

    logger.info(f"获取到 {len(articles)} 篇制裁相关新闻稿")
    return articles


def match_reason(records: list[dict], articles: list[dict]) -> list[dict]:
    """
    将制裁原因匹配到对应的 SDN 条目
    规则：如果新闻稿内容包含实体名称或简称 → 认为是该实体的制裁原因
    """
    for record in records:
        record["制裁原因"] = ""
        name = record.get("实体名称", "")
        if not name:
            continue

        # 提取名称的核心部分用于匹配
        name_parts = re.split(r"[,;]?\s*(?:a\.k\.a\.|f\.k\.a\.|aka|fka)\s*", name, flags=re.I)
        primary_name = name_parts[0].strip().lower()

        for article in articles:
            text = (article.get("标题", "") + " " + article.get("原因描述", "")).lower()
            # 检查新闻稿是否提到该实体
            if primary_name in text:
                record["制裁原因"] = article.get("原因描述", article.get("标题", ""))
                record["原因来源"] = article.get("链接", "")
                break

    matched = sum(1 for r in records if r.get("制裁原因"))
    logger.info(f"已匹配原因: {matched}/{len(records)} 条")
    return records


def export_csv(records: list[dict], output: Path):
    """导出为 CSV（RAGFlow 可直接入库）"""
    fields = ["实体编号", "实体名称", "实体类型", "项目", "依据法规", "制裁原因", "备注", "下载日期"]

    # 从 Program 字段提取法规编号作为"依据法规"
    for r in records:
        program = r.get("项目", "")
        # 示例: "UKRAINE-EO13661" → "第13661号行政令"
        # 示例: "IRAN-HR" → "Iran Human Rights"
        r["依据法规"] = program

    with open(output, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)

    logger.info(f"CSV 导出完成: {output} ({len(records)} 条)")


def upload_to_ragflow(csv_path: Path):
    """
    通过 RAGFlow API 上传 CSV 到知识库
    """
    ragflow_url = os.environ.get("RAGFLOW_URL", "http://ragflow:9380")
    api_key = os.environ.get("RAGFLOW_API_KEY", "")
    kb_name = os.environ.get("KB_NAME", "ofac_sanctions")

    if not api_key:
        logger.warning("未配置 RAGFLOW_API_KEY，跳过入库")
        return

    logger.info(f"正在上传到 RAGFlow: {kb_name}")

    try:
        # 1. 获取或创建知识库
        session = requests.Session()
        session.headers.update({"Authorization": f"Bearer {api_key}"})

        # 查找知识库
        resp = session.get(f"{ragflow_url}/api/v1/datasets")
        datasets = resp.json().get("data", [])

        kb_id = None
        for ds in datasets:
            if ds.get("name") == kb_name:
                kb_id = ds.get("id")
                break

        if not kb_id:
            # 创建知识库，用 laws pipeline 处理制裁文本
            resp = session.post(f"{ragflow_url}/api/v1/datasets", json={
                "name": kb_name,
                "parser_id": "laws",
                "parser_config": {"chunk_token_num": 1024},
            })
            kb_id = resp.json().get("data", {}).get("id")

        if not kb_id:
            logger.error("无法获取或创建知识库")
            return

        # 2. 上传文件
        with open(csv_path, "rb") as f:
            resp = session.post(
                f"{ragflow_url}/api/v1/datasets/{kb_id}/documents",
                files={"file": (csv_path.name, f, "text/csv")},
            )

        if resp.status_code in (200, 201):
            logger.info(f"✓ 上传成功: {csv_path.name}")
        else:
            logger.error(f"上传失败: {resp.status_code} {resp.text}")

    except Exception as e:
        logger.error(f"RAGFlow 上传异常: {e}")


def main():
    load_env()
    parser = argparse.ArgumentParser(description="OFAC 制裁名单同步工具")
    parser.add_argument("--download", action="store_true", help="下载最新 SDN List")
    parser.add_argument("--parse", action="store_true", help="解析 SDN List → CSV")
    parser.add_argument("--sync", action="store_true", help="全流程：下载→解析→入库")
    parser.add_argument("--cron", action="store_true", help="定时模式（每日检查更新）")
    args = parser.parse_args()

    if args.cron:
        logger.info("=== OFAC 制裁名单每日同步 ===")
        filepath = download_ofac_list()
        if not filepath:
            logger.info("使用本地最新文件...")
            files = sorted(DATA_DIR.glob("ofac_sdn_*.txt"))
            filepath = files[-1] if files else None

        if filepath:
            records = parse_ofac_list(filepath)
            articles = fetch_press_releases()
            records = match_reason(records, articles)
            csv_path = DATA_DIR / f"ofac_sanctions_{datetime.now():%Y%m%d}.csv"
            export_csv(records, csv_path)
            upload_to_ragflow(csv_path)
        return

    if args.download or args.sync:
        filepath = download_ofac_list()
        if not filepath:
            return

    if args.parse or args.sync:
        files = sorted(DATA_DIR.glob("ofac_sdn_*.txt"))
        if not files:
            logger.error("没有找到 SDN 数据文件，先用 --download")
            return
        filepath = files[-1]
        records = parse_ofac_list(filepath)

        if args.sync:
            articles = fetch_press_releases()
            records = match_reason(records, articles)

        csv_path = DATA_DIR / f"ofac_sanctions_{datetime.now():%Y%m%d}.csv"
        export_csv(records, csv_path)

        if args.sync:
            upload_to_ragflow(csv_path)

    if not any([args.download, args.parse, args.sync, args.cron]):
        parser.print_help()


if __name__ == "__main__":
    main()
