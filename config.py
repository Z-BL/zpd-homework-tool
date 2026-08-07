"""
配置模块：知识点、作业类型、理论框架、ZPD 层级规则
"""

# ============================================================
# 学段与学科
# ============================================================
GRADE_LEVELS = ["小学", "初中", "高中"]
SUBJECTS = ["数学"]  # 当前仅支持数学学科

# ============================================================
# 知识点（按学段+学科组织）
# ============================================================
# 当前仅配置初中数学的 41 个知识点
KNOWLEDGE_POINTS = {
    ("初中", "数学"): [
        "有理数", "实数", "整式及其加减", "整式的乘法", "因式分解",
        "分式", "二次根式", "一元一次方程", "二元一次方程组",
        "一元一次不等式（组）", "一元二次方程应用", "变量之间的关系",
        "一次函数", "二次函数", "反比例函数", "几何体", "线段", "角",
        "相交线", "平行线", "三角形", "等腰三角形", "直角三角形",
        "全等三角形", "尺规作图", "勾股定理", "平行四边形",
        "特殊平行四边形", "圆", "与圆有关的位置关系",
        "定义、命题、定理", "轴对称", "图形平移与旋转", "相似三角形",
        "解直角三角形", "投影", "平面直角坐标系", "抽样与数据分析",
        "统计", "概率", "其他知识点"
    ]
}


def get_knowledge_points(grade_level: str, subject: str) -> list:
    """根据学段和学科获取知识点列表"""
    return KNOWLEDGE_POINTS.get((grade_level, subject), [])

# ============================================================
# ZPD 三层级定义
# ============================================================
ZPD_LEVELS = {
    "distal": {
        "id": "distal",
        "label": "远端发展区",
        "description": "学生尚未具备的知识/技能，需要完整支架或较低难度入口",
        "icon": "🚀"
    },
    "proximal": {
        "id": "proximal",
        "label": "最近发展区",
        "description": "学生在适当支持下能够完成的任务，核心作业区域",
        "icon": "🎯"
    },
    "existing": {
        "id": "existing",
        "label": "现有发展区",
        "description": "学生已掌握的内容，需要巩固或向更高阶发展",
        "icon": "✅"
    }
}

# ============================================================
# 理论层级定义（用于潜能适配型作业的递进题目生成）
# ============================================================
THEORY_LEVELS = {
    "bloom": [
        {"id": "remember",   "name": "记忆",  "order": 1,
         "desc": "识别和再现所学知识——从记忆中提取事实、术语、基本概念"},
        {"id": "understand", "name": "理解",  "order": 2,
         "desc": "解释、归纳和推断信息——用自己的话表述，把握信息意义"},
        {"id": "apply",      "name": "应用",  "order": 3,
         "desc": "运用知识解决新问题——在陌生情境中使用已有方法"},
        {"id": "analyze",    "name": "分析",  "order": 4,
         "desc": "分解信息并建立关联——区分要素、识别关系、组织架构"},
        {"id": "evaluate",   "name": "评价",  "order": 5,
         "desc": "基于标准做出判断——评判合理性、检测逻辑谬误、比较方案"},
        {"id": "create",     "name": "创造",  "order": 6,
         "desc": "组合元素形成新结构——生成新方案、设计新模型、提出新观点"},
    ],
    "solo": [
        {"id": "prestructural",      "name": "前结构",   "order": 1,
         "desc": "无法理解问题，回答无意义——学生与问题之间尚未建立联系"},
        {"id": "unistructural",       "name": "单点结构", "order": 2,
         "desc": "仅涉及单一信息点——抓住一个线索就直接跳到结论"},
        {"id": "multistructural",     "name": "多点结构", "order": 3,
         "desc": "涉及多个独立信息点——能列举多个相关要点但未建立联系"},
        {"id": "relational",          "name": "关联结构", "order": 4,
         "desc": "建立信息间的逻辑联系——能整合多要点并说明因果关系"},
        {"id": "extended_abstract",   "name": "抽象扩展", "order": 5,
         "desc": "超越给定信息进行抽象思考——迁移到新情境，提出假设与推广"},
    ],
}


def get_theory_levels(theory_id: str) -> list:
    """获取指定理论的层级定义"""
    return THEORY_LEVELS.get(theory_id, [])


