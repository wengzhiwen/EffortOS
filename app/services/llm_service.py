import os
import time

from flask import current_app
from openai import OpenAI


def _get_client() -> OpenAI:
    """获取 OpenAI 客户端实例。"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 环境变量未设置")
    return OpenAI(api_key=api_key)


def _get_model() -> str:
    """获取配置的模型名称。"""
    try:
        return current_app.config.get("OPENAI_MODEL", "gpt-5.4-mini-2026-03-17")
    except RuntimeError:
        return os.environ.get("OPENAI_MODEL", "gpt-5.4-mini-2026-03-17")


def chat(
    messages: list[dict],
    max_tokens: int = 2000,
    temperature: float = 0.7,
    retries: int = 2,
) -> str:
    """调用 OpenAI Chat API，带重试。

    模型名称从配置中读取，不再硬编码。
    """
    client = _get_client()
    model = _get_model()

    for attempt in range(retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            if attempt == retries:
                raise
            time.sleep(2 ** attempt)

    return ""


# ============================================================
# 运动科学分析引擎 — 基于理论计算分析结论
# ============================================================


def analyze_training_load(ctl: float, atl: float, tsb: float) -> dict:
    """基于 PMC 理论分析训练负荷状态。"""
    # TSB 分级
    if tsb > 25:
        tsb_level = "非常清新"
        tsb_risk = "训练不足风险"
        tsb_advice = "当前恢复非常充分，适合进行高质量训练或比赛。但长期处于高 TSB 可能意味着训练量不足。"
    elif tsb > 10:
        tsb_level = "清新"
        tsb_risk = "无"
        tsb_advice = "恢复状态良好，适合重要训练课或比赛。这是赛前减量的理想状态。"
    elif tsb > -10:
        tsb_level = "中性"
        tsb_risk = "无"
        tsb_advice = "正常训练状态，可以在保持训练的同时注意恢复。"
    elif tsb > -30:
        tsb_level = "疲劳"
        tsb_risk = "注意恢复"
        tsb_advice = "训练积累期的正常状态，说明训练刺激充足。需要确保充足的恢复（睡眠、营养）。"
    else:
        tsb_level = "过度疲劳"
        tsb_risk = "过度训练风险"
        tsb_advice = "⚠️ 警告：TSB 过低，存在过度训练风险。建议立即减量或休息 2-3 天，密切关注身体信号。"

    # CTL 趋势判断
    if ctl < 20:
        ctl_level = "低训练负荷"
        ctl_advice = "长期训练量较低，建议逐步增加训练频率和时长。"
    elif ctl < 50:
        ctl_level = "中等训练负荷"
        ctl_advice = "训练负荷适中，可以在此基础上逐步增加。"
    elif ctl < 80:
        ctl_level = "高训练负荷"
        ctl_advice = "训练量充足，注意保持恢复节奏，避免受伤。"
    else:
        ctl_level = "极高训练负荷"
        ctl_advice = "训练量非常大，需要特别注意恢复和营养补充。"

    # ATL/CTL 比率
    ratio = atl / ctl if ctl > 0 else 0
    if ratio > 2.0:
        ratio_assessment = "急性负荷远高于慢性负荷，训练量突增，有受伤风险"
    elif ratio > 1.5:
        ratio_assessment = "近期训练量增加较快，属于正常负荷积累期"
    elif ratio > 0.8:
        ratio_assessment = "急性负荷与慢性负荷平衡良好"
    else:
        ratio_assessment = "近期训练量较少，处于恢复/减量阶段"

    return {
        "tsb_level": tsb_level,
        "tsb_risk": tsb_risk,
        "tsb_advice": tsb_advice,
        "ctl_level": ctl_level,
        "ctl_advice": ctl_advice,
        "atl_ctl_ratio": round(ratio, 2),
        "ratio_assessment": ratio_assessment,
    }


def analyze_weekly_volume(week_tss: float, week_count: int, avg_weekly_tss: float = 0) -> dict:
    """分析周训练量。"""
    if avg_weekly_tss > 0:
        change_pct = ((week_tss - avg_weekly_tss) / avg_weekly_tss) * 100
        if change_pct > 30:
            volume_change = f"本周训练量比平均水平高 {change_pct:.0f}%，增幅较大，注意恢复"
        elif change_pct > 10:
            volume_change = f"本周训练量比平均水平高 {change_pct:.0f}%，属于正常波动"
        elif change_pct > -10:
            volume_change = "本周训练量与平均水平基本持平"
        elif change_pct > -30:
            volume_change = f"本周训练量比平均水平低 {abs(change_pct):.0f}%，属于恢复周"
        else:
            volume_change = f"本周训练量比平均水平低 {abs(change_pct):.0f}%，大幅减量"
    else:
        volume_change = "暂无历史数据对比"

    # 训练频率评估
    if week_count == 0:
        frequency = "本周无训练记录，建议保持至少每周 3 次的训练频率"
    elif week_count < 3:
        frequency = f"本周训练 {week_count} 次，频率偏低，建议增加到 3-5 次"
    elif week_count <= 6:
        frequency = f"本周训练 {week_count} 次，频率适中"
    else:
        frequency = f"本周训练 {week_count} 次，频率较高，注意恢复"

    return {
        "total_tss": week_tss,
        "training_count": week_count,
        "volume_change": volume_change,
        "frequency_assessment": frequency,
    }


def analyze_activity_distribution(activities: list[dict]) -> dict:
    """分析运动类型分布。"""
    type_tss = {}
    type_count = {}
    for a in activities:
        atype = a.get("activity_type", "other")
        tss = a.get("computed_metrics", {}).get("tss") or 0
        type_tss[atype] = type_tss.get(atype, 0) + tss
        type_count[atype] = type_count.get(atype, 0) + 1

    # 判断是否过于单一
    total = sum(type_count.values())
    if total == 0:
        return {"distribution": type_tss, "diversity": "无训练数据"}

    dominant = max(type_count.values())
    if total > 3 and dominant / total > 0.8:
        diversity = "训练类型较为单一，建议增加交叉训练以降低过度使用伤害风险"
    elif len(type_count) >= 3:
        diversity = "训练类型多样化，有助于全面发展"
    else:
        diversity = "训练类型适中"

    return {
        "distribution": {k: round(v, 1) for k, v in type_tss.items()},
        "count": type_count,
        "diversity": diversity,
    }


def generate_weekly_report(
    week_activities: list[dict],
    pmc_data: dict,
    params: dict,
) -> str:
    """生成训练周报。

    核心改变：先基于运动科学理论计算出分析结论，再让 LLM 组织语言。
    """
    total_tss = sum(
        a.get("computed_metrics", {}).get("tss", 0) or 0
        for a in week_activities
    )

    # Step 1: 基于理论计算分析结论
    load_analysis = analyze_training_load(
        pmc_data.get("ctl", 0), pmc_data.get("atl", 0), pmc_data.get("tsb", 0)
    )
    volume_analysis = analyze_weekly_volume(total_tss, len(week_activities))
    distribution = analyze_activity_distribution(week_activities)

    # Step 2: 构建活动摘要
    activity_summary = "\n".join(
        f"- {a.get('start_time', '')[:10]} {a.get('activity_type', '')} "
        f"「{a.get('name', '未命名')}」TSS: {a.get('computed_metrics', {}).get('tss', '—')} "
        f"时长: {a.get('data_summary', {}).get('duration_seconds', 0) // 60}分钟"
        for a in week_activities
    )

    # Step 3: 将分析结论交给 LLM 组织语言
    user_prompt = f"""请根据以下分析结论，组织一份训练周报。直接使用这些结论，不要重新分析原始数据。

