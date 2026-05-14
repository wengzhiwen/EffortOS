import json
import logging
import os
import time
from datetime import datetime, timezone

from flask import current_app
from openai import OpenAI

logger = logging.getLogger(__name__)

# LLM 日志目录
_LLM_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs", "llm")


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


def _write_llm_log(log_data: dict):
    """将 LLM 请求/响应日志写入 JSON 文件。"""
    os.makedirs(_LLM_LOG_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    filepath = os.path.join(_LLM_LOG_DIR, f"{ts}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)


def chat(
    messages: list[dict],
    max_completion_tokens: int = 2000,
    temperature: float = 0.7,
    retries: int = 2,
) -> str:
    """调用 OpenAI Chat API，带重试。完整的请求和响应记录到 logs/llm/ 目录。"""
    client = _get_client()
    model = _get_model()

    log_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "params": {
            "max_completion_tokens": max_completion_tokens,
            "temperature": temperature,
            "retries": retries,
        },
        "request": messages,
        "response": None,
        "error": None,
        "usage": None,
        "latency_ms": None,
    }

    for attempt in range(retries + 1):
        t0 = time.monotonic()
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_completion_tokens=max_completion_tokens,
                temperature=temperature,
            )
            latency = int((time.monotonic() - t0) * 1000)

            content = response.choices[0].message.content
            log_data["response"] = content
            log_data["latency_ms"] = latency
            if response.usage:
                log_data["usage"] = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            _write_llm_log(log_data)
            return content
        except Exception as e:
            latency = int((time.monotonic() - t0) * 1000)
            log_data["error"] = str(e)
            log_data["latency_ms"] = latency
            log_data["attempt"] = attempt
            if attempt == retries:
                _write_llm_log(log_data)
                raise
            logger.warning("LLM 调用失败 (attempt %d/%d): %s", attempt + 1, retries, e)
            time.sleep(2**attempt)

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


_LANG_INSTRUCTION = {
    "zh_CN": "\n\n【语言要求 — 最高优先级】你必须使用简体中文撰写所有输出内容。summary、plan 中的 type 描述、outlook 全部用简体中文。JSON 的 key 保持英文不变。",
    "zh_TW": "\n\n【語言要求 — 最高優先級】你必須使用繁體中文撰寫所有輸出內容。summary、plan 中的 type 描述、outlook 全部用繁體中文。JSON 的 key 保持英文不變。",
    "en": "\n\n【LANGUAGE REQUIREMENT — HIGHEST PRIORITY】You MUST write ALL output content in English. This includes summary, plan type descriptions, outlook, and ALL text values. Do NOT use Chinese under any circumstances. JSON keys stay as specified (English), but ALL text values must be in English.",
    "ja": "\n\n【言語要件 — 最優先】すべての出力内容を日本語で記述してください。summary、plan の type 記述、outlook はすべて日本語で書いてください。いかなる場合でも中国語を使用しないでください。JSON の key は英文のまま変更しないでください。",
}