# ============================================================
# ZPD 区 → 理论层级映射（用于潜能适配型作业的分区生成）
# ============================================================
ZPD_TO_THEORY_MAPPING = {
    "bloom": {
        "distal": {
            "label": "远端发展区 — 基础入门",
            "student_profile": "得分率 < 0.3，尚未建立基本理解",
            "goal": "提供知识讲解和引导，帮助学生建立基本概念",
            "level_ids": ["remember", "understand"],
        },
        "proximal": {
            "label": "最近发展区 — 核心学习区",
            "student_profile": "得分率 0.3–0.7，在适当支持下能够完成",
            "goal": "在支架支持下逐步推进认知复杂度，实现认知跃迁",
            "level_ids": ["apply", "analyze"],
        },
        "existing": {
            "label": "现有发展区 — 拓展挑战",
            "student_profile": "得分率 ≥ 0.7，已掌握该知识点",
            "goal": "独立完成高阶认知任务，推动向更深层次发展",
            "level_ids": ["evaluate", "create"],
        },
    },
    "solo": {
        "distal": {
            "label": "远端发展区 — 基础入门",
            "student_profile": "得分率 < 0.3，尚未建立基本理解",
            "goal": "提供知识讲解和引导，帮助学生建立基本概念",
            "level_ids": ["prestructural", "unistructural"],
        },
        "proximal": {
            "label": "最近发展区 — 核心学习区",
            "student_profile": "得分率 0.3–0.7，在适当支持下能够完成",
            "goal": "在支架支持下逐步推进思维结构复杂度",
            "level_ids": ["multistructural", "relational"],
        },
        "existing": {
            "label": "现有发展区 — 拓展挑战",
            "student_profile": "得分率 ≥ 0.7，已掌握该知识点",
            "goal": "独立完成高阶思维任务，迁移到新情境",
            "level_ids": ["extended_abstract"],
        },
    },
}


def get_zpd_theory_mapping(theory_id: str) -> dict:
    """获取指定理论的 ZPD 区映射"""
    return ZPD_TO_THEORY_MAPPING.get(theory_id, {})


# ============================================================
# 认知支架阶段定义（用于认知支持型作业）
# ============================================================
COGNITIVE_STAGES = {
    "polya": [
        {"id": "understand", "name": "理解问题", "order": 1,
         "desc": "分析题意，明确已知未知"},
        {"id": "plan", "name": "制订计划", "order": 2,
         "desc": "确定解题策略和步骤"},
        {"id": "execute", "name": "执行计划", "order": 3,
         "desc": "按计划逐步完成计算"},
        {"id": "reflect", "name": "回顾反思", "order": 4,
         "desc": "检验结果，总结方法"},
    ],
    "toulmin": [
        {"id": "claim", "name": "主张", "order": 1,
         "desc": "明确要证明的结论"},
        {"id": "evidence", "name": "证据", "order": 2,
         "desc": "收集支撑结论的数据"},
        {"id": "reasoning", "name": "推理", "order": 3,
         "desc": "从证据推导到结论的逻辑链"},
        {"id": "support", "name": "支持", "order": 4,
         "desc": "引用定理、公式作为依据"},
        {"id": "rebuttal", "name": "反驳", "order": 5,
         "desc": "检验论证是否存在漏洞"},
        {"id": "qualifier", "name": "限定词", "order": 6,
         "desc": "明确结论的适用条件和边界"},
    ],
}

# ZPD 三区支架风格
ZPD_SCAFFOLD_TYPES = {
    "distal": {
        "label": "远端发展区",
        "icon": "🚀",
        "style": "知识讲解型",
        "desc": "提供完整概念讲解和基础引导，帮助学生理解题意",
    },
    "proximal": {
        "label": "最近发展区",
        "icon": "🎯",
        "style": "逻辑帮助型",
        "desc": "提供逻辑推理线索和方向性提示，不直接给出答案",
    },
    "existing": {
        "label": "现有发展区",
        "icon": "✅",
        "style": "扩展思考型",
        "desc": "提供开放性问题，引导独立思考和知识迁移",
    },
}


def get_cognitive_stages(theory_id: str) -> list:
    """获取认知阶段的定义"""
    return COGNITIVE_STAGES.get(theory_id, [])


def get_zpd_scaffold_types() -> dict:
    """获取 ZPD 支架风格"""
    return ZPD_SCAFFOLD_TYPES


