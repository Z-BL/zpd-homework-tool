/**
 * app.js — 面向最近发展区的精准作业设计工具
 * 5 步向导交互逻辑
 */

// ============================================================
// 全局状态
// ============================================================
const state = {
    currentStep: 1,
    config: null,
    gradeLevel: "初中",    // 学段（Step 1 选择）
    subject: "数学",       // 学科（Step 1 选择）
    selectedKp: null,
    selectedType: null,
    selectedTheory: null,
    confirmedPrompt: null,
    systemPrompt: null,
    homeworkResults: null,
    editedContents: {}     // level_id -> edited text
};

// ============================================================
// 初始化
// ============================================================
document.addEventListener("DOMContentLoaded", async () => {
    await loadConfig();
    renderStep1();
    updateStepIndicator();
    updateButtons();
    bindEvents();
});

async function loadConfig() {
    try {
        const res = await fetch("/api/config");
        state.config = await res.json();
        updateApiBadge(state.config.api_status);
    } catch (e) {
        console.error("Failed to load config:", e);
        updateApiBadge({ available: false, message: "无法连接服务器" });
    }
}

function updateApiBadge(apiStatus) {
    const dot = document.querySelector(".api-dot");
    const text = document.getElementById("apiBadgeText");
    if (apiStatus && apiStatus.available) {
        dot.className = "api-dot connected";
        text.textContent = "DeepSeek API 已就绪";
    } else {
        dot.className = "api-dot disconnected";
        text.textContent = apiStatus ? apiStatus.message : "API 未配置";
    }
}

// ============================================================
// 步骤导航
// ============================================================
function bindEvents() {
    document.getElementById("btnNext").addEventListener("click", goNext);
    document.getElementById("btnPrev").addEventListener("click", goPrev);
    document.getElementById("kpSearch").addEventListener("input", filterKp);
    document.getElementById("theorySelect").addEventListener("change", onTheoryChange);
    document.getElementById("btnGeneratePrompt").addEventListener("click", generatePrompt);
    document.getElementById("btnGenerateHomework").addEventListener("click", generateHomework);

    // Step indicator clicks
    document.querySelectorAll(".step").forEach(el => {
        el.addEventListener("click", () => {
            const step = parseInt(el.dataset.step);
            if (step <= state.currentStep || isStepCompleted(step - 1)) {
                goToStep(step);
            }
        });
    });
}

function goToStep(step) {
    // 对话类型最多 6 步，其他最多 5 步
    const maxStep = (state.selectedType === "dynamic_interactive" || state.selectedType === "collaborative_inquiry") ? 6 : 5;
    if (step < 1 || step > maxStep) return;

    // 进入 Step 3 前检查
    if (step >= 3 && !state.selectedKp) {
        alert("请先在 Step 1 中选择知识点");
        goToStep(1);
        return;
    }
    if (step >= 3 && !state.selectedType) {
        alert("请先在 Step 2 中选择作业类型");
        goToStep(2);
        return;
    }

    // 渲染目标步骤
    state.currentStep = step;
    if (step === 2) renderStep2();
    if (step === 3) renderStep3();
    if (step === 4) renderStep4();
    if (step === 5) renderStep5();
    if (step === 6) initChatPage();

    // 更新 UI
    document.querySelectorAll(".step-panel").forEach(p => p.classList.remove("active"));
    document.getElementById("step" + step).classList.add("active");
    updateStepIndicator();
    updateButtons();
}

function goNext() {
    if (!validateCurrentStep()) return;
    const maxStep = (state.selectedType === "dynamic_interactive" || state.selectedType === "collaborative_inquiry") ? 6 : 5;
    if (state.currentStep < maxStep) {
        goToStep(state.currentStep + 1);
    }
}

function goPrev() {
    if (state.currentStep > 1) {
        goToStep(state.currentStep - 1);
    }
}

function isStepCompleted(step) {
    switch (step) {
        case 1: return !!state.selectedKp;
        case 2: return !!state.selectedType;
        case 3: return !!state.selectedTheory;
        case 4: return !!state.confirmedPrompt;
        case 5: return !!state.homeworkResults;
        default: return true;
    }
}

function validateCurrentStep() {
    switch (state.currentStep) {
        case 1:
            if (!state.selectedKp) {
                alert("请先选择一个知识点");
                return false;
            }
            return true;
        case 2:
            if (!state.selectedType) {
                alert("请先选择一种作业类型");
                return false;
            }
            return true;
        case 3: {
            const theory = document.getElementById("theorySelect").value;
            if (!theory) {
                alert("请先选择理论框架");
                return false;
            }
            state.selectedTheory = theory;
            // 收集补充字段
            const supplement = {};
            document.querySelectorAll("#supplementFields input, #supplementFields textarea").forEach(el => {
                supplement[el.name] = el.value;
            });
            state.supplement = supplement;
            return true;
        }
        case 4:
            if (!state.confirmedPrompt) {
                alert("请先生成提示词");
                return false;
            }
            // 检测提示词是否被修改，若修改则清空作业
            const newPrompt = document.getElementById("userPromptText").value;
            if (newPrompt !== state.confirmedPrompt) {
                state.homeworkResults = null;
                state.editedContents = {};
            }
            state.confirmedPrompt = newPrompt;
            return true;
        case 5:
            return true;
        default:
            return true;
    }
}

function updateStepIndicator() {
    document.querySelectorAll(".step").forEach(el => {
        const step = parseInt(el.dataset.step);
        el.classList.remove("active", "completed");
        if (step === state.currentStep) {
            el.classList.add("active");
        } else if (step < state.currentStep) {
            el.classList.add("completed");
        }
    });
}

function updateButtons() {
    const btnPrev = document.getElementById("btnPrev");
    const btnNext = document.getElementById("btnNext");

    btnPrev.style.display = state.currentStep > 1 ? "inline-block" : "none";

    const isDialogue = state.selectedType === "dynamic_interactive" || state.selectedType === "collaborative_inquiry";

    if (state.currentStep === 6) {
        btnNext.style.display = "none";
    } else if (state.currentStep === 5 && isDialogue) {
        btnNext.textContent = "💬 开始对话 →";
        btnNext.style.display = "inline-block";
    } else if (state.currentStep === 5) {
        btnNext.textContent = "✅ 完成";
        btnNext.style.display = "inline-block";
    } else {
        btnNext.textContent = "下一步 →";
        btnNext.style.display = "inline-block";
    }
}

// ============================================================
// 下游数据清除
// ============================================================
function clearDownstream(step) {
    // step: 当前被修改的步骤号，清除该步骤及之后的所有数据
    if (step <= 1) {
        state.selectedKp = null;
        state.selectedType = null;
        state.selectedTheory = null;
        state.confirmedPrompt = null;
        state.systemPrompt = null;
        state.homeworkResults = null;
        state.editedContents = {};
        state.supplement = {};
        disableGeneratePromptBtn();
    } else if (step <= 2) {
        state.selectedType = null;
        state.selectedTheory = null;
        state.confirmedPrompt = null;
        state.systemPrompt = null;
        state.homeworkResults = null;
        state.editedContents = {};
        state.supplement = {};
        disableGeneratePromptBtn();
    } else if (step <= 3) {
        state.selectedTheory = null;
        state.confirmedPrompt = null;
        state.systemPrompt = null;
        state.homeworkResults = null;
        state.editedContents = {};
        state.supplement = {};
        disableGeneratePromptBtn();
    } else if (step <= 4) {
        state.confirmedPrompt = null;
        state.systemPrompt = null;
        state.homeworkResults = null;
        state.editedContents = {};
        state.chatData = null;
    }
}

