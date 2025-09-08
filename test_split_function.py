#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils import split_html_text_for_telegram

def test_basic_split():
    """Тест базового разделения текста"""
    print("=== Тест 1: Базовое разделение ===")
    
    # Короткий текст - не должен разделяться
    short_text = "<b>Короткий текст</b>"
    result = split_html_text_for_telegram(short_text, 100)
    print(f"Короткий текст: {result}")
    assert len(result) == 1
    assert result[0] == short_text
    
    # Длинный текст без тегов
    long_text = "А" * 5000
    result = split_html_text_for_telegram(long_text, 4000)
    print(f"Длинный текст без тегов разделен на {len(result)} частей")
    assert len(result) == 2
    assert len(result[0]) <= 4000
    assert len(result[1]) <= 4000
    
    print("✓ Базовое разделение работает корректно\n")

def test_html_tags_preservation():
    """Тест сохранения HTML тегов"""
    print("=== Тест 2: Сохранение HTML тегов ===")
    
    # Текст с незакрытыми тегами при разделении
    html_text = "<b>Это очень " + "длинный " * 800 + "текст с жирным шрифтом</b>"
    result = split_html_text_for_telegram(html_text, 4000)
    
    print(f"Текст с тегами разделен на {len(result)} частей")
    
    # Проверяем, что каждая часть имеет корректные теги
    for i, part in enumerate(result):
        print(f"Часть {i+1}: длина {len(part)}")
        print(f"Начало: {part[:50]}...")
        print(f"Конец: ...{part[-50:]}")
        
        # Проверяем, что теги корректно закрыты
        open_count = part.count('<b>')
        close_count = part.count('</b>')
        print(f"Открывающих <b>: {open_count}, Закрывающих </b>: {close_count}")
        assert open_count == close_count, f"В части {i+1} неравное количество открывающих и закрывающих тегов"
    
    print("✓ HTML теги сохраняются корректно\n")

def test_nested_tags():
    """Тест вложенных тегов"""
    print("=== Тест 3: Вложенные теги ===")
    
    # Текст с вложенными тегами
    html_text = "<b><i>Это очень " + "длинный " * 800 + "текст с вложенными тегами</i></b>"
    result = split_html_text_for_telegram(html_text, 4000)
    
    print(f"Текст с вложенными тегами разделен на {len(result)} частей")
    
    for i, part in enumerate(result):
        print(f"Часть {i+1}: длина {len(part)}")
        
        # Проверяем количество тегов
        b_open = part.count('<b>')
        b_close = part.count('</b>')
        i_open = part.count('<i>')
        i_close = part.count('</i>')
        
        print(f"<b>: {b_open}, </b>: {b_close}, <i>: {i_open}, </i>: {i_close}")
        
        assert b_open == b_close, f"В части {i+1} неравное количество <b> тегов"
        assert i_open == i_close, f"В части {i+1} неравное количество <i> тегов"
    
    print("✓ Вложенные теги обрабатываются корректно\n")

def test_self_closing_tags():
    """Тест самозакрывающихся тегов"""
    print("=== Тест 4: Самозакрывающиеся теги ===")
    
    html_text = "Текст с переносом<br>строки " + "очень " * 800 + "длинный текст"
    result = split_html_text_for_telegram(html_text, 4000)
    
    print(f"Текст с <br> разделен на {len(result)} частей")
    
    # Проверяем, что <br> теги остались без изменений
    total_br = html_text.count('<br>')
    result_br = sum(part.count('<br>') for part in result)
    
    print(f"Исходных <br>: {total_br}, В результате: {result_br}")
    assert total_br == result_br, "Количество <br> тегов изменилось"
    
    print("✓ Самозакрывающиеся теги обрабатываются корректно\n")

def test_complex_example():
    """Тест сложного примера"""
    print("=== Тест 5: Сложный пример ===")
    
    html_text = f"""
    <b>Заголовок</b>
    <br>
    <i>Это очень длинный текст {"с повторениями " * 500}</i>
    <br>
    <b><i>Вложенные теги {"тоже очень длинные " * 300}</i></b>
    <br>
    Обычный текст в конце
    """
    
    result = split_html_text_for_telegram(html_text, 4000)
    
    print(f"Сложный пример разделен на {len(result)} частей")
    
    for i, part in enumerate(result):
        print(f"\n--- Часть {i+1} (длина: {len(part)}) ---")
        print(f"Начало: {part[:100]}...")
        print(f"Конец: ...{part[-100:]}")
        
        # Проверяем длину
        assert len(part) <= 4000, f"Часть {i+1} превышает лимит: {len(part)} символов"
        
        # Проверяем баланс тегов
        tags_to_check = ['b', 'i']
        for tag in tags_to_check:
            open_count = part.count(f'<{tag}>')
            close_count = part.count(f'</{tag}>')
            assert open_count == close_count, f"В части {i+1} неравное количество <{tag}> тегов: {open_count} vs {close_count}"
    
    print("✓ Сложный пример обрабатывается корректно\n")

if __name__ == "__main__":
    print("Запуск тестов функции split_html_text_for_telegram\n")
    
    try:
        test_basic_split()
        test_html_tags_preservation()
        test_nested_tags()
        test_self_closing_tags()
        test_complex_example()
        
        print("🎉 Все тесты прошли успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")
        sys.exit(1)