# ============================================================
# 动态交互型 × ZPD 对话风格（第三种作业）
# ============================================================
DIALOGUE_STYLES = {
    "distal": {
        "label": "远端发展区",
        "icon": "🚀",
        "style": "教学式引导",
        "description": "先讲解再提问，以建立信心为主",
        "strategy": "先简要讲解概念（约 80 字），再提出一个基础问题。连续 1 次回答不上就给出答案和讲解。",
        "max_stuck": 1,
    },
    "proximal": {
        "label": "最近发展区",
        "icon": "🎯",
        "style": "苏格拉底追问",
        "description": "追问→澄清→方向提示，支架逐步升级",
        "strategy": "优先追问和澄清，不直接讲解。连续 2 次卡住才给方向性提示，连续 3 次卡住才给步骤答案。",
        "max_stuck": 2,
    },
    "existing": {
        "label": "现有发展区",
        "icon": "✅",
        "style": "挑战式对话",
        "description": "反问+拓展，减少提示，鼓励独立思考",
        "strategy": "以反问和拓展问题为主，最少限度给提示。连续 3 次卡住才给方向性提示。引导学生自己发现答案。",
        "max_stuck": 3,
    },
}

# ============================================================
# 协作探究型 × ZPD 角色分配（第四种作业）
# ============================================================
INQUIRY_ROLES = {
    "distal": {
        "label": "远端发展区",
        "icon": "🚀",
        "style": "讲解式探究",
        "description": "2 角色引导，讲解为主",
        "roles": [
            {"name": "问题澄清智能体", "desc": "帮助学生明确问题，拆解为可操作的子问题"},
            {"name": "方法指导智能体", "desc": "提供探究方法和思维工具指导"},
        ],
        "stages": [
            {"name": "讲解式探究", "desc": "智能体主动讲解背景知识 → 引导拆解问题 → 示范建模方法"},
        ],
    },
    "proximal": {
        "label": "最近发展区",
        "icon": "🎯",
        "style": "引导式探究",
        "description": "3 角色协作，支架支持",
        "roles": [
            {"name": "问题澄清智能体", "desc": "帮助学生明确问题，拆解为可操作的子问题"},
            {"name": "证据收集与质疑智能体", "desc": "引导寻找证据，对薄弱环节提出质疑"},
            {"name": "反思反馈智能体", "desc": "汇总过程数据，生成综合评价"},
        ],
        "stages": [
            {"name": "问题澄清", "desc": "引导重述问题 → 识别已知/未知 → 拆解子问题"},
            {"name": "探究与论证", "desc": "形成观点 → 证据检验 → 方法支持 → 循环迭代"},
        ],
    },
    "existing": {
        "label": "现有发展区",
        "icon": "✅",
        "style": "自主式探究",
        "description": "5 角色完整配置，学生自主为主",
        "roles": [
            {"name": "问题澄清智能体", "desc": "帮助学生明确问题，拆解为可操作的子问题"},
            {"name": "证据收集与质疑智能体", "desc": "引导寻找证据，对薄弱环节提出质疑"},
            {"name": "方法指导智能体", "desc": "提供探究方法和思维工具指导"},
            {"name": "反思反馈智能体", "desc": "汇总过程数据，生成综合评价报告"},
            {"name": "工作流编排智能体", "desc": "根据学生所处阶段调度对应角色"},
        ],
        "stages": [
            {"name": "问题澄清", "desc": "引导重述问题 → 识别已知/未知 → 拆解子问题"},
            {"name": "探究与论证", "desc": "形成观点 → 证据检验 → 方法支持 → 循环迭代"},
            {"name": "总结与反思", "desc": "汇总交互数据 → 综合评价报告 → 反思对话"},
        ],
    },
}


def get_dialogue_styles() -> dict:
    """获取 ZPD 对话风格"""
    return DIALOGUE_STYLES


def get_inquiry_roles() -> dict:
    """获取 ZPD 探究角色"""
    return INQUIRY_ROLES


