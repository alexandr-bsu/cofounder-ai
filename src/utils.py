from typing import List
import mistune
import re
from mistune.plugins.formatting import strikethrough
from mistune_telegram import TelegramHTMLRenderer

from typing import Any, TypeVar

T = TypeVar("T", bound="AsyncMixin")

# https://dev.to/akarshan/asynchronous-python-magic-how-to-create-awaitable-constructors-with-asyncmixin-18j5
# https://web.archive.org/web/20230915163459/https://dev.to/akarshan/asynchronous-python-magic-how-to-create-awaitable-constructors-with-asyncmixin-18j5
class AsyncMixin:
    """
    Асинхронный миксин для поддержки асинхронной инициализации объектов.
    """
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.__storedargs = args, kwargs
        self.async_initialized = False

    async def __ainit__(self, *args: Any, **kwargs: Any) -> None:
        pass

    async def __initobj(self: T) -> T:
        assert not self.async_initialized
        self.async_initialized = True
        await self.__ainit__(*self.__storedargs[0], **self.__storedargs[1])
        return self

    def __await__(self):
        return self.__initobj().__await__()

def get_paths_from_map(paths: List[str], path_map):
    real_paths = []
    for path in paths:
        mapped_path = path_map.get(path, None)
        if mapped_path is not None:
            real_paths.append(mapped_path)
    
    return real_paths

def read_file_content(file_path):
    if file_path is None:
        return None

    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def tansform_files_to_context(file_paths: List[str] = [], path_map={}):
    real_paths = get_paths_from_map(file_paths, path_map)

    system_prompt = f"""
    Ты помощник с доступом к файлам. Ниже предоставлено содержимое файлов. используй их как контекст, для помощи ответа на запрос пользователя
    Контекст:
    
    """
    file_counter = 1
    for file_path in real_paths:
        content=read_file_content(file_path)
        
        if content is None:
            continue

        system_prompt+=f"""
        Файл #{file_counter}:
        {content}
        
        """    

        file_counter += 1

    system_prompt += "В следующем сообщении будет запрос пользователя: "
    return system_prompt

async def transorm_history_to_llm_format(history):
    llm_history = []
    for record in history.data:
        llm_history.append({'role': record['role'], 'content': record['message']})
    
    return llm_history

telegram_style = mistune.create_markdown(renderer=TelegramHTMLRenderer(), plugins=[strikethrough])
def transform_markdown_to_telegram_html(markdown_text: str):
    result = telegram_style(markdown_text)
    
    # Удаляем повторяющиеся подряд теги
    result = re.sub(r'(<(/?)([a-zA-Z][a-zA-Z0-9]*)[^>]*>)\1+', r'\1', result)
    
    return result
    
