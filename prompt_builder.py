"""
提示词构建模块：根据作业类型填充提示词模板
"""

from config import (get_homework_type, get_theory, get_theory_levels,
                       get_zpd_theory_mapping, get_cognitive_stages,
                       get_zpd_scaffold_types, get_dialogue_styles,
                       get_inquiry_roles)


def build_system_prompt(homework_type_id: str, theory_id: str) -> str:
    """根据作业类型和理论构建 System Prompt"""
    ht = get_homework_type(homework_type_id)
    theory = get_theory(homework_type_id, theory_id)

    if not ht or not theory:
        return "你是一位资深的中小学数学教育专家。"

    base = f"""你是一位资深的中小学数学教育专家，精通最近发展区（ZPD）理论和{theory['name']}。

你的核心任务是：根据不同学习层级学生的特点，生成差异化、精准适配的作业内容。

你必须严格遵守以下原则：
1. 学科知识准确无误，符合中小学数学课程标准
2. 难度梯度合理，三个发展区（现有发展区、最近发展区、远端发展区）之间有清晰递进关系
3. 语言表述清晰、适合学生阅读水平
4. 严格按照要求的输出格式生成内容
5. 不提供超出要求的额外内容，聚焦作业本身
6. 题目设计要贴近生活实际，具有现实意义"""
    return base


def build_user_prompt(
    homework_type_id: str,
    theory_id: str,
    knowledge_point: str,
    grade_level: str = "",
    subject: str = "",
    supplement: dict = None
) -> str:
    """根据作业类型构建 User Prompt（生成的提示词 → 教师确认后用于调用 AI）"""
    ht = get_homework_type(homework_type_id)
    theory = get_theory(homework_type_id, theory_id)

    if not ht or not theory:
        return ""

    if supplement is None:
        supplement = {}

    grade = grade_level or "【未填写】"
    subj = subject or "【未填写】"

    if homework_type_id == "potential_adaptive":
        return _build_potential_adaptive_prompt(
            knowledge_point, theory, grade, subj, supplement)
    elif homework_type_id == "cognitive_support":
        return _build_cognitive_support_prompt(
            knowledge_point, theory, grade, subj, supplement)
    elif homework_type_id == "dynamic_interactive":
        return _build_dynamic_interactive_prompt(
            knowledge_point, theory, grade, subj, supplement)
    elif homework_type_id == "collaborative_inquiry":
        return _build_collaborative_inquiry_prompt(
            knowledge_point, theory, grade, subj, supplement)
    return ""


