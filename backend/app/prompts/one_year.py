"""一年战略任务分解与战略屋Prompt加载器"""
from app.prompts import load_prompt

ONE_YEAR_PROMPT = load_prompt("one_year.txt")


def get_one_year_prompt(prediction: str, context_text: str, strategy_base_section: str, search_section: str) -> str:
    """
    生成一年战略任务分解与战略屋prompt
    :param prediction: 用户预判内容
    :param context_text: 上下文信息
    :param strategy_base_section: 前序报告基础段落（已包含格式化）
    :param search_section: 搜索数据段落（已包含格式化）
    :return: 完整的prompt字符串
    """
    return ONE_YEAR_PROMPT.format(
        prediction=prediction,
        context_text=context_text,
        strategy_base_section=strategy_base_section,
        search_section=search_section
    )
