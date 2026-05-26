# Daily Digest — 每日资讯摘要推送

每天自动抓取新闻热点、科技前沿、学术前沿资讯，通过 DeepSeek API 生成中文摘要，邮件推送。

## 信息源

**新闻热点：** 微博热搜、知乎热榜、36氪快讯
**科技前沿：** Hacker News、GitHub Trending、Papers with Code
**学术前沿：** arXiv (cs.AI/CL/CV/LG + eess.SP)、Hugging Face Daily Papers

## 快速开始

1. Fork 此仓库
2. 修改 `config.yaml` 中的邮箱地址
3. 在仓库 Settings → Secrets and variables → Actions 中添加：
   - `DEEPSEEK_API_KEY`：DeepSeek API 密钥 (platform.deepseek.com)
   - `QQ_SMTP_PASSWORD`：QQ邮箱 SMTP 授权码

## 本地运行

```bash
pip install -r requirements.txt
DEEPSEEK_API_KEY=your_key QQ_SMTP_PASSWORD=your_pass python main.py
```

## 定时推送

GitHub Actions 每天北京时间 9:00 自动运行，也可在 Actions 页面手动触发。
