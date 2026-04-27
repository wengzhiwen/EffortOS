# EffortOS 运动数据指标体系 — 调研报告

## 一、单次运动指标（Activity 级别）

### 1.1 基础数据摘要（DataSummary）— 从文件直接提取

| 指标 | 英文名 | 单位 | 说明 |
|------|--------|------|------|
| 总时长 | duration_seconds | 秒 | 时间戳首尾差 |
| 总距离 | total_distance | 米 | GPS 或距离累加 |
| 平均心率 | avg_heart_rate | bpm | 心率时间序列平均 |
| 最大心率 | max_heart_rate | bpm | 心率最大值 |
| 平均功率 | avg_power | W | 功率时间序列平均 |
| 最大功率 | max_power | W | 功率最大值 |
| 平均速度 | avg_speed | m/s | 速度平均 |
| 最大速度 | max_speed | m/s | 速度最大值 |
| 平均踏频 | avg_cadence | rpm | 踏频平均 |
| 最大踏频 | max_cadence | rpm | 踏频最大值 |
| 累计爬升 | elevation_gain | 米 | 海拔差累加（正值） |
| 累计下降 | elevation_loss | 米 | 海拔差累加（负值绝对值） |

### 1.2 功率衍生指标（仅骑行有功率数据时）

#### 标准化功率（Normalized Power, NP）

对功率变异性加权的平均功率，反映运动的真实生理消耗。

```
NP = ( mean( rolling_avg_power^4 ) ) ^ 0.25
```
- 30 秒滚动平均 → 取 4 次方 → 求均值 → 开 4 次方根
- 所需用户参数：无

#### 强度因子（Intensity Factor, IF）

```
IF = NP / FTP
```
- 所需用户参数：FTP

#### 变异性指数（Variability Index, VI）

```
VI = NP / 平均功率
```
- 所需用户参数：无
- VI ≈ 1.0 表示非常平稳（计时赛），> 1.15 表示高度变化（间歇）

#### 功率效率因子（Power Efficiency Factor, EF）

```
EF = NP / 平均心率
```
- 所需用户参数：无
- 纵向追踪用：EF 逐月上升说明有氧能力在提高

#### 总做功（Work）

```
Work = sum(power_i * dt_i)  单位：千焦 kJ
```

### 1.3 心率衍生指标（所有有心率数据的运动）

#### 心率强度因子（HR_IF）

```
HR_IF = 平均心率 / LTHR
```
- 所需用户参数：LTHR（按运动类型分别设定）

#### 心率效率因子（HR_EF）

```
HR_EF = 平均速度 / 平均心率
```

### 1.4 TSS（训练压力分数）— 核心指标

100 TSS = 在阈值强度下运动 1 小时。

#### 基于功率的 TSS（Power TSS）— 骑行有功率时的首选

```
TSS = duration_hours * IF^2 * 100
    = (duration_seconds * NP * IF) / (FTP * 3600) * 100
```
- 所需用户参数：FTP

#### 基于心率的 TSS（hrTSS）— 无功率时的备选

```
hrTSS = duration_hours * HR_IF^2 * 100
      = duration_hours * (avg_hr / LTHR)^2 * 100
```
- 所需用户参数：LTHR（按运动类型）

#### TSS 计算策略

| 运动类型 | 首选 TSS | 备选 | 所需参数 |
|---------|---------|------|---------|
| 骑行（有功率） | 功率 TSS | hrTSS | FTP |
| 骑行（无功率） | hrTSS | — | cycling_lthr |
| 跑步 | hrTSS | — | running_lthr |
| 步行 | hrTSS | — | walking_lthr |

### 1.5 分区时间统计

#### 心率分区时间（hr_zones_time）— Joe Friel 5 区

| 区间 | 名称 | 范围（%LTHR） |
|------|------|--------------|
| Z1 | 恢复区 | < 68% |
| Z2 | 有氧耐力区 | 68% - 83% |
| Z3 | 节奏区 | 83% - 94% |
| Z4 | 阈值区 | 94% - 105% |
| Z5 | VO2max+ | > 105% |

#### 功率分区时间（power_zones_time）— Coggan 7 区

| 区间 | 名称 | 范围（%FTP） |
|------|------|-------------|
| Z1 | 主动恢复 | < 55% |
| Z2 | 耐力区 | 55% - 75% |
| Z3 | 节奏区 | 75% - 90% |
| Z4 | 阈值区 | 90% - 105% |
| Z5 | VO2max 区 | 105% - 120% |
| Z6 | 无氧能力区 | 120% - 150% |
| Z7 | 神经肌肉区 | > 150% |

## 二、用户维度累积指标（PMC 体系）

### CTL — 慢性训练负荷 / "Fitness"

```
CTL_today = CTL_yesterday + (TSS_today - CTL_yesterday) * alpha_ctl
alpha_ctl = 1 - e^(-1/42) ≈ 0.02353
```
- 时间常数：42 天（约 6 周）
- 反映长期有氧适应水平

### ATL — 急性训练负荷 / "Fatigue"

```
ATL_today = ATL_yesterday + (TSS_today - ATL_yesterday) * alpha_atl
alpha_atl = 1 - e^(-1/7) ≈ 0.13307
```
- 时间常数：7 天
- 反映当前疲劳程度

### TSB — 训练压力平衡 / "Form"

```
TSB_today = CTL_today - ATL_today
```

| TSB 范围 | 状态 |
|---------|------|
| > +25 | 非常清新（比赛高峰） |
| +10 ~ +25 | 清新（适合比赛） |
| -10 ~ +10 | 中性（正常训练） |
| -10 ~ -30 | 疲劳（训练积累期） |
| < -30 | 过度疲劳（有风险） |

### PMC 计算要点

1. 以日历天为单位，每日 TSS = 当天所有运动 TSS 之和
2. 无运动日 TSS = 0，CTL/ATL 仍会衰减
3. 初始值：CTL_0 = ATL_0 = 0
4. 用户修改参数后，从生效日期起重算所有 TSS，再重算 CTL/ATL/TSB

## 三、ComputedMetrics 模型字段扩展

```
# 已有：
tss, hr_tss, intensity_factor, normalized_power, hr_zones_time, power_zones_time

# 需新增：
variability_index      # VI（骑行）
efficiency_factor      # EF（功率EF 或 HR EF）
work_kj                # 总做功 kJ（骑行）
hr_intensity_factor    # HR_IF（全部运动）
tss_method             # TSS 方法标记："power" / "hr" / null
```
