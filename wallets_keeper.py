from filter import BalanceFilter
import asyncio
import pandas as pd
import sqlite3
from utils.utils import file_exists
# from utils.utils import save_json, load_json


class WalletsKeeper:
	def __init__(self, owner_id, wallet_addresses=[], wallet_balances = {}, db_filename='wallets.db', csv_db='wallets.csv'):
		self.owner_id = owner_id
		self.balances = {}
		self.csv_db_filename = csv_db
		if file_exists(csv_db):
			self.wallets_df = pd.read_csv(csv_db, index_col='owner_id')
		else:
			self.wallets_df = pd.DataFrame()
		self.user_wallets = self.wallets_df[self.wallets_df.index == self.owner_id]
		# print('READ user_wallets:', self.user_wallets)
		self.wallet_addresses = set(wallet_addresses) | set(self.user_wallets['address'])
		if wallet_balances == {}:
			# print('READING wallet addresses to get balances:', )
			for wallet in self.wallet_addresses:
				self.balances[wallet] = BalanceFilter(wallet)
		else:
			self.balances = wallet_balances
		# connection = sqlite3.connect(db_filename)
		# cursor = connection.cursor()

	def add_note(self, note, wallet_address=None, name=None):
		if wallet_address:
			self.wallets_df.loc[self.wallets_df['address'] == wallet_address, 'note'] = note
		if name:
			self.wallets_df.loc[self.wallets_df['name'] == name, 'note'] = note

	def set_name(self, name, wallet_address):
		self.wallets_df.loc[self.wallets_df['address'] == wallet_address, 'name'] = name

	def change_address(self, new_address, wallet_address=None, name=None):
		if wallet_address:
			self.wallets_df.loc[self.wallets_df['address'] == wallet_address, 'address'] = new_address
		if name:
			self.wallets_df.loc[self.wallets_df['name'] == name, 'address'] = new_address

	def update_wallets_list(self):
		self.wallets_df = pd.read_csv(self.csv_db_filename, index_col='owner_id')
		self.user_wallets = self.wallets_df[self.wallets_df.index == self.owner_id]
		self.wallet_addresses = self.user_wallets['address']
		self.balances = [BalanceFilter(wallet) for wallet in self.wallet_addresses]

	def delete_wallet(self, wallet_address=None, name=None):
		if name:
			self.wallets_df.drop(self.wallets_df[self.wallets_df['name'] == name, 'address'].index)
		if wallet_address:
			self.wallets_df.drop(self.wallets_df[self.wallets_df['address'] == wallet_address, 'address'].index)
		# delete wallet from balances:
		del self.balances[wallet_address]
		self.save_db()
		self.update_wallets_list()

	def add_wallet(self, wallet_address, name=None, note=None, save=False):
		new_entry = {'owner_id': [self.owner_id], 'name': [name], 'address': [wallet_address], 'note': [note], 'total_usd_balance': [0]}
		new_entry = pd.DataFrame(new_entry).set_index('owner_id')
		self.wallets_df = self.wallets_df.append(new_entry)
		self.user_wallets = self.user_wallets.append(new_entry)
		if save:
			self.save_db()
		self.balances[wallet_address] = BalanceFilter(wallet_address)
		self.wallet_addresses.add(wallet_address)
		# self.wallets_df.loc[len(self.wallets_df.index)] = [self.owner_id, name, wallet_address, note, 0]

	def save_db(self):
		print('saving wallets_df...')
		self.wallets_df.to_csv(self.csv_db_filename)

	async def update_wallet_balance(self, wallet_address=None, name=None):
		if name:
			wallet_address = self.wallets_df.loc[self.wallets_df['name'] == name, 'wallet_address'] 
		if wallet_address:
			await self.balances[wallet_address].reload_balance()
			self.wallets_df.loc[self.wallets_df['address'] == wallet_address, 'total_usd_balance'] = self.balances[wallet_address].total_sum_usd()


	async def load_balances(self, wallets=[]):
		if wallets == []:
			wallets = self.wallet_addresses

		tasks = [asyncio.create_task(self.balances[wallet].reload_balance()) for wallet in wallets]
		await asyncio.wait(tasks)


		print('Loaded balances [from WalletsKeeper]')
		self.saved_usd_balance = self.get_total_portfolio_usd_balance()
		await asyncio.sleep(4)
		# save_json(self.balances, 'debug_balances.json')

		# for index, taks in enumerate(tasks):
		# 	wallet_balance = task.result()
		# 	# balances[wallets[index]] = wallet_balance

	def get_total_portfolio_usd_balance(self):
		total_balance = 0
		for wallet in self.wallet_addresses:
			total_balance += self.balances[wallet].total_sum_usd()
		return total_balance

	def get_top_chain_balances(self, top_chains=5):
		wallet_addresses_list = list(self.wallet_addresses)
		wallet_addresses_list.sort(key=lambda wallet: self.balances[wallet].total_sum_usd())
		wallet_chain_balances = {}
		for wallet in wallet_addresses_list:
			chain_balances = self.balances[wallet].get_balance_by_chains()
			for chain_name in chain_balances:
				wallet_chain_balances[wallet + ' ' + chain_name] = chain_balances[chain_name]
		sorted_wallet_chains = sorted(wallet_chain_balances.keys(), key=lambda wallet_chain: wallet_chain_balances[wallet_chain])

		top_wallet_chains = {wallet_chain : wallet_chain_balances[wallet_chain] for wallet_chain in sorted_wallet_chains[:top_chains]}
		return top_wallet_chains

	def get_wallet_name(self, wallet_address):
		index = self.wallets_df[self.wallets_df['address'] == wallet_address].index[0]
		print(index)
		name = self.wallets_df.loc[index, 'name']
		if pd.isna(name):
			return ''
		return name

	def get_wallet_notes(self, wallet_address, limit_chars=15):
		index = self.wallets_df[self.wallets_df['address'] == wallet_address].index[0]
		note = self.wallets_df.loc[index, 'note']
		if pd.isna(note):
			return ''
		if len(note) > limit_chars:
			note = note[:limit_chars - 3] + '...'
		return note



	def filter(self, wallet_notes=[], wallet_names=[], wallet_addresses=[], tokens=[], chains=[], inplace=False):
		filtered_df = self.wallets_df
		if len(wallet_notes) > 0:
			filtered_df = filtered_df[any(note in filtered_df['note'] for note in wallet_notes)]
		if len(wallet_addresses) > 0:
			filtered_df = filtered_df[any(wallet_address == filtered_df['address'] for wallet_address in wallet_addresses)]
		if len(wallet_names) > 0:
			filtered_df = filtered_df[any(name in filtered_df['name'] for name in wallet_names)]

		filtered_balances = {}
		for wallet in filtered_df['address']:
			filtered_balances[wallet] = self.balances[wallet].filter(tokens=tokens, chains=chains)

		if inplace:
			self.balances = filtered_balances
			self.wallet_addresses = filtered_df['address']
		return WalletsKeeper(wallet_addresses = filtered_df['address'], wallet_balances = filtered_balances)

	def __del__(self):
		self.save_db()


