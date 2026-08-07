"""
三层次 ZPD 作业生成模块
为远端发展区、最近发展区、现有发展区分别生成作业
"""

import concurrent.futures
from config import ZPD_LEVELS, get_homework_type, get_theory
from prompt_builder import build_system_prompt, get_zpd_level_instruction
from llm_client import call_llm


def generate_all_levels(
    homework_type_id: str,
    theory_id: str,
    knowledge_point: str,
    confirmed_prompt: str,
    progress_callback=None
) -> dict:
    """
    为三个 ZPD 层级并行生成作业。
    潜能适配型例外：使用理论层级驱动的单次生成。
    """
    if homework_type_id == "potential_adaptive":
        return generate_by_theory_levels(
            homework_type_id, theory_id, knowledge_point,
            confirmed_prompt, progress_callback
        )

    system_prompt = build_system_prompt(homework_type_id, theory_id)

    levels = ["distal", "proximal", "existing"]
    results = {}

    # 使用线程池并行调用三个层级
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {}
        for level_id in levels:
            if progress_callback:
                progress_callback(level_id, "generating")
            future = executor.submit(
                _generate_single_level,
                homework_type_id, level_id, knowledge_point,
                system_prompt, confirmed_prompt
            )
            futures[future] = level_id

        for future in concurrent.futures.as_completed(futures):
            level_id = futures[future]
            try:
                content = future.result()
                zpd_info = ZPD_LEVELS.get(level_id, {})
                results[level_id] = {
                    "label": zpd_info.get("label", level_id),
                    "description": zpd_info.get("description", ""),
                    "icon": zpd_info.get("icon", ""),
                    "content": content
                }
                if progress_callback:
                    progress_callback(level_id, "done")
            except Exception as e:
                results[level_id] = {
                    "label": ZPD_LEVELS.get(level_id, {}).get("label", level_id),
                    "description": "",
                    "icon": ZPD_LEVELS.get(level_id, {}).get("icon", ""),
                    "content": f"生成失败：{str(e)}",
                    "error": str(e)
                }
                if progress_callback:
                    progress_callback(level_id, "error")

    # 确保顺序：distal, proximal, existing
    ordered_results = {}
    for level_id in levels:
        if level_id in results:
            ordered_results[level_id] = results[level_id]

    return ordered_results


def generate_by_theory_levels(
    homework_type_id: str,
    theory_id: str,
    knowledge_point: str,
    confirmed_prompt: str,
    progress_callback=None
) -> dict:
    """
    按理论层级生成作业（当前用于潜能适配型）。
    单次 API 调用，返回按层级拆分的内容。
    """
    from config import get_theory_levels

    system_prompt = build_system_prompt(homework_type_id, theory_id)

    if progress_callback:
        progress_callback("all", "generating")

    try:
        content = call_llm(system_prompt, confirmed_prompt)
        parsed = _parse_theory_levels(content, theory_id)

        if progress_callback:
            progress_callback("all", "done")

        return {
            "type": "theory_levels",
            "theory_id": theory_id,
            "levels": parsed["levels"],
            "full_content": content,
        }
    except Exception as e:
        if progress_callback:
            progress_callback("all", "error")
        return {
            "type": "theory_levels",
            "theory_id": theory_id,
            "levels": [],
            "full_content": f"生成失败：{str(e)}",
            "error": str(e),
        }


def _parse_theory_levels(content: str, theory_id: str) -> dict:
    """
    解析 AI 输出：先按 ZPD 区分割（## 标记），再提取各区内理论层级（【】标记）。
    """
    from config import get_theory_levels, get_zpd_theory_mapping
    import re

    theory_levels = get_theory_levels(theory_id)
    mapping = get_zpd_theory_mapping(theory_id)
    zones = []

    # 按 ZPD 区分割：## 区名
    zone_pattern = r'##\s*(.+?)(?:\n|$)'
    zone_parts = re.split(zone_pattern, content)

    if len(zone_parts) < 3:
        # 没有匹配到 ZPD 区格式，回退到旧解析方式
        return _parse_flat_levels(content, theory_id)

    # zone_parts[0] 是第一个 ## 前的内容（忽略）
    zone_order = ["distal", "proximal", "existing"]
    for i in range(1, len(zone_parts) - 1, 2):
        zone_title = zone_parts[i].strip()
        zone_body = zone_parts[i + 1].strip() if i + 1 < len(zone_parts) else ""

        # 匹配 ZPD 区
        matched_zid = None
        for zid in zone_order:
            z = mapping.get(zid, {})
            z_label = z.get("label", "")
            if z_label and zone_title.startswith(z_label[:6]):
                matched_zid = zid
                break
        if not matched_zid:
            for zid in zone_order:
                if zid in zone_title.lower() or zone_title in ["远端", "最近", "现有"]:
                    matched_zid = zid
                    break
        if not matched_zid:
            matched_zid = zone_order[len(zones)] if len(zones) < 3 else zone_title

        # 提取区内理论层级
        level_pattern = r'【(.+?)】'
        level_parts = re.split(level_pattern, zone_body)
        zone_levels = []

        for j in range(1, len(level_parts) - 1, 2):
            lname = level_parts[j].strip()
            lbody = level_parts[j + 1].strip() if j + 1 < len(level_parts) else ""

            matched_lv = None
            for lv in theory_levels:
                if lv["name"] == lname:
                    matched_lv = lv
                    break

            if matched_lv:
                zone_levels.append({
                    "id": matched_lv["id"],
                    "name": matched_lv["name"],
                    "order": matched_lv["order"],
                    "desc": matched_lv["desc"],
                    "content": lbody,
                })

        zones.append({
            "zone_id": matched_zid,
            "zone_label": mapping.get(matched_zid, {}).get("label", zone_title),
            "student_profile": mapping.get(matched_zid, {}).get("student_profile", ""),
            "goal": mapping.get(matched_zid, {}).get("goal", ""),
            "icon": _zpd_zone_icon(matched_zid),
            "levels": zone_levels,
        })

    # 若未能解析出任何区，回退
    if not zones:
        return _parse_flat_levels(content, theory_id)

    # 收集全部层级用于扁平列表
    all_levels = []
    for z in zones:
        all_levels.extend(z["levels"])

    return {
        "zones": zones,
        "levels": all_levels,
        "raw": content,
    }


