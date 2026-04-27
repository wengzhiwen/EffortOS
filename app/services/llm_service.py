import os
import time

from openai import OpenAI


def _get_client() -> OpenAI:
    """获取 OpenAI 客户端实例。"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 环境变量未设置")
    return OpenAI(api_key=api_key)


def chat(
    messages: list[dict],
    model: str = "gpt-4o-mini",
    max_tokens: int = 2000,
    temperature: float = 0.7,
    retries: int = 2,
) -> str:
    """调用 OpenAI Chat API，带重试。

    参数:
        messages: [{"role": "system"|"user"|"assistant", "content": "..."}]
        model: 模型名称
        max_tokens: 最大输出 token 数
        temperature: 温度参数
        retries: 重试次数

    返回: 助手回复文本
    """
    client = _get_client()

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


SYSTEM_PROMPT = """你是 EffortOS 运动分析平台的 AI 教练。你负责分析运动员的训练数据并提供建议。

你的分析基于以下核心指标：
- TSS（训练压力分数）：100 TSS = 在阈值强度运动 1 小时
- CTL（慢性训练负荷 / Fitness）：42 天指数加权平均，反映长期适应水平
- ATL（急性训练负荷 / Fatigue）：7 天指数加权平均，反映当前疲劳程度
- TSB（训练压力平衡 / Form）：CTL - ATL，正值表示恢复充分，负值表示疲劳

运动类型包括：骑行（含室内）、跑步（含室内）、步行。

你的建议应该：
1. 基于数据分析，而非泛泛而谈
2. 具体且可操作（给出具体的训练建议）
3. 中文回复
4. 关注训练负荷管理和恢复
5. 如果发现过度训练风险，明确警告"""


def generate_weekly_report(
    week_activities: list[dict],
    pmc_data: dict,
    params: dict,
) -> str:
    """生成训练周报。

    参数:
        week_activities: 本周活动列表 [{"name": ..., "activity_type": ..., "tss": ..., ...}]
        pmc_data: {"ctl": ..., "atl": ..., "tsb": ...}
        params: {"ftp": ..., "max_heart_rate": ..., ...}
    """
    activity_summary = "\n".join(
        f"- {a.get('start_time', '')[:10]} {a.get('activity_type', '')} "
        f"「{a.get('name', '未命名')}」TSS: {a.get('computed_metrics', {}).get('tss', '—')} "
        f"时长: {a.get('data_summary', {}).get('duration_seconds', 0) // 60}分钟"
        for a in week_activities
    )

    total_tss = sum(
        a.get("computed_metrics", {}).get("tss", 0) or 0
        for a in week_activities
    )

    user_prompt = f"""请分析以下训练数据并生成周报：

## 本周运动（共 {len(week_activities)} 次，总 TSS {total_tss:.0f}）
{activity_summary if activity_summary else "本周无运动记录"}

## 当前训练状态
- CTL (Fitness): {pmc_data.get('ctl', 0):.1f}
- ATL (Fatigue): {pmc_data.get('atl', 0):.1f}
- TSB (Form): {pmc_data.get('tsb', 0):.1f}

## 用户参数
- FTP: {params.get('ftp', '未设置')} W
- 最大心率: {params.get('max_heart_rate', '未设置')} bpm

请包含：1) 本周训练总结 2) 负荷分析 3) 恢复建议 4) 下周建议"""

    return chat([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ])


def generate_suggestion(
    pmc_data: dict,
    recent_tss: list[float],
    params: dict,
    question: str = "",
) -> str:
    """生成个性化训练建议。

    参数:
        pmc_data: {"ctl": ..., "atl": ..., "tsb": ...}
        recent_tss: 最近 7 天的每日 TSS 列表
        params: 用户参数
        question: 用户提问（可选）
    """
    tss_str = ", ".join(f"{t:.0f}" for t in recent_tss) if recent_tss else "无数据"

    user_prompt = f"""请基于以下数据给出训练建议：

## 当前状态
- CTL (Fitness): {pmc_data.get('ctl', 0):.1f}
- ATL (Fatigue): {pmc_data.get('atl', 0):.1f}
- TSB (Form): {pmc_data.get('tsb', 0):.1f}

## 最近 7 天 TSS
{tss_str}

## 用户参数
- FTP: {params.get('ftp', '未设置')} W
- 最大心率: {params.get('max_heart_rate', '未设置')} bpm

{"用户提问：" + question if question else "请给出综合训练建议。"}"""

    return chat([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ])
