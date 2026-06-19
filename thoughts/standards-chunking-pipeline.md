# 标准文档（ISO/ASTM/DIN/GB）的 Chunking 方案

> 2026-06-18 验证结论

---

## 问题

RAGFlow 没有针对标准文档的专用 chunking pipeline。
但标准文档（ISO、ASTM、DIN、GB 等）有独特结构：
- 层级编号条款（5.2.1、5.2.1.1）
- 交叉引用（"见第 4.2.3 节"）
- 规范性引用和术语定义段
- Annex 附录

## 验证过程

对比了 RAGFlow 自带的 chunking pipeline：

| Pipeline | 适合标准？ | 理由 |
|---|---|---|
| `naive` | ⚠️ 一般 | 通用分块，不保留条款层级 |
| `paper` | ⚠️ 一般 | 针对论文结构（摘要→引言→方法→结论），和标准不对齐 |
| `manual` | ⚠️ 一般 | 针对操作手册，不处理条款编号 |
| `laws` | **✅ 可用** | 子弹头检测 + 树状合并，和标准文档结构高度相似 |

## 结论

**用 `laws` pipeline 处理标准文档。** 原因：

- `laws` 的 `bullets_category` 子弹头检测能识别层级编号
- `tree_merge` 能按层级合并条款，保持父子结构
- `remove_contents_table` 自动去掉目录
- `make_colon_as_title` 处理标题行

## 配置建议

创建知识库时选 `laws` 解析器，参数：

| 参数 | 建议值 |
|---|---|
| chunk_token_num | 512-1024（标准条款通常较长）|
| delimiter | `\n!?。；！？`（默认即可）|
| layout_recognize | DeepDOC（默认）|

## 未来改进

如果 `laws` 在某些标准文档上不够好，可以考虑：
- 写一个 `standard.py` pipeline（继承 `laws` 的 PDF 解析逻辑，替换子弹头检测为正则匹配标准编号格式 `^\d+(\.\d+)+\s`）
- 在 `rag/app/` 下创建 → 注册 FACTORY → 加 ParserType → 加 parser_config 默认值
