import os
import uuid
import tempfile
from typing import Optional, Tuple
import fitz
from docx import Document
import asyncio

class FileParser:
    """
    文件解析服务
    支持PDF和Word文档解析
    """
    
    def __init__(self):
        self.upload_dir = "uploads"
        os.makedirs(self.upload_dir, exist_ok=True)
    
    async def parse_file(self, file_content: bytes, filename: str) -> str:
        """
        解析文件内容
        
        Args:
            file_content: 文件内容
            filename: 原始文件名
        
        Returns:
            文件内容文本
        """
        ext = os.path.splitext(filename)[1].lower()
        
        if ext == ".pdf":
            return await asyncio.to_thread(self._parse_pdf, file_content)
        elif ext in [".docx", ".doc"]:
            return await asyncio.to_thread(self._parse_docx, file_content, filename)
        elif ext in [".txt", ".md"]:
            return await asyncio.to_thread(self._parse_text, file_content)
        else:
            return f"不支持的文件类型: {ext}"
    
    def _parse_pdf(self, file_content: bytes) -> str:
        """
        解析PDF文件
        使用PyMuPDF提取文本
        """
        text_parts = []
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp:
            temp.write(file_content)
            temp_path = temp.name
        
        try:
            doc = fitz.open(temp_path)
            for page in doc:
                text = page.get_text()
                if text.strip():
                    text_parts.append(text.strip())
            doc.close()
        finally:
            os.unlink(temp_path)
        
        return "\n\n".join(text_parts)
    
    def _parse_docx(self, file_content: bytes, filename: str) -> str:
        """
        解析Word文档
        使用python-docx提取文本
        """
        text_parts = []
        ext = os.path.splitext(filename)[1].lower()
        
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp:
            temp.write(file_content)
            temp_path = temp.name
        
        try:
            doc = Document(temp_path)
            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                if text:
                    text_parts.append(text)
        except Exception as e:
            return f"解析Word文档失败: {str(e)}"
        finally:
            os.unlink(temp_path)
        
        return "\n\n".join(text_parts)
    
    def _parse_text(self, file_content: bytes) -> str:
        """
        解析文本文件
        """
        try:
            return file_content.decode('utf-8')
        except UnicodeDecodeError:
            return file_content.decode('gbk', errors='ignore')

file_parser = FileParser()