function disableGeneratePromptBtn() {
    const btn = document.getElementById("btnGeneratePrompt");
    if (btn) {
        btn.disabled = true;
        btn.textContent = "✨ 生成提示词";
    }
}

// ============================================================
// Step 1: 学段/学科/知识点选择
// ============================================================
function renderStep1() {
    // 先注入学段和学科选择器（在搜索框上方）
    const step1 = document.getElementById("step1");
    let selectorRow = document.getElementById("gradeSubjectRow");
    if (!selectorRow) {
        selectorRow = document.createElement("div");
        selectorRow.id = "gradeSubjectRow";
        selectorRow.className = "grade-subject-row";
        const searchBox = step1.querySelector(".search-box");
        searchBox.parentNode.insertBefore(selectorRow, searchBox);
    }
    selectorRow.innerHTML = `
        <div class="selector-group">
            <label>学段</label>
            <select id="gradeLevelSelect">
                ${state.config.grade_levels.map(g =>
                    `<option value="${g}" ${g === state.gradeLevel ? 'selected' : ''}>${g}</option>`
                ).join("")}
            </select>
        </div>
        <div class="selector-group">
            <label>学科</label>
            <select id="subjectSelect">
                ${state.config.subjects.map(s =>
                    `<option value="${s}" ${s === state.subject ? 'selected' : ''}>${s}</option>`
                ).join("")}
            </select>
        </div>
    `;

    document.getElementById("gradeLevelSelect").addEventListener("change", (e) => {
        state.gradeLevel = e.target.value;
        state.selectedKp = null;
        renderKnowledgePointGrid();
    });
    document.getElementById("subjectSelect").addEventListener("change", (e) => {
        state.subject = e.target.value;
        state.selectedKp = null;
        renderKnowledgePointGrid();
    });

    renderKnowledgePointGrid();
}

function renderKnowledgePointGrid() {
    const grid = document.getElementById("kpGrid");

    // 从 config 中获取对应学段+学科的知识点
    let points = [];
    if (state.config.knowledge_points) {
        const key = `${state.gradeLevel}|${state.subject}`;
        points = state.config.knowledge_points[key] || [];
    }

    if (points.length === 0) {
        grid.innerHTML = `<div class="no-kp-msg">
            暂未收录「${state.gradeLevel}${state.subject}」的知识点，敬请期待
        </div>`;
    } else {
        grid.innerHTML = points.map(kp =>
            `<div class="kp-card${kp === state.selectedKp ? ' selected' : ''}" data-kp="${escapeHtml(kp)}" onclick="selectKp(this, '${escapeJs(kp)}')">${escapeHtml(kp)}</div>`
        ).join("");
    }

    if (state.selectedKp) {
        document.getElementById("kpSelectedName").textContent = state.selectedKp;
        document.getElementById("kpSelected").style.display = "block";
    } else {
        document.getElementById("kpSelected").style.display = "none";
    }
}

function filterKp() {
    const query = document.getElementById("kpSearch").value.toLowerCase();
    document.querySelectorAll(".kp-card").forEach(card => {
        const text = card.textContent.toLowerCase();
        card.style.display = text.includes(query) ? "" : "none";
    });
}

function selectKp(el, kp) {
    const changed = state.selectedKp !== kp;
    document.querySelectorAll(".kp-card").forEach(c => c.classList.remove("selected"));
    el.classList.add("selected");
    state.selectedKp = kp;
    document.getElementById("kpSelectedName").textContent = kp;
    document.getElementById("kpSelected").style.display = "block";
    if (changed) {
        clearDownstream(2);
    }
}

// ============================================================
// Step 2: 作业类型选择
// ============================================================
function renderStep2() {
    const container = document.getElementById("typeCards");
    const types = state.config.homework_types;

    container.innerHTML = types.map(ht => `
        <div class="type-card" data-type="${ht.id}" onclick="selectType('${ht.id}')">
            <div class="type-name">${escapeHtml(ht.name)}</div>
            <div class="type-desc">${escapeHtml(ht.description)}</div>
            <span class="type-output">📤 ${escapeHtml(ht.output_form)}</span>
        </div>
    `).join("");

    if (state.selectedType) {
        const card = container.querySelector(`[data-type="${state.selectedType}"]`);
        if (card) card.classList.add("selected");
    }
}

function selectType(typeId) {
    const changed = state.selectedType !== typeId;
    document.querySelectorAll(".type-card").forEach(c => c.classList.remove("selected"));
    const card = document.querySelector(`[data-type="${typeId}"]`);
    if (card) card.classList.add("selected");
    state.selectedType = typeId;
    if (changed) {
        clearDownstream(3);
    }
}

// ============================================================
// Step 3: 理论与补充信息
// ============================================================
function renderStep3() {
    const ht = state.config.homework_types.find(t => t.id === state.selectedType);
    if (!ht) return;

    document.getElementById("step3TypeName").textContent =
        `当前作业类型：${ht.name}`;

    // 理论选择
    const theorySelect = document.getElementById("theorySelect");
    theorySelect.innerHTML = '<option value="">-- 请选择理论 --</option>' +
        ht.theories.map(t => `<option value="${t.id}">${t.name} — ${t.desc}</option>`).join("");

    if (state.selectedTheory) {
        theorySelect.value = state.selectedTheory;
        renderSupplementFields(ht);
    }

    // 补充字段
    renderSupplementFields(ht);
}

function onTheoryChange() {
    const newTheory = document.getElementById("theorySelect").value;
    const changed = state.selectedTheory !== newTheory;
    state.selectedTheory = newTheory;
    if (changed && newTheory) {
        clearDownstream(4);
    }
    const ht = state.config.homework_types.find(t => t.id === state.selectedType);
    if (ht) {
        const theory = ht.theories.find(t => t.id === state.selectedTheory);
        document.getElementById("theoryHint").textContent = theory ? theory.desc : "";
        renderSupplementFields(ht);
    }
}

function renderSupplementFields(ht) {
    const container = document.getElementById("supplementFields");
    const saved = state.supplement || {};

    container.innerHTML = ht.supplement_fields.map(f => `
        <div class="form-group">
            <label for="field_${f.key}">${escapeHtml(f.label)}</label>
            ${f.type === 'textarea'
                ? `<textarea id="field_${f.key}" name="${f.key}" placeholder="${escapeHtml(f.placeholder)}">${escapeHtml(saved[f.key] || '')}</textarea>`
                : `<input type="text" id="field_${f.key}" name="${f.key}" placeholder="${escapeHtml(f.placeholder)}" value="${escapeHtml(saved[f.key] || '')}">`
            }
        </div>
    `).join("");
}

// ============================================================
// Step 4: 提示词生成
// ============================================================
function renderStep4() {
    const userPromptEl = document.getElementById("userPromptText");
    const systemPromptEl = document.getElementById("systemPromptText");
    const promptInfoEl = document.getElementById("promptInfo");
    const promptMetaEl = document.getElementById("promptMeta");
    const btn = document.getElementById("btnGeneratePrompt");

    if (state.confirmedPrompt) {
        // 已有提示词，回显内容
        userPromptEl.value = state.confirmedPrompt;
        systemPromptEl.value = state.systemPrompt || "";
        btn.textContent = "✅ 提示词已生成（可在左侧编辑）";
        btn.disabled = false;
    } else {
        // 无提示词，清空面板
        userPromptEl.value = "";
        systemPromptEl.value = "";
        promptInfoEl.textContent = "";
        promptMetaEl.textContent = "";
        btn.textContent = "✨ 生成提示词";
        btn.disabled = !state.selectedTheory;
    }
}