def split_html_text_for_telegram(html_text: str, max_length: int = 4000) -> List[str]:
    """
    Разделяет HTML текст на части не более max_length символов,
    сохраняя корректность HTML разметки.
    
    Args:
        html_text: Исходный HTML текст
        max_length: Максимальная длина каждой части (по умолчанию 4000)
    
    Returns:
        Список строк с валидной HTML разметкой
    """
    if len(html_text) <= max_length:
        return [html_text]
    
    # Паттерн для поиска HTML тегов
    tag_pattern = re.compile(r'<(/?)([a-zA-Z][a-zA-Z0-9]*)[^>]*>')
    
    # Самозакрывающиеся теги (не требуют закрытия)
    self_closing_tags = {'br', 'hr', 'img', 'input', 'area', 'base', 'col', 'embed', 'link', 'meta', 'param', 'source', 'track', 'wbr'}
    
    parts = []
    current_pos = 0
    global_open_tags = []  # Глобальный стек открытых тегов
    
    while current_pos < len(html_text):
        # Рассчитываем размер открывающих тегов
        opening_tags_length = sum(len(f'<{tag}>') for tag in global_open_tags) if global_open_tags else 0
        
        # Грубая оценка размера закрывающих тегов (может быть больше реального)
        max_closing_tags_length = sum(len(f'</{tag}>') for tag in global_open_tags) if global_open_tags else 0
        
        # Определяем конечную позицию для текущей части с учетом всех тегов
        available_length = max_length - opening_tags_length - max_closing_tags_length
        end_pos = min(current_pos + available_length, len(html_text))
        
        # Если мы не в конце текста, ищем безопасное место для разреза
        if end_pos < len(html_text):
            # Ищем последний пробел или символ переноса перед лимитом
            safe_break = end_pos
            for i in range(end_pos - 1, current_pos, -1):
                if html_text[i] in [' ', '\n', '\t']:
                    safe_break = i
                    break
            end_pos = safe_break
        
        # Извлекаем текущую часть
        current_part = html_text[current_pos:end_pos]
        
        # Копируем текущее состояние стека тегов
        part_open_tags = global_open_tags.copy()
        
        # Анализируем теги в текущей части и обновляем стек
        for match in tag_pattern.finditer(current_part):
            is_closing = bool(match.group(1))  # True если это закрывающий тег
            tag_name = match.group(2).lower()
            
            if tag_name in self_closing_tags:
                continue
                
            if is_closing:
                # Убираем соответствующий открывающий тег из стека
                if part_open_tags and part_open_tags[-1] == tag_name:
                    part_open_tags.pop()
            else:
                # Добавляем открывающий тег в стек
                part_open_tags.append(tag_name)
        
        # Добавляем открывающие теги в начало (если есть)
        if global_open_tags:
            opening_tags = ''.join(f'<{tag}>' for tag in global_open_tags)
            current_part = opening_tags + current_part
        
        # Если есть незакрытые теги, закрываем их
        if part_open_tags:
            closing_tags = ''.join(f'</{tag}>' for tag in reversed(part_open_tags))
            current_part += closing_tags
        
        # Проверяем, не превышает ли итоговая длина лимит
        while len(current_part) > max_length and end_pos > current_pos:
            # Уменьшаем размер части
            end_pos = int(end_pos * 0.9)  # Уменьшаем на 10%
            if end_pos <= current_pos:
                end_pos = current_pos + 1
            
            # Ищем безопасное место для разреза
            if end_pos < len(html_text):
                safe_break = end_pos
                for i in range(end_pos - 1, current_pos, -1):
                    if html_text[i] in [' ', '\n', '\t']:
                        safe_break = i
                        break
                end_pos = safe_break
            
            # Пересчитываем часть
            current_part = html_text[current_pos:end_pos]
            
            # Пересчитываем теги
            part_open_tags = global_open_tags.copy()
            for match in tag_pattern.finditer(current_part):
                is_closing = bool(match.group(1))
                tag_name = match.group(2).lower()
                
                if tag_name in self_closing_tags:
                    continue
                    
                if is_closing:
                    if part_open_tags and part_open_tags[-1] == tag_name:
                        part_open_tags.pop()
                else:
                    part_open_tags.append(tag_name)
            
            # Добавляем открывающие теги в начало
            if global_open_tags:
                opening_tags = ''.join(f'<{tag}>' for tag in global_open_tags)
                current_part = opening_tags + current_part
            
            # Закрываем незакрытые теги
            if part_open_tags:
                closing_tags = ''.join(f'</{tag}>' for tag in reversed(part_open_tags))
                current_part += closing_tags
        
        parts.append(current_part)
        
        # Обновляем глобальный стек для следующей итерации
        global_open_tags = part_open_tags.copy()
        current_pos = end_pos
    
    return parts

def map_step_name_to_step_id(step_name: str):
    step_map = {
        'Имя клиента': '68afedd3db06f3077d03cb93',
        'Бизнес-модель': '68a713e46eea3358683ccab1',
        'Оффер': '68a71753ffcdc54781081bcf',
        'Маршутизация запросов по офферу': '68b0149dcb1c3a18ea01e043',
        'Команда': '68a81e80856ba478a0400418'
    }

    return step_map[step_name]