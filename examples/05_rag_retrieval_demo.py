# -*- coding: utf-8 -*-
"""
RAG 检索环节 Demo：在 RAG 流程中如何使用 TreeSearch 做检索

RAG 流程简述：
  用户问题 → [检索] 从知识库取出相关片段 → [生成] 将问题 + 片段交给 LLM 生成答案

本 Demo 演示：
  1. 用 TreeSearch 对文档建树索引（支持 Markdown / 代码等）
  2. 用 TreeSearch.search() 做关键词/结构感知检索，得到带分数的节点
  3. 将检索结果整理成「上下文片段列表」，供后续 LLM 使用
  4. （可选）拼接成 prompt 的示例，便于接入真实 LLM

运行方式：
  python examples/05_rag_retrieval_demo.py
"""
import os
import sys

# 保证能 import treesearch（在项目根或 examples 下执行）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from treesearch import TreeSearch


# ---------------------------------------------------------------------------
# 1. 检索器封装：把 TreeSearch 当作 RAG 的「检索模块」使用
# ---------------------------------------------------------------------------

def generate_with_siliconflow(
    *,
    question: str,
    context: str,
    api_key: str | None = None,
    base_url: str = "https://api.siliconflow.cn/v1",
    model: str = "Pro/zai-org/GLM-5",
) -> str:
    """
    RAG 的「生成」环节：调用 SiliconFlow 的 OpenAI 兼容接口，让模型基于检索上下文回答。

    说明：
    - API Key 建议通过环境变量提供：SILICONFLOW_API_KEY
    - 这里使用 OpenAI SDK（openai>=1.x）的写法，base_url 指向 SiliconFlow

    Args:
        question: 用户问题
        context: 检索得到的参考内容（通常是多个片段拼接）
        api_key: SiliconFlow API Key；若为 None，则从环境变量读取
        base_url: SiliconFlow OpenAI 兼容地址
        model: SiliconFlow 模型名（示例：Pro/zai-org/GLM-5）

    Returns:
        str: 模型回答文本
    """
    api_key = api_key or os.getenv("SILICONFLOW_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "缺少 API Key。请设置环境变量 SILICONFLOW_API_KEY（或 OPENAI_API_KEY）后重试。"
        )

    # 延迟 import：不调用生成时不强制依赖 openai 包
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=base_url)

    system_prompt = (
        "你是一个严谨的 RAG 助手。请只根据给定的【参考内容】回答问题。\n"
        "如果参考内容不足以回答，请明确说明“不确定/信息不足”，并指出缺少什么信息。\n"
        "回答尽量结构化（分点/小标题），必要时引用参考内容中的关键词或原文片段。\n"
    )

    user_prompt = (
        f"【问题】\n{question}\n\n"
        f"【参考内容】\n{context}\n\n"
        "请基于参考内容作答："
    )

    # 使用流式输出：边收到 token 边累积完整回答（此处不直接打印，由上层统一输出）
    stream = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        stream=True,
    )

    full_text_parts: list[str] = []
    for chunk in stream:
        delta = chunk.choices[0].delta
        content = getattr(delta, "content", None) or ""
        if content:
            full_text_parts.append(content)

    return "".join(full_text_parts).strip()


def build_rag_retriever(doc_globs, index_db_path="./rag_index.db"):
    """
    构建 RAG 检索器：对指定文档建索引，返回一个检索函数。

    Args:
        doc_globs: 要索引的文件路径或 glob，例如 ["docs/*.md", "data/*.md"]
        index_db_path: 索引数据库路径，同一路径可复用已有索引

    Returns:
        retrieve(query, top_k, ...) 函数，见下方 retrieve_for_rag
    """
    ts = TreeSearch(*doc_globs, db_path=index_db_path)
    # 若传入了路径，首次 search 时会自动建索引；这里显式建索引便于后续多次检索
    ts.index(*doc_globs)
    return ts