async function generatePrompt() {
    if (!state.selectedKp || !state.selectedType || !state.selectedTheory) {
        alert("请先完成前三个步骤");
        return;
    }

    // 收集补充信息
    const supplement = {};
    document.querySelectorAll("#supplementFields input, #supplementFields textarea").forEach(el => {
        supplement[el.name] = el.value;
    });

    // 生成新提示词前清空旧作业（因为提示词变了，旧作业已过时）
    state.homeworkResults = null;
    state.editedContents = {};

    const btn = document.getElementById("btnGeneratePrompt");
    btn.disabled = true;
    btn.textContent = "⏳ 生成中...";

    try {
        const res = await fetch("/api/generate-prompt", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                grade_level: state.gradeLevel,
                subject: state.subject,
                knowledge_point: state.selectedKp,
                homework_type: state.selectedType,
                theory: state.selectedTheory,
                supplement: supplement
            })
        });

        const data = await res.json();
        if (data.error) {
            alert("生成失败：" + data.error);
            return;
        }

        document.getElementById("userPromptText").value = data.user_prompt;
        document.getElementById("systemPromptText").value = data.system_prompt;
        document.getElementById("promptInfo").textContent =
            `作业类型：${data.homework_type_name} | 理论：${data.theory_name} | 知识点：${data.knowledge_point}`;
        document.getElementById("promptMeta").textContent =
            `System Prompt 角色：资深中小学数学教育专家，精通最近发展区理论和${data.theory_name}`;

        state.confirmedPrompt = data.user_prompt;
        state.systemPrompt = data.system_prompt;
        btn.textContent = "✅ 提示词已生成（可在左侧编辑）";

    } catch (e) {
        alert("生成失败：" + e.message);
        btn.disabled = false;
        btn.textContent = "✨ 生成提示词";
    }
}

// Step 3 选择理论后启用「生成提示词」按钮
document.addEventListener("change", (e) => {
    if (e.target.id === "theorySelect" && e.target.value) {
        document.getElementById("btnGeneratePrompt").disabled = false;
    }
});

// ============================================================
// Step 5: 三层次作业
// ============================================================
function renderStep5() {
    const hw = state.homeworkResults;
    const isStructured = hw && (hw.type === "theory_levels" || hw.type === "cognitive_stages" || hw.type === "dialogue_config" || hw.type === "inquiry_config");

    if (hw) {
        document.getElementById("generateActions").style.display = "none";
        document.getElementById("zpdTabs").style.display = isStructured ? "none" : "block";
        if (hw.type === "theory_levels") {
            renderTheoryLevels();
        } else if (hw.type === "cognitive_stages") {
            renderCognitiveStages();
        } else if (hw.type === "dialogue_config") {
            renderDialogueConfig();
        } else if (hw.type === "inquiry_config") {
            renderInquiryConfig();
        } else {
            renderTabs();
        }
    } else {
        document.getElementById("generateActions").style.display = "block";
        document.getElementById("zpdTabs").style.display = "none";
        // 隐藏理论层级容器
        const tlContainer = document.getElementById("theoryLevelsContainer");
        if (tlContainer) tlContainer.style.display = "none";
        document.getElementById("btnGenerateHomework").style.display = "inline-block";
        document.getElementById("generatingText").style.display = "none";
        document.getElementById("generatingError").style.display = "none";
    }
}

async function generateHomework() {
    if (!state.confirmedPrompt) {
        alert("请先在 Step 4 中生成提示词");
        return;
    }

    // 同步最新编辑
    state.confirmedPrompt = document.getElementById("userPromptText").value;

    const btn = document.getElementById("btnGenerateHomework");
    const loadingText = document.getElementById("generatingText");
    const errorText = document.getElementById("generatingError");

    btn.style.display = "none";
    loadingText.style.display = "block";
    errorText.style.display = "none";

    try {
        const res = await fetch("/api/generate-homework", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                knowledge_point: state.selectedKp,
                homework_type: state.selectedType,
                theory: state.selectedTheory,
                prompt: state.confirmedPrompt,
                system_prompt: state.systemPrompt
            })
        });

        const data = await res.json();
        if (data.error) {
            errorText.textContent = "❌ " + data.error;
            errorText.style.display = "block";
            loadingText.style.display = "none";
            btn.style.display = "inline-block";
            return;
        }

        state.homeworkResults = data.homework;
        state.editedContents = {};

        // 结构化类型有 .type 字段，标准 ZPD 结果没有
        if (data.homework && data.homework.type) {
            renderStep5();
        } else {
            renderStep5();
            renderTabs();
        }

    } catch (e) {
        errorText.textContent = "❌ 请求失败：" + e.message;
        errorText.style.display = "block";
        loadingText.style.display = "none";
        btn.style.display = "inline-block";
    }
}

function renderTabs() {
    if (!state.homeworkResults) return;

    const levels = ["distal", "proximal", "existing"];
    const tabButtons = document.getElementById("tabButtons");
    const tabPanels = document.getElementById("tabPanels");

    tabButtons.innerHTML = levels.map((lid, i) => {
        const hw = state.homeworkResults[lid];
        if (!hw) return "";
        return `<button class="tab-btn${i === 0 ? ' active' : ''}" data-level="${lid}" onclick="switchTab('${lid}')">
            <span class="tab-icon">${hw.icon || ''}</span>${hw.label}
        </button>`;
    }).join("");

    tabPanels.innerHTML = levels.map((lid, i) => {
        const hw = state.homeworkResults[lid];
        if (!hw) return "";
        const content = state.editedContents[lid] !== undefined
            ? state.editedContents[lid]
            : hw.content;
        const hasError = !!hw.error;
        return `<div class="tab-panel${i === 0 ? ' active' : ''}" id="panel_${lid}">
            <div class="level-header">
                <h3>${hw.icon || ''} ${hw.label}</h3>
                ${hasError ? '<span style="color:var(--danger);">⚠️ 生成失败</span>' : ''}
            </div>
            <p class="level-desc">${escapeHtml(hw.description)}</p>
            <div class="level-content" id="content_${lid}">${escapeHtml(content)}</div>
            <div class="level-actions">
                <button class="btn btn-sm btn-secondary" onclick="editLevel('${lid}')">📝 编辑</button>
                <button class="btn btn-sm btn-warning" onclick="showRegenerateModal('${lid}')">🔄 重新生成</button>
                <button class="btn btn-sm btn-success" onclick="confirmLevel('${lid}')">✅ 确认</button>
            </div>
        </div>`;
    }).join("");

    document.getElementById("zpdTabs").style.display = "block";

    // LaTeX 渲染
    if (window.MathJax) {
        MathJax.typesetPromise([document.getElementById("zpdTabs")]).catch(console.error);
    }
}

// 层级 → ZPD 区 映射（前端推断，不依赖 AI 输出格式）
// 值可以是单个字符串或数组（表示同时属于多个区）
const LEVEL_ZONE_MAP = {
    bloom: {
        remember: 'distal', understand: 'distal',
        apply: 'proximal', analyze: 'proximal',
        evaluate: 'existing', create: 'existing',
    },
    solo: {
        prestructural: 'distal', unistructural: 'distal',
        multistructural: 'proximal', relational: ['proximal', 'existing'],
        extended_abstract: 'existing',
    },
};

function _zoneBadgeClass(zid) {
    if (zid === 'distal') return 'zone-badge-distal';
    if (zid === 'proximal') return 'zone-badge-proximal';
    return 'zone-badge-existing';
}

function _zoneShortName(zid) {
    if (zid === 'distal') return '远端发展区';
    if (zid === 'proximal') return '最近发展区';
    return '现有发展区';
}

