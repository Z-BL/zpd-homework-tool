"""
Flask 主应用 — 面向最近发展区的精准作业设计工具
"""

from flask import Flask, render_template, request, jsonify

from config import (
    KNOWLEDGE_POINTS,
    HOMEWORK_TYPES,
    ZPD_LEVELS,
    GRADE_LEVELS,
    SUBJECTS,
    get_homework_type,
    get_theory,
    get_knowledge_points
)
from prompt_builder import build_system_prompt, build_user_prompt
from llm_client import check_api_available
from homework_generator import generate_all_levels, regenerate_single_level

app = Flask(__name__)


# ============================================================
# 页面路由
# ============================================================
@app.route("/")
def index():
    """返回主页面"""
    return render_template("index.html")


# ============================================================
# API 路由
# ============================================================
@app.route("/api/config", methods=["GET"])
def api_config():
    """返回前端所需的所有配置数据"""
    # 将 tuple-keyed 的知识点字典转为 JSON 兼容格式
    kp_json = {}
    for (grade, subj), points in KNOWLEDGE_POINTS.items():
        kp_json[f"{grade}|{subj}"] = points

    return jsonify({
        "grade_levels": GRADE_LEVELS,
        "subjects": SUBJECTS,
        "knowledge_points": kp_json,
        "homework_types": HOMEWORK_TYPES,
        "zpd_levels": ZPD_LEVELS,
        "api_status": check_api_available()
    })


@app.route("/api/generate-prompt", methods=["POST"])
def api_generate_prompt():
    """
    Step 3→4：根据教师选择生成提示词（不调用 AI）
    请求体：
    {
        "grade_level": "初中",
        "subject": "数学",
        "knowledge_point": "一元二次方程应用",
        "homework_type": "potential_adaptive",
        "theory": "bloom",
        "supplement": { ... }
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "请求体不能为空"}), 400

    grade_level = data.get("grade_level", "")
    subject = data.get("subject", "")
    knowledge_point = data.get("knowledge_point", "")
    homework_type_id = data.get("homework_type", "")
    theory_id = data.get("theory", "")
    supplement = data.get("supplement", {})

    # 验证参数
    if not knowledge_point:
        return jsonify({"error": "请选择知识点"}), 400
    if not homework_type_id:
        return jsonify({"error": "请选择作业类型"}), 400
    if not theory_id:
        return jsonify({"error": "请选择理论框架"}), 400

    ht = get_homework_type(homework_type_id)
    theory = get_theory(homework_type_id, theory_id)
    if not ht:
        return jsonify({"error": f"无效的作业类型: {homework_type_id}"}), 400
    if not theory:
        return jsonify({"error": f"无效的理论: {theory_id}"}), 400

    # 构建提示词
    system_prompt = build_system_prompt(homework_type_id, theory_id)
    user_prompt = build_user_prompt(
        homework_type_id, theory_id, knowledge_point,
        grade_level, subject, supplement
    )

    return jsonify({
        "user_prompt": user_prompt,
        "system_prompt": system_prompt,
        "homework_type_name": ht["name"],
        "theory_name": theory["name"],
        "knowledge_point": knowledge_point
    })


@app.route("/api/generate-homework", methods=["POST"])
def api_generate_homework():
    """
    Step 4→5：调用 DeepSeek API 生成三层次作业
    请求体：
    {
        "knowledge_point": "...",
        "homework_type": "potential_adaptive",
        "theory": "bloom",
        "prompt": "（教师确认后的完整提示词）",
        "system_prompt": "..."
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "请求体不能为空"}), 400

    knowledge_point = data.get("knowledge_point", "")
    homework_type_id = data.get("homework_type", "")
    theory_id = data.get("theory", "")
    confirmed_prompt = data.get("prompt", "")

    if not confirmed_prompt:
        return jsonify({"error": "提示词不能为空"}), 400

    # 检查 API 可用性
    api_status = check_api_available()
    if not api_status["available"]:
        return jsonify({"error": api_status["message"]}), 500

    try:
        results = generate_all_levels(
            homework_type_id=homework_type_id,
            theory_id=theory_id,
            knowledge_point=knowledge_point,
            confirmed_prompt=confirmed_prompt
        )
        return jsonify({
            "homework": results,
            "knowledge_point": knowledge_point,
            "homework_type": homework_type_id,
            "theory": theory_id
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/regenerate-level", methods=["POST"])
def api_regenerate_level():
    """
    Step 5：单独重新生成某个 ZPD 层级
    请求体：
    {
        "knowledge_point": "...",
        "homework_type": "potential_adaptive",
        "theory": "bloom",
        "level": "proximal",
        "adjustment": "题目难度再提高一些...",
        "prompt": "（原始提示词）"
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "请求体不能为空"}), 400

    knowledge_point = data.get("knowledge_point", "")
    homework_type_id = data.get("homework_type", "")
    theory_id = data.get("theory", "")
    level_id = data.get("level", "")
    adjustment = data.get("adjustment", "")
    confirmed_prompt = data.get("prompt", "")

    if not level_id or level_id not in ZPD_LEVELS:
        return jsonify({"error": f"无效的层级: {level_id}"}), 400

    api_status = check_api_available()
    if not api_status["available"]:
        return jsonify({"error": api_status["message"]}), 500

    try:
        result = regenerate_single_level(
            homework_type_id=homework_type_id,
            theory_id=theory_id,
            knowledge_point=knowledge_point,
            level_id=level_id,
            confirmed_prompt=confirmed_prompt,
            adjustment=adjustment
        )
        return jsonify({"level": level_id, "result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/check-api", methods=["GET"])
def api_check():
    """检查 API Key 配置状态"""
    return jsonify(check_api_available())


# ============================================================
# 启动
# ============================================================
if __name__ == "__main__":
    import sys
    import os
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    port = int(os.environ.get("PORT", 5001))

    print("=" * 60)
    print("  [ZPD] 面向最近发展区的精准作业设计工具")
    print("=" * 60)
    api_status = check_api_available()
    if api_status["available"]:
        print(f"  [OK] {api_status['message']}")
    else:
        print(f"  [WARN] {api_status['message']}")
    print(f"  URL: http://localhost:{port}")
    print("=" * 60)
    app.run(debug=True, host="0.0.0.0", port=port)
