import markdown
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from io import BytesIO
from typing import Tuple
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import re
import urllib.request
import tempfile

class ReportExportService:
    """
    报告导出服务
    支持Markdown、PDF、Word格式导出
    """
    
    def __init__(self):
        self.chinese_font = None
        self.font_initialized = False
    
    def _init_fonts(self):
        """初始化中文字体，支持 Windows 和 Linux (Railway)"""
        if self.font_initialized:
            return
        
        self.font_initialized = True
        self.chinese_font = None
        
        font_paths = [
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/simsun.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                    self.chinese_font = 'ChineseFont'
                    print(f"字体初始化成功: {font_path}")
                    return
                except Exception as e:
                    print(f"字体注册失败 {font_path}: {e}")
                    continue
        
        print("未找到系统中文字体，尝试下载 Noto Sans SC...")
        
        try:
            font_url = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansSC-Regular.otf"
            font_dir = os.path.join(tempfile.gettempdir(), "fonts")
            os.makedirs(font_dir, exist_ok=True)
            font_path = os.path.join(font_dir, "NotoSansSC-Regular.otf")
            
            if not os.path.exists(font_path):
                print(f"下载字体到: {font_path}")
                urllib.request.urlretrieve(font_url, font_path)
                print("字体下载完成")
            
            if os.path.exists(font_path) and os.path.getsize(font_path) > 1000:
                pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                self.chinese_font = 'ChineseFont'
                print("字体注册成功: NotoSansSC-Regular.otf")
            else:
                print("字体文件无效")
        except Exception as e:
            print(f"字体下载失败: {e}")
            print("将使用默认字体 (可能不支持中文)")
        
        if not self.chinese_font:
            print("警告: 未找到中文字体，PDF 导出可能会出现乱码")
    
    def export_markdown(self, content: str, title: str) -> Tuple[bytes, str]:
        """
        导出Markdown格式
        """
        filename = f"{title}.md"
        return content.encode('utf-8'), filename
    
    def export_pdf(self, content: str, title: str) -> Tuple[bytes, str]:
        """
        导出PDF格式
        使用reportlab生成PDF
        """
        # 延迟初始化字体，避免服务启动时阻塞
        self._init_fonts()
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        styles = getSampleStyleSheet()
        
        font_name = self.chinese_font if self.chinese_font else 'Helvetica'
        
        title_style = ParagraphStyle(
            'ChineseTitle',
            parent=styles['Title'],
            fontName=font_name,
            fontSize=18,
            leading=24,
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        heading1_style = ParagraphStyle(
            'ChineseHeading1',
            parent=styles['Heading1'],
            fontName=font_name,
            fontSize=16,
            leading=20,
            spaceBefore=16,
            spaceAfter=10
        )
        
        heading2_style = ParagraphStyle(
            'ChineseHeading2',
            parent=styles['Heading2'],
            fontName=font_name,
            fontSize=14,
            leading=18,
            spaceBefore=12,
            spaceAfter=8
        )
        
        heading3_style = ParagraphStyle(
            'ChineseHeading3',
            parent=styles['Heading3'],
            fontName=font_name,
            fontSize=12,
            leading=16,
            spaceBefore=10,
            spaceAfter=6
        )
        
        body_style = ParagraphStyle(
            'ChineseBody',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=11,
            leading=16,
            alignment=TA_JUSTIFY,
            spaceBefore=4,
            spaceAfter=4
        )
        
        bullet_style = ParagraphStyle(
            'ChineseBullet',
            parent=body_style,
            leftIndent=20,
            bulletIndent=10
        )
        
        story = []
        
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 0.5*cm))
        
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            line = self._escape_html(line)
            
            if line.startswith('# '):
                text = line[2:]
                story.append(Paragraph(text, heading1_style))
            elif line.startswith('## '):
                text = line[3:]
                story.append(Paragraph(text, heading2_style))
            elif line.startswith('### '):
                text = line[4:]
                story.append(Paragraph(text, heading3_style))
            elif line.startswith('- '):
                text = '• ' + line[2:]
                story.append(Paragraph(text, bullet_style))
            elif line.startswith('**') and line.endswith('**'):
                text = '<b>' + line.strip('*') + '</b>'
                story.append(Paragraph(text, body_style))
            else:
                story.append(Paragraph(line, body_style))
        
        doc.build(story)
        buffer.seek(0)
        
        filename = f"{title}.pdf"
        return buffer.read(), filename
    
    def _escape_html(self, text: str) -> str:
        """转义HTML特殊字符"""
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        return text
    
    def export_docx(self, content: str, title: str) -> Tuple[bytes, str]:
        """
        导出Word格式
        统一格式：标题、副标题、正文使用一致的样式
        """
        doc = Document()
        
        title_heading = doc.add_heading(title, 0)
        title_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
        self._set_heading_font(title_heading, 22, RGBColor(0, 51, 102))
        
        lines = content.split('\n')
        
        for line in lines:
            original_line = line
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('# '):
                heading = doc.add_heading(line[2:], 1)
                self._set_heading_font(heading, 18, RGBColor(0, 51, 102))
            elif line.startswith('## '):
                heading = doc.add_heading(line[3:], 2)
                self._set_heading_font(heading, 16, RGBColor(0, 76, 153))
            elif line.startswith('### '):
                heading = doc.add_heading(line[4:], 3)
                self._set_heading_font(heading, 14, RGBColor(0, 102, 153))
            elif line.startswith('- '):
                p = doc.add_paragraph(style='List Bullet')
                run = p.add_run(line[2:])
                self._set_run_font(run, 11)
            elif line.startswith('**') and line.endswith('**'):
                p = doc.add_paragraph()
                run = p.add_run(line.strip('*'))
                run.bold = True
                self._set_run_font(run, 11)
            else:
                p = doc.add_paragraph()
                run = p.add_run(line)
                self._set_run_font(run, 11)
        
        docx_buffer = BytesIO()
        doc.save(docx_buffer)
        docx_buffer.seek(0)
        
        filename = f"{title}.docx"
        return docx_buffer.read(), filename
    
    def _set_heading_font(self, heading, size: int, color: RGBColor):
        """设置标题字体"""
        for run in heading.runs:
            run.font.size = Pt(size)
            run.font.color.rgb = color
            run.font.bold = True
            run.font.name = '微软雅黑'
            run._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    
    def _set_run_font(self, run, size: int):
        """设置正文字体"""
        run.font.size = Pt(size)
        run.font.name = '微软雅黑'
        run._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

report_export_service = ReportExportService()