function _zoneIcon(zid) {
    if (zid === 'distal') return '🚀';
    if (zid === 'proximal') return '🎯';
    return '✅';
}

function _resolveZoneId(lvId, theoryId, fallbackZone) {
    const map = LEVEL_ZONE_MAP[theoryId];
    if (map && map[lvId]) {
        const val = map[lvId];
        // 数组取第一个作为主区（用于上色）
        return Array.isArray(val) ? val[0] : val;
    }
    if (fallbackZone && fallbackZone.zone_id) return fallbackZone.zone_id;
    return '';
}

function _resolveZoneIds(lvId, theoryId) {
    const map = LEVEL_ZONE_MAP[theoryId];
    if (map && map[lvId]) {
        const val = map[lvId];
        return Array.isArray(val) ? val : [val];
    }
    return [];
}

function _buildLevelCardHTML(lv, theoryId, zone) {
    const primaryZid = _resolveZoneId(lv.id, theoryId, zone);
    const allZids = _resolveZoneIds(lv.id, theoryId);
    const content = state.editedContents[lv.id] !== undefined
        ? state.editedContents[lv.id]
        : (lv.content || '');

    // 构建标签 HTML
    const badges = '<span class="zone-badge-group">' + allZids.map(function(zid) {
        const bc = _zoneBadgeClass(zid);
        return '<span class="btn btn-sm zone-badge ' + bc + '">' + _zoneIcon(zid) + ' ' + _zoneShortName(zid) + '</span>';
    }).join('') + '</span>';

    return [
        '<div class="zone-level-card zone-card-' + primaryZid + '" id="levelCard_' + lv.id + '">',
        '  <div class="level-card-header">',
        '    <span class="level-order">' + lv.order + '</span>',
        '    <span class="level-name">' + escapeHtml(lv.name) + '</span>',
        '    <span class="level-desc">' + escapeHtml(lv.desc) + '</span>',
        '  </div>',
        '  <div class="level-card-content" id="content_' + lv.id + '">' + escapeHtml(content) + '</div>',
        '  <div class="level-card-actions">',
        '    <button class="btn btn-sm btn-secondary" onclick="editTheoryLevel(\'' + lv.id + '\')">📝 编辑</button>',
        '    <button class="btn btn-sm btn-warning" onclick="regenerateTheoryLevel(\'' + lv.id + '\')">🔄 重新生成</button>',
        '    ' + badges,
        '  </div>',
        '</div>',
    ].join('\n');
}

function _buildZoneGroupHTML(zone, theoryId) {
    const zid = zone.zone_id || '';
    const badgeClass = _zoneBadgeClass(zid);
    const icon = zone.icon || _zoneIcon(zid);
    const label = escapeHtml(zone.zone_label || _zoneShortName(zid));
    const goal = escapeHtml(zone.goal || '');
    const levels = zone.levels || [];

    const levelCards = [];
    for (let li = 0; li < levels.length; li++) {
        levelCards.push(_buildLevelCardHTML(levels[li], theoryId, zone));
        if (li < levels.length - 1) {
            levelCards.push('<div class="level-connector"><span>⬇ 递进</span></div>');
        }
    }

    return [
        '<div class="zone-group">',
        '  <div class="zone-header ' + badgeClass + '">',
        '    <span class="zone-icon">' + icon + '</span>',
        '    <span class="zone-label">' + label + '</span>',
        '    <span class="zone-goal">' + goal + '</span>',
        '  </div>',
        '  <div class="zone-levels">',
        levelCards.join('\n'),
        '  </div>',
        '</div>',
    ].join('\n');
}

function renderTheoryLevels() {
    const hw = state.homeworkResults;
    if (!hw || hw.type !== "theory_levels") return;

    const zones = hw.zones || [];
    const levels = hw.levels || [];

    if (zones.length === 0 && levels.length === 0) {
        document.getElementById("zpdTabs").style.display = "none";
        return;
    }

    let container = document.getElementById("theoryLevelsContainer");
    if (!container) {
        container = document.createElement("div");
        container.id = "theoryLevelsContainer";
        container.className = "theory-levels-container";
        document.getElementById("step5").appendChild(container);
    }
    container.style.display = "block";

    const theoryId = hw.theory_id || "";
    const isBloom = theoryId === "bloom";

    let html = '';
    html += '<div class="theory-header">';
    html += '<h3>📊 基于<span class="theory-badge">' + (isBloom ? '布卢姆认知目标分类' : 'SOLO分类理论') + '</span> × 最近发展区三层级作业</h3>';
    html += '<p class="theory-desc">';
    html += isBloom
        ? '共 3 个 ZPD 区 × 6 个认知层级，各区面向不同水平学生，区内题目逐级递进'
        : '共 3 个 ZPD 区 × 5 个结构层级，各区面向不同水平学生，区内题目逐级递进';
    html += '</p></div>';

    if (zones.length > 0) {
        html += '<div class="zpd-zones-flow">';
        for (let zi = 0; zi < zones.length; zi++) {
            html += _buildZoneGroupHTML(zones[zi], theoryId);
            if (zi < zones.length - 1) {
                html += '<div class="zone-connector"><span>⬇</span></div>';
            }
        }
        html += '</div>';
    } else {
        // 回退：平铺层级卡片，前端推断 ZPD 区
        html += '<div class="zpd-zones-flow">';
        for (let i = 0; i < levels.length; i++) {
            const lv = levels[i];
            html += _buildLevelCardHTML(lv, theoryId, null);
            if (i < levels.length - 1) {
                html += '<div class="level-connector"><span>⬇ 递进</span></div>';
            }
        }
        html += '</div>';
    }

    container.innerHTML = html;

    // LaTeX 渲染
    if (window.MathJax) {
        MathJax.typesetPromise([container]).catch(console.error);
    }
}

function renderCognitiveStages() {
    const hw = state.homeworkResults;
    if (!hw || hw.type !== "cognitive_stages") return;

    const stages = hw.stages || [];
    const question = hw.question || "";
    const theoryId = hw.theory_id || "";
    const isPolya = theoryId === "polya";

    let container = document.getElementById("theoryLevelsContainer");
    if (!container) {
        container = document.createElement("div");
        container.id = "theoryLevelsContainer";
        container.className = "theory-levels-container";
        document.getElementById("step5").appendChild(container);
    }
    container.style.display = "block";

    let html = '';
    html += '<div class="theory-header">';
    html += '<h3>📊 基于<span class="theory-badge">' + (isPolya ? '波利亚解题理论' : '图尔敏论证模型') + '</span> × 最近发展区三区支架</h3>';
    html += '<p class="theory-desc">' + (isPolya ? '4 个解题阶段' : '6 个论证阶段') + ' × 3 种 ZPD 支架风格</p>';
    html += '</div>';

    // 题干
    if (question) {
        html += '<div class="stage-question-card">';
        html += '<div class="stage-question-header">📋 题干</div>';
        html += '<div class="stage-question-content" id="content_question">' + escapeHtml(question) + '</div>';
        html += '</div>';
    }

    // 阶段卡片
    html += '<div class="zpd-zones-flow">';
    for (let si = 0; si < stages.length; si++) {
        const st = stages[si];
        const zones = st.zones || {};
        const zoneIds = ["distal", "proximal", "existing"];

        html += '<div class="stage-group">';
        html += '<div class="stage-header">';
        html += '<span class="stage-order">' + st.order + '</span>';
        html += '<span class="stage-name">' + escapeHtml(st.name) + '</span>';
        html += '<span class="stage-desc">' + escapeHtml(st.desc) + '</span>';
        html += '</div>';
        html += '<div class="stage-zones-row">';

        for (let zi = 0; zi < zoneIds.length; zi++) {
            const zid = zoneIds[zi];
            const z = zones[zid];
            const badgeClass = 'zone-badge-' + zid;
            const content = z ? (z.content || '') : '';

            html += '<div class="stage-zone-card zone-card-' + zid + '">';
            html += '<div class="stage-zone-header ' + badgeClass + '">';
            html += '<span>' + (z ? (z.icon || '') + ' ' + escapeHtml(z.label || '') + ' · ' + escapeHtml(z.style || '') : '') + '</span>';
            html += '</div>';
            html += '<div class="stage-zone-content" id="content_' + st.id + '_' + zid + '">' + escapeHtml(content) + '</div>';
            html += '</div>';
        }

        html += '</div></div>';
        if (si < stages.length - 1) {
            html += '<div class="zone-connector"><span>⬇</span></div>';
        }
    }
    html += '</div>';

    container.innerHTML = html;

    if (window.MathJax) {
        MathJax.typesetPromise([container]).catch(console.error);
    }
}

