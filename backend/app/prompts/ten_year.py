"""十年战略预判分析Prompt加载器"""
from app.prompts import load_prompt

TEN_YEAR_PROMPT = load_prompt("ten_year.txt")


def get_ten_year_prompt(prediction: str, context_text: str, search_section: str) -> str:
    """
    生成十年战略预判分析prompt
    :param prediction: 用户预判内容
    :param context_text: 上下文信息
    :param search_section: 搜索数据段落（已包含格式化）
    :return: 完整的prompt字符串
    """
    return TEN_YEAR_PROMPT.format(
        prediction=prediction,
        context_text=context_text,
        search_section=search_section
    )
