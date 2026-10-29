# 关键词稀释诊断报告 · {{site}}

- 诊断日期：{{date}}
- 目标页面：{{url}}
- 主攻词：{{primary_keyword}}（月搜索量 {{volume}}，KD {{kd}}）
- 站点 DR：{{dr}}
- 数据来源：`analyze_keyword_dilution.py` / `simulate_link_equity.py` 输出

## 1. 结论摘要

| 指标 | 整改前 | 整改后 | 目标 |
| --- | --- | --- | --- |
| 主词 relevance | {{before_relevance}} | {{after_relevance}} | ≥ 0.75 |
| dilution_index | {{before_dilution}} | {{after_dilution}} | ≤ 0.25 |
| Title 精确短语 | {{before_title_phrase}} | {{after_title_phrase}} | 命中 |
| H1 精确短语 | {{before_h1_phrase}} | {{after_h1_phrase}} | 命中 |
| 意图冲突 | {{before_conflicts}} | {{after_conflicts}} | 无 |
| 单页权重份额 | {{before_share}}% | {{after_share}}% | 见第 4 节 |

一句话结论：{{one_line_verdict}}

## 2. 页面字段证据

| 字段 | 内容 | token 数 | 长度惩罚 | 覆盖率 | 精确短语 | 字段得分 |
| --- | --- | --- | --- | --- | --- | --- |
| Title | {{title}} | {{title_tokens}} | {{title_penalty}} | {{title_coverage}} | {{title_exact}} | {{title_relevance}} |
| H1 | {{h1}} | {{h1_tokens}} | {{h1_penalty}} | {{h1_coverage}} | {{h1_exact}} | {{h1_relevance}} |
| 正文 | {{word_count}} words | {{body_tokens}} | — | {{body_coverage}} | {{body_exact}} | {{body_relevance}} |

命中明细：

- Title 命中的查询词：{{title_hits}}
- Title 缺失的查询词：{{title_missing}}
- H1 命中的查询词：{{h1_hits}}
- 首次命中位置（Title）：第 {{title_position}} 个 token

## 3. 意图冲突

| 关键词 | 月搜索量 | 意图 | 页面覆盖率 | 意图纯度 | 判定 |
| --- | --- | --- | --- | --- | --- |
| {{kw1}} | {{vol1}} | {{intent1}} | {{cov1}} | {{purity1}} | {{verdict1}} |
| {{kw2}} | {{vol2}} | {{intent2}} | {{cov2}} | {{purity2}} | {{verdict2}} |
| {{kw3}} | {{vol3}} | {{intent3}} | {{cov3}} | {{purity3}} | {{verdict3}} |

冲突结论：{{conflict_summary}}

## 4. 整站权重

| 指标 | 数值 |
| --- | --- |
| 页面总数 | {{total_pages}} |
| 分组数 | {{group_count}} |
| 索引配额压力 | {{quota_pressure}}x |
| 需裁剪页数 | {{prune_count}} |
| 核心组单页份额（当前） | {{avg_share_before}}% |
| 核心组单页份额（聚焦后） | {{avg_share_after}}% |
| 聚焦增益 | {{focus_gain}}x |

分组明细：

| 分组 | 页面数 | 权重份额 | 单页均值 |
| --- | --- | --- | --- |
| {{group}} | {{group_pages}} | {{group_share}}% | {{group_avg}}% |

## 5. 整改方案（一页一词）

| 维度 | 整改前 | 整改后 |
| --- | --- | --- |
| 首页主攻词 | {{before_keywords}} | {{after_keyword}} |
| 首页 Title | {{before_title}} | {{after_title}} |
| 首页 H1 | {{before_h1}} | {{after_h1}} |
| 被剥离意图 | 全部挤在首页 | {{split_pages}} |
| 多语言策略 | {{before_locales}} | {{after_locales}} |
| 内链结构 | {{before_links}} | {{after_links}} |

拆分清单：

| 新 URL | 承接关键词 | 独立交互/内容 | 内链来源 |
| --- | --- | --- | --- |
| {{new_url}} | {{new_keyword}} | {{unique_feature}} | {{link_source}} |

## 6. 验收与复查

```bash
# 页面级
python3 scripts/analyze_keyword_dilution.py -f {{page_file}} -k "{{primary_keyword}}" --json

# 整站级
python3 scripts/simulate_link_equity.py -s {{site_json}} --compare-group {{core_group}} --json

# 可竞争性
python3 scripts/calculate_kd_roi.py -k "{{primary_keyword}}" -v {{volume}} -d {{kd}} -c {{cpc}} -a {{dr}} --json
```

通过标准：

- [ ] 主词 relevance ≥ 0.75，`KWD-01` 不再出现
- [ ] Title/H1 均包含完整连续短语
- [ ] `conflicts` 为空
- [ ] `focus_gain` 回落到 1.0 附近（说明已聚焦）
- [ ] `prune_count` 为 0 或已执行裁剪

## 7. 风险提示

- {{risk_1}}
- {{risk_2}}
- 本报告基于启发式模型，数值用于横向比较与改造验收，不代表 Google 实际排序分数。
