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
    为三个 ZPD 层级并行生成作业

    Args:
        homework_type_id: 作业类型 ID
        theory_id: 理论 ID
        knowledge_point: 知识点
        confirmed_prompt: Step 4 确认后的提示词
        progress_callback: 可选，进度回调函数(level_id, status)

    Returns:
        {
            "distal": {"label": "远端发展区", "content": "..."},
            "proximal": {"label": "最近发展区", "content": "..."},
            "existing": {"label": "现有发展区", "content": "..."}
        }
    """
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
    重新生成单个 ZPD 层级的作业

    Args:
        homework_type_id: 作业类型 ID
        theory_id: 理论 ID
        knowledge_point: 知识点
        level_id: 要重新生成的层级
        confirmed_prompt: 原始确认提示词
        adjustment: 教师的调整要求

    Returns:
        单层级结果 dict
    """
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
