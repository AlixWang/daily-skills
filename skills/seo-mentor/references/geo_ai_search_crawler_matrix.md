# AI Search Crawlers & Governance Matrix

| Crawler User-Agent | Operator | Role & Purpose | Recommended Policy |
| :--- | :--- | :--- | :--- |
| **OAI-SearchBot** | OpenAI | ChatGPT Search real-time web indexer | **ALLOW** (Never block if ChatGPT traffic is wanted) |
| **ChatGPT-User** | OpenAI | User-initiated link inspection in ChatGPT chat | **ALLOW** (Enables users to ask about your site directly) |
| **PerplexityBot** | Perplexity AI | Search and real-time citation fetcher | **ALLOW** (Powers Perplexity citations & answers) |
| **Perplexity-User**| Perplexity AI | User-triggered real-time URL inspection | **ALLOW** |
| **Claude-SearchBot**| Anthropic | Claude Search real-time indexer | **ALLOW** |
| **Applebot** / **Applebot-Extended** | Apple | Apple Intelligence & Siri search grounding | **ALLOW** |
| **Google-Extended** | Google | Powers Gemini & Google AI ecosystem grounding | **ALLOW** |
| **GPTBot** | OpenAI | Offline model pre-training scraper | Optional (Block if you object to LLM training data extraction) |
| **ClaudeBot** | Anthropic | Offline model pre-training scraper | Optional |
| **CCBot** | Common Crawl | Massive open web dump scraper | Optional |
| **Bytespider** | ByteDance | Heavy training crawler | Optional / Disallow if bandwidth is constrained |
