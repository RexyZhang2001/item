# 耀耀工厂代码节点：def handler(params) -> dict
# 入参 input 请绑：VLM-Detection助手 → StructuredContent → result（String）
# 若无 result，可试：json（Object）

import json


def _load_detection_json(raw):
    if raw is None:
        return None

    # 业务 JSON 对象（绑 json 时）
    if isinstance(raw, dict) and raw.get("ok") is True and (
        raw.get("image_url") or raw.get("images")
    ):
        return raw

    # 绑 StructuredContent/result：整段 JSON 字符串
    if isinstance(raw, str):
        s = raw.strip()
        if s.startswith("{"):
            return json.loads(s)
        return None

    if not isinstance(raw, dict):
        return None

    # 绑了 StructuredContent 对象
    sc = raw.get("StructuredContent") or raw.get("structuredContent")
    if isinstance(sc, dict):
        result = sc.get("result")
        if isinstance(result, str) and result.strip().startswith("{"):
            return json.loads(result.strip())
        if isinstance(result, dict) and result.get("ok"):
            return result

    # 绑了 json 字段但类型是 Object
    j = raw.get("json")
    if isinstance(j, dict) and j.get("ok"):
        return j
    if isinstance(j, str) and j.strip().startswith("{"):
        return json.loads(j.strip())

    # MCP content[0].text（若平台以后能选到）
    content = raw.get("content")
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                text = block.get("text") or block.get("data")
                if text and str(text).strip().startswith("{"):
                    return json.loads(str(text).strip())

    return None


def handler(params):
    raw = params.get("input") if isinstance(params, dict) else params
    data = _load_detection_json(raw)

    if data is None:
        raise ValueError(
            "无法解析。入参请绑：VLM-Detection助手 → StructuredContent → result；"
            "或 json。不要绑 path/url。"
            f" 当前类型={type(raw).__name__}"
        )

    if not data.get("ok"):
        raise ValueError(data.get("error") or "检测失败")

    u1 = data.get("image_url") or ""
    u2 = data.get("image_human_url") or ""
    u3 = data.get("image_machine_url") or ""
    images = data.get("images") or []
    if len(images) >= 3:
        u1 = u1 or images[0].get("url", "")
        u2 = u2 or images[1].get("url", "")
        u3 = u3 or images[2].get("url", "")

    if not (u1 and u2 and u3):
        raise ValueError("缺少三张图 url")

    counts = data.get("counts") or {}

    ret = {
        "image_url": u1,
        "image_human_url": u2,
        "image_machine_url": u3,
        "image_count": data.get("image_count", 3),
        "stream_url": data.get("stream_url", ""),
        "worker_boxes": counts.get("worker", 0),
        "machinery_boxes": counts.get("machinery", 0),
        "vlm_input": [
            {"type": "image_url", "image_url": {"url": u1}},
            {"type": "image_url", "image_url": {"url": u2}},
            {"type": "image_url", "image_url": {"url": u3}},
        ],
    }
    return ret