def retrieve_for_rag(ts, query, top_k=5, max_nodes_per_doc=3, text_mode="full"):
    """
    执行检索，返回适合塞进 RAG 上下文的片段列表。

    Args:
        ts: TreeSearch 实例（已 index 过文档）
        query: 用户问题或检索关键词
        top_k: 最多返回多少个文档参与排序（内部会先做文档级 routing）
        max_nodes_per_doc: 每个文档最多取几个节点
        text_mode: "full" 用节点全文，"summary" 用摘要，适合控制上下文长度

    Returns:
        list[dict]: 每个元素为 {
            "text": str,        # 用于拼进 LLM 上下文的正文
            "title": str,       # 节点标题（如章节名）
            "doc_name": str,   # 文档名
            "score": float,     # 相关性分数，可用于排序或过滤
            "node_id": str,    # 可选，用于追溯来源
        }
    """
    result = ts.search(
        query,
        top_k_docs=top_k,
        max_nodes_per_doc=max_nodes_per_doc,
        text_mode=text_mode,
        include_ancestors=True,  # 带上层级信息，便于 LLM 理解上下文位置
    )

    # 统一用 flat_nodes：已按分数排好序，且包含 doc 信息
    chunks = []
    for node in result.get("flat_nodes", []):
        text = (node.get("text") or "").strip()
        if not text:
            continue
        chunks.append({
            "text": text,
            "title": node.get("title", ""),
            "doc_name": node.get("doc_name", ""),
            "score": node.get("score", 0.0),
            "node_id": node.get("node_id", ""),
        })
    return chunks


def format_context_for_llm(chunks, max_chars=8000, separator="\n\n---\n\n"):
    """
    把检索到的片段格式化成一段「上下文」字符串，便于拼进 LLM 的 system/user prompt。

    Args:
        chunks: retrieve_for_rag() 返回的列表
        max_chars: 上下文总长度上限（按字符粗算）
        separator: 片段之间的分隔符

    Returns:
        str: 可直接放在 prompt 里的 context 字符串
    """
    parts = []
    total = 0
    for c in chunks:
        # 可选：带标题和来源，方便模型引用
        block = f"[{c['doc_name']}] {c['title']}\n{c['text']}"
        if total + len(block) + len(separator) > max_chars:
            # 截断最后一个片段以不超出上限
            remain = max_chars - total - len(separator) - 100
            if remain > 0:
                parts.append(block[:remain] + "\n...(略)")
            break
        parts.append(block)
        total += len(block) + len(separator)
    return separator.join(parts)


# ---------------------------------------------------------------------------
# 2. 示例：从问题 → 检索 → 生成（调用 SiliconFlow 在线服务）
# ---------------------------------------------------------------------------

def main():
    # 使用仓库自带的示例文档
    examples_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(examples_dir, "data", "markdowns")
    index_db = os.path.join(examples_dir, "indexes", "rag_demo", "index.db")
    os.makedirs(os.path.dirname(index_db), exist_ok=True)

    if not os.path.isdir(data_dir):
        print(f"示例数据目录不存在: {data_dir}")
        print("请先准备若干 .md 文件，或修改 DATA_DIR 指向你的文档目录。")
        return

    # 构建检索器（对 data/markdowns/*.md 建索引）
    ts = build_rag_retriever([f"{data_dir}/*.md"], index_db_path=index_db)

    # 模拟 RAG 中的多轮「用户问题 → 检索」
    questions = [
        "如何配置语音通话？",
        "agent 工具怎么注册？",
    ]

    for q in questions:
        # 只输出「问题」和最终「答案」，中间过程不打印
        print(f"用户问题: {q}")

        # RAG 检索环节：从知识库取回相关片段（不打印中间信息）
        chunks = retrieve_for_rag(ts, q, top_k=3, max_nodes_per_doc=2, text_mode="full")

        # 把片段拼成给 LLM 的上下文（可控制长度，避免超出上下文窗口）
        context = format_context_for_llm(chunks, max_chars=4000)

        # RAG 生成环节：把「问题 + 上下文」交给 LLM，得到最终答案
        try:
            answer = generate_with_siliconflow(
                question=q,
                context=context,
                model=os.getenv("SILICONFLOW_MODEL", "Pro/zai-org/GLM-5"),
            )
        except Exception as e:
            print("（生成环节未执行成功）")
            print(f"原因: {e}")
            print("提示：先设置环境变量 SILICONFLOW_API_KEY，再重试。例如：")
            print('  export SILICONFLOW_API_KEY="YOUR_API_KEY"')
            print('  export SILICONFLOW_MODEL="Pro/zai-org/GLM-5"  # 可选')
            print()
            continue

        print("LLM 回答:")
        print(answer)
        print()  # 问答之间空一行，便于阅读


if __name__ == "__main__":
    main()