def _build_potential_adaptive_prompt(
    knowledge_point: str, theory: dict, grade: str,
    subject: str, s: dict
) -> str:
    original_question = (s.get("original_question") or "").strip()
    teaching_goal = (s.get("teaching_goal") or "").strip()
    student_data = (s.get("student_data") or "").strip()

    theory_name = theory["name"]
    theory_id = theory["id"]
    mapping = get_zpd_theory_mapping(theory_id)

    # 构建理论层级总览
    all_levels = get_theory_levels(theory_id)
    levels_text = "\n".join(
        f"   {lv['order']}. {lv['name']}——{lv['desc']}" for lv in all_levels
    )

    # 构建 ZPD 区输出格式
    zone_order = ["distal", "proximal", "existing"]
    output_format_lines = []
    for zid in zone_order:
        zone = mapping.get(zid, {})
        zone_label = zone.get("label", zid)
        level_ids = zone.get("level_ids", [])
        level_names = []
        for lid in level_ids:
            lv = next((l for l in all_levels if l["id"] == lid), None)
            level_names.append(lv["name"] if lv else lid)

        output_format_lines.append(f"## {zone_label}")
        for i, nm in enumerate(level_names):
            output_format_lines.append(f"【{nm}】")
    output_format_text = "\n".join(output_format_lines)

    # 构建可选用部分
    parts = [f"我是{grade}{subject}的老师，正在设计一份基于最近发展区的精准作业。"]

    if original_question:
        parts.append(f"作业原题目是：\n{original_question}")

    parts.append(f"知识点是：{knowledge_point}")

    if teaching_goal:
        parts.append(f"教学目标：\n{teaching_goal}")

    if student_data:
        parts.append(f"学生学情数据：\n{student_data}")

    # 构建各区设计要求
    zone_requirements = []
    for zid in zone_order:
        zone = mapping.get(zid, {})
        zone_label = zone.get("label", zid)
        student_profile = zone.get("student_profile", "")
        goal = zone.get("goal", "")
        level_ids = zone.get("level_ids", [])
        level_names = []
        for lid in level_ids:
            lv = next((l for l in all_levels if l["id"] == lid), None)
            level_names.append(lv["name"] if lv else lid)
        names_str = "、".join(level_names)
        zone_requirements.append(
            f"  - 【{zone_label}】（{student_profile}）→ {goal}\n"
            f"    对应理论层级：{names_str}，为该区生成 {len(level_ids)} 道题"
        )
    zone_req_text = "\n".join(zone_requirements)

    parts.append(f"""请同时依据「最近发展区理论」和「{theory_name}」完成以下任务。两种理论不是并列关系——ZPD 是顶层框架，{theory_name} 是每个 ZPD 区内的认知递进路径。

---
【总体框架】

本作业将学生按最近发展区划分为三个群体，每个群体完成与其能力匹配的题目：

{zone_req_text}

---
【{theory_name} 层级总览】

{theory_name}的全部层级由低到高为：
{levels_text}

---
【题目设计要求】

1. 严格按照上述三个 ZPD 区分组输出，每个区内的题目按 {theory_name} 层级顺序排列。

2. 同一 ZPD 区内的题目间具备递进关系：前一道题为后一道搭认知支架。

3. 三个 ZPD 区之间由易到难递进。

4. 所有数学公式必须使用 LaTeX 格式：
   - 行内公式用 $...$ 包裹
   - 独立公式用 $$...$$ 包裹

5. 每道题有实际应用背景，体现知识点的实用价值。

---
【输出格式（严格要求）】

请严格按照以下格式输出，使用「## ZPD区名称」（两个 # 号）标记每个区，用「【层级名称】」标记每道题：

{output_format_text}

注意：不要输出任何与作业无关的额外说明。""")

    return "\n\n".join(parts)


def _build_cognitive_support_prompt(
    knowledge_point: str, theory: dict, grade: str,
    subject: str, s: dict
) -> str:
    original_question = (s.get("original_question") or "").strip()
    cognitive_difficulty = (s.get("cognitive_difficulty") or "").strip()

    theory_name = theory['name']
    theory_id = theory['id']
    stages = get_cognitive_stages(theory_id)
    scaffold = get_zpd_scaffold_types()

    # 构建阶段列表
    stages_text = "\n".join(
        f"   {st['order']}. {st['name']}——{st['desc']}" for st in stages
    )
    n_stages = len(stages)

    # 构建 ZPD 支架风格说明
    scaffold_lines = []
    for zid in ["distal", "proximal", "existing"]:
        sc = scaffold.get(zid, {})
        scaffold_lines.append(
            f"  - {sc['icon']} {sc['label']}（{sc['style']}）：{sc['desc']}"
        )
    scaffold_text = "\n".join(scaffold_lines)

    # 构建输出格式
    output_lines = ["【题干】"]
    for st in stages:
        output_lines.append(f"## {st['name']}")
        for zid in ["distal", "proximal", "existing"]:
            sc = scaffold.get(zid, {})
            output_lines.append(f"【{sc['label']}】")
    output_format = "\n".join(output_lines)

    parts = [f'我是{grade}{subject}的老师，我正在将一项最近发展区内的作业设计为"支架型作业"。']

    if original_question:
        parts.append(f"作业原始题目是：\n{original_question}")

    parts.append(f"所属知识点为：{knowledge_point}")

    if cognitive_difficulty:
        parts.append(f"学生典型认知困难：\n{cognitive_difficulty}")

    parts.append(f"""请基于最近发展区理论和「{theory_name}」设计支架型作业。

---
【理论框架：{theory_name}】

{theory_name}将解题过程分为{n_stages}个阶段，由前到后依次为：
{stages_text}

---
【ZPD 三区支架风格】

针对每个解题阶段，请分别为三类学生设计不同类型支架：
{scaffold_text}

---
【题目设计要求】

1. 先呈现完整的题干（使用 LaTeX 格式书写数学公式）。

2. 按{n_stages}个阶段依次组织，每个阶段内按三种 ZPD 支架风格分别输出：
   - 远端发展区 → {scaffold.get('distal', {}).get('style', '')}：{scaffold.get('distal', {}).get('desc', '')}
   - 最近发展区 → {scaffold.get('proximal', {}).get('style', '')}：{scaffold.get('proximal', {}).get('desc', '')}
   - 现有发展区 → {scaffold.get('existing', {}).get('style', '')}：{scaffold.get('existing', {}).get('desc', '')}

3. 所有数学公式使用 LaTeX 格式（行内 $...$，块级 $$...$$）。

4. 每种支架保留必要的思考空间，不直接呈现完整解答。

---
【输出格式（严格要求）】

{output_format}""")

    return "\n\n".join(parts)