# ============================================================
# 四种作业类型配置
# ============================================================
HOMEWORK_TYPES = [
    {
        "id": "potential_adaptive",
        "name": "潜能适配型作业",
        "short_name": "潜能适配型",
        "description": "分析学情基础，生成递进任务序列。基于学生先前学习数据，"
                       "在三个发展区生成由浅入深、前后衔接的作业任务。",
        "output_form": "递进题目序列（纸质/在线作业单）",
        "theories": [
            {"id": "bloom", "name": "布卢姆认知目标分类",
             "desc": "将认知过程分为记忆、理解、应用、分析、评价、创造六个层次"},
            {"id": "solo", "name": "SOLO分类理论",
             "desc": "将学习成果分为前结构、单点结构、多点结构、关联结构、抽象扩展结构"}
        ],
        "supplement_fields": [
            {"key": "original_question", "label": "作业原题目", "type": "textarea",
             "placeholder": "请输入本次作业的原题目，如：某工厂今年1月份产值为50万元..."},
            {"key": "teaching_goal", "label": "教学目标", "type": "textarea",
             "placeholder": "如：能够根据实际问题建立一元二次方程模型并求解"},
            {"key": "student_data", "label": "学生学情数据", "type": "textarea",
             "placeholder": "描述学生的先前学习数据，如测验成绩分布、常见错误等。\n"
                            "如：班级平均分75，其中85分以上12人，60-85分20人，60分以下8人..."}
        ]
    },
    {
        "id": "cognitive_support",
        "name": "认知支持型作业",
        "short_name": "认知支持型",
        "description": "识别学生认知困难环节，配置步骤化支架引导。"
                       "在解题过程中嵌入问题式、示例式、讲解式支架。",
        "output_form": "题干 + 步骤支架 + 反思问题（纸质/在线作业单）",
        "theories": [
            {"id": "polya", "name": "波利亚解题理论",
             "desc": "四阶段：理解问题 → 制订计划 → 执行计划 → 回顾反思"},
            {"id": "toulmin", "name": "图尔敏论证模型",
             "desc": "论证六要素：主张、证据、推理、支持、反驳、限定词"}
        ],
        "supplement_fields": [
            {"key": "original_question", "label": "作业原始题目", "type": "textarea",
             "placeholder": "请输入本次作业的原始题目"},
            {"key": "cognitive_difficulty", "label": "学生典型认知困难", "type": "textarea",
             "placeholder": "描述学生在解题过程中的典型错误、未完成步骤或解释偏差。\n"
                            "如：学生在理解题意时容易忽略隐含条件；执行计算步骤时容易出错..."}
        ]
    },
    {
        "id": "dynamic_interactive",
        "name": "动态交互型作业",
        "short_name": "动态交互型",
        "description": "单智能体形式，面向每名学生开展持续对话辅导。"
                       "依据学生对话表现即时调整追问和提示策略。",
        "output_form": "智能体配置 + 对话规则（智能体链接/平台部署）",
        "theories": [
            {"id": "socratic", "name": "苏格拉底启发式学习",
             "desc": "通过追问、澄清、反诘引导学生自己发现答案"}
        ],
        "supplement_fields": [
            {"key": "original_question", "label": "作业原题目", "type": "textarea",
             "placeholder": "请输入学生要完成的具体作业题目和支架方案"},
            {"key": "teaching_goal", "label": "教学目标", "type": "textarea",
             "placeholder": "如：通过完成这道题，希望学生能够掌握二次方程的建模方法，"
                          "重点发展学生的数学建模能力和方程求解能力"}
        ]
    },
    {
        "id": "collaborative_inquiry",
        "name": "协作探究型作业",
        "short_name": "协作探究型",
        "description": "多智能体协作方式，为学生推进探究任务提供多角色'他者'支持。"
                       "5个专业智能体角色各司其职，协同引导学生完成探究。",
        "output_form": "多智能体角色配置 + 工作流（智能体链接/平台部署）",
        "theories": [
            {"id": "inquiry", "name": "探究式学习理论",
             "desc": "学生通过提出问题→收集证据→形成解释→评价反思→交流发表的循环推进探究"}
        ],
        "supplement_fields": [
            {"key": "inquiry_theme", "label": "探究主题", "type": "text",
             "placeholder": "如：校园绿化面积的数学建模与优化方案"},
            {"key": "task_context", "label": "任务情境", "type": "textarea",
             "placeholder": "描述任务背景、角色设定、待解决的真实问题。\n"
                            "如：学校计划扩建操场，现有预算50万元..."},
            {"key": "expected_output", "label": "预期成果形式", "type": "text",
             "placeholder": "如：实验报告、论证文章、方案设计、口头报告等"},
            {"key": "student_performance", "label": "学生已有表现/学情", "type": "textarea",
             "placeholder": "学生的前备知识、已有能力水平、可能的困难点"}
        ]
    }
]

# ============================================================
# 帮助函数
# ============================================================
def get_homework_type(type_id: str) -> dict | None:
    """根据 id 获取作业类型配置"""
    for ht in HOMEWORK_TYPES:
        if ht["id"] == type_id:
            return ht
    return None


def get_theory(homework_type_id: str, theory_id: str) -> dict | None:
    """获取指定作业类型下的理论配置"""
    ht = get_homework_type(homework_type_id)
    if ht:
        for t in ht["theories"]:
            if t["id"] == theory_id:
                return t
    return None


def get_zpd_level(level_id: str) -> dict | None:
    """获取 ZPD 层级配置"""
    return ZPD_LEVELS.get(level_id)
