import asyncio

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from services.bot.state_manager import Form
from services.bot.keyboards import main_menu_keyboard, post_approval_keyboard, back_button
from services.pyrogram_service.pyrogram_client import PyrogramService
from services.openai_service.openai_client import OpenAIService
from services.bot.bot_utils import process_next_post, send_content_message
router = Router()
pyrogram_service = PyrogramService.get_instance()
openai_service = OpenAIService()


@router.message(F.text == "/start")
async def start_handler(message: types.Message, state: FSMContext):
    await message.answer("Добро пожаловать в бот Blogger AI", reply_markup=main_menu_keyboard())
    await state.clear()


@router.callback_query(F.data == "new_channel")
async def process_new_channel(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    await callback_query.message.answer("Введите логин исходного канала (например, @source_channel):")
    await state.set_state(Form.source_channel)


@router.message(Form.source_channel)
async def process_source_channel(message: types.Message, state: FSMContext):
    source_channel = message.text.strip()
    data = await state.get_data()
    channels = data.get('channels', [])
    channels.append({'source_channel': source_channel, 'destination_channel': '', 'instruction': ''})
    await state.update_data(channels=channels)
    await state.update_data(source_channel=source_channel)
    await message.answer("Введите логин канала для публикации (например, @destination_channel):")
    await state.set_state(Form.destination_channel)


@router.message(Form.destination_channel)
async def process_destination_channel(message: types.Message, state: FSMContext):
    destination_channel = message.text.strip()
    user_id = message.from_user.id
    try:
        member = await message.bot.get_chat_member(destination_channel, user_id)
        if member.status in ('administrator', 'creator'):
            data = await state.get_data()
            channels = data.get('channels', [])
            channels[-1]['destination_channel'] = destination_channel
            await state.update_data(channels=channels)
            await message.answer("Вы являетесь администратором канала. Теперь введите инструкцию для изменения поста.")
            await state.update_data(destination_channel=destination_channel)
            await state.set_state(Form.user_instruction)
        else:
            await message.answer("Вы не администратор этого канала.")
            await state.clear()
    except Exception as e:
        await message.answer(f"Ошибка проверки: {e}")
        await state.clear()


@router.message(Form.user_instruction)
async def process_user_instruction(message: types.Message, state: FSMContext):
    instruction = message.text.strip()
    data = await state.get_data()
    channels = data.get('channels', [])
    channels[-1]['instruction'] = instruction
    instruction = message.text.strip()
    await state.update_data(instruction=instruction)
    await process_next_post(message, state)


async def process_next_post(message: types.Message, state: FSMContext):
    data = await state.get_data()
    source_channel = data.get('source_channel')
    instruction = data.get('instruction')
    last_processed_message_id = data.get('last_processed_message_id', 0)
    destination_channel = data.get('destination_channel')

    last_message = await pyrogram_service.get_last_message(source_channel)
    if not last_message:
        await message.answer("Последний пост уже был обработан.")
        await state.clear()
        return

    content: str = last_message.text or last_message.caption or ""
    if not content:
        await message.answer("Пустой пост. Пропуск...")
        await process_next_post(message, state)
        return

    modified_content = await openai_service.modify_post(content, instruction)
    await state.update_data(modified_content=modified_content)

    await message.answer(modified_content, reply_markup=post_approval_keyboard())
    await state.update_data(last_processed_message_id=last_message.id)
    await state.set_state(Form.approve_post)


@router.callback_query(F.data == "publish")
async def process_publish(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    destination_channel = data.get('destination_channel')
    modified_content = data.get('modified_content')
    last_message = await pyrogram_service.get_last_message(data.get('source_channel'))
    if not destination_channel or not modified_content:
        await callback_query.message.answer(f"Ошибка публикации: не найдены данные. {data}")
        return

    try:
        await send_content_message(destination_channel, modified_content, last_message)

        msg = await callback_query.message.edit_text("Пост опубликован!")
        await state.clear()
        await start_handler(callback_query.message, state)
        await asyncio.sleep(5)
        await msg.delete()
    except Exception as e:
        await callback_query.message.answer(f"Ошибка публикации: {e}")


@router.callback_query(F.data == "skip")
async def process_skip(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Пропуск поста...")
    await process_next_post(callback_query.message, state)


@router.callback_query(F.data == "stop")
async def process_stop(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Публикация остановлена.")
    await state.clear()


@router.callback_query(F.data == "change_instruction")
async def process_change_instruction(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Введите новую инструкцию.")
    await state.set_state(Form.update_instruction)


@router.message(Form.update_instruction)
async def process_new_instruction(message: types.Message, state: FSMContext):
    new_instruction = message.text.strip()
    await state.update_data(instruction=new_instruction)
    await message.answer(f"Новая инструкция сохранена: {new_instruction}")
    await process_next_post(message, state)


@router.callback_query(F.data == "channel_list")
async def process_channel_list(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    channels = data.get('channels')

    if not channels:
        await callback_query.message.edit_text("Список каналов пуст.", reply_markup=back_button())
        return

    channel_info = "Список каналов:\n\n"
    for idx, channel in enumerate(channels, 1):
        channel_info += (
            f"{idx}. Исходный канал: {channel['source_channel']}\n"
            f"   Канал назначения: {channel['destination_channel']}\n"
            f"   Текущая инструкция: {channel['instruction']}\n\n"
        )

    await callback_query.message.answer(channel_info)


@router.callback_query(F.data == "back")
async def process_back(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик возврата на главное меню."""
    await callback_query.message.bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    await start_handler(callback_query.message, state)
    await state.clear()