def _build_dynamic_interactive_prompt(
    knowledge_point: str, theory: dict, grade: str,
    subject: str, s: dict
) -> str:
    original_question = (s.get("original_question") or "").strip()
    teaching_goal = (s.get("teaching_goal") or "").strip()

    theory_name = theory['name']
    styles = get_dialogue_styles()

    style_lines = []
    out_lines = ["【题干】"]
    for zid in ["distal", "proximal", "existing"]:
        ds = styles.get(zid, {})
        style_lines.append(
            "  {} {}·{}：{}\n     策略：{}".format(
                ds.get('icon', ''), ds.get('label', ''),
                ds.get('style', ''), ds.get('description', ''),
                ds.get('strategy', ''))
        )
        out_lines.append("## {}·{}".format(ds.get('label', ''), ds.get('style', '')))
        out_lines.append("【开场引导语】")
        out_lines.append("【对话规则与追问策略】")
        out_lines.append("【支架升级路径】")
        out_lines.append("【形成性评价模板】")
    style_text = "\n".join(style_lines)
    output_format = "\n".join(out_lines)

    parts = ['你是一名"最近发展区作业导师"，面向中学生开展一对一作业辅导。']

    if original_question:
        parts.append("【作业题目】\n" + original_question)

    parts.append("【学科与年级】\n" + grade + subject)

    if teaching_goal:
        parts.append("【本题的教学目标】\n" + teaching_goal)

    parts.append("""请基于最近发展区理论和「""" + theory_name + """」为三类学生分别设计对话配置。

---
【ZPD 三区对话风格】

针对同一道题，不同学生需要不同的引导方式：
""" + style_text + """

---
【设计要求】

1. 为三个 ZPD 区分别设计完整的智能体对话配置：开场引导语、对话规则与追问策略、支架升级路径、形成性评价模板。

2. 各区引导密度不同——远端多讲少问，最近追问为主，现有反问拓展。

3. 所有数学公式使用 LaTeX 格式。

4. 每个区的开场语必须先请学生说出对题目的理解。

---
【输出格式（严格要求）】

""" + output_format)

    return "\n\n".join(parts)


