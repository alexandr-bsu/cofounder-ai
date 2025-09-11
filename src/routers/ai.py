import asyncio
from uuid import uuid4
from fastapi import APIRouter, BackgroundTasks
from src.schemas import ConversationHistoryMessage, LLMRequest, InitConverastionRequest, UserMessageRequest, BackToBotRequest
from src.services.llm_service import llm
from src.services.history_service import HistoryService
from src.utils import transorm_history_to_llm_format, tansform_files_to_context, transform_markdown_to_telegram_html, split_html_text_for_telegram, map_step_name_to_step_id
import re
from src.services.target_hunter_service import TargetHunterService

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


async def init_conversation_background(request: InitConverastionRequest):
    hs = await HistoryService()
    ths = await TargetHunterService()

    conversation_id = str(uuid4())

    ai_response = await ask(LLMRequest(topic=request.topic, profile_id=request.profile_id))
    await hs.add_message_to_conversation_history(ConversationHistoryMessage(topic=request.topic, message=ai_response['instructions_with_context'][0]['content'], conversation_id=conversation_id, role=ai_response['instructions_with_context'][0]['role'], profile_id=request.profile_id))
    await hs.add_message_to_conversation_history(ConversationHistoryMessage(topic=request.topic, message=ai_response['instructions_with_context'][1]['content'], conversation_id=conversation_id, role=ai_response['instructions_with_context'][1]['role'], profile_id=request.profile_id))
    await hs.add_message_to_conversation_history(ConversationHistoryMessage(topic=request.topic, message=ai_response['content'], conversation_id=conversation_id, role='assistant', profile_id=request.profile_id))

    # Контент подготовленный в формате telegram
    telegram_chuncks = ai_response['content_telegram_chunks']

    for chunk in telegram_chuncks:
        await ths.go_to_step(
            step_id='68be7106d0dbaa14e10c8be3',
            uid=request.uid,
            payload={
                "response": {
                    "text": chunk,
                    "conversationId": conversation_id
                }
            }
        )
        await asyncio.sleep(1)

    return telegram_chuncks


async def process_conversation_background(request: UserMessageRequest):
    hs = await HistoryService()
    ths = await TargetHunterService()
    ai_response = await ask(LLMRequest(topic=request.topic, profile_id=request.profile_id, prompt=request.prompt))

    await hs.add_message_to_conversation_history(ConversationHistoryMessage(topic=request.topic, message=request.prompt, conversation_id=request.conversation_id, role='user', profile_id=request.profile_id))
    await hs.add_message_to_conversation_history(ConversationHistoryMessage(topic=request.topic, message=ai_response['content'], conversation_id=request.conversation_id, role='assistant', profile_id=request.profile_id))

    # Контент подготовленный в формате telegram
    telegram_chuncks = ai_response['content_telegram_chunks']

    for chunk in telegram_chuncks:
        await ths.go_to_step(
            step_id='68afe458915d25156227c07f',
            uid=request.uid,
            payload={
                "response": {
                    "text": chunk,
                    "conversationId": request.conversation_id
                }
            }
        )
        await asyncio.sleep(1)

    return telegram_chuncks


@router.post('/addMessageToConversationHistory', status_code=201)
async def add_message_to_conversation_history(message: ConversationHistoryMessage, background_tasks: BackgroundTasks):
    background_tasks.add_task(add_message_to_conversation_background, message)
    return {"success": True}


@router.post('/initConversation', status_code=200)
async def init_conversation(request: InitConverastionRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(init_conversation_background, request)
    return {"succes": True}


@router.post('/processConversation', status_code=200)
async def init_conversation(request: UserMessageRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(process_conversation_background, request)
    return {"succes": True}

# TODO add extract entities api


@router.post('/parseEntities', status_code=202)
async def parse_entities():
    return {"succes": True}

# TODO add save extracted entities api


@router.post('/saveEntities', status_code=202)
async def save_entities():
    return {"succes": True}


async def transfer_back_to_bot_mode_background(request: BackToBotRequest):
    step_map = {
        'Генерация специализации': map_step_name_to_step_id('Имя клиента'),
        'Генерация гипотезы': map_step_name_to_step_id('Бизнес модель'),
        'Генерация бизнес модели': map_step_name_to_step_id('Оффер'),
        'Генерация описания продукта': map_step_name_to_step_id('Маршутизация запросов по офферу'),
        'Генерация вопросов на CustDev': map_step_name_to_step_id('Маршутизация запросов по офферу'),
        'Генерация оффера для клиента': map_step_name_to_step_id('Маршутизация запросов по офферу'),
        'Генерация оффера для кофаундера': map_step_name_to_step_id('Команда'),
        'Генерация оффера для кофаундера (без перенаправлений)': '68b01fae13001b42b560dda1'
    }

    ths = await TargetHunterService()
    await ths.go_to_step(step_id=step_map[request.topic], uid=request.uid)

@router.post('/transferBackToBotMode', status_code=200)
async def transfer_back_to_bot_mode(request: BackToBotRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(transfer_back_to_bot_mode_background, request)
    return {"succes": True}

async def ask(request: LLMRequest):
    history_service = await HistoryService()

    message_history = await transorm_history_to_llm_format(
        await history_service.get_history(
            profile_id=request.profile_id,
            init_topic=request.topic if not request.prompt else None)
    )
    system_instructions = await history_service.get_instructions(topic=request.topic)

    # инициируем общение если не указан prompt
    if not request.prompt:
        if system_instructions:
            message_history.append({'role': 'system', 'content': tansform_files_to_context(
                system_instructions['context'], path_map=path_map)})
            message_history.append(
                {'role': 'user', 'content': system_instructions['message']})

    response = await llm.infer(query=request.prompt, history=message_history, session_id=f'{request.profile_id}:{request.topic}')

    content = response.response.choices[0].message.content

    # Постобработка ответа ИИ
    content = re.sub(r'<think>.*?</think>', '',
                     content, flags=re.DOTALL).strip()
    content_telegram_chunks = transform_markdown_to_telegram_html(content)
    content_telegram_chunks = split_html_text_for_telegram(
        content_telegram_chunks)

    return {'content': content, "content_telegram_chunks": content_telegram_chunks, 'instructions_with_context': [
        {'role': 'system', 'content': tansform_files_to_context(
            system_instructions['context'], path_map=path_map)},
        {'role': 'user', 'content': system_instructions['message']}
    ] if not request.prompt and system_instructions else []}
