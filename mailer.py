import datetime
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fetchers.base import Item

logger = logging.getLogger(__name__)

CATEGORY_LABELS = {
    "news": "\U0001f525 新闻热点",
    "tech": "\U0001f4bb 科技前沿",
    "academic": "\U0001f4da 学术前沿",
}

CSS = """
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
       'PingFang SC', 'Microsoft YaHei', sans-serif;
       max-width: 720px; margin: 0 auto; padding: 20px;
       background: #f5f5f5; }
.container { background: #fff; border-radius: 8px; padding: 24px;
             box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.header { text-align: center; padding-bottom: 16px;
          border-bottom: 1px solid #eee; margin-bottom: 20px; }
.header h1 { color: #1a1a1a; font-size: 22px; margin: 0 0 4px 0; }
.header .date { color: #888; font-size: 14px; }
.section { margin-bottom: 24px; }
.section h2 { color: #333; font-size: 17px; border-left: 3px solid #1677ff;
              padding-left: 10px; margin: 0 0 12px 0; }
.item { padding: 8px 0; border-bottom: 1px dashed #f0f0f0; }
.item:last-child { border-bottom: none; }
.item a { color: #1677ff; text-decoration: none; font-weight: 500; }
.item a:hover { text-decoration: underline; }
.item .summary { color: #555; font-size: 13px; margin-top: 2px; }
.item .source { color: #aaa; font-size: 11px; }
.footer { text-align: center; color: #bbb; font-size: 12px;
          margin-top: 24px; padding-top: 16px; border-top: 1px solid #eee; }
"""


def build_html(items: list[Item], date: datetime.date) -> str:
    grouped: dict[str, list[Item]] = {"news": [], "tech": [], "academic": []}
    for item in items:
        if item.category in grouped:
            grouped[item.category].append(item)

    date_str = f"{date.year}年{date.month}月{date.day}日"

    sections_html = ""
    for category, label in CATEGORY_LABELS.items():
        cat_items = grouped.get(category, [])
        if not cat_items:
            continue
        items_html = ""
        for item in cat_items:
            items_html += (
                f'<div class="item">'
                f'<a href="{item.url}">{item.title}</a>'
                f'<span class="source"> [{item.source}]</span>'
                f'<div class="summary">{item.snippet}</div>'
                f'</div>\n'
            )
        count = len(cat_items)
        sections_html += (
            f'<div class="section">'
            f'<h2>{label} ({count}条)</h2>'
            f'{items_html}'
            f'</div>\n'
        )

    if not sections_html:
        sections_html = '<p style="text-align:center;color:#888;">今日暂无资讯</p>'

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"></head>
<body>
<div class="container">
  <div class="header">
    <h1>\U0001f4f0 每日资讯摘要</h1>
    <div class="date">{date_str}</div>
  </div>
  {sections_html}
  <div class="footer">由 GitHub Actions 自动生成 | {date_str}</div>
</div>
<style>{CSS}</style>
</body>
</html>"""


def send_mail(
    items: list[Item],
    email_config: dict,
    password: str,
) -> None:
    today = datetime.date.today()
    html = build_html(items, today)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"每日资讯摘要 | {today.isoformat()}"
    msg["From"] = email_config["from_address"]
    msg["To"] = email_config["to_address"]
    msg.attach(MIMEText(html, "html", "utf-8"))

    smtp_host = email_config["smtp_host"]
    smtp_port = email_config["smtp_port"]

    logger.info(f"Connecting to {smtp_host}:{smtp_port}")
    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
        server.starttls()
        server.login(email_config["from_address"], password)
        server.send_message(msg)

    logger.info(
        f"Email sent: {len(items)} items to {email_config['to_address']}"
    )
