from aiogram import Bot, Dispatcher
from aiogram import types, F, Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder

import asyncio
import config
from web3 import Web3
from utils.utils import patch_http_connection_pool, file_exists
import random
from user import User
import pandas as pd


def load_users(db_csv_filename='wallets.csv'):
	users = {}
	if file_exists(db_csv_filename):
		db_df = pd.read_csv(db_csv_filename)
		for owner_id in set(db_df['owner_id']):
			users[owner_id] = User(owner_id)
	return users

patch_http_connection_pool(maxsize=6000)
bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)
router = Router()
dp = Dispatcher(bot=bot, storage=MemoryStorage())
dp.include_router(router)
users = load_users()


@router.message(Command("start"))
async def start_handler(msg: Message):
	print('chat id (owner_id) :', msg.chat.id)
	builder = InlineKeyboardBuilder()
	if msg.chat.id not in users:
		builder.add(types.InlineKeyboardButton(
			text="Добавить кошелек",
			callback_data="add_wallet")
		)
	
		users[msg.chat.id] = User(msg.chat.id)
		await msg.answer(
			"<b>Вы пока что не добавили ни одного кошелька</b>",
			reply_markup=builder.as_markup()
		)
	else:
		builder.add(types.InlineKeyboardButton(
			text="Перейти в меню",
			callback_data="main_menu")
		)
		await msg.answer('Вы уже добавили свой кошелек', reply_markup=builder.as_markup())




@dp.callback_query(F.data == "add_wallet")
async def ask_wallet_address(callback: types.CallbackQuery):
	users[callback.message.chat.id].wait_wallet()
	await callback.message.answer("Отправьте ваш адрес evm кошелька:")





@router.message()
# @dp.message_handler(lambda message: True)
async def message_handler(msg: Message):
	
	user = users[msg.chat.id]
	filter_commands = ['filter_chains', 'filter_tokens', 'filter_wallet_addresses', 'filter_wallet_names', 'filter_wallet_notes']

	if msg.text[:2] == '0x' and users[msg.chat.id].is_waiting_wallet():
		# меню редактирования кошелька
		address = msg.text
		# if address in user.wallet_keeper.user_wallets['address']:
		# 	await msg.answer('Этот кошелек уже добавлен в базу данных. Введите другой: ')
		# 	return

		users[msg.chat.id].add_new_wallet(address)
		print(f'Added address {address} to user {msg.chat.id}')
		# amount = Web3.from_wei(web3.eth.get_balance(address), 'ether')
		# print(f'Your balance: {amount} eth')
		# await msg.answer(f'Your balance: {amount} eth')

		name_text = "Добавить имя"
		if user.new_name or address in user.wallet_keeper.user_wallets['address']:
			name_text = 'Изменить имя'
		note_text = "Добавить заметку"
		if user.new_note or address in user.wallet_keeper.user_wallets['address']:
			note_text = 'Изменить заметку'


		builder = InlineKeyboardBuilder()
		builder.row(types.InlineKeyboardButton(
			text=note_text,
			callback_data="add_wallet_note")
		)
		builder.row(types.InlineKeyboardButton(
			text=name_text,
			callback_data="add_wallet_name")
		)
		
		builder.row(types.InlineKeyboardButton(
			text="Изменить адрес кошелька",
			callback_data="add_wallet")
		)
		builder.row(types.InlineKeyboardButton(
			text="Сохранить и выйти в меню",
			callback_data="save_changes")
		)
		if not user.is_new():
			builder.row(types.InlineKeyboardButton(
				text="Назад в меню (отменить изменения)",
				callback_data="cancel_changes")
			)
		if user.wallets_count() > 1:
			builder.row(types.InlineKeyboardButton(
				text="Удалить кошелек",
				callback_data="delete_wallet")
			)
		await msg.answer(
			f'Вы успешно добавили новый кошелек {address}',
			reply_markup=builder.as_markup()
		)
	elif user.is_waiting_name():
		name = msg.text
		if name in user.wallet_keeper.user_wallets['name']:
			await msg.answer('Это имя уже принадлежит одному из ваших кошельков. Введите другое:')
			return
		users[msg.chat.id].add_new_name(name)
		# save_changes(None, msg=msg)

	elif user.is_waiting_note():
		note = msg.text
		users[msg.chat.id].add_new_note(note)

	elif any(command in msg.text for command in filter_commands):
		command, args = msg.text.split()
		command = command[7:] # убрать filter_
		kwargs = {command: args}
		user.set_filter_kwargs(kwargs)




