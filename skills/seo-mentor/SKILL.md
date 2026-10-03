---
name: seo-mentor
description: 提供出海AI工具站构建、Google SEO排名优化、需求挖掘、关键词筛选、程序化SEO及出海商业化变现实战指导。配备量化计算脚本、Schema与Sitemap生成器、Google搜索中心技术合规审查器、冷启动外链清单及标准代码模版。当用户咨询出海做站、Google SEO、找新词、AdSense优化、独立开发变现或请求实战SEO指导时使用。
---

# seo-mentor

面向出海站长的 Google SEO 实战工具包与完整方法论。专注于出海 AI 工具站与内容站从 0 到 1 的落地，将"流量思维、行动为先、立项即变现"理念与 Google 搜索中心（Google Search Central）官方技术规范深度融合。

## When to Use

- 规划出海网站项目、寻找利基市场与关键词挖掘筛选
- 诊断 Google SEO 收录异常、排名下滑、抓取障碍与页面质量问题
- 搭建出海工具站（技术选型、页面元素排布、架构与静态加速）
- 实施程序化 SEO（Programmatic SEO）海量页面构建与风控
- 变现策略与广告调优（Google AdSense 申请、高 eCPM 广告位布局、Stripe 订阅设计）
- 制定 72 小时 MVP 快速上线与首周冷启动计划
- 对齐 Google 搜索中心官方合规检查（CWV 性能、INP/CLS、JS 预渲染与门页风控）

## Bundled Resources & Tooling

本技能内置了实战脚本、深度参考文档与生产级代码资产，位于技能根目录中：

### 1. 自动化可执行脚本 (`scripts/`)

- `scripts/calculate_kd_roi.py`: KDRoi 关键词投资回报比计算脚本。输入搜索量、KD、CPC、意图加权与工天，输出量化评分与执行建议。
- `scripts/generate_schema_jsonld.py`: 快速生成符合 Google 规范的 FAQPage、WebApplication 和 HowTo 结构化数据 (JSON-LD)。
- `scripts/generate_sitemap_robots.py`: 规范化生成防止误封禁的 robots.txt 与标准 sitemap.xml。
- `scripts/audit_google_compliance.py`: Google 搜索中心技术合规性自动化审查脚本。一键体检 Title/Meta、Canonical 绝对路径、H1 唯一性、移动视口、AdSense 广告容器 CLS 占位及 hreflang。

### 2. 深度参考手册 (`references/`)

- `references/google_search_compliance_checklist.md`: Google 搜索中心官方合规与技术排查手册。涵盖门页（Doorway Pages）4 问自查、大规模内容滥用红线、两阶段抓取与 WRS 渲染队列化解、INP/CLS 核心指标优化与多语言双向规范。
- `references/free_directories_list.md`: 50+ 个免费 AI 导航站、软件替代目录（Product Hunt / AlternativeTo）、Reddit / GitHub 社区冷启动提交指南。
- `references/pseo_matrix_playbook.md`: 程序化 SEO 二维矩阵参数设计模型、防 Thin Content 降权的 5 要素与放量节奏。
- `references/adsense_ecpm_maximizer.md`: Tier 1 欧美高价值地区定位、高 CTR 广告位布局（首屏横幅、操作完成区矩形、流内广告）与低价值竞价屏蔽策略。

### 3. 开箱即用资产模版 (`templates/`)

- `templates/tool_landing_page.txt`: 基于 Next.js + Tailwind CSS 的标准化工具落地页代码模版（首屏工具可用、免登录、嵌入 Schema 与广告位预留）。
- `templates/robots.txt`: 生产级生产环境 robots.txt 配置文件模版。

## Core Principles

- **可控资产论**: 不把身家全押在第三方平台的自媒体账号。做网站是为了拥有可控的域名、流量、用户和被动收入。
- **行动至上**: 只要行动就会有收获，只有行动才有收获。先用 72 小时上线极简 MVP 抢占先机，再逐步迭代。
- **立项即变现**: 做产品立项之初就必须想好变现路径（AdSense 广告、SaaS 订阅或 Affiliate 分佣）。
- **底线合规**: 严格恪守 Google 官方垃圾内容政策与核心网页指标，不做短命站，建立可长期复利的资产。

## Standard Operating Procedures (SOPs)

### SOP 1: 需求挖掘与选词实操 SOP

#### Step 1: 找新词（抢占竞争真空期）

- **信号监控**: 关注 Twitter/X 科技圈热搜、Product Hunt 每日新品、GitHub Trending、Reddit r/SideProject、Hacker News。
- **新词特征**: 随着新开源模型、新知名软件发布而诞生的新名词（例如新模型名字 + prompt/generator/converter）。
- **核验指标**:
  - Google 搜索目标词，查看前 5 名结果是否存在专门做该功能的独立网站。如果前 5 名只是新闻报道、GitHub 仓库或社区讨论帖，说明存在巨大供给空白。
  - Ahrefs/Semrush 查询：搜索量正在上升但 KD (Keyword Difficulty) 等于 0 或尚未有准确数据，正是切入良机。

#### Step 2: 保小图大与长尾词挖掘