function renderDialogueConfig() {
    const hw = state.homeworkResults;
    if (!hw || hw.type !== "dialogue_config") return;

    const zones = hw.zones || [];
    const question = hw.question || "";
    if (state._configZoneIndex === undefined) state._configZoneIndex = 1;
    const zi = state._configZoneIndex;
    const z = zones[zi] || {};
    const zid = z.zone_id || '';

    let container = document.getElementById("theoryLevelsContainer");
    if (!container) {
        container = document.createElement("div");
        container.id = "theoryLevelsContainer";
        container.className = "theory-levels-container";
        document.getElementById("step5").appendChild(container);
    }
    container.style.display = "block";

    let html = '<div class="theory-header"><h3>🤖 最近发展区作业导师 — 苏格拉底启发式对话配置</h3>';
    html += '<p class="theory-desc">3 种 ZPD 对话风格 × 智能体配置</p>';
    html += '<div class="config-zone-tabs">';
    for (let ti = 0; ti < zones.length; ti++) {
        const tz = zones[ti];
        const tzid = tz.zone_id || '';
        html += '<span class="chat-zone-tab zone-badge-' + tzid + (ti === zi ? ' active' : '') + '" onclick="state._configZoneIndex=' + ti + ';renderDialogueConfig()">' + (tz.icon||'') + ' ' + (tz.label||'') + ' · ' + (tz.style||'') + '</span>';
    }
    html += '</div></div>';

    if (question) {
        html += '<div class="stage-question-card"><div class="stage-question-header">📋 作业题目</div>';
        html += '<div class="stage-question-content">' + escapeHtml(question) + '</div></div>';
    }

    const badgeClass = 'zone-badge-' + zid;
    html += '<div class="stage-group">';
    html += '<div class="stage-header ' + badgeClass + '">';
    html += '<span>' + (z.icon || '') + ' ' + escapeHtml(z.label || '') + ' · ' + escapeHtml(z.style || '') + '</span>';
    html += '<span style="font-size:0.8rem;opacity:0.8;margin-left:auto">' + escapeHtml(z.description || '') + '</span>';
    html += '</div>';

    const sections = [
        {key: 'opening', title: '🎤 开场引导语', content: z.opening},
        {key: 'rules', title: '📋 对话规则与追问策略', content: z.rules},
        {key: 'scaffold_path', title: '🪜 支架升级路径', content: z.scaffold_path},
        {key: 'evaluation', title: '📊 形成性评价模板', content: z.evaluation},
    ];
    for (let si = 0; si < sections.length; si++) {
        const sec = sections[si];
        html += '<div class="dialogue-section">';
        html += '<div class="dialogue-section-title">' + sec.title + '</div>';
        html += '<div class="dialogue-section-content">' + escapeHtml(sec.content || '') + '</div>';
        html += '</div>';
    }
    html += '</div>';

    container.innerHTML = html;
    if (window.MathJax) { MathJax.typesetPromise([container]).catch(function() {}); }
}

function renderInquiryConfig() {
    const hw = state.homeworkResults;
    if (!hw || hw.type !== "inquiry_config") return;

    const zones = hw.zones || [];
    const theme = hw.theme || "";
    if (state._configZoneIndex === undefined) state._configZoneIndex = 1;
    const zi = state._configZoneIndex;
    const z = zones[zi] || {};
    const zid = z.zone_id || '';

    let container = document.getElementById("theoryLevelsContainer");
    if (!container) {
        container = document.createElement("div");
        container.id = "theoryLevelsContainer";
        container.className = "theory-levels-container";
        document.getElementById("step5").appendChild(container);
    }
    container.style.display = "block";

    let html = '<div class="theory-header"><h3>🔬 协作探究作业编排系统 — 探究式学习</h3>';
    html += '<p class="theory-desc">3 种 ZPD 探究方案 × 多智能体角色配置</p>';
    html += '<div class="config-zone-tabs">';
    for (let ti = 0; ti < zones.length; ti++) {
        const tz = zones[ti];
        const tzid = tz.zone_id || '';
        html += '<span class="chat-zone-tab zone-badge-' + tzid + (ti === zi ? ' active' : '') + '" onclick="state._configZoneIndex=' + ti + ';renderInquiryConfig()">' + (tz.icon||'') + ' ' + (tz.label||'') + ' · ' + (tz.style||'') + '</span>';
    }
    html += '</div></div>';

    if (theme) {
        html += '<div class="stage-question-card"><div class="stage-question-header">🔍 探究主题</div>';
        html += '<div class="stage-question-content">' + escapeHtml(theme) + '</div></div>';
    }

    const badgeClass = 'zone-badge-' + zid;
    html += '<div class="stage-group">';
    html += '<div class="stage-header ' + badgeClass + '">';
    html += '<span>' + (z.icon || '') + ' ' + escapeHtml(z.label || '') + ' · ' + escapeHtml(z.style || '') + '</span>';
    html += '<span style="font-size:0.8rem;opacity:0.8;margin-left:auto">' + escapeHtml(z.description || '') + '</span>';
    html += '</div>';

    // 角色
    html += '<div class="dialogue-section"><div class="dialogue-section-title">👥 角色配置（' + ((z.roles || []).length) + ' 个角色）</div>';
    for (let ri = 0; ri < (z.roles || []).length; ri++) {
        const r = z.roles[ri];
        html += '<div class="dialogue-section-content" style="margin-bottom:8px"><strong>' + escapeHtml(r.name) + '</strong>：' + escapeHtml(r.desc || '') + '<br>' + escapeHtml(r.content || '') + '</div>';
    }
    html += '</div>';

    // 阶段
    html += '<div class="dialogue-section"><div class="dialogue-section-title">📐 探究阶段（' + ((z.stages || []).length) + ' 个阶段）</div>';
    for (let si = 0; si < (z.stages || []).length; si++) {
        const s = z.stages[si];
        html += '<div class="dialogue-section-content" style="margin-bottom:8px"><strong>阶段 ' + (si+1) + '：' + escapeHtml(s.name) + '</strong> — ' + escapeHtml(s.desc || '') + '<br>' + escapeHtml(s.content || '') + '</div>';
    }
    html += '</div>';

    // 行为规则
    html += '<div class="dialogue-section"><div class="dialogue-section-title">⚠️ 行为边界与升级规则</div>';
    html += '<div class="dialogue-section-content">' + escapeHtml(z.rules || '') + '</div></div>';

    html += '</div>';

    container.innerHTML = html;
    if (window.MathJax) { MathJax.typesetPromise([container]).catch(function() {}); }
}

