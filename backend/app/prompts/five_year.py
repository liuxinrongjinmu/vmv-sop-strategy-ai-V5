"""五年关键驱动因素分析Prompt加载器"""
from app.prompts import load_prompt

FIVE_YEAR_PROMPT = load_prompt("five_year.txt")


def get_five_year_prompt(prediction: str, context_text: str, prev_report_section: str, search_section: str) -> str:
    """
    生成五年关键驱动因素分析prompt
    :param prediction: 用户预判内容
    :param context_text: 上下文信息
    :param prev_report_section: 前序十年报告段落（已包含格式化）
    :param search_section: 搜索数据段落（已包含格式化）
    :return: 完整的prompt字符串
    """
    return FIVE_YEAR_PROMPT.format(
        prediction=prediction,
        context_text=context_text,
        prev_report_section=prev_report_section,
        search_section=search_section
    )
