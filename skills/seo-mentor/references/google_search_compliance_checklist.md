# Google 搜索中心 (Google Search Central) 官方合规与技术排查手册

本手册基于 Google 搜索中心官方文档（Google Search Essentials、Spam Policies、JavaScript SEO、Core Web Vitals 及 Structured Data Guidelines），为出海站长提供权威的技术防线与算法排雷指引。

## 一、 垃圾内容政策 (Spam Policies) 防御红线

### 1. 门页违规 (Doorway Pages) 自查 4 问
根据 Google 官方定义，为特定搜索查询建立的大量类似页面，若仅作为中间跳板，属于严重违规。进行程序化 SEO 时必须通过以下自查：
- [ ] 独立求解能力：用户进入该页面后，能否直接在该页面完成需求（如直接完成 HEIC 到 JPG 的本地转换与下载），而无需被迫二次跳转到主站首页？
- [ ] 实质性内容差异：除标题与参数名不同外，页面是否具备针对该参数的真实技术参数表、专有 FAQ 或特定说明？
- [ ] 用户意图契合度：页面是否只为了聚集特定词的搜索流量，还是真正为该特定格式/场景提供了最佳交互体验？
- [ ] 内链网状健康度：页面是否孤立存在？是否有清晰的面包屑导航（Breadcrumb）和相关场景的双向内链？

### 2. 大规模内容滥用 (Scaled Content Abuse) 红线
- 严禁全站使用 AI 机械批量拼凑毫无信息增量的文本。
- 程序化生成的页面中，由真实结构化数据或专用代码计算驱动的内容比例不得低于 40%。

## 二、 JavaScript SEO 与渲染架构规范

### 1. 规避两阶段抓取与渲染队列延迟
- Googlebot 运行机制：
  1. 第一阶段（Crawl）：下载初始 HTML 并提取纯文本与直出链接。
  2. 第二阶段（Render）：将包含复杂客户端 JS 的页面推入 Web Rendering Service (WRS) 队列，等待可用 Chromium 算力渲染。
- 官方黄金准则：
  - 静态预渲染 (SSG / Static Generation) 或服务端渲染 (SSR)：页面的 title、meta description、h1、核心功能说明与 FAQ 必须直接存在于服务端返回的初始 HTML 源码中。
  - 客户端水合 (Client-side Hydration)：工具的重度计算（WASM/Canvas）仅在用户交互时激活，绝不阻塞初始 HTML 内容的直接输出。

## 三、 核心网页指标 (Core Web Vitals) 性能优化

### 1. INP (Interaction to Next Paint) 交互延迟（须 < 200ms）
- 必须使用 Web Workers 将重型图像与数据计算移至后台线程，确保主线程始终能够即时响应用户的点击与拖拽。

### 2. CLS (Cumulative Layout Shift) 累积布局偏移（须 < 0.1）
- 在加载 Google AdSense 异步广告代码前，必须在父容器上通过 CSS 预设最小高度与宽度（如 min-height: 250px; min-width: 300px;），严禁无占位直接插入，避免广告渲染时把操作区剧烈下推。

### 3. LCP (Largest Contentful Paint) 最大内容绘制（须 < 2.5s）
- 启用 Cloudflare 边缘缓存与 HTTP/3。
- 首屏关键 CSS 采用内联，非关键资源推迟加载（defer / async）。

## 四、 结构化数据 (Schema.org) 真实性准则

### 1. 人机可见性一致原则 (Human Visibility)
- Google 明确规定：JSON-LD 标记中的所有内容必须对普通浏览用户完全可见。
- 严禁在 FAQPage JSON-LD 中添加页面正文未展示的问题。
- 严禁在工具站中伪造虚假的 AggregateRating 或用户评论。

## 五、 多语言与抓取预算 (Crawl Budget) 保护

### 1. 杜绝 500 错误与软 404
- 捕获国际化路由异常，语言包缺失时必须静默回退至英文缺省版，绝不向爬虫返回报错界面。

### 2. Hreflang 严格双向确认
- 语言标签必须具备双向确认，且必须包含未匹配地区的兜底标签：hreflang='x-default'。
