from fastapi import APIRouter
from src.schemas import LLMRequest
from src.services.llm_service import llm
from src.services.supabase_service import SupabaseService
from src.utils import transorm_history_to_llm_format, tansform_files_to_context
import re
import time

router = APIRouter(prefix='/ai')

path_map = {
    'list_communities': 'docs/list_communities.csv'
}




@router.post('/ask')
async def ask(request: LLMRequest):
    start_time = time.time()

    supabase = SupabaseService()

    message_history = await transorm_history_to_llm_format(await supabase.get_history(profile_id=request.profile_id))
    system_instructions = await supabase.get_instructions(topic=request.topic)

    if not message_history:
        if system_instructions:
             message_history.append({'role': 'system', 'content': tansform_files_to_context(system_instructions['context'], path_map=path_map)})
                              
    response = await llm.infer(query=request.prompt if request.prompt else system_instructions.get('message', 'Сообщи, что задан пустой запрос'), history=message_history)

    content = response.response.choices[0].message.content
    # Удаляем все содержимое think тегов
    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
    
    execution_time = time.time() - start_time
    print(f"Функция ask выполнена за {execution_time:.2f} секунд")
    
    return content
     