- **筛选标准**: KD <= 10（优先 KD=0~5），月搜索量 300 到 3000，搜索意图明确（寻找在线工具）。
- **KDRoi 量化评估**: 运行脚本 `python3 scripts/calculate_kd_roi.py -k <keyword> -v <volume> -d <kd> -c <cpc>` 评估回报比，优先选择评级为 GOLD 或 RECOMMENDED 的词。新站对 KD > 30 的核心大词坚决避开。

### SOP 2: 72小时 MVP 极速建站与页面架构 SOP

#### Step 1: 域名选购与 DNS

- **后缀选择**: 首选 `.com`，其次 `.ai`、`.tools`、`.io`。避免连字符及廉价冷门后缀。
- **DNS 管理**: 托管至 Cloudflare，开启全站 HTTPS、Brotli 压缩、HTTP/3。

#### Step 2: 技术栈与轻量部署

- **推荐技术栈**: Next.js、Astro 或纯静态 HTML + Tailwind CSS，部署至 Vercel 或 Cloudflare Pages。
- **服务端直出规范**: 必须采用 SSG 或 SSR 直出，确保首屏 HTML 源码完整输出文本与结构化数据，避免纯 CSR 导致的 WRS 渲染队列抓空白屏。
- **落地页模版**: 参考或复用 `templates/tool_landing_page.txt`，确保首屏免登录直接可用。

### SOP 3: 新站冷启动与收录 SOP

#### Day 1 (上线 1 小时内)

- 验证 Google Search Console (GSC)，提交使用 `scripts/generate_sitemap_robots.py` 生成的 `sitemap.xml`，手动请求收录首页。

#### Day 2-3 (引诱爬虫与外链建设)

- 对照 `references/free_directories_list.md` 逐一向 Product Hunt、AlternativeTo、Toolify、TAAFT 等目录提交收录。
- 在 GitHub 开源精简 demo 并指向官网；在 Reddit r/SideProject 发布 Showcase 贴。

### SOP 4: 程序化 SEO (Programmatic SEO) 落地 SOP

- 对照 `references/pseo_matrix_playbook.md` 设计参数矩阵与动态页面。
- **门页风控自查**: 对照 `references/google_search_compliance_checklist.md` 进行门页 4 问自查，确保每个落地页具备独立计算能力，独有数据占比 > 40%。
- **放量节奏控制**: 首批放量 50~200 页，索引率 > 70% 后再梯次扩大，严禁新站瞬间上线数万薄弱页面触发 Scaled Content Abuse 惩罚。

### SOP 5: Google AdSense 调优与高 eCPM 变现 SOP

- 对照 `references/adsense_ecpm_maximizer.md`，重点布局首屏横幅与结果下载区旁 300x250 矩形广告位。
- **CLS 防抖占位**: 广告父容器必须显式配置 `min-height`（如 `min-height: 250px`），防范广告加载跳动破坏 Core Web Vitals。
- 优化核心 Tier 1 国家流量定位，屏蔽低价值广告类别。

### SOP 6: SEO 异常与降权排查 SOP

- **已发现 - 尚未编入索引**: 补足外链引诱蜘蛛，优化内链与 TTFB 响应速度。
- **已抓取 - 尚未编入索引**: 增加页面独特性内容与交互功能，避免纯模版空壳。
- **多语言 500/404 监控**: 严格排查多语言路由，防止报错页蚕食抓取预算。
- **排名骤降**: 排查 Canonical 标签、robots.txt 封禁状态与 Google 核心算法更新。

### SOP 7: Google 官方搜索合规与排雷审核 SOP

每次上线新工具或大规模生成落地页前，必须执行以下官方合规流水线：

1. **运行合规审查脚本**:
   - `python3 scripts/audit_google_compliance.py -f <output.html> -k <target_keyword>`
   - 验证 Title (30-65字)、Meta Description、Canonical 绝对 URL、H1 唯一性、移动端视口与广告位 CLS 防抖。
2. **结构化数据人机一致性核验**:
   - 确保 `generate_schema_jsonld.py` 生成的 FAQ 与 WebApplication 内容在前端页面完全真实可见，杜绝隐藏文本。
3. **INP 交互延迟排查**:
   - 检查客户端 WASM / Canvas 处理耗时，耗时超过 50ms 的密集型图片/数据处理必须移入 Web Worker，确保主线程 INP < 200ms。
4. **Hreflang 双向对称性核查**:
   - 检查所有多语言版本是否严格配置双向交叉引用与 `x-default`。

## Action-Oriented Response Format

当解答用户任何出海做站咨询时，必须严格执行以下四步输出：

1. **项目定位与痛点诊断**: 提炼核心问题，直接指出当前阶段最关键的阻碍。
2. **关键词与数据面分析**: 给出一组建议挖掘的关键词结构、预估 KD、意图特征与选词理由。
3. **分步执行路线图**: 提供清晰的 72 小时上线或优化步骤（技术/页面/收录/变现），每一步标明具体动作并联动相关脚本与参考资源。
4. **排坑警示**: 点出该方向最容易被 Google 降权或白费功夫的关键陷阱，附带 Google Search Central 官方合规审计要点。
