# 每日资讯摘要推送系统 — 设计文档

## 概述

自动抓取新闻热点、科技前沿、学术前沿资讯，通过 DeepSeek API 生成中文摘要，每天定时通过邮件推送给用户。

- **用户：** 单人使用
- **学术/科技领域：** 电子信息、人工智能、计算机
- **触发方式：** GitHub Actions 每天北京时间 9:00 定时运行
- **推送渠道：** QQ邮箱 SMTP

---

## 项目结构

```
daily-digest/
├── main.py                  # 编排入口：串联全流程
├── config.yaml              # 信息源、领域关键词、推送时间配置
├── requirements.txt
├── pyproject.toml
├── fetchers/
│   ├── __init__.py
│   ├── base.py              # 抽象基类：定义抓取器接口
│   ├── news.py              # 新闻热点（微博/知乎/36氪）
│   ├── tech.py              # 科技前沿（HN, GitHub Trending, Papers with Code）
│   └── academic.py          # 学术前沿（arXiv API）
├── summarizer.py            # DeepSeek API 摘要生成
├── mailer.py                # HTML 邮件生成 + QQ邮箱 SMTP 发送
├── dedup.py                 # URL 去重 + 标题相似度去重
└── .github/workflows/
    └── daily.yml            # 定时触发 + 环境变量注入
```

---

## 数据流

```
GitHub Actions 触发 (UTC 1:00 / CST 9:00)
  → main.py 读取 config.yaml
  → 并行调用 fetchers/*.py 抓取各信息源
  → dedup.py 去重合并
  → summarizer.py 逐条调用 DeepSeek 生成摘要
  → mailer.py 组装 HTML 邮件
  → 通过 QQ SMTP 发送到用户邮箱
```

---

## 模块设计

### 1. 信息源与抓取器 (`fetchers/`)

#### 新闻热点 (`news.py`)
| 源 | 抓取方式 | URL |
|---|---|---|
| 微博热搜 | requests + HTML 解析 | https://weibo.com/ajax/side/hotSearch |
| 知乎热榜 | requests + HTML 解析 | https://www.zhihu.com/hot |
| 36氪快讯 | requests + HTML 解析 | https://36kr.com/newsflashes |

#### 科技前沿 (`tech.py`)
| 源 | 抓取方式 | URL |
|---|---|---|
| Hacker News Top 30 | HN 官方 JSON API | https://hacker-news.firebaseio.com/v0/topstories |
| GitHub Trending | requests + HTML 解析 | https://github.com/trending |
| Papers with Code Trending | requests + HTML 解析 | https://paperswithcode.com/ |

#### 学术前沿 (`academic.py`)
| 源 | 抓取方式 | URL |
|---|---|---|
| arXiv API (cs.AI, cs.CL, cs.CV, cs.LG, eess.SP) | arXiv 官方 API | http://export.arxiv.org/api/query |
| Hugging Face Daily Papers | requests + HTML 解析 | https://huggingface.co/papers |

#### 统一数据模型 (`base.py`)
```python
@dataclass
class Item:
    title: str
    url: str
    source: str          # "weibo" | "zhihu" | "hackernews" | "arxiv" ...
    snippet: str         # 原始简短描述，供 AI 摘要用
    category: str        # "news" | "tech" | "academic"
```

每个抓取器实现 `fetch() -> List[Item]` 接口。

### 2. 去重 (`dedup.py`)

- URL 完全相同 → 直接去重
- 标题相似度 > 0.85（基于 difflib.SequenceMatcher）→ 视为重复，保留先抓到的
- 跨源去重（同一篇论文可能同时出现在 arXiv 和 Hugging Face）

### 3. AI 摘要 (`summarizer.py`)

- 调用 DeepSeek Chat API（`deepseek-chat` 模型）
- 输入 `title + snippet`，输出 30~50 字中文摘要
- Prompt：
  ```
  用一句中文（30~50字）概括以下内容的要点，直接给出摘要，不要任何前缀：
  标题：{title}
  内容：{snippet}
  ```
- 按 category 分组逐条处理
- 失败重试 2 次，仍失败则降级为原文 snippet
- 控制并发：顺序请求，间隔 0.5s，避免触发 rate limit

### 4. 邮件生成与发送 (`mailer.py`)

**邮件格式：**
- Subject: `每日资讯摘要 | YYYY-MM-DD`
- HTML body，按 category 分组展示
- 每条：标题（超链接）—— AI 摘要
- 纯 HTML + 内联 CSS，不依赖外部资源，兼容主流邮箱客户端
- 页脚标注 "由 GitHub Actions 自动生成"

**发送：**
- QQ 邮箱 SMTP：`smtp.qq.com:587`，STARTTLS
- 发件人 = 收件人（自己发给自己）
- 授权码通过 GitHub Secrets 注入（`QQ_SMTP_PASSWORD`）

### 5. 配置 (`config.yaml`)

```yaml
academic:
  arxiv_categories: ["cs.AI", "cs.CL", "cs.CV", "cs.LG", "eess.SP"]
  keywords: []

tech:
  sources: ["hackernews", "github_trending", "paperswithcode"]

news:
  sources: ["weibo", "zhihu", "36kr"]

email:
  smtp_host: "smtp.qq.com"
  smtp_port: 587
  to_address: "your@qq.com"
  send_time: "09:00"

deepseek:
  model: "deepseek-chat"
  max_tokens_per_item: 80
```

### 6. 编排入口 (`main.py`)

```python
def main():
    config = load_config("config.yaml")
    items = []
    items += fetch_news(config.news)
    items += fetch_tech(config.tech)
    items += fetch_academic(config.academic)
    items = deduplicate(items)
    items = summarize(items, config.deepseek)
    send_mail(items, config.email)
```

---

## 部署方案

### GitHub Actions (`daily.yml`)

- **触发：** `schedule: cron(0 1 * * *)` — UTC 1:00 = 北京时间 9:00
- **手动触发：** `workflow_dispatch`
- **环境：** `ubuntu-latest`, Python 3.12
- **Secrets：**
  - `DEEPSEEK_API_KEY` — DeepSeek API 密钥
  - `QQ_SMTP_PASSWORD` — QQ 邮箱 SMTP 授权码
- **日志保留：** 7 天

### 用户需准备

1. QQ 邮箱开启 SMTP 服务，获取授权码
2. DeepSeek API key（platform.deepseek.com 注册）
3. GitHub 仓库，配置两个 Secrets
4. 修改 `config.yaml` 中的邮箱地址

---

## 费用估算

- GitHub Actions：免费（公开仓库无限制，私有仓库 2000 分钟/月足够）
- DeepSeek API：约 ¥0.01~0.05/天（每天 50~80 条，每条约 150 tokens）
- QQ 邮箱 SMTP：免费

---

## 非功能需求

- **容错：** 单个信息源抓取失败不影响其他源，记录日志继续
- **去重：** URL 精确去重 + 标题相似度去重
- **限流：** API 请求间隔 0.5s，避免触发 rate limit
- **降级：** DeepSeek 调用失败时保留原文 snippet，不丢失信息
