from balances import Balance
from utils.price_checker import PriceChecker
from utils.utils import _set, save_json
import asyncio


class BalanceFilter:
	def __init__(self, wallet_address, chain_balances={}, tokens=None, chain_names=None):
		self.tokens = _set(tokens)
		self.chain_names = _set(chain_names)
		self.chain_balances = chain_balances

		self.wallet_address = wallet_address
		self.balance_checker = Balance(wallet_address)
		self.price_checker = PriceChecker()
		# self.prices = self.price_checker.get_token_prices(['ETH', 'USDT', 'USDC'])
		self.prices = self.price_checker.current_prices
		self.balance_checker.load_chains()
		self.balance_checker.load_contracts()


	async def reload_balance(self):

		# if asyncio.get_event_loop().is_closed():
		# 	asyncio.set_event_loop(asyncio.new_event_loop())

		# self.chain_balances = asyncio.run(self.balance_checker.get_all_balances())
		self.chain_balances = await self.balance_checker.get_all_balances()
		# save_json(self.chain_balances, 'my_balances.json')
		print('Loaded balances [from BalanceFilter]')
		# print(self.chain_balances)
		self.filter(inplace=True)
		return self.chain_balances

	def sort_chains(self):
		self.sorted_chains = self.chain_balances.keys.sort(key=lambda chain_name: self.get_chain_balance_usd(chain_name))
		return self.sorted_chains

	def get_unique_tokens(self):
		unique_tokens = set()
		for chain in self.chain_balances:
			token_balances = self.chain_balances[chain]
			for token in token_balances:
				unique_tokens.add(token)
		return unique_tokens


	# возвращает баланс заданной сети в $ 
	def get_chain_balance_usd(self, chain_name):
		return self.filter(chain_names=[chain_name]).total_sum_usd()

	def get_token_balance(self, token):
		usd_balance = self.filter(tokens=[token]).total_sum_usd()
		token_balance = usd_balance / self.prices[token]
		return (token_balance, usd_balance)

	def get_balance_by_chains(self):
		balances_by_chains = {}
		for chain_name in self.chain_balances:
			balances_by_chains[chain_name] = self.get_chain_balance_usd(chain_name)
		return balances_by_chains

	def get_balance_by_tokens(self):
		unique_tokens = self.get_unique_tokens()
		balance_by_tokens = {}
		for token in unique_tokens:
			balance_by_tokens[token] = self.get_token_balance(token) # (token_balance, usd_balance)
		return balance_by_tokens


	def total_sum_usd(self):
		total_balance = 0
		unique_tokens = set()
		for chain in self.chain_balances:
			token_balances = self.chain_balances[chain]
			for token in token_balances:
				unique_tokens.add(token)

		self.prices = self.price_checker.get_token_prices(list(unique_tokens))

		for chain in self.chain_balances:
			token_balances = self.chain_balances[chain]
			for token in token_balances:
				total_balance += self.prices[token] * token_balances[token]

		return total_balance

	def filter(self, tokens=None, chain_names=None, inplace=False):
		tokens = _set(tokens) | self.tokens
		chain_names = _set(chain_names) | self.chain_names
		balances = {}
		if len(tokens) == 0 and len(chain_names) == 0:
			return self

		for chain in chain_names:
			if chain in self.chain_balances:
				balances[chain] = {}
				token_balances = self.chain_balances[chain]
				for token in token_balances:
					if token in tokens:
						balances[chain][token] = token_balances[token]

		if inplace:
			self.chain_balances = balances
		return BalanceFilter(self.wallet_address, chain_balances=balances, tokens=tokens, chain_names=chain_names)

	def set_filters(tokens=None, chain_names=None):
		self.tokens = tokens
		self.chain_names = chain_names
		return self

	def add_filters(tokens=None, chain_names=None):
		self.tokens |= _set(tokens)
		self.chain_names |= _set(chain_names)
		return self

	def get_specific_balance(self, chain_name, token):
		token_balance = self.chain_balances[chain_name][token]
		usd_balance = token_balance * PriceChecker.get_token_price(token)
		return (token_balance, usd_balance)


async def main():
	# TESTS: 
	wallet_address = '000000000000000000000000000'
	balance = BalanceFilter(wallet_address)
	print('Loading your wallet balance...')
	await balance.reload_balance()
	print('Total wallet balance:', balance.total_sum_usd())
	# await balance.reload_balance()
	# print('Total wallet balance:', balance.total_sum_usd())


if __name__ == '__main__':
	asyncio.run(main())