def _parse_flat_levels(content: str, theory_id: str) -> dict:
    """回退解析：按理论层级标记平铺（旧格式兼容）"""
    from config import get_theory_levels
    import re

    theory_levels = get_theory_levels(theory_id)
    parsed_levels = []

    pattern = r'【(.+?)】'
    parts = re.split(pattern, content)

    for i in range(1, len(parts) - 1, 2):
        name = parts[i].strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""

        matched = None
        for lv in theory_levels:
            if lv["name"] == name:
                matched = lv
                break

        if matched:
            parsed_levels.append({
                "id": matched["id"],
                "name": matched["name"],
                "order": matched["order"],
                "desc": matched["desc"],
                "content": body,
            })

    if not parsed_levels:
        parsed_levels = [{
            "id": "full", "name": "全部内容",
            "order": 1, "desc": "", "content": content,
        }]

    parsed_levels.sort(key=lambda x: x["order"])
    return {"levels": parsed_levels, "raw": content}


def _zpd_zone_icon(zid: str) -> str:
    icons = {"distal": "🚀", "proximal": "🎯", "existing": "✅"}
    return icons.get(zid, "")


def _generate_single_level(
    homework_type_id: str,
    level_id: str,
    knowledge_point: str,
    system_prompt: str,
    confirmed_prompt: str
) -> str:
    """为单个 ZPD 层级生成作业"""
    level_instruction = get_zpd_level_instruction(
        homework_type_id, level_id, knowledge_point
    )

    # 获取作业类型名称和层级名称
    ht = get_homework_type(homework_type_id)
    ht_name = ht["short_name"] if ht else homework_type_id
    zpd_info = ZPD_LEVELS.get(level_id, {})
    zpd_label = zpd_info.get("label", level_id)

    # 组合完整用户提示词
    full_user_prompt = f"""{confirmed_prompt}

---

{level_instruction}

---

重要提示：你正在为「{zpd_label}」学生生成{ht_name}内容。请严格按照上述输出要求生成，只输出作业内容本身，不要加额外的解释说明。"""

    return call_llm(system_prompt, full_user_prompt)


def regenerate_single_level(
    homework_type_id: str,
    theory_id: str,
    knowledge_point: str,
    level_id: str,
    confirmed_prompt: str,
    adjustment: str = ""
) -> dict:
    """
    重新生成单个层级的作业（ZPD 层级或理论层级）。
    """
    # 理论层级重新生成（潜能适配型）
    from config import get_theory_levels
    theory_levels = get_theory_levels(theory_id)
    matched_level = next((lv for lv in theory_levels if lv["id"] == level_id), None)

    if matched_level:
        return _regenerate_theory_level(
            homework_type_id, theory_id, knowledge_point,
            level_id, matched_level, confirmed_prompt, adjustment
        )

    # ZPD 层级重新生成（其他类型）
    system_prompt = build_system_prompt(homework_type_id, theory_id)
    level_instruction = get_zpd_level_instruction(
        homework_type_id, level_id, knowledge_point
    )

    ht = get_homework_type(homework_type_id)
    ht_name = ht["short_name"] if ht else homework_type_id
    zpd_info = ZPD_LEVELS.get(level_id, {})
    zpd_label = zpd_info.get("label", level_id)

    adjustment_text = ""
    if adjustment:
        adjustment_text = f"""

【教师调整要求】
{adjustment}"""

    full_user_prompt = f"""{confirmed_prompt}

---

{level_instruction}
{adjustment_text}

---

重要提示：你正在为「{zpd_label}」学生重新生成{ht_name}内容。请严格按照上述输出要求和教师的调整要求生成，只输出作业内容本身，不要加额外的解释说明。"""

    content = call_llm(system_prompt, full_user_prompt)

    return {
        "label": zpd_label,
        "description": zpd_info.get("description", ""),
        "icon": zpd_info.get("icon", ""),
        "content": content
    }


def _regenerate_theory_level(
    homework_type_id: str,
    theory_id: str,
    knowledge_point: str,
    level_id: str,
    level_info: dict,
    confirmed_prompt: str,
    adjustment: str = ""
) -> dict:
    """单独重新生成一个理论层级的题目"""
    system_prompt = build_system_prompt(homework_type_id, theory_id)

    adjustment_text = ""
    if adjustment:
        adjustment_text = f"""

【教师调整要求】
{adjustment}"""

    full_user_prompt = f"""{confirmed_prompt}

---

【特别注意】
你只需要重新生成「{level_info['name']}」这一个层级的题目。
请以【{level_info['name']}】作为标题输出。

该层级说明：{level_info['desc']}
{adjustment_text}

---

重要提示：只输出「{level_info['name']}」层级的题目内容，不要输出其他层级。数学公式使用 LaTeX 格式。"""

    content = call_llm(system_prompt, full_user_prompt)

    return {
        "label": level_info["name"],
        "description": level_info["desc"],
        "icon": "",
        "content": content
    }