@dp.callback_query(F.data == "add_wallet_name")
async def add_wallet_name(callback: types.CallbackQuery):
	users[callback.message.chat.id].wait_name()
	await callback.message.answer('Отправьте имя кошелька:')

@dp.callback_query(F.data == "add_wallet_note")
async def add_wallet_note(callback: types.CallbackQuery):
	users[callback.message.chat.id].wait_note()
	await callback.message.answer('Отправьте заметку:')

@dp.callback_query(F.data == "save_changes")
async def save_changes(callback: types.CallbackQuery, msg=None):
	builder = InlineKeyboardBuilder()
	builder.add(types.InlineKeyboardButton(
		text="Перейти в меню",
		callback_data="main_menu")
	)
	if msg is None:
		msg = callback.message
	users[msg.chat.id].save_new_wallet()
	await msg.answer('Изменения сохранены', reply_markup=builder.as_markup())

@dp.callback_query(F.data == "cancel_changes")
async def cancel_changes(callback: types.CallbackQuery):
	builder = InlineKeyboardBuilder()
	builder.add(types.InlineKeyboardButton(
		text="Перейти в меню",
		callback_data="main_menu")
	)
	users[callback.message.chat.id].cancel_changes()
	await callback.message.answer('Изменения отменены', reply_markup=builder.as_markup())

@dp.callback_query(F.data == "delete_wallet")
async def delete_wallet(callback: types.CallbackQuery):
	builder = InlineKeyboardBuilder()
	builder.add(types.InlineKeyboardButton(
		text="Перейти в меню",
		callback_data="main_menu")
	)
	users[callback.message.chat.id].delete_current_wallet()
	await callback.message.answer('Кошелек удален', reply_markup=builder.as_markup())


@dp.callback_query(F.data == "main_menu")
async def main_menu(callback: types.CallbackQuery):
	# Главное меню бота 
	builder = InlineKeyboardBuilder()
	builder.row(types.InlineKeyboardButton(
		text='Обновить',
		callback_data="main_menu")
	)
	builder.row(types.InlineKeyboardButton(
		text='Смотреть весь баланс',
		callback_data="balance_filter_menu")
	)
	builder.row(types.InlineKeyboardButton(
		text='Смотреть транзакции',
		callback_data="transactions_filter_menu")
	)
	builder.row(types.InlineKeyboardButton(
		text='Смотреть P&L',
		callback_data="pnl_menu")
	)
	builder.row(types.InlineKeyboardButton(
		text='Поставить оповещение',
		callback_data="set_notification")
	)
	builder.row(types.InlineKeyboardButton(
		text='Редактировать кошельки',
		callback_data="edit_wallets_menu")
	)


	await users[callback.message.chat.id].wallet_keeper.load_balances()

	await bot.edit_message_text( 
		text=f'Ваш суммарный баланс (на всех кошельках): {users[callback.message.chat.id].wallet_keeper.saved_usd_balance}',
		chat_id=callback.message.chat.id,
		message_id=callback.message.message_id,
		reply_markup=builder.as_markup()
	)




@dp.callback_query(F.data == "edit_wallets_menu")
async def edit_wallets_menu(callback: types.CallbackQuery):
	builder = InlineKeyboardBuilder()
	builder.add(types.InlineKeyboardButton(
		text="Добавить кошелек",
		callback_data="add_wallet")
	)
	builder.add(types.InlineKeyboardButton(
		text="Назад в меню",
		callback_data="main_menu")
	)
	user = users[callback.message.chat.id]
	wallets_text = user.get_wallets_as_text()
	await callback.message.answer(
		text=f'Ваши кошельки: {wallets_text}\n Добавьте новый кошелек или ведите адрес кошелька, который вы хотите редактировать:',
		reply_markup = builder.as_markup()
	)




