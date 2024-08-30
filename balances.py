from token_amount import TokenAmount
from web3 import Web3
from web3.eth import AsyncEth
from web3 import AsyncWeb3, AsyncHTTPProvider

import wget
import json
import time
from utils.utils import save_json, load_json, patch_http_connection_pool
from utils.logger import Logger
from multiprocessing import Pool
import asyncio
import requests
from aiohttp import ClientSession


# patch_http_connection_pool(maxsize=1100)


class Balance:
	def __init__(self, address, chains_filename='parsers/chains2.json', symbols_filename='parsers/token_symbols.json',
	 contracts_filename='parsers/token_contracts_cg.json', abi_filename='abi.json'):
		self.address = address
		self.chains = []
		self.chains_with_contracts_list = {}
		self.chains_with_contracts_dict = {}
		self.chain_balances = {}
		self.chains_filename = chains_filename
		self.symbols_filename = symbols_filename
		self.token_symbols = []
		self.contracts_filename = contracts_filename
		self.contracts = {}
		self.abi_for_all = load_json(abi_filename)
		self.logger = Logger('balance_logs')
		self.pool_set = False

	def load_chains(self):
		with open(self.chains_filename, 'r') as f:
			self.chains = json.load(f)

	def load_symbols(self):
		with open(self.symbols_filename, 'r') as symbols_file:
			self.token_symbols = json.load(symbols_file)

	def load_contracts(self):
		with open(self.contracts_filename, 'r') as contracts_file:
			self.chains_with_contracts_list = json.load(contracts_file)
		print('Length of chains with contracts:', len(self.chains_with_contracts_list))

		for chain in self.chains_with_contracts_list:
			token_dict = {}
			if self.chains_with_contracts_list[chain] != None:
				for token in self.chains_with_contracts_list[chain]:
					if token['symbol'] not in token_dict:
						token_dict[token['symbol']] = token
					else:
						token_dict[token['symbol'] + '_ab'] = token
				self.chains_with_contracts_dict[chain] = token_dict

	async def connect_web3(self, rpc):
		print('Connecting to rpc:', rpc)
		args = {
			'limit': 500
		}
		web3 = AsyncWeb3(AsyncHTTPProvider(rpc)) # request_kwargs
		print('Successfully connected to rpc.')
		return web3

	async def get_balance(self, web3, token_contract=None, native=False, token_decimals=18):
		if native:
			balance_wei = await web3.eth.get_balance(Web3.to_checksum_address(self.address))
		else:
			contract = web3.eth.contract(abi=self.abi_for_all, address=Web3.to_checksum_address(token_contract.lower()))
			balance_wei = await contract.functions.balanceOf(Web3.to_checksum_address(self.address.lower())).call()
		self.logger.log(f'Getting balance for {token_contract}\n')

		# token_balance = Web3.from_wei(balance_wei, self.token_symbol_to_short_name(token))
		token_balance = balance_wei / (10 ** token_decimals)
		return token_balance

	async def get_chain_balances(self, chain, top_tokens=40):
		if 'rpc' not in chain:
			print('No RPC found for chain:', chain['name'])
			# not_founds += 1
			return {}
		rpc = chain['rpc']
		web3 = await self.connect_web3(rpc)
		chain_name = chain['name']
		if chain_name in self.chains_with_contracts_list and self.chains_with_contracts_list[chain_name] != None:
			token_balances = {}
			native_balance = await self.get_balance(web3, native=True, token_decimals = chain['nativeCurrency']['decimals'])
			if native_balance > 0:
				print(f'Your native balance in chain {chain_name} : {native_balance}')
			chain_tokens = self.chains_with_contracts_list[chain_name]
			tasks = []
			for token in chain_tokens[:top_tokens]:
				contract = token['address']
				tasks.append(asyncio.create_task(self.get_balance(web3, token_contract=contract, token_decimals = token['decimals'])))

			await asyncio.wait(tasks)
			for index, task in enumerate(tasks):
				token_balance = 0
				try:
					# token_balance = await self.get_balance(web3, token_contract=contract, token_decimals = token['decimals'])
					token_balance = task.result()
					print(f"Successfully loaded balance for {chain_tokens[index]['symbol']} in chain {chain_name}: {token_balance}")
				except Exception as err:
					print(f"ERROR Couldn't load balance for {chain_tokens[index]['symbol']} in chain {chain_name}")
					print(err)
				if token_balance != 0:
					token_balances[chain_tokens[index]['symbol']] = token_balance

			if token_balances != {} or native_balance != 0:
				native_symbol = chain['nativeCurrency']['symbol']
				token_balances[native_symbol] = native_balance
				self.chain_balances[chain_name] = token_balances
				return {'chain_name': chain_name, 'token_balances': token_balances}
			return {}

	async def get_all_balances(self, top_chains=40, top_tokens=40):
		tasks = [asyncio.create_task(self.get_chain_balances(chain)) for chain in self.chains[:top_chains]]
		await asyncio.wait(tasks)

		for index, task in enumerate(tasks):
			try:
				balance = task.result()
				if balance != {}:
					self.chain_balances[balance['chain_name']] = balance['token_balances']
			except Exception as err:
				print(f"ERROR Couldn't load balance for the chain {self.chains[index]['name']}, index {index}")
				print(err)

		return self.chain_balances


def main():
	bal = Balance('')
	print('getting balance')
	money = bal.get_all_balances() 
	print(money)


if __name__ == '__main__':
	main()


# chains2.json , token_contracts.json - нужные файлы с сетями и их rpc  и с контрактами токенов во всех сетях 
# (получил их из coinmarketcap api) - https://coinmarketcap.com/api/documentation/v1/#tag/cryptocurrency


