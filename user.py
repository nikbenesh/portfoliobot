from wallets_keeper import WalletsKeeper
# from utils.price_checker import PriceChecker



class User:
	def __init__(self, chat_id, user_id = None):
		self.chat_id = chat_id
		self.user_id = user_id
		self.waiting = None
		# self.waiting_wallet_address = False
		# self.wait_name = False
		# self.wait_note = False
		self.wallet_keeper = WalletsKeeper(chat_id)
		self.new_wallet_address = None
		self.new_name = None
		self.new_note = None
		self.sent_msgs = set()
		self.set_filtered_keeper = None
		# self.price_checker = PriceChecker()

	def get_wallets_as_text(self):
		text = ''
		for wallet in self.wallet_keeper.wallet_addresses:
			text += f'{self.get_wallet_name(wallet)} | {wallet} | {self.get_wallet_notes(wallet, limit_chars=15)}'
		return text


	def msg_sent(self, msg_id):
		self.sent_msgs.add(msg_id)

	def is_sent(self, msg_id):
		return msg_id in self.sent_msgs

	def wait_for(self, option):
		self.waiting = option

	def wait_wallet(self):
		self.wait_for('wallet_address')

	def wait_name(self):
		self.wait_for('wallet_name')

	def wait_note(self):
		self.wait_for('wallet_note')

	def is_waiting_wallet(self):
		return self.waiting == 'wallet_address'

	def is_waiting_name(self):
		return self.waiting == 'wallet_name'

	def is_waiting_note(self):
		return self.waiting == 'wallet_note'

	def is_new(self):
		return len(self.wallet_keeper.user_wallets.index) == 0

	def wallets_count(self):
		return len(self.wallet_keeper.user_wallets.index)

	def add_wallet(self, wallet_address, name=None, note=None):
		self.wallet_keeper.add_wallet(wallet_address, name=name, note=note)
		self.wallet_keeper.save_db()

	def save_new_wallet(self):
		if self.new_wallet_address in self.wallet_keeper.wallet_addresses:
			if self.new_note:
				self.wallet_keeper.add_note(self.new_note, wallet_address=self.new_wallet_address)
			if self.new_name:
				self.wallet_keeper.set_name(self.new_name, self.new_wallet_address)
		else:
			self.wallet_keeper.add_wallet(self.new_wallet_address, name=self.new_name, note=self.new_note)
		self.wallet_keeper.save_db()
		self.cancel_changes()

	def cancel_changes(self):
		self.new_wallet_address = None
		self.new_name = None
		self.new_note = None

	def delete_current_wallet(self):
		self.wallet_keeper.delete_wallet(wallet_address=self.new_wallet_address)
		self.cancel_changes()

	def add_new_wallet(self, wallet_address):
		self.new_wallet_address = wallet_address
		self.waiting = None

	def add_new_name(self, name):
		self.new_name = name
		self.waiting = None

	def add_new_note(self, note):
		self.new_note = note
		self.waiting = None

	def get_wallet_name(self, wallet_address):
		return self.wallet_keeper.get_wallet_name(wallet_address)

	def get_wallet_notes(self, wallet_address, limit_chars=15):
		return self.wallet_keeper.get_wallet_notes(wallet_address, limit_chars=limit_chars)

	def set_filter_kwargs(self, **filter_kwargs):
		# self.set_filter_kwargs = filter_kwargs
		for arg in filter_kwargs:
			self.set_filter_kwargs[arg] = filter_kwargs[arg]

	# filters:  wallet_notes=[], wallet_names=[], wallets=[], tokens=[], chains=[]
	# show = wallets, and/or chains, and/or tokens 
	def filter_balance(self, show=['wallet', 'chain', 'token'], **filter_kwargs):
		if self.set_filtered_keeper is None:
			filtered_wk = self.wallet_keeper.filter(filter_kwargs)
		else:
			filtered_wk = self.set_filtered_keeper.filter(filter_kwargs)
		self.set_filtered_keeper = filtered_wk
		msg_text = ''
		iter_wallets = filtered_wk.wallet_addresses
		if 'wallet' not in show:
			all_wallets_chain_balance = {}
			for wallet in filtered_wk.wallet_addresses:
				wallet_chain_balance = filtered_wk.balances[wallet].chain_balance
				for chain_name in wallet_chain_balance:
					if chain_name not in all_wallets_chain_balance:
						all_wallets_chain_balance[chain_name] = wallet_chain_balance[chain_name]
					else:
						token_balances = wallet_chain_balance[chain_name]
						for token_symbol in token_balances:
							if token_symbol in all_wallets_chain_balance[chain_name]:
								all_wallets_chain_balance[chain_name][token_symbol] += token_balances[token_symbol]
							else:
								all_wallets_chain_balance[chain_name][token_symbol] = token_balances[token_symbol]
			iter_wallets = [1]


		for wallet in iter_wallets:
			if 'wallet' in show:
				msg_text += f'- Wallet {self.get_wallet_name(wallet)} | {wallet} | {self.get_wallet_notes(wallet, limit_chars=15)} : \
				 ${filtered_wk.balances[wallet].total_sum_usd()}'
				wallet_chain_balance = filtered_wk.balances[wallet].chain_balance
			else:
				wallet_chain_balance = all_wallets_chain_balance

			if 'chain' not in show:
				wallet_chain_balance = [1]
			for chain_name in wallet_chain_balance:
				#### ......
				if 'chain' in show:
					msg_text += f'-- Chain {chain_name}: ${self.wallet_keeper.balances[wallet].get_chain_balance_usd(chain_name)}'
					token_balances = wallet_chain_balance[chain_name]
				else:
					if 'wallet' in show:
						token_balances = filtered_wk.balances[wallet].get_balance_by_tokens()
					else:
						token_balances = BalanceFilter('', chain_balances=all_wallets_chain_balance).get_balance_by_tokens()
				if 'token' in show:
					for token_symbol in token_balances:
						if type(token_balances[token_symbol]) is tuple:
							token_value, usd_value = token_balances[token_symbol]
							msg_text += f'<b>--- {token_symbol:5}: {token_value} | ${usd_value}</b> <br>'
						else:
							msg_text += f'<b>--- {token_symbol:5}: {token_balances[token_symbol]} | $</b> <br>'
							# price_checker.get_token_usd_value(token_symbol, token_balances[token_symbol])

		self.filtered_balance_text = msg_text
		return msg_text


	def set_filtered_balance():
		self.set_filtered_keeper
		self.set_filtered_show







