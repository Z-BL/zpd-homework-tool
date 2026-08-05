"""
提示词构建模块：根据作业类型填充提示词模板
"""

from config import get_homework_type, get_theory


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
    original_question = s.get("original_question", "【未填写】")
    teaching_goal = s.get("teaching_goal", "【未填写】")
    student_data = s.get("student_data", "【未填写】")

    return f"""我是{grade}{subject}的老师，正在设计一份基于最近发展区的精准作业。

作业原题目是：
{original_question}

知识点是：{knowledge_point}

教学目标：{teaching_goal}

学生学情数据：
{student_data}

请依据最近发展区理论和{theory['name']}完成以下任务：

1. 判断学生得分情况，按照掌握程度划分为三个层级：
   - 现有发展区（已掌握，得分率 0.7-1.0）
   - 最近发展区（需支持，得分率 0.3-0.7）
   - 远端发展区（未掌握，得分率 0-0.3）

2. 对于该知识点「{knowledge_point}」，请分别为三个发展区生成作业：
   - 为**现有发展区**学生：出 3 道后继知识的题目（即下一步可以学什么），题目应具有挑战性，推动学生向更高层次发展
   - 为**最近发展区**学生：出当前知识点下的认知进阶类题目（认知复杂度递进的一组题，3 道），由易到难排列
   - 为**远端发展区**学生：先呈现当前知识点的简要知识讲解，再出 1 道该知识点最基础的题目

3. 认知进阶依据{theory['name']}设计，确保题目难度有清晰的认知层级递进。

4. 三个区间作业的具体比例可根据学情灵活调整，现有发展区和最近发展区原则上应占据主体。"""


def _build_cognitive_support_prompt(
    knowledge_point: str, theory: dict, grade: str,
    subject: str, s: dict
) -> str:
    original_question = s.get("original_question", "【未填写】")
    cognitive_difficulty = s.get("cognitive_difficulty", "【未填写】")

    theory_name = theory['name']
    theory_desc = theory.get('desc', '')

    return f"""我是{grade}{subject}的老师，我正在将一项最近发展区内的作业设计为"支架型作业"。

作业原始题目是：
{original_question}

所属知识点为：{knowledge_point}

学生典型认知困难：
{cognitive_difficulty}

请基于「{theory_name}」（{theory_desc}）设计支架。

要求：
1. 保持原作业任务的核心目标不降低
2. 不直接给出答案，而是将解题步骤拆解为「{theory_name}」的步骤，给学生提供引导性支架
3. 支架设计应保留必要的思考空间，避免直接呈现完整解答
4. 支架形态可包括：问题式（启发性提问）、示例式（类题示范）、讲解式（概念/方法说明）
5. 最后要设计一个反思问题，帮助学生从元认知层面总结方法

请按以下格式输出：
- 题干
- 步骤支架（每个步骤包含：支架引导语 + 支架答案/提示）
- 反思问题"""


def _build_dynamic_interactive_prompt(
    knowledge_point: str, theory: dict, grade: str,
    subject: str, s: dict
) -> str:
    homework_topic = s.get("homework_topic", "【未填写】")
    teaching_goal = s.get("teaching_goal", "【未填写】")

    theory_name = theory['name']

    return f"""你是一名"最近发展区作业导师"，面向中学生开展一对一作业辅导。

---

【作业题目】
{homework_topic}

【学科与年级】
{grade}{subject}

【本题的教学目标】
{teaching_goal}

---

你的任务不是直接告诉学生答案，而是根据学生回答判断其理解状态，并依据「{theory_name}」进行引导。你需要结合追问、澄清、提示、示例和反思，引导学生在最近发展区内完成作业。

---

【对话规则】

1. 先请学生说出自己对题目的理解或初步思路。
2. 每次只提出一个问题或一个提示。
3. 优先使用追问、澄清和方向性提示，而不是直接讲解。
4. 当学生连续两次无法推进时，再给出该步骤支架的答案。
5. 发现学生依赖AI索要答案时，提醒其先表达自己的想法。
6. 不直接输出完整答案，不一次性给出所有支架，不替学生完成全部思考过程。
7. 学生完成后，要求其用自己的话总结方法，并输出形成性评价。

---

【支架升级规则】

1. 如果学生能够表达基本思路，只使用追问和澄清。
2. 如果学生理解题意但没有方法，进入"方向提示"级别。
3. 如果学生有方法但执行受阻，进入"步骤提示"级别。
4. 如果学生完成任务但不能解释理由，进入"反思引导"级别。
5. 如果学生连续两次回答"不会""不知道"或明显偏离方向，可以升级一级支架。
6. 每次只升级一级，不要一次性提供完整解法。

---

【形成性评价格式】

对话结束后，请生成一份形成性评价，包括：
1. 学生已经能够做到：
2. 学生主要困难在于：
3. 本次经历的引导阶段：
4. 本次使用过的支架：
5. 学生思路发生的变化：
6. 下一步建议完成的作业或练习：
7. 给学生的一句学习建议："""