function editTheoryLevel(levelId) {
    const contentDiv = document.getElementById("content_" + levelId);
    if (!contentDiv) return;

    if (contentDiv.classList.contains("editing")) {
        const textarea = contentDiv.querySelector("textarea");
        if (textarea) {
            state.editedContents[levelId] = textarea.value;
            contentDiv.innerHTML = escapeHtml(textarea.value);
            contentDiv.classList.remove("editing");
            // 重新渲染 LaTeX
            if (window.MathJax) {
                MathJax.typesetPromise([contentDiv]).catch(console.error);
            }
        }
    } else {
        const hwLevels = state.homeworkResults.levels || [];
        const lv = hwLevels.find(l => l.id === levelId);
        const currentContent = state.editedContents[levelId] !== undefined
            ? state.editedContents[levelId]
            : (lv ? lv.content : "");
        contentDiv.classList.add("editing");
        contentDiv.innerHTML = `<textarea>${escapeHtml(currentContent)}</textarea>`;
    }
}

async function regenerateTheoryLevel(levelId) {
    const hw = state.homeworkResults;
    if (!hw || hw.type !== "theory_levels") return;

    const lv = (hw.levels || []).find(l => l.id === levelId);
    if (!lv) return;

    // 移除旧 modal
    document.querySelector(".modal-overlay")?.remove();

    const modal = document.createElement("div");
    modal.className = "modal-overlay";
    modal.innerHTML = `
        <div class="modal-box">
            <h3>🔄 重新生成「${lv.name}」层级题目</h3>
            <p style="color:var(--gray-500);font-size:0.85rem;margin-bottom:8px;">
                请描述您希望如何调整该层级的题目（可选，留空则按原要求重新生成）：
            </p>
            <textarea id="regenerateAdjustment" placeholder="例如：题目难度再提高一些，增加一个生活化情境..."></textarea>
            <div class="modal-actions">
                <button class="btn btn-secondary btn-sm" onclick="closeModal()">取消</button>
                <button class="btn btn-primary btn-sm" id="btnConfirmRegenerate">🔄 重新生成</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);

    document.getElementById("btnConfirmRegenerate").addEventListener("click", () => {
        const adjustment = document.getElementById("regenerateAdjustment").value;
        closeModal();
        doRegenerateTheoryLevel(levelId, adjustment);
    });

    modal.addEventListener("click", (e) => {
        if (e.target === modal) closeModal();
    });
}

async function doRegenerateTheoryLevel(levelId, adjustment) {
    if (!state.confirmedPrompt) return;

    const contentDiv = document.getElementById("content_" + levelId);
    if (contentDiv) {
        contentDiv.innerHTML = "⏳ 正在重新生成中...";
    }

    try {
        const res = await fetch("/api/regenerate-level", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                knowledge_point: state.selectedKp,
                homework_type: state.selectedType,
                theory: state.selectedTheory,
                level: levelId,
                adjustment: adjustment,
                prompt: state.confirmedPrompt
            })
        });

        const data = await res.json();
        if (data.error) {
            alert("重新生成失败：" + data.error);
            return;
        }

        // 更新层级内容
        const hwLevels = state.homeworkResults.levels || [];
        const lv = hwLevels.find(l => l.id === levelId);
        if (lv) {
            lv.content = data.result.content || data.result;
        }
        delete state.editedContents[levelId];
        renderTheoryLevels();

    } catch (e) {
        alert("请求失败：" + e.message);
    }
}

function switchTab(levelId) {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
    document.querySelector(`[data-level="${levelId}"]`)?.classList.add("active");
    document.getElementById("panel_" + levelId)?.classList.add("active");
}

// --- 编辑作业 ---
function editLevel(levelId) {
    const contentDiv = document.getElementById("content_" + levelId);
    if (!contentDiv) return;

    if (contentDiv.classList.contains("editing")) {
        // 保存编辑
        const textarea = contentDiv.querySelector("textarea");
        if (textarea) {
            state.editedContents[levelId] = textarea.value;
            contentDiv.innerHTML = escapeHtml(textarea.value);
            contentDiv.classList.remove("editing");
        }
    } else {
        // 进入编辑模式
        const currentContent = state.editedContents[levelId] !== undefined
            ? state.editedContents[levelId]
            : state.homeworkResults[levelId]?.content || "";
        contentDiv.classList.add("editing");
        contentDiv.innerHTML = `<textarea>${escapeHtml(currentContent)}</textarea>`;
    }
}

// --- 确认作业 ---
function confirmLevel(levelId) {
    // 如果正在编辑，先保存
    const contentDiv = document.getElementById("content_" + levelId);
    if (contentDiv && contentDiv.classList.contains("editing")) {
        const textarea = contentDiv.querySelector("textarea");
        if (textarea) {
            state.editedContents[levelId] = textarea.value;
            contentDiv.innerHTML = escapeHtml(textarea.value);
            contentDiv.classList.remove("editing");
        }
    }

    const hw = state.homeworkResults[levelId];
    const btn = document.querySelector(`#panel_${levelId} .btn-success`);
    if (btn) {
        btn.textContent = "✅ 已确认";
        btn.disabled = true;
    }
    alert(`${hw?.label || levelId} 作业已确认！`);
}