def generate_weekly_report(
    recent_activities: list,
    recent_pmc: list,
    latest_pmc: dict,
    params: dict,
    future_days: list,
    today_str: str,
    recent_history: list = None,
    lang: str = "zh_CN",
) -> str:
    """生成训练报告。

    基于最近 7 天活动数据 + 每日 PMC 时间序列进行负荷评估，
    并给出未来 7 天逐日训练建议（含 PMC 预测）。
    """
    total_tss = sum(a.get("computed_metrics", {}).get("tss", 0) or 0 for a in recent_activities)

    load_analysis = analyze_training_load(latest_pmc.get("ctl", 0), latest_pmc.get("atl", 0), latest_pmc.get("tsb", 0))
    volume_analysis = analyze_weekly_volume(total_tss, len(recent_activities))
    distribution = analyze_activity_distribution(recent_activities)

    # 活动摘要
    recent_summary = "\n".join(
        f"- {a.get('start_time', '')[:10]} {a.get('activity_type', '')} "
        f"「{a.get('name', '未命名')}」TSS: {a.get('computed_metrics', {}).get('tss', '—')} "
        f"强度: {a.get('computed_metrics', {}).get('intensity_level', '—')} "
        f"时长: {a.get('data_summary', {}).get('duration_seconds', 0) // 60}分钟"
        for a in recent_activities
    )

    # 最近 7 天每日 PMC 表格
    pmc_table_rows = []
    for entry in recent_pmc:
        pmc_table_rows.append(
            f"| {entry['date']} | {entry['tss']:.0f} | {entry['ctl']:.1f} | {entry['atl']:.1f} | {entry['tsb']:.1f} |"
        )
    pmc_table = "| 日期 | TSS | CTL | ATL | TSB |\n|------|-----|-----|-----|-----|\n" + "\n".join(pmc_table_rows)

    # 未来 7 天日期列表
    future_days_str = "\n".join(f"{i + 1}. {d}" for i, d in enumerate(future_days))

    ctl = latest_pmc.get("ctl", 0)
    atl = latest_pmc.get("atl", 0)

    # 最近训练历史表格
    history_section = ""
    if recent_history:
        hist_rows = []
        for h in recent_history:
            tss_str = f"{h['tss']:.0f}" if h["tss"] else "—"
            hr_tss_str = f"{h['hr_tss']:.0f}" if h["hr_tss"] else "—"
            hist_rows.append(
                f"| {h['date']} | {h['name']} | {h['type']} | {h['duration_min']}min | {tss_str} | {hr_tss_str} | {h['intensity'] or '—'} |"
            )
        history_section = (
            "## 最近训练记录（参考复用）\n"
            "以下为用户近期完成的训练，安排计划时可参考相似的课程达成相近训练效果：\n\n"
            "| 日期 | 名称 | 类型 | 时长 | TSS | hrTSS | 强度 |\n"
            "|------|------|------|------|-----|-------|------|\n" + "\n".join(hist_rows) + "\n\n---\n\n"
        )

    user_prompt = f"""今天是 {today_str}。请根据以下数据生成训练报告。

## 最近 7 天训练概况
- 训练次数：{volume_analysis["training_count"]} 次
- 总 TSS：{volume_analysis["total_tss"]:.0f}
- {volume_analysis["frequency_assessment"]}
- {volume_analysis["volume_change"]}

## 最近 7 天活动明细
{recent_summary if recent_summary else "最近 7 天无运动记录"}

## 最近 7 天每日 PMC 变化
{pmc_table}

## 当前负荷状态
- CTL (Fitness): {ctl:.1f} — {load_analysis["ctl_level"]}
- ATL (Fatigue): {atl:.1f}
- TSB (Form): {latest_pmc.get("tsb", 0):.1f} — {load_analysis["tsb_level"]}
- ATL/CTL: {load_analysis["atl_ctl_ratio"]} — {load_analysis["ratio_assessment"]}

## 运动类型分布
- TSS 分布：{distribution["distribution"]}
- {distribution["diversity"]}

{history_section}---

## PMC 预测公式（用于逐日预测）
从当前值开始，每天按以下公式递推：
- CTL_new = CTL + (当天TSS - CTL) × 0.02353
- ATL_new = ATL + (当天TSS - ATL) × 0.13307
- TSB = CTL - ATL

当前起点：CTL={ctl:.1f}, ATL={atl:.1f}, TSB={ctl - atl:.1f}

## 训练强度分类体系
本系统将训练分为以下类型（按强度递增）：
- **恢复**：Z1（心率<68%LTHR / 功率<55%FTP），TSS 约 15-25/h
- **有氧耐力**：Z2 为主（心率68%-83%LTHR / 功率55%-75%FTP），Z3 以上 <10%，时长 ≥45min，TSS 约 30-50/h
- **节奏**：Z3 累计 ≥30min（心率83%-94%LTHR / 功率75%-90%FTP），TSS 约 50-70/h
- **阈值**：Z4 累计 ≥25min（心率94%-105%LTHR / 功率90%-105%FTP），TSS 约 60-80/h
- **VO2max**：Z5+ 累计 ≥15min，≥3组连续3分钟以上间歇（心率>105%LTHR / 功率105%-120%FTP），TSS 约 70-100/h

## 未来 7 天日期
{future_days_str}

---

## 训练计划约束规则（必须严格遵守）
1. **TSB 控制线**：目标是让 TSB 在 -10 到 -15 之间波动，偶尔触及 -20 但不得持续低于 -20。7 天末 TSB 应在 -10 左右
2. **ATL/CTL 比率**：可以瞬时超过 1.5（主课表日），但次日必须通过恢复日降回 1.5 以下，整体大部分时间 ≤ 1.5
3. **VO2max 课表**：每周仅安排一次，且前后各一天不得安排阈值或 VO2max 等高强度课程
4. **核心课表组合**：每周 3 次核心训练 = 1 次 VO2max + 1 次阈值 + 1 次节奏。若疲劳累积大（TSB < -15 或 ATL/CTL > 1.5），去掉 1 次阈值以充分恢复
5. **有氧耐力填充**：核心课表之外的训练日安排有氧耐力（Z2），不要全部留空为休息日。7 天内至少 4 天有训练（3 次核心 + 1-2 次有氧耐力）
6. **恢复日**：只标注「休息」，不提供运动建议，TSS=0
7. **预测 PMC**：每天的计划必须包含预估 TSS，并用上述公式计算预测的 CTL、ATL、TSB
8. **TSS 量级参考**（用于安排预估 TSS）：
   - VO2max 课表：60-100 TSS（参考用户历史中 vo2max 分类的 TSS）
   - 阈值课表：50-80 TSS
   - 节奏课表：40-65 TSS
   - 有氧耐力：30-55 TSS
   - 安排 TSS 时应参考当前 CTL 值：日均 TSS ≈ CTL 时可维持，> CTL 时 CTL 会上升。要让 CTL 有可见的成长，7 天总 TSS 应显著大于 7 × CTL

## 输出格式要求（严格遵守 JSON 格式）
你必须返回一个 JSON 对象，不要输出任何 JSON 之外的内容。结构如下：

```json
{{
  "summary": "最近 7 天总结的 markdown 文本（3-5 句话，必须重点分析 ATL/CTL 比值和 TSB 的联合变化趋势，判断疲劳累积或恢复状态）",
  "plan": [
    {{
      "date": "05-07 周四",
      "type": "indoor_cycling「LSD60」",
      "intensity": "endurance",
      "duration_min": 60,
      "tss": 42,
      "ctl": 25.6,
      "atl": 29.3,
      "tsb": -3.7
    }}
  ],
  "outlook": "下周展望的 markdown 文本：如果按计划执行完 7 天，CTL 预计从 XX 变化到 XX，ATL/CTL 比值从 XX 变化到 XX，TSB 从 XX 变化到 XX。总结这周训练的主要目标和对体能的影响。"
}}
```

字段说明：
- summary: markdown 格式，重点分析 ATL/CTL 比值趋势和 TSB 变化，判断当前是疲劳积累期还是恢复期
- plan: 7 天计划数组，intensity 使用以下英文值之一：rest / recovery / endurance / tempo / threshold / vo2max。休息日 intensity=rest，type="休息"，tss=0，duration_min=0
- outlook: markdown 格式，总结计划执行后的 CTL、ATL/CTL、TSB 变化
- 安排训练时参考「最近训练记录」中的历史课程，尽量复用用户已完成过的类似训练"""

    lang_instruction = _LANG_INSTRUCTION.get(lang, _LANG_INSTRUCTION["zh_CN"])
    return chat(
        [
            {
                "role": "system",
                "content": (
                    "你是 EffortOS 运动分析平台的专业教练。你接收运动科学分析引擎已经计算好的结论和每日 PMC 数据，"
                    "据此制定未来 7 天训练计划。你必须严格遵守用户给出的训练约束规则（TSB、ATL/CTL、课表组合等），"
                    "并使用 PMC 递推公式逐日预测 CTL/ATL/TSB。你只输出 JSON，不输出其他内容。"
                ),
            },
            {"role": "user", "content": user_prompt + lang_instruction},
        ],
        max_completion_tokens=3000,
    )