def _build_collaborative_inquiry_prompt(
    knowledge_point: str, theory: dict, grade: str,
    subject: str, s: dict
) -> str:
    inquiry_theme = s.get("inquiry_theme", "【未填写】")
    task_context = s.get("task_context", "【未填写】")
    expected_output = s.get("expected_output", "【未填写】")
    student_performance = s.get("student_performance", "【未填写】")

    return f"""你是一个"协作探究作业编排系统"，面向中学生开展多智能体协作的探究式作业辅导。
本系统包含多个专业智能体角色，各司其职，协同工作，帮助学生在最近发展区内完成探究任务。

---

【探究任务信息】

探究主题：{inquiry_theme}

学科与年级：{grade}{subject}

学习目标：围绕「{knowledge_point}」知识点，培养学生的探究能力和综合素养

任务情境：{task_context}

预期成果形式：{expected_output}

学生已有表现/学情：{student_performance}

---

你的任务不是直接给出探究结论，而是通过编排多个专业智能体角色，在探究式学习理论、科学论证理论和协作学习理论的指导下，为学生提供多维度的"他者"支持，帮助学生在最近发展区内完成探究任务。

---

【五个智能体角色】

角色一：问题澄清智能体 — 帮助学生明确探究问题，拆解复杂问题为可操作的子问题
角色二：证据收集与质疑智能体 — 引导学生寻找证据支持主张，对薄弱环节提出质疑
角色三：方法指导智能体 — 提供探究方法和思维工具的指导
角色四：反思反馈智能体 — 汇总过程数据，生成综合评价报告
角色五（协调者）：工作流编排智能体 — 根据学生所处阶段调度对应角色

---

【协作工作流】

第一阶段：问题澄清（由问题澄清智能体主导）
- 呈现探究任务情境 → 引导重述问题 → 识别已知/未知 → 拆解子问题

第二阶段：探究与论证（证据质疑 + 方法指导协同）
- 形成初步观点 → 证据检验 → 方法支持 → 收集完善 → 再次检验（循环迭代）

第三阶段：总结与反思（由反思反馈智能体主导）
- 汇总交互数据 → 生成综合评价报告 → 反思对话

---

【行为边界与升级规则】

1. 所有智能体均不直接给出探究结论或完整答案
2. 支持强度由弱到强：先启发 → 再提示 → 再示例 → 最后讲解
3. 每次交互聚焦一个关键问题
4. 学生在某阶段自主推进顺利时，减少干预
5. 学生连续两次在同一问题上受阻时，升级支持强度"""


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
    if level_id == "distal":
        return f"""
【当前任务：为「远端发展区」学生生成作业】
学生情况：{li['description']} — 该学生对「{kp}」尚未建立基本理解。
输出要求：
1. 先提供一个简短的「{kp}」知识讲解（约150-200字），帮助学生建立基本概念
2. 然后出 1 道最基础的题目，确保学生能够独立完成
3. 题目难度应为基础入门级别，建立学生信心"""
    elif level_id == "proximal":
        return f"""
【当前任务：为「最近发展区」学生生成作业】
学生情况：{li['description']} — 该学生对「{kp}」有一定理解但需支持。
输出要求：
1. 出 3 道认知复杂度递进的题目（由易到难排列）
2. 题目的认知层级应有清晰递进，从记忆/理解到应用/分析
3. 每道题标注其对应的认知层级
4. 题目之间应有内容上的衔接关系"""
    elif level_id == "existing":
        return f"""
【当前任务：为「现有发展区」学生生成作业】
学生情况：{li['description']} — 该学生对「{kp}」已掌握。
输出要求：
1. 出 3 道后继知识/拓展类的题目
2. 题目应具有挑战性，推动学生向更高层次发展
3. 可涉及「{kp}」与其他知识点的综合应用
4. 题目难度应有区分度"""


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
