# 关键词稀释模型（可执行版）

本手册解释 `analyze_keyword_dilution.py` 与 `simulate_link_equity.py` 背后的数学假设，以及如何用真实竞品数据标定参数。

> 边界声明：这里的 BM25、意图纯度与 PageRank 都是**启发式模型**，用于把「页面在几个词之间被摊薄」这件事变成可比较的数字。它们不是 Google 的线上排序公式，也不能用来预测具体排名。请把输出当作诊断标尺，而不是评分真理。

## 一、三层稀释模型

| 层 | 现实问题 | 脚本 | 核心指标 |
| --- | --- | --- | --- |
| 页面级 | Title/H1 塞入过多词，字段长度惩罚放大，精确短语被拆断 | `analyze_keyword_dilution.py` | `relevance`、`dilution_index`、`exact_phrase` |
| 意图级 | 一个页面同时讨好多个意图，语义重心落在中间地带 | `analyze_keyword_dilution.py` | `intent_purity`、`conflicts` |
| 整站级 | 外链权重与抓取配额被数百个页面均摊 | `simulate_link_equity.py` | `share_pct`、`focus_gain`、`prune_count` |

## 二、页面级：BM25 字段长度惩罚

单个词项在字段中的得分：

```text
term(t, D) = idf(t) * tf(t) * (k1 + 1) / (tf(t) + k1 * (1 - b + b * |D| / avgdl))
```

- `|D|`：字段 token 数；`avgdl`：同类字段的平均 token 数。
- `b` 控制长度惩罚强度，`k1` 控制词频饱和速度。
- 字段得分归一化为 `coverage = Σterm / Σidf`，上限 1.0。归一化后的 1.0 表示「查询词全部命中且字段长度正好等于平均值」。

脚本默认值：

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| `k1` | 1.2 | BM25 常规取值 |
| `b` | 0.75 | 常规取值；想弱化长度惩罚可降到 0.5 |
| `avgdl_title` | 6 | 出海工具站竞品 Title 的经验长度（英文词） |
| `avgdl_h1` | 5 | 竞品 H1 的经验长度 |
| `avgdl_body` | 正文实际词数 | 即正文不做长度惩罚，只做覆盖度 |

### 短语连续性

`has_exact_phrase()` 在归一化 token 序列上做连续子序列匹配。命中则字段权重不折半，否则乘 0.5：

```text
title_rel = coverage(title) * (1.0 if exact_phrase else 0.5)
```

这条规则对应「域名反词序 + Title 把词拆开」的场景：单词都在，但拿不到连续命中加分。

### 页面总分

```text
relevance      = 0.6 * title_rel + 0.3 * h1_rel + 0.1 * body_rel
dilution_index = 1 - relevance
```

判定区间：`< 0.5` DILUTED、`0.5–0.75` PARTIAL、`≥ 0.75` FOCUSED。

### 用竞品语料标定

`--corpus` 接受一个纯文本文件，每行一个竞品 Title：

```bash
python3 scripts/analyze_keyword_dilution.py -f page.html -k "free tts online" \
  --corpus competitor-titles.txt --json
```

脚本会用该语料计算 `avgdl_title`（平均 token 数）与每个查询词的 IDF。语料越贴近真实 SERP 前十，分数越有参考价值；没有语料时使用上面的经验默认值，并在 `params.idf_mode` 里标记为 `uniform`。

## 三、意图级：覆盖度分布近似

没有 embedding 依赖时，用「同一页面在各目标词上的覆盖度」近似语义重心：

```text
cov_k    = 0.5 * title_coverage_k + 0.3 * h1_coverage_k + 0.2 * body_coverage_k
purity_k = cov_k / Σ_j cov_j
```

冲突判定：前两名差距 `< 0.10` 且第二名 `≥ 0.30`。这表示页面在两个意图之间几乎平均用力，任一方向的纯度都不够。

局限：两个词如果本身高度同义（如 `tts` 与 `text to speech`），会天然拉不开差距，此时应把它们视为同一意图簇，而不是冲突。

## 四、整站级：内部链接权重分配

```text
pr(i) = (1 - d) / N + d * ( Σ_{j→i} pr(j) / outdeg(j) + dangling / N )
pr(home) += (1 - d) * external_weight
```

- `d = 0.85`，迭代到 `Σ|Δ| < 1e-9` 或 200 轮。
- 悬空页（无出链）的权重按全站均分。
- 首页额外注入 `external_weight`，代表外链带来的整站权重。

输出中每页的 `share_pct` 是归一化后的份额。`--compare-group en-core` 会只用该组页面重建子图，再算一次，得到 `focus_gain`：

```text
focus_gain = 聚焦后单页平均份额 / 聚焦前单页平均份额
```

### 拓扑输入

```json
{
  "site": "https://example.com",
  "external_weight": 1.0,
  "pages": [
    {"url": "/", "group": "en-core", "links_to": ["/tool-a", "/blog/x"]},
    {"url": "/tool-a", "group": "en-core"},
    {"url": "/es/", "group": "locale-es"}
  ]
}
```

- `links_to` 省略时按星型拓扑补边（首页 ↔ 全部页面），并在 `warnings` 中提示。
- 指向不存在页面的边会被丢弃，同样记入 `warnings`。
- `--index-quota`（默认 200）用于估算新站索引配额的超额页数 `prune_count`。

## 五、结果怎么读

| 现象 | 含义 | 动作 |
| --- | --- | --- |
| `relevance < 0.5` 且 `KWD-01` | Title 没有连续短语，或字段过长 | 前置精确短语，把次要词移出 Title |
| `KWD-03` 长度惩罚 > 1.3 | 分母膨胀 | 精简 Title 到 `avgdl_title × 1.3` 以内 |
| `conflicts` 非空 | 多意图拉扯 | 保留主词，其余拆独立落地页 |
| `focus_gain ≥ 10` | 页面数摊薄明显 | noindex/下线非核心组，先保核心页收录 |
| `prune_count > 0` | 超出索引配额 | 按 `recommendations` 裁剪后再放量 |

## 六、已知局限

1. 不抓取 SERP，`avgdl` 与 IDF 依赖用户提供的语料；默认值只是经验先验。
2. 意图纯度是覆盖度代理，不是神经语义相似度；同义词会被低估。
3. PageRank 模拟的是链接拓扑，不包含 Google 的信任传播、垃圾信号与沙盒效应。
4. 中文/日文按 unigram+bigram 处理，长词匹配粒度与英文不同，跨语言比较时只看趋势。
5. `relevance` 是页面内部指标，不含外链权威度；要与 `calculate_kd_roi.py -a <DR>` 联合判断可竞争性。