def _build_collaborative_inquiry_prompt(
    knowledge_point: str, theory: dict, grade: str,
    subject: str, s: dict
) -> str:
    inquiry_theme = (s.get("inquiry_theme") or "").strip()
    task_context = (s.get("task_context") or "").strip()
    expected_output = (s.get("expected_output") or "").strip()
    student_performance = (s.get("student_performance") or "").strip()

    theory_name = theory['name']
    inquiry = get_inquiry_roles()

    # 构建三区角色说明 + 输出格式
    role_lines = []
    out_lines = ["【探究主题】"]
    for zid in ["distal", "proximal", "existing"]:
        ir = inquiry.get(zid, {})
        roles = ir.get("roles", [])
        stages = ir.get("stages", [])
        role_names = "、".join([r["name"] for r in roles])
        stage_names = " → ".join([s["name"] for s in stages])

        role_lines.append(
            "  {} {}·{}（{}角色）：{}\n    角色：{}\n    阶段：{}".format(
                ir.get('icon', ''), ir.get('label', ''),
                ir.get('style', ''), str(len(roles)),
                ir.get('description', ''),
                role_names, stage_names)
        )

        out_lines.append("## {}·{}".format(ir.get('label', ''), ir.get('style', '')))
        for r in roles:
            out_lines.append("【角色：{}】".format(r["name"]))
        for s in stages:
            out_lines.append("【阶段：{}】".format(s["name"]))
        out_lines.append("【行为规则】")
        out_lines.append("")

    role_text = "\n".join(role_lines)
    output_format = "\n".join(out_lines)

    parts = ['你是一个"协作探究作业编排系统"，面向中学生开展多智能体协作的探究式作业辅导。']

    inquiry_info = []
    if inquiry_theme:
        inquiry_info.append("探究主题：" + inquiry_theme)
    inquiry_info.append("学科与年级：" + grade + subject)
    inquiry_info.append("学习目标：围绕「" + knowledge_point + "」知识点，培养学生的探究能力和综合素养")
    if task_context:
        inquiry_info.append("任务情境：" + task_context)
    if expected_output:
        inquiry_info.append("预期成果形式：" + expected_output)
    if student_performance:
        inquiry_info.append("学生已有表现/学情：" + student_performance)

    parts.append("【探究任务信息】\n\n" + "\n\n".join(inquiry_info))

    parts.append("""请基于最近发展区理论和「""" + theory_name + """」为三类学生分别设计多智能体协作探究配置。

---
【ZPD 三区协作探究方案】

不同水平的学生需要不同规模的角色配置和不同深度的探究流程：
""" + role_text + """

---
【设计要求】

1. 为三个 ZPD 区分别设计多智能体角色配置和探究工作流。各区角色数量和阶段深度不同——远端少角色多讲解，最近适中角色适度支架，现有全角色自主探究。

2. 所有角色均不直接给出探究结论或完整答案。

3. 所有数学公式使用 LaTeX 格式。

---
【输出格式（严格要求）】

""" + output_format)

    return "\n\n".join(parts)


# ============================================================
# 为三层次 ZPD 生成作业的专用提示词附加内容
# ============================================================
def get_zpd_level_instruction(
    homework_type_id: str,
    level_id: str,
    knowledge_point: str
) -> str:
    """获取特定 ZPD 层级的作业生成指令"""
    ht = get_homework_type(homework_type_id)

    level_instructions = {
        "distal": {
            "label": "远端发展区",
            "description": "学生尚未掌握该知识点，需要最基础的支持"
        },
        "proximal": {
            "label": "最近发展区",
            "description": "学生在适当支持下能够完成，是核心作业区域"
        },
        "existing": {
            "label": "现有发展区",
            "description": "学生已掌握该知识点，需要巩固和拓展"
        }
    }

    li = level_instructions.get(level_id, level_instructions["proximal"])

    if homework_type_id == "potential_adaptive":
        return _zpd_instruction_potential(level_id, knowledge_point, li)
    elif homework_type_id == "cognitive_support":
        return _zpd_instruction_cognitive(level_id, knowledge_point, li)
    elif homework_type_id == "dynamic_interactive":
        return _zpd_instruction_dynamic(level_id, knowledge_point, li)
    elif homework_type_id == "collaborative_inquiry":
        return _zpd_instruction_collaborative(level_id, knowledge_point, li)
    return ""


def _zpd_instruction_potential(level_id: str, kp: str, li: dict) -> str:
    """潜能适配型：单一理论层级驱动，不再按 ZPD 三区分开调用"""
    return ""  # 此类型使用单次全层级生成，不需要分 ZPD 层级的独立指令