## 本周训练概况
- 训练次数：{volume_analysis['training_count']} 次
- 总 TSS：{volume_analysis['total_tss']:.0f}
- {volume_analysis['frequency_assessment']}
- {volume_analysis['volume_change']}

## 活动明细
{activity_summary if activity_summary else "本周无运动记录"}

## 训练负荷分析（PMC）
- CTL (Fitness): {pmc_data.get('ctl', 0):.1f} — {load_analysis['ctl_level']}
- ATL (Fatigue): {pmc_data.get('atl', 0):.1f}
- TSB (Form): {pmc_data.get('tsb', 0):.1f} — {load_analysis['tsb_level']}
- ATL/CTL 比率: {load_analysis['atl_ctl_ratio']} — {load_analysis['ratio_assessment']}

## 负荷状态评估
- 风险等级：{load_analysis['tsb_risk']}
- CTL 评估：{load_analysis['ctl_advice']}
- TSB 建议：{load_analysis['tsb_advice']}

## 运动类型分布
- TSS 分布：{distribution['distribution']}
- {distribution['diversity']}

请组织成一份清晰的周报，包含：本周总结、负荷分析、风险评估、下周建议。使用 markdown 格式。"""

    return chat([
        {
            "role": "system",
            "content": "你是 EffortOS 运动分析平台的文案编辑。你接收运动科学分析引擎已经计算好的结论，将其组织成流畅的中文训练周报。不要质疑或修改分析结论，只需将其以专业、友好的语气呈现给用户。使用 markdown 格式。",
        },
        {"role": "user", "content": user_prompt},
    ])


def generate_suggestion(
    pmc_data: dict,
    recent_tss: list[float],
    params: dict,
    question: str = "",
) -> str:
    """生成个性化训练建议。

    先基于理论分析，再让 LLM 组织语言。
    """
    # Step 1: 计算分析结论
    load_analysis = analyze_training_load(
        pmc_data.get("ctl", 0), pmc_data.get("atl", 0), pmc_data.get("tsb", 0)
    )

    # 分析最近 7 天训练趋势
    active_days = sum(1 for t in recent_tss if t > 0)
    avg_daily_tss = sum(recent_tss) / len(recent_tss) if recent_tss else 0
    if len(recent_tss) >= 2 and recent_tss[-1] > recent_tss[0]:
        tss_trend = "上升"
    elif len(recent_tss) >= 2 and recent_tss[-1] < recent_tss[0]:
        tss_trend = "下降"
    else:
        tss_trend = "平稳"

    if active_days >= 6:
        rest_assessment = "过去 7 天训练非常频繁，建议安排 1-2 天恢复日"
    elif active_days >= 4:
        rest_assessment = "训练频率适中，保持当前节奏"
    elif active_days >= 2:
        rest_assessment = "训练频率偏低，可以适当增加"
    else:
        rest_assessment = "过去一周训练很少，需要逐步恢复训练节奏"

    tss_str = ", ".join(f"{t:.0f}" for t in recent_tss) if recent_tss else "无数据"

    # Step 2: 交给 LLM 组织语言
    user_prompt = f"""请根据以下分析结论给出训练建议。直接使用这些结论，不要重新分析。