@dp.callback_query(F.data == "balance_filter_menu")
async def balance_filter_menu(callback: types.CallbackQuery):
	builder = InlineKeyboardBuilder()
	builder.row(types.InlineKeyboardButton(
		text='Обновить',
		callback_data="balance_filter_menu")
	)
	builder.row(types.InlineKeyboardButton(
		text='Cмотреть баланс всех кошельков во всех сетях и во всех токенах',
		callback_data="balance_all")
	)
	builder.row(types.InlineKeyboardButton(
		text='Cмотреть баланс по кошелькам',
		callback_data="balance_by_wallets")
	)
	builder.row(types.InlineKeyboardButton(
		text='Cмотреть баланс по сетям',
		callback_data="balance_by_chains")
	)
	builder.row(types.InlineKeyboardButton(
		text='Cмотреть баланс по токенам',
		callback_data="balance_by_tokens")
	)
	builder.row(types.InlineKeyboardButton(
		text='Cмотреть баланс по своему фильтру',
		callback_data="balance_custom_filter")
	)
	builder.row(types.InlineKeyboardButton(
		text='Назад в меню',
		callback_data="main_menu")
	)
	user = users[callback.message.chat.id]

	await user.wallet_keeper.load_balances()
	balance_top_chains = user.wallet_keeper.get_top_chain_balances(top_chains=5)
	top5_text = f'Ваш суммарный баланс (на всех кошельках): {user.wallet_keeper.saved_usd_balance}'
	for wallet_chain in balance_top_chains:
		wallet_address, chain_name = wallet_chain.split()
		wallet_name = user.get_wallet_name(wallet_address)
		top5_text += f'<b> - {wallet_name} | {wallet_address} | {chain_name} : {balance_top_chains[wallet_chain]}</b> \n'

	# if not user.is_sent(callback.message.message_id):
	await callback.message.answer(
		text=top5_text,
		reply_markup = builder.as_markup()
	)
	# 	users[callback.message.chat.id].msg_sent(callback.message.message_id)
	# else:
	await bot.edit_message_text( 
		text=top5_text,
		chat_id=callback.message.chat.id,
		message_id=callback.message.message_id,
		reply_markup=builder.as_markup()
	)




async def show_filtered_balance(callback, callback_data, msg_text, builder = None):
	if builder is None:
		builder = InlineKeyboardBuilder()
	builder.add(types.InlineKeyboardButton(
		text='Обновить',
		callback_data=callback_data)
	)
	builder.add(types.InlineKeyboardButton(
		text='Назад',
		callback_data="balance_filter_menu")
	)
	user = users[callback.message.chat.id]
	msg_text = f'Ваш суммарный баланс (на всех кошельках): {user.wallet_keeper.saved_usd_balance}\n' + msg_text

	if not user.is_sent(callback.message.message_id):
		await callback.message.answer(
			text=msg_text,
			reply_markup = builder.as_markup()
		)
		users[callback.message.chat.id].msg_sent(callback.message.message_id)
	else:
		await bot.edit_message_text( 
			text=msg_text,
			chat_id=callback.message.chat.id,
			message_id=callback.message.message_id,
			reply_markup=builder.as_markup()
		)




@dp.callback_query(F.data == "balance_all")
async def balance_all(callback: types.CallbackQuery):
	user = users[callback.message.chat.id]
	await user.wallet_keeper.load_balances()

	# for wallet in user.wallet_keeper.wallet_addresses:
	# 	msg_text += f'- Wallet {user.get_wallet_name(wallet)} | {wallet} | {user.get_wallet_notes(wallet, limit_chars=15)} | \
	# 	 ${user.wallet_keeper.balances[wallet].total_sum_usd()} :'
	# 	wallet_chain_balance = user.wallet_keeper.balances[wallet].chain_balance
	# 	for chain_name in wallet_chain_balance:
	# 		msg_text += f'-- Chain {chain_name}: ${user.wallet_keeper.balances[wallet].get_chain_balance_usd(chain_name)}'
	# 		token_balances = wallet_chain_balance[chain_name]
	# 		for token_symbol in token_balances:
	# 			msg_text += f'<b>--- {token_symbol:5}: {token_balances[token_symbol]} | ${get_usd_value(token_symbol, token_balances[token_symbol])}</b> \n'
	msg_text = user.filter_balance(show=['wallet', 'chain', 'token'])
	await show_filtered_balance(callback, 'balance_all', msg_text)



@dp.callback_query(F.data == "balance_by_wallets")
async def balance_by_wallets(callback: types.CallbackQuery):
	user = users[callback.message.chat.id]
	await user.wallet_keeper.load_balances()

	msg_text = user.filter_balance(show=['wallet'])
	await show_filtered_balance(callback, 'balance_by_wallets', msg_text)
	


@dp.callback_query(F.data == "balance_by_chains")
async def balance_by_chains(callback: types.CallbackQuery):
	user = users[callback.message.chat.id]
	await user.wallet_keeper.load_balances()

	msg_text = user.filter_balance(show=['chain'])
	await show_filtered_balance(callback, 'balance_by_chains', msg_text)
	


@dp.callback_query(F.data == "balance_by_tokens")
async def balance_by_tokens(callback: types.CallbackQuery):
	user = users[callback.message.chat.id]
	await user.wallet_keeper.load_balances()

	msg_text = user.filter_balance(show=['token'])
	await show_filtered_balance(callback, 'balance_by_tokens', msg_text)
	