def generate_suggestion(
    pmc_data: dict,
    recent_tss: list,
    params: dict,
    question: str = "",
    best_efforts_list=None,
    intensity_counts=None,
    lang: str = "zh_CN",
) -> str:
    """生成个性化训练建议。

    先基于理论分析，再让 LLM 组织语言。
    """
    # Step 1: 计算分析结论
    load_analysis = analyze_training_load(pmc_data.get("ctl", 0), pmc_data.get("atl", 0), pmc_data.get("tsb", 0))

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

    # 构建最佳表现段落
    best_efforts_section = ""
    if best_efforts_list:
        lines = []
        for entry in best_efforts_list:
            be = entry["best_efforts"]
            parts = []
            for metric in ("power", "heart_rate"):
                if metric in be:
                    peaks = be[metric]
                    # 取短/中/长窗口代表值
                    short = next((peaks[k] for k in ("5", "10", "15") if k in peaks), None)
                    mid = next((peaks[k] for k in ("60", "300") if k in peaks), None)
                    long_ = next((peaks[k] for k in ("1200", "3600") if k in peaks), None)
                    label = "功率" if metric == "power" else "心率"
                    vals = []
                    if short is not None:
                        vals.append(f"短时峰值{label} {short:.0f}")
                    if mid is not None:
                        vals.append(f"5分钟均{label} {mid:.0f}")
                    if long_ is not None:
                        vals.append(f"长时均{label} {long_:.0f}")
                    if vals:
                        parts.append("、".join(vals))
            if parts:
                lines.append(f"- {entry['date']} ({entry['type']}): {'; '.join(parts)}")
        if lines:
            best_efforts_section = "\n## 近期最佳表现\n" + "\n".join(lines)

    # 构建强度分布段落
    intensity_section = ""
    if intensity_counts:
        total = sum(intensity_counts.values())
        level_names = {
            "recovery": "恢复",
            "endurance": "耐力",
            "tempo": "节奏",
            "threshold": "阈值",
            "vo2max": "VO2max",
        }
        parts = [f"{level_names.get(k, k)} {v}次({v * 100 // total}%)" for k, v in intensity_counts.items()]
        intensity_section = f"\n## 近期训练强度分布\n- {'、'.join(parts)}"

    # Step 2: 交给 LLM 组织语言
    user_prompt = f"""请根据以下分析结论给出训练建议。直接使用这些结论，不要重新分析。

## 训练负荷状态
- CTL (Fitness): {pmc_data.get("ctl", 0):.1f} — {load_analysis["ctl_level"]}
- ATL (Fatigue): {pmc_data.get("atl", 0):.1f}
- TSB (Form): {pmc_data.get("tsb", 0):.1f} — {load_analysis["tsb_level"]}
- ATL/CTL 比率: {load_analysis["atl_ctl_ratio"]} — {load_analysis["ratio_assessment"]}

## 负荷评估
- 风险：{load_analysis["tsb_risk"]}
- TSB 建议：{load_analysis["tsb_advice"]}
- CTL 建议：{load_analysis["ctl_advice"]}

## 最近 7 天
- 每日 TSS：{tss_str}
- 活跃天数：{active_days}/7
- 日均 TSS：{avg_daily_tss:.0f}
- 趋势：训练量{tss_trend}
- {rest_assessment}
{best_efforts_section}{intensity_section}

{"用户提问：" + question if question else "请给出综合训练建议。如果最佳表现数据中有突出的峰值表现，可以提及并给出突破建议。"}"""

    lang_instruction = _LANG_INSTRUCTION.get(lang, _LANG_INSTRUCTION["zh_CN"])
    return chat(
        [
            {
                "role": "system",
                "content": "你是 EffortOS 运动分析平台的文案编辑。你接收运动科学分析引擎已经计算好的结论，将其组织成个性化的训练建议。不要质疑或修改分析结论，只需以专业教练的语气呈现给用户。如果用户有提问，结合分析结论回答。使用 markdown 格式。",
            },
            {"role": "user", "content": user_prompt + lang_instruction},
        ]
    )