// --- 重新生成 ---
function showRegenerateModal(levelId) {
    const hw = state.homeworkResults[levelId];
    if (!hw) return;

    // 移除旧 modal
    document.querySelector(".modal-overlay")?.remove();

    const modal = document.createElement("div");
    modal.className = "modal-overlay";
    modal.innerHTML = `
        <div class="modal-box">
            <h3>🔄 重新生成「${hw.label}」作业</h3>
            <p style="color:var(--gray-500);font-size:0.85rem;margin-bottom:8px;">
                请描述您希望如何调整该层级的作业（可选，留空则按原要求重新生成）：
            </p>
            <textarea id="regenerateAdjustment" placeholder="例如：题目难度再提高一些，增加一道应用题..."></textarea>
            <div class="modal-actions">
                <button class="btn btn-secondary btn-sm" onclick="closeModal()">取消</button>
                <button class="btn btn-primary btn-sm" id="btnConfirmRegenerate">🔄 重新生成</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);

    document.getElementById("btnConfirmRegenerate").addEventListener("click", () => {
        const adjustment = document.getElementById("regenerateAdjustment").value;
        closeModal();
        doRegenerate(levelId, adjustment);
    });

    modal.addEventListener("click", (e) => {
        if (e.target === modal) closeModal();
    });
}

function closeModal() {
    document.querySelector(".modal-overlay")?.remove();
}

async function doRegenerate(levelId, adjustment) {
    const hw = state.homeworkResults[levelId];
    if (!hw) return;

    const contentDiv = document.getElementById("content_" + levelId);
    if (contentDiv) {
        contentDiv.innerHTML = "⏳ 正在重新生成中...";
    }

    try {
        const res = await fetch("/api/regenerate-level", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                knowledge_point: state.selectedKp,
                homework_type: state.selectedType,
                theory: state.selectedTheory,
                level: levelId,
                adjustment: adjustment,
                prompt: state.confirmedPrompt
            })
        });

        const data = await res.json();
        if (data.error) {
            alert("重新生成失败：" + data.error);
            return;
        }

        // 更新结果
        state.homeworkResults[levelId] = data.result;
        delete state.editedContents[levelId];
        renderTabs();

    } catch (e) {
        alert("请求失败：" + e.message);
    }
}

// ============================================================
// Step 6: 对话交互
// ============================================================
const ZONE_ORDER = ["distal", "proximal", "existing"];

// ---- 通用 ----
function _initChatData(hw, buildFn) {
    if (!state.chatData) {
        state.chatData = {};
        for (let zi = 0; zi < ZONE_ORDER.length; zi++) {
            const zid = ZONE_ORDER[zi];
            state.chatData[zid] = { history: [], systemPrompt: buildFn(hw, zi) };
        }
        state._activeChatZone = "proximal";
    }
}

function _currentChat() {
    return (state.chatData || {})[state._activeChatZone || "proximal"] || { history: [], systemPrompt: "" };
}

function _renderZoneTabs(hw) {
    var subtitle = document.getElementById("chatSubtitle");
    subtitle.innerHTML = ZONE_ORDER.map(function(zid, zi) {
        var z = (hw.zones || [])[zi] || {};
        var active = zid === state._activeChatZone;
        var count = (state.chatData[zid] || {}).history ? state.chatData[zid].history.length : 0;
        var badgeClass = "zone-badge-" + zid;
        return '<span class="chat-zone-tab ' + badgeClass + (active ? ' active' : '') + '" onclick="switchChatZone(\'' + zid + '\')">' + (z.icon || '') + ' ' + (z.label || zid) + ' · ' + (z.style || '') + (count > 0 ? ' (' + count + '条)' : '') + '</span>';
    }).join("");
}

function switchChatZone(zid) {
    state._activeChatZone = zid;
    document.getElementById("chatInput").value = "";
    document.getElementById("btnSend").style.display = "inline-block";
    document.getElementById("chatInput").style.display = "";
    document.getElementById("btnEndChat").style.display = "inline-block";
    var hw = state.homeworkResults;
    if (hw && hw.type === "dialogue_config") { _loadDialogueMessages(); initDialogueChat(); }
    else if (hw && hw.type === "inquiry_config") { _loadInquiryMessages(); initInquiryChat(); }
}

function appendChatBubble(role, text) {
    var msgs = document.getElementById("chatMessages");
    var div = document.createElement("div");
    div.className = "chat-bubble chat-" + role;
    div.innerHTML = '<div class="chat-bubble-content">' + escapeHtml(text) + '</div>';
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
    if (window.MathJax) { MathJax.typesetPromise([div]).catch(function() {}); }
}

function _showChatQuestion(text) {
    var old = document.getElementById("chatQuestionCard");
    if (old) old.remove();
    if (!text) return;
    var div = document.createElement("div");
    div.id = "chatQuestionCard";
    div.style.cssText = "margin:0 16px;padding:8px 12px;background:var(--gray-100);border-radius:8px;font-size:0.85rem;color:var(--gray-700);white-space:pre-wrap;line-height:1.5";
    div.textContent = "📋 " + text;
    var container = document.getElementById("chatContainer");
    container.insertBefore(div, document.getElementById("chatMessages"));
}

function _resetChatUI() {
    document.getElementById("chatInput").value = "";
    document.getElementById("btnSend").style.display = "inline-block";
    document.getElementById("chatInput").style.display = "";
    document.getElementById("btnEndChat").style.display = "inline-block";
    var old = document.getElementById("inquiryControls");
    if (old) old.remove();
}

// ---- 第三种：动态交互型 ----
function initChatPage() {
    var hw = state.homeworkResults;
    if (hw && hw.type === "inquiry_config") { initInquiryChat(); return; }
    initDialogueChat();
}

function _buildDialoguePrompt(hw, zoneIndex) {
    var z = (hw.zones || [])[zoneIndex] || {};
    return [
        "你是最近发展区作业导师。请严格按照以下配置进行一对一辅导对话。",
        "当前模式：" + (z.label || "") + " · " + (z.style || ""),
        "", "【开场引导语】", z.opening || "",
        "", "【对话规则与追问策略】", z.rules || "",
        "", "【支架升级路径】", z.scaffold_path || "",
        "", "【形成性评价模板】", z.evaluation || "",
        "", "重要：不直接给出完整答案，每次只问一个问题或给一个提示。数学公式使用 LaTeX 格式（$...$）。",
    ].join("\n");
}

function _getDialogueOpening(hw, zi) {
    return ((hw.zones || [])[zi] || {}).opening || "你好！让我们开始吧。";
}

function initDialogueChat() {
    var hw = state.homeworkResults;
    _initChatData(hw, _buildDialoguePrompt);
    _resetChatUI();
    _renderZoneTabs(hw);
    _showChatQuestion(hw.question || "");
    _loadDialogueMessages();
    document.getElementById("btnSend").onclick = sendDialogueMessage;
    document.getElementById("chatInput").onkeydown = function(e) {
        if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendDialogueMessage(); }
    };
    document.getElementById("btnEndChat").onclick = endDialogueChat;
}

function _loadDialogueMessages() {
    var chat = _currentChat();
    var msgs = document.getElementById("chatMessages");
    msgs.innerHTML = "";
    if (chat.history.length === 0) {
        var opening = _getDialogueOpening(state.homeworkResults, ZONE_ORDER.indexOf(state._activeChatZone));
        chat.history.push({role: "assistant", content: opening});
        appendChatBubble("assistant", opening);
    } else {
        for (var i = 0; i < chat.history.length; i++) {
            appendChatBubble(chat.history[i].role, chat.history[i].content);
        }
    }
}

async function sendDialogueMessage() {
    var input = document.getElementById("chatInput");
    var msg = input.value.trim();
    if (!msg) return;
    var chat = _currentChat();
    appendChatBubble("user", msg);
    chat.history.push({role: "user", content: msg});
    input.value = "";
    var btn = document.getElementById("btnSend"); btn.disabled = true; btn.textContent = "\u23f3...";
    try {
        var res = await fetch("/api/chat", { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({ system_prompt: chat.systemPrompt, history: chat.history.slice(0,-1), message: msg }) });
        var data = await res.json();
        if (data.error) { appendChatBubble("assistant", "\u274c " + data.error); }
        else { var reply = data.reply || ""; appendChatBubble("assistant", reply); chat.history.push({role:"assistant", content: reply}); }
    } catch (e) { appendChatBubble("assistant", "\u274c \u8bf7\u6c42\u5931\u8d25\uff1a" + e.message); }
    btn.disabled = false; btn.textContent = "\u53d1\u9001";
}

async function endDialogueChat() {
    var chat = _currentChat();
    appendChatBubble("assistant", "\u23f3 \u6b63\u5728\u751f\u6210\u5f62\u6210\u6027\u8bc4\u4ef7...");
    var evalPrompt = chat.systemPrompt + "\n\n\u5bf9\u8bdd\u5df2\u7ed3\u675f\u3002\u8bf7\u6839\u636e\u3010\u5f62\u6210\u6027\u8bc4\u4ef7\u6a21\u677f\u3011\u751f\u6210\u4e00\u4efd\u5b8c\u6574\u7684\u5f62\u6210\u6027\u8bc4\u4ef7\u3002";
    try {
        var res = await fetch("/api/chat", { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({ system_prompt: evalPrompt, history: chat.history, message: "\u5bf9\u8bdd\u7ed3\u675f\uff0c\u8bf7\u751f\u6210\u5f62\u6210\u6027\u8bc4\u4ef7\u3002" }) });
        var data = await res.json();
        document.getElementById("chatMessages").lastChild.remove();
        if (data.error) { appendChatBubble("assistant", "\u274c " + data.error); }
        else { appendChatBubble("assistant", "\ud83d\udcca **\u5f62\u6210\u6027\u8bc4\u4ef7**\n\n" + (data.reply || "")); }
    } catch (e) { appendChatBubble("assistant", "\u274c " + e.message); }
    document.getElementById("btnEndChat").style.display = "none";
    document.getElementById("btnSend").style.display = "none";
    document.getElementById("chatInput").style.display = "none";
}

// ---- 第四种：协作探究型 ----
function _buildInquiryPrompt(hw, zoneIndex) {
    var z = (hw.zones || [])[zoneIndex] || {};
    var parts = ["你是协作探究多角色系统。根据对话状态自动选择角色和推进阶段。", "", "当前模式：" + (z.label||"") + " · " + (z.style||""), "", "【角色配置】"];
    for (var ri = 0; ri < (z.roles || []).length; ri++) {
        parts.push((z.roles[ri].name || "") + "：" + (z.roles[ri].desc || "") + "\n" + (z.roles[ri].content || ""));
    }
    parts.push("", "【阶段流程】");
    for (var si = 0; si < (z.stages || []).length; si++) {
        parts.push("阶段" + (si+1) + "：" + (z.stages[si].name || "") + "\n" + (z.stages[si].content || ""));
    }
    parts.push("", "【自动编排规则】");
    parts.push("1. 每次回复前自动选择最合适的角色身份，以【角色名】开头");
    parts.push("2. 当学生理解达到当前阶段目标时，自动推进：输出【NEXT_STAGE】");
    parts.push("3. 遇到困难可回退：输出【PREV_STAGE】");
    parts.push("4. 根据对话状态灵活切换角色，不需要轮询");
    parts.push("", "【行为规则】" + (z.rules || ""), "", "重要：标注【角色名】回复，不直接给结论。数学公式 LaTeX 格式。");
    return parts.join("\n");
}

function _getInquiryOpening(hw, zi) {
    var z = (hw.zones || [])[zi] || {};
    var stages = z.stages || [];
    var stageName = stages.length > 0 ? stages[0].name : "探究";
    var roles = z.roles || [];
    var firstName = roles.length > 0 ? roles[0].name : "智能体";
    return "【" + firstName + "】欢迎来到协作探究！当前阶段：「" + stageName + "」。请先告诉我你对这个探究主题的理解。";
}

function initInquiryChat() {
    var hw = state.homeworkResults;
    _initChatData(hw, _buildInquiryPrompt);
    _resetChatUI();
    _renderZoneTabs(hw);
    _renderInquiryHeader(hw);
    _showChatQuestion(hw.theme || "");
    _loadInquiryMessages();
    document.getElementById("btnSend").onclick = sendInquiryMessage;
    document.getElementById("chatInput").onkeydown = function(e) {
        if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendInquiryMessage(); }
    };
    document.getElementById("btnEndChat").onclick = endInquiryChat;
}

function _renderInquiryHeader(hw) {
    var old = document.getElementById("inquiryControls");
    if (old) old.remove();
    var z = (hw.zones || [])[ZONE_ORDER.indexOf(state._activeChatZone)] || {};
    var stages = z.stages || [];
    if (!state._inquiryStage) state._inquiryStage = 0;

    var div = document.createElement("div");
    div.id = "inquiryControls";
    div.style.cssText = "display:flex;align-items:center;gap:16px;padding:6px 16px;border-top:1px solid var(--gray-200);background:var(--gray-25);flex-shrink:0;font-size:0.82rem";

    var rolesSpan = document.createElement("span");
    rolesSpan.textContent = "🤖 角色：" + ((z.roles || []).map(function(r){return r.name;}).join(" / "));
    div.appendChild(rolesSpan);

    var stageSpan = document.createElement("span");
    stageSpan.textContent = "📐 阶段：" + (state._inquiryStage + 1) + "/" + stages.length + " " + (stages[state._inquiryStage] || {}).name;
    stageSpan.id = "inquiryStageLabel";
    div.appendChild(stageSpan);

    var hintSpan = document.createElement("span");
    hintSpan.style.cssText = "color:var(--gray-400);font-size:0.75rem;margin-left:auto";
    hintSpan.textContent = "AI 自动切换角色与阶段";
    div.appendChild(hintSpan);

    var container = document.getElementById("chatContainer");
    container.insertBefore(div, document.getElementById("chatMessages"));
}

function _checkStageTransition(reply) {
    if (!reply) return;
    var hw = state.homeworkResults;
    var z = (hw.zones || [])[ZONE_ORDER.indexOf(state._activeChatZone)] || {};
    var stages = z.stages || [];
    if (reply.indexOf("【NEXT_STAGE】") !== -1) {
        if (state._inquiryStage < stages.length - 1) state._inquiryStage++;
    } else if (reply.indexOf("【PREV_STAGE】") !== -1) {
        if (state._inquiryStage > 0) state._inquiryStage--;
    }
}

function _loadInquiryMessages() {
    var chat = _currentChat();
    var msgs = document.getElementById("chatMessages");
    msgs.innerHTML = "";
    if (chat.history.length === 0) {
        var opening = _getInquiryOpening(state.homeworkResults, ZONE_ORDER.indexOf(state._activeChatZone));
        chat.history.push({role: "assistant", content: opening});
        appendChatBubble("assistant", opening);
    } else {
        for (var i = 0; i < chat.history.length; i++) {
            appendChatBubble(chat.history[i].role, chat.history[i].content);
        }
    }
}

async function sendInquiryMessage() {
    var input = document.getElementById("chatInput");
    var msg = input.value.trim();
    if (!msg) return;
    var chat = _currentChat();
    appendChatBubble("user", msg);
    chat.history.push({role: "user", content: msg});
    input.value = "";
    var btn = document.getElementById("btnSend"); btn.disabled = true; btn.textContent = "\u23f3...";
    try {
        var res = await fetch("/api/chat", { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({ system_prompt: chat.systemPrompt, history: chat.history.slice(0,-1), message: msg }) });
        var data = await res.json();
        if (data.error) { appendChatBubble("assistant", "\u274c " + data.error); }
        else {
            var reply = data.reply || "";
            _checkStageTransition(reply);
            reply = reply.replace(/\u3010NEXT_STAGE\u3011/g, "").replace(/\u3010PREV_STAGE\u3011/g, "").trim();
            appendChatBubble("assistant", reply);
            chat.history.push({role:"assistant", content: reply});
            initInquiryChat();
        }
    } catch (e) { appendChatBubble("assistant", "\u274c \u8bf7\u6c42\u5931\u8d25\uff1a" + e.message); }
    btn.disabled = false; btn.textContent = "\u53d1\u9001";
}

async function endInquiryChat() {
    var chat = _currentChat();
    appendChatBubble("assistant", "\u23f3 \u6b63\u5728\u751f\u6210\u5f62\u6210\u6027\u8bc4\u4ef7...");
    try {
        var res = await fetch("/api/chat", { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({ system_prompt: chat.systemPrompt, history: chat.history, message: "\u63a2\u7a76\u7ed3\u675f\uff0c\u8bf7\u751f\u6210\u4e00\u4efd\u7efc\u5408\u5f62\u6210\u6027\u8bc4\u4ef7\u3002" }) });
        var data = await res.json();
        document.getElementById("chatMessages").lastChild.remove();
        if (data.error) { appendChatBubble("assistant", "\u274c " + data.error); }
        else { appendChatBubble("assistant", "\ud83d\udcca **\u5f62\u6210\u6027\u8bc4\u4ef7**\n\n" + (data.reply || "")); }
    } catch (e) { appendChatBubble("assistant", "\u274c " + e.message); }
    document.getElementById("btnEndChat").style.display = "none";
    document.getElementById("btnSend").style.display = "none";
    document.getElementById("chatInput").style.display = "none";
    var ctrl = document.getElementById("inquiryControls");
    if (ctrl) ctrl.style.display = "none";
}

// ============================================================
// 工具函数
// ============================================================
function escapeHtml(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

function escapeJs(str) {
    return str.replace(/\\/g, "\\\\").replace(/'/g, "\\'").replace(/"/g, "\\\"");
}
