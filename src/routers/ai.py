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

    supabase = SupabaseService()

    message_history = await transorm_history_to_llm_format(await supabase.get_history(profile_id=request.profile_id))
    system_instructions = await supabase.get_instructions(topic=request.topic)

    # инициируем общение если не указан prompt
    if not request.prompt:
        if system_instructions:
            message_history.append({'role': 'system', 'content': tansform_files_to_context(system_instructions['context'], path_map=path_map)})
            message_history.append({'role': 'user', 'content': system_instructions['message']})

    response = await llm.infer(query=request.prompt, history=message_history)

    content = response.response.choices[0].message.content
    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
    
    return {'content': content, 'instructions_with_context': [
        {'role': 'system', 'content': tansform_files_to_context(system_instructions['context'], path_map=path_map)},
        {'role': 'user', 'content': system_instructions['message']}
    ] if not request.prompt and system_instructions else []}
     