# №№№№#### 
async def show_custom_filter_menu(callback):
	builder = InlineKeyboardBuilder()
	builder.row(types.InlineKeyboardButton(
		text='Фильтр по кошелькам',
		callback_data='filter_by_wallet')
	)
	builder.row(types.InlineKeyboardButton(
		text='Фильтр по сетям',
		callback_data='filter_by_chains')
	)
	builder.row(types.InlineKeyboardButton(
		text='Фильтр по токенам',
		callback_data='filter_by_tokens')
	)

	uder = users[callback.message.chat.id]

	filters_text = ''
	for arg in user.set_filter_kwargs:
		filters_text += f"{arg}: {' '.join(user.set_filter_kwargs[arg])}"
	msg_text = 'Текущие фильтры:\n' + filters_text
	msg_text += user.filter_balance(*user.set_filter_kwargs)
	await show_filtered_balance(callback, 'balance_custom_filter', msg_text, builder=builder)
	

@dp.callback_query(F.data == "filter_by_chains")
async def filter_by_chains(callback: types.CallbackQuery):
	msg_text = 'Отправьте названия сетей в формате: filter_chains имя_сети1 имя_сети2 имя_сети3 ...'
	await callback.message.answer(msg_text)


@dp.callback_query(F.data == "filter_by_tokens")
async def filter_by_tokens(callback: types.CallbackQuery):
	msg_text = 'Введите названия токенов в формате: filter_tokens имя_токена1 имя_токена2 имя_токена3 ...'
	await callback.message.answer(msg_text)

@dp.callback_query(F.data == "filter_by_wallet")
async def filter_by_wallet(callback: types.CallbackQuery): ## FREFGE
	builder = InlineKeyboardBuilder()
	builder.row(types.InlineKeyboardButton(
		text='Фильтр по адресам кошкльков',
		callback_data='filter_by_wallet_addresses')
	)
	builder.row(types.InlineKeyboardButton(
		text='Фильтр по сетям',
		callback_data='filter_by_chains')
	)
	builder.row(types.InlineKeyboardButton(
		text='Фильтр по токенам',
		callback_data='filter_by_tokens')
	)
	builder.row(types.InlineKeyboardButton(
		text='Назад',
		callback_data="balance_custom_filter")
	)

	uder = users[callback.message.chat.id]
	msg_text = 'По какому параметру вы хотите фильтровать кошельки?'
	await callback.message.answer(msg_text, reply_markup = builder.as_markup())




@dp.callback_query(F.data == "filter_by_wallet_addresses")
async def filter_by_wallet_address(callback: types.CallbackQuery):
	msg_text = 'Введите адреса в формате: filter_wallet_addresses адрес_кошелька1 адрес_кошелька2 адрес_кошелька3 ...'
	await callback.message.answer(msg_text)

@dp.callback_query(F.data == "filter_by_wallet_name")
async def filter_by_wallet_name(callback: types.CallbackQuery):
	msg_text = 'Введите названия кошкльков в формате: filter_wallet_names имя_кошклька1 имя_кошклька2 имя_кошклька3 ...'
	await callback.message.answer(msg_text)

@dp.callback_query(F.data == "filter_by_wallet_note")
async def filter_by_wallet_note(callback: types.CallbackQuery):
	msg_text = 'Введите заметки по кошелькам в формате: filter_wallet_notes заметка1 заметка2 заметка3 ...'
	await callback.message.answer(msg_text)




@dp.callback_query(F.data == "balance_custom_filter")
async def balance_custom_filter(callback: types.CallbackQuery):
	await show_custom_filter_menu(callback)



# сообщение с кнопками 
@dp.message(Command("random"))
async def cmd_random(message: types.Message):
	builder = InlineKeyboardBuilder()
	builder.add(types.InlineKeyboardButton(
		text="Нажми меня",
		callback_data="random_value")
	)
	await message.answer(
		"Нажмите на кнопку, чтобы бот отправил число от 1 до 10",
		reply_markup=builder.as_markup()
	)

# что делать, если нажали ту кнопку 
@dp.callback_query(F.data == "random_value")
async def send_random_value(callback: types.CallbackQuery):
	await callback.message.answer(str(random.randint(1, 10)))





async def main():
	await bot.delete_webhook(drop_pending_updates=True)
	await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())



if __name__ == "__main__":
	# logging.basicConfig(level=logging.INFO)
	asyncio.run(main())

