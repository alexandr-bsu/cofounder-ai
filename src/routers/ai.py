from fastapi import APIRouter, BackgroundTasks
from src.schemas import ConversationHistoryMessage, LLMRequest
from src.services.llm_service import llm
from src.services.history_service import HistoryService
from src.utils import transorm_history_to_llm_format, tansform_files_to_context, transform_markdown_to_telegram_html, split_html_text_for_telegram
import re

router = APIRouter(prefix='/ai')

path_map = {
    'list_communities': 'docs/list_communities.csv',
    'questions': 'docs/questions.csv',
    'professional_community_page': 'docs/professional_community.txt',
    'hypothesis': 'docs/hypothesis.txt',
    'product': 'docs/product.txt',
    'client_offer': 'docs/client_offer.txt',
    'custdev': 'docs/custdev.txt',
    'cofounder_offer': 'docs/cofounder_offer.txt',
    'business_model': 'docs/business_model.txt'
}

async def add_message_to_conversation_background(message: ConversationHistoryMessage):
    hs = await HistoryService()
    await hs.add_message_to_conversation_history(message)

@router.post('/addMessageToConversationHistory', status_code=201)
async def add_message_to_conversation_history(message: ConversationHistoryMessage, background_tasks: BackgroundTasks):
    background_tasks.add_task(add_message_to_conversation_background, message)
    return {"success": True}

@router.post('/ask')
async def ask(request: LLMRequest):
    history_service = HistoryService()

    message_history = await transorm_history_to_llm_format(
        await history_service.get_history(
            profile_id=request.profile_id,
            init_topic=request.topic if not request.prompt else None)
            )
    system_instructions = await history_service.get_instructions(topic=request.topic)

    # инициируем общение если не указан prompt
    if not request.prompt:
        if system_instructions:
            message_history.append({'role': 'system', 'content': tansform_files_to_context(system_instructions['context'], path_map=path_map)})
            message_history.append({'role': 'user', 'content': system_instructions['message']})

    response = await llm.infer(query=request.prompt, history=message_history, session_id=f'{request.profile_id}:{request.topic}')

    content = response.response.choices[0].message.content
    
    # Постобработка ответа ИИ
    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
    content_telegram_chunks = transform_markdown_to_telegram_html(content)
    content_telegram_chunks = split_html_text_for_telegram(content_telegram_chunks)

    return {'content': content, "content_telegram_chunks": content_telegram_chunks, 'instructions_with_context': [
        {'role': 'system', 'content': tansform_files_to_context(system_instructions['context'], path_map=path_map)},
        {'role': 'user', 'content': system_instructions['message']}
    ] if not request.prompt and system_instructions else []}
     