## 训练负荷状态
- CTL (Fitness): {pmc_data.get('ctl', 0):.1f} — {load_analysis['ctl_level']}
- ATL (Fatigue): {pmc_data.get('atl', 0):.1f}
- TSB (Form): {pmc_data.get('tsb', 0):.1f} — {load_analysis['tsb_level']}
- ATL/CTL 比率: {load_analysis['atl_ctl_ratio']} — {load_analysis['ratio_assessment']}

## 负荷评估
- 风险：{load_analysis['tsb_risk']}
- TSB 建议：{load_analysis['tsb_advice']}
- CTL 建议：{load_analysis['ctl_advice']}

## 最近 7 天
- 每日 TSS：{tss_str}
- 活跃天数：{active_days}/7
- 日均 TSS：{avg_daily_tss:.0f}
- 趋势：训练量{tss_trend}
- {rest_assessment}

{"用户提问：" + question if question else "请给出综合训练建议。"}"""

    return chat([
        {
            "role": "system",
            "content": "你是 EffortOS 运动分析平台的文案编辑。你接收运动科学分析引擎已经计算好的结论，将其组织成个性化的中文训练建议。不要质疑或修改分析结论，只需以专业教练的语气呈现给用户。如果用户有提问，结合分析结论回答。使用 markdown 格式。",
        },
        {"role": "user", "content": user_prompt},
    ])
