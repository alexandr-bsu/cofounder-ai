from typing import List

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