def _zpd_instruction_cognitive(level_id: str, kp: str, li: dict) -> str:
    if level_id == "distal":
        return f"""
【当前任务：为「远端发展区」学生生成作业】
学生情况：{li['description']} — 需要完整支架引导。
输出要求：
1. 题干 + 完整的四步骤支架引导（理解问题→制订计划→执行计划→回顾反思）
2. 每个步骤包含：引导性问题 + 支架提示/答案
3. 最后包含反思问题
4. 支架要详细、耐心，逐步引导学生完成"""
    elif level_id == "proximal":
        return f"""
【当前任务：为「最近发展区」学生生成作业】
学生情况：{li['description']} — 需要中等支架支持。
输出要求：
1. 题干 + 两个关键步骤的支架引导（制订计划 + 执行计划）
2. 引导性问题保留思考空间
3. 包含反思问题
4. 支架适度，不过于详细也不过于简略"""
    elif level_id == "existing":
        return f"""
【当前任务：为「现有发展区」学生生成作业】
学生情况：{li['description']} — 需要最低限度支架。
输出要求：
1. 题干 + 1条启发性提示
2. 附一个"需要帮助时展开"的完整支架区域（可折叠查看）
3. 包含反思问题
4. 以学生的自主探索为主"""


def _zpd_instruction_dynamic(level_id: str, kp: str, li: dict) -> str:
    if level_id == "distal":
        return f"""
【当前任务：为「远端发展区」学生配置智能体】
学生情况：{li['description']} — 仅做启发追问，不提供直接提示。
输出要求：生成该层级下的智能体对话配置，包括：
1. 开场引导语（请学生说出对题目的理解）
2. 追问策略（只做追问和澄清，不提供方向性提示）
3. 困难应对方式（连续两次无法推进时，给出最轻微的提示）
4. 形成性评价模板"""
    elif level_id == "proximal":
        return f"""
【当前任务：为「最近发展区」学生配置智能体】
学生情况：{li['description']} — 追问 + 方向提示。
输出要求：生成该层级下的智能体对话配置，包括：
1. 开场引导语
2. 追问 + 方向提示策略（首次受阻时给出方向性建议）
3. 支架升级路径
4. 形成性评价模板"""
    elif level_id == "existing":
        return f"""
【当前任务：为「现有发展区」学生配置智能体】
学生情况：{li['description']} — 追问 + 步骤提示 + 类题示例。
输出要求：生成该层级下的智能体对话配置，包括：
1. 开场引导语
2. 追问 + 步骤提示 + 示例策略（在学生需要时可提供类似例题示范）
3. 支架升级路径
4. 形成性评价模板"""


def _zpd_instruction_collaborative(level_id: str, kp: str, li: dict) -> str:
    if level_id == "distal":
        return f"""
【当前任务：为「远端发展区」学生配置多智能体系统】
学生情况：{li['description']} — 需要5个角色完整协作。
输出要求：生成完整的五角色多智能体系统配置：
1. 五个智能体角色完整配置（问题澄清、证据质疑、方法指导、反思反馈、工作流编排）
2. 包含三个阶段完整工作流
3. 每个角色的介入时机、行为规则、话风特征"""
    elif level_id == "proximal":
        return f"""
【当前任务：为「最近发展区」学生配置多智能体系统】
学生情况：{li['description']} — 需要3个关键角色协作。
输出要求：生成精简的三角色多智能体系统配置：
1. 问题澄清 + 证据质疑 + 反思反馈（精简流程）
2. 两个阶段工作流（问题澄清 → 探究论证 → 总结反思）
3. 适度支架强度"""
    elif level_id == "existing":
        return f"""
【当前任务：为「现有发展区」学生配置多智能体系统】
学生情况：{li['description']} — 需要2个角色引导为主。
输出要求：生成双角色多智能体系统配置：
1. 问题澄清 + 反思反馈（以引导为主）
2. 简化工作流（以学生自主探究为主，智能体仅做关键节点引导）
3. 强调学生的自主性和创造性"""
