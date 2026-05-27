import datetime
import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from fpdf import FPDF
from fetchers.base import Item

logger = logging.getLogger(__name__)

CATEGORY_LABELS = {
    "news": "社会热点",
    "tech": "科技前沿",
    "academic": "学术前沿",
}

FONT_PATHS = [
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simsun.ttc",
]


def _find_cjk_font() -> str:
    for p in FONT_PATHS:
        if os.path.exists(p):
            return p
    logger.warning("No CJK font found, PDF Chinese text may not render")
    return "Helvetica"


class DigestPDF(FPDF):
    def __init__(self):
        super().__init__("P", "mm", "A4")
        self.font_path = _find_cjk_font()
        self.add_font("cjk", fname=self.font_path)
        self.set_auto_page_break(True, 15)

    def header(self):
        if self.page_no() == 1:
            self.set_font("cjk", "", 22)
            self.cell(0, 12, "每日资讯摘要", align="C", new_x="LMARGIN", new_y="NEXT")
            today = datetime.date.today()
            date_str = f"{today.year}年{today.month}月{today.day}日"
            self.set_font("cjk", "", 10)
            self.set_text_color(120, 120, 120)
            self.cell(0, 8, date_str, align="C", new_x="LMARGIN", new_y="NEXT")
            self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("cjk", "", 8)
        self.set_text_color(180, 180, 180)
        self.cell(0, 10, "由 GitHub Actions 自动生成", align="C")

    def add_section(self, label: str, count: int):
        self.ln(4)
        self.set_font("cjk", "", 15)
        self.set_text_color(30, 30, 30)
        self.cell(0, 8, f"{label}  ({count}条)", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(22, 119, 255)
        self.set_line_width(0.6)
        line_y = self.get_y()
        self.line(10, line_y, 200, line_y)
        self.ln(4)

    def add_item(self, item: Item):
        self.set_font("cjk", "", 11)
        self.set_text_color(22, 119, 255)
        self.multi_cell(0, 6, item.title)

        self.set_font("cjk", "", 7)
        self.set_text_color(160, 160, 160)
        self.cell(0, 4, f"来源: {item.source}", new_x="LMARGIN", new_y="NEXT")

        self.set_font("cjk", "", 9)
        self.set_text_color(60, 60, 60)
        self.multi_cell(0, 5.5, item.snippet)

        self.set_x(self.l_margin)
        self.set_font("Courier", "", 7)
        self.set_text_color(140, 140, 140)
        self.multi_cell(0, 4, item.url)

        self.ln(2)


def build_pdf(items: list[Item], date: datetime.date) -> bytes:
    grouped: dict[str, list[Item]] = {"news": [], "tech": [], "academic": []}
    for item in items:
        if item.category in grouped:
            grouped[item.category].append(item)

    pdf = DigestPDF()
    pdf.add_page()

    has_content = False
    for category in ["news", "tech", "academic"]:
        cat_items = grouped.get(category, [])
        if not cat_items:
            continue
        has_content = True
        pdf.add_section(CATEGORY_LABELS[category], len(cat_items))
        for item in cat_items:
            pdf.add_item(item)

    if not has_content:
        pdf.set_font("cjk", "", 12)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 10, "今日暂无资讯", align="C")

    return pdf.output()


def send_mail(
    items: list[Item],
    email_config: dict,
    password: str,
) -> None:
    today = datetime.date.today()
    pdf_bytes = build_pdf(items, today)

    msg = MIMEMultipart()
    msg["Subject"] = f"每日资讯摘要 | {today.isoformat()}"
    msg["From"] = email_config["from_address"]
    msg["To"] = email_config["to_address"]

    body = MIMEText(
        f"今日资讯摘要 ({len(items)} 条)，详见附件 PDF。\n\n"
        f"由 GitHub Actions 自动生成 | {today.isoformat()}",
        "plain", "utf-8",
    )
    msg.attach(body)

    pdf_attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
    pdf_attachment.add_header(
        "Content-Disposition", "attachment",
        filename=f"daily-digest-{today.isoformat()}.pdf",
    )
    msg.attach(pdf_attachment)

    smtp_host = email_config["smtp_host"]
    smtp_port = email_config["smtp_port"]

    logger.info(f"Connecting to {smtp_host}:{smtp_port}")
    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
        server.starttls()
        server.login(email_config["from_address"], password)
        server.send_message(msg)

    logger.info(
        f"Email sent: PDF ({len(pdf_bytes)} bytes, {len(items)} items) "
        f"to {email_config['to_address']}"
    )
