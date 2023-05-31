from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import serv_functions
import logging
import config


class States(StatesGroup):
    get_bed = State()
    get_humidity = State()
    get_frequency = State()
    get_duration = State()
    get_new_bed = State()
    get_new_humidity = State()
    get_new_frequency = State()
    get_new_duration = State()


logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()
bot = Bot(token=config.TG_TOKEN)
dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands=['start'], state='*')
async def start(message: types.Message, state: FSMContext):
    await state.finish()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Последние измерения', callback_data='last_measures'))
    kb.add(types.InlineKeyboardButton(text='Статистика', callback_data='statistic'))
    kb.add(types.InlineKeyboardButton(text='Управление конфигурациями', callback_data='configurations'))
    await message.answer('Выберите действие:', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data == 'start')
async def start_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await start(callback_query.message, state)
    await callback_query.message.delete()


@dp.callback_query_handler(lambda query: query.data == 'last_measures')
async def give_last_measures(callback_query: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Вентилятор', callback_data='fan'))
    kb.add(types.InlineKeyboardButton(text='Окна', callback_data='windows'))
    for i in range(config.beds_number):
        kb.add(types.InlineKeyboardButton(text=f'Грядка {i+1}', callback_data=f'bed_{i+1}'))
    kb.add(types.InlineKeyboardButton(text='Назад', callback_data='start'))
    await callback_query.message.edit_text('Выберите раздел:', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data == 'fan')
async def give_fan(callback_query: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Назад', callback_data='last_measures'))
    devices = serv_functions.get_devices_status()
    text = f'''ПОСЛЕДНИЕ ИЗМЕРЕНИЯ
Вентилятор: {devices.get('fan').strip()}'''
    await callback_query.message.answer(text, reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data == 'windows')
async def give_windows(callback_query: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Назад', callback_data='last_measures'))
    devices = serv_functions.get_devices_status()
    text = f'''ПОСЛЕДНИЕ ИЗМЕРЕНИЯ
Окна: {devices.get('windows').strip()}'''
    await callback_query.message.answer(text, reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data.startswith('bed_'))
async def give_bed(callback_query: types.CallbackQuery):
    bed_number = int(callback_query.data.split('_')[-1])
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Назад', callback_data='last_measures'))
    tp = serv_functions.get_temp_press()
    h = serv_functions.get_humidity()
    text = f'''ПОСЛЕДНИЕ ИЗМЕРЕНИЯ
Грядка {bed_number}
Температура: {str(tp[bed_number-1].get('values').get('temperature') )+ "C" if tp[bed_number-1].get('values') else 'Не отслеживается'}
Давление: {str(tp[bed_number-1]['values'].get('pressure')) + "мм. рт. ст." if tp[bed_number-1].get('values') else 'Не отслеживается'}
Влажность: {str(h[bed_number-1].get('value')) + "%" if h[bed_number-1].get('value') else 'Не отслеживается'}'''
    await callback_query.message.edit_text(text, reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data == 'statistic')
async def give_statistic(callback_query: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup()
    for i in range(config.beds_number):
        kb.add(types.InlineKeyboardButton(text=f'Грядка {i+1}', callback_data=f'st_{i+1}'))
    kb.add(types.InlineKeyboardButton(text='Назад', callback_data='start'))
    await callback_query.message.edit_text('Выберите грядку:', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data.startswith('st_'))
async def give_statistic(callback_query: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Назад', callback_data='statistic'))
    bed_number = int(callback_query.data.split('_')[-1])
    measures = serv_functions.get_measures()
    text = f'''СТАТИСТИКА'''
    text += f'\n<b>Грядка {bed_number}</b>'
    text += '\n<i>Температура</i>\n'
    text += '\n'.join([f'{item[1]} | {item[0]} С' for item in measures[bed_number-1]['measures']['temperature']])
    text += '\n<i>Давление</i>\n'
    text += '\n'.join([f'{item[1]} | {item[0]} мм. рт. ст.' for item in measures[bed_number-1]['measures']['pressure']])
    text += '\n<i>Влажность</i>\n'
    text += '\n'.join([f'{item[1]} | {item[0]}%' for item in measures[bed_number-1]['measures']['humidity']])
    await callback_query.message.edit_text(text, reply_markup=kb, parse_mode='HTML')


@dp.callback_query_handler(lambda query: query.data == 'configurations', state='*')
async def configurations_panel(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Создать новую конфигурация', callback_data='start_creating_configuration'))
    kb.add(types.InlineKeyboardButton(text='Редактировать существующую конфигурацию', callback_data='edit_configurations'))
    kb.add(types.InlineKeyboardButton(text='Назад', callback_data='start'))
    await callback_query.message.edit_text('Выберите действие:', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data == 'start_creating_configuration')
async def start_creating_configuration(callback_query: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Назад', callback_data='configurations'))
    await States.get_new_bed.set()
    await callback_query.message.edit_text('Пришлите номер грядки для конфигурации:', reply_markup=kb)


@dp.message_handler(state=States.get_new_bed)
async def get_new_bed(message: types.Message, state: FSMContext):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Назад', callback_data='configurations'))
    bed_number = message.text
    if not bed_number.isdigit():
        await message.answer('Значение должно быть целым числом',reply_markup=kb)
        return
    await state.finish()
    async with state.proxy() as data:
        data['bed_number'] = int(bed_number)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Автополив', callback_data='newmode_auto'))
    kb.add(types.InlineKeyboardButton(text='Полив по расписанию', callback_data='newmode_schedule'))
    kb.add(types.InlineKeyboardButton(text='Назад', callback_data='configurations'))
    await message.answer('Выберите режим полива', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data.startswith('newmode_'))
async def get_newmode(callback_query: types.CallbackQuery, state: FSMContext):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Назад', callback_data='configurations'))
    mode = callback_query.data.split('_')[-1]
    if mode == 'auto':
        await States.get_new_humidity.set()
        await callback_query.message.edit_text('Пришлите значение для минимального порога влажности:', reply_markup=kb)
    elif mode == 'schedule':
        await States.get_new_frequency.set()
        await callback_query.message.edit_text('Пришлите значение для частоты полива:', reply_markup=kb)


@dp.message_handler(state=States.get_new_humidity)
async def get_new_humidity(message: types.Message, state: FSMContext):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Назад', callback_data='configurations'))
    humidity = message.text
    if not humidity.isdigit():
        await message.answer('Значение должно быть целым числом')
        return
    humidity = int(humidity)
    async with state.proxy() as data:
        config = {
            'bed': data.get('bed_number'),
            'active': False,
            'auto': True,
            'minHumidity': humidity,
            'wateringFrequency': None,
            'wateringDuration': None
        }
    serv_functions.create_configuration(config)
    await message.answer('Новая конфигурация создана', reply_markup=kb)
    await state.finish()


@dp.message_handler(state=States.get_new_frequency)
async def get_new_frequency(message: types.Message, state: FSMContext):
    frequency = message.text
    if not frequency.isdigit():
        await message.answer('Значение должно быть целым числом!')
        return
    frequency = int(frequency)
    async with state.proxy() as data:
        data['frequency'] = frequency
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Назад', callback_data='configurations'))
    await States.get_new_duration.set()
    await message.answer('Пришлите значение для длительности полива:', reply_markup=kb)


@dp.message_handler(state=States.get_new_duration)
async def get_new_duration(message: types.Message, state: FSMContext):
    duration = message.text
    if not duration.isdigit():
        await message.answer('Значение должно быть целым числом!')
        return
    duration = int(duration)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Назад', callback_data='configurations'))
    async with state.proxy() as data:
        config = {
            'bed': data.get('bed_number'),
            'active': False,
            'auto': False,
            'minHumidity': None,
            'wateringFrequency': data.get('frequency'),
            'wateringDuration': duration
        }
    serv_functions.create_configuration(config)
    await message.answer('Новая конфигурация создана', reply_markup=kb)
    await state.finish()


@dp.callback_query_handler(lambda query: query.data == 'edit_configurations')
async def edit_configurations(callback_query: types.CallbackQuery):
    configurations = serv_functions.get_configurations()
    kb = types.InlineKeyboardMarkup()
    for config in configurations:
        status = config.get('active')
        conf_id = config.get('id')
        label = f'''✅ ID {conf_id} грядка {config.get('bed')}''' if status else f'''❌ ID {conf_id} грядка {config.get('bed')}'''
        kb.add(types.InlineKeyboardButton(text=label, callback_data=f'edit_{conf_id}'))
    kb.add(types.InlineKeyboardButton(text='Назад', callback_data='configurations'))
    await callback_query.message.edit_text('Выберите конфигурацию для изменения:', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data.startswith('edit_'), state='*')
async def edit(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    config_id = int(callback_query.data.split(('_'))[-1])
    config = serv_functions.get_configuration_by_id(config_id)
    print(config)
    async with state.proxy() as data:
        data['cofig_id'] = config_id
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Изменить грядку', callback_data=f'bed_{config_id}'))
    kb.add(types.InlineKeyboardButton(text='Изменить режим полива', callback_data=f'watering-mode_{config_id}'))
    if not config.get('active'):
        kb.add(types.InlineKeyboardButton(text='Включить эту конфигурацию', callback_data=f'enable_{config_id}'))
    kb.add(types.InlineKeyboardButton(text='Назад', callback_data='edit_configurations'))
    text = f'''Конфигураця ID {config_id}
Грядка: {config.get('bed')}
Статус: {'Активна' if config.get('active') else 'Неактивна'}
Режим полива: {'Автоматический' if config.get('auto') else 'По расписанию'}'''
    if config.get('auto'):
        text += f'''\nМинимальная влажность: {config.get('minHumidity')}'''
    else:
        text += f'''\nЧастота полива: {config.get('wateringFrequency')}
Длительность полива: {config.get('wateringDuration')}'''
    await callback_query.message.edit_text(text, reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data.startswith('bed_'))
async def change_bed(callback_query:types.CallbackQuery, state: FSMContext):
    conf_id = int(callback_query.data.split('_')[-1])
    async with state.proxy() as data:
        data['conf_id'] = conf_id
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Назад', callback_data=f'edit_{conf_id}'))
    await callback_query.message.edit_text('Пришлите номер грядки:', reply_markup=kb)
    await States.get_bed.set()


@dp.message_handler(state=States.get_bed)
async def change_bed_2(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        conf_id = data.get('conf_id')
    config = serv_functions.get_configuration_by_id(conf_id)
    bed_number = message.text
    if not bed_number.isdigit():
        await message.answer('Номер грядки должен быть числом!')
        return
    bed_number = int(bed_number)
    config['bed'] = bed_number
    serv_functions.change_configuration(config)
    await state.finish()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Назад', callback_data=f'edit_{conf_id}'))
    await message.answer('Номер грядки изменён', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data.startswith('watering-mode_'), state='*')
async def change_watering_mode(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    conf_id = int(callback_query.data.split('_')[-1])
    async with state.proxy() as data:
        data['conf_id'] = conf_id
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Автополив', callback_data='mode_auto'))
    kb.add(types.InlineKeyboardButton(text='Полив по расписанию', callback_data='mode_schedule'))
    kb.add(types.InlineKeyboardButton(text='Назад', callback_data=f'edit_{conf_id}'))
    await callback_query.message.edit_text('Выберите режим полива', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data.startswith('mode_'))
async def get_mode(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        conf_id = data.get('conf_id')
    mode = callback_query.data.split('_')[-1]
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Назад', callback_data=f'watering-mode_{conf_id}'))
    if mode == 'auto':
        await callback_query.message.edit_text('Пришлите значение для минимального порога влажности:', reply_markup=kb)
        await States.get_humidity.set()
    elif mode == 'schedule':
        await callback_query.message.edit_text('Пришлите значение для частоты полива:', reply_markup=kb)
        await States.get_frequency.set()


@dp.message_handler(state=States.get_humidity)
async def get_humidity(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        conf_id = data.get('conf_id')
    humidity = message.text
    if not humidity.isdigit():
        await message.answer('Значение должно быть целым числом')
        return
    humidity = int(humidity)
    config = serv_functions.get_configuration_by_id(conf_id)
    config['auto'] = True
    config['minHumidity'] = humidity
    config['wateringFrequency'] = None
    config['wateringDuration'] = None
    serv_functions.change_configuration(config)
    kb = types.InlineKeyboardMarkup()
    await state.finish()
    kb.add(types.InlineKeyboardButton(text='Назад', callback_data=f'edit_{conf_id}'))
    await message.answer('Режим полива изменён', reply_markup=kb)


@dp.message_handler(state=States.get_frequency)
async def get_frequency(message: types.Message, state: FSMContext):
    frequency = message.text
    if not frequency.isdigit():
        await message.answer('Значение должно быть целым числом!')
        return
    frequency = int(frequency)
    async with state.proxy() as data:
        conf_id = data.get('conf_id')
        data['frequency'] = frequency
    await States.get_duration.set()
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Назад', callback_data=f'watering-mode_{conf_id}'))
    await message.answer('Пришлите значение для продолжительности полива:', reply_markup=kb)


@dp.message_handler(state=States.get_duration)
async def get_duration(message: types.Message, state: FSMContext):
    duration = message.text
    if not duration.isdigit():
        await message.answer('Значение должно быть целым числом!')
        return
    duration = int(duration)
    async with state.proxy() as data:
        conf_id = data.get('conf_id')
        frequency = data.get('frequency')
    config = serv_functions.get_configuration_by_id(conf_id)
    config['auto'] = False
    config['minHumidity'] = None
    config['wateringFrequency'] = frequency
    config['wateringDuration'] = duration
    serv_functions.change_configuration(config)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Назад', callback_data=f'edit_{conf_id}'))
    await message.answer('Режим полива изменён', reply_markup=kb)


@dp.callback_query_handler(lambda query: query.data.startswith('enable_'))
async def enable_configuration(callback_query: types.CallbackQuery):
    conf_id = int(callback_query.data.split('_')[-1])
    serv_functions.enable_configuration(conf_id)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Назад', callback_data=f'edit_{conf_id}'))
    await callback_query.message.edit_text('Конфигурация включена', reply_markup=kb)



if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
