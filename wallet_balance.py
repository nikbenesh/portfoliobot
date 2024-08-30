from balance import Balance
from utils import get_token_price


# filter = (tokens , chains)

class WalletBalance:
	def __init__(self, wallet_address, balance_filter=None):
		self.wallet_address = wallet_address
		self.chain_balances = {}
		self.filtered_balance = {}
		self.balance_checker = Balance(wallet_address)
		balance_checker.load_chains()
		balance_checker.load_contracts()

	def reload_balance(self):
		self.chain_balances = self.balance_checker.get_all_balances()
		

	# возвращает баланс заданной сети в $ 
	def get_chain_balance(self, chain_name):
		balance = 0
		token_balances = self.chain_balances[chain_name]
		for token in token_balances:
			balance += get_token_price(token) * token_balances[token]
		return balance

	def get_token_balance(self, token):
		token_balance = 0
		for chain in self.chain_balances:
			if token in chain_balances[chain]:
				token_balances += chain_balances[chain][token]
		return (token_balance, token_balance * get_token_price(token))

	def get_total_balance(self):
		total_balance = 0
		for chain in self.chain_balances:
			token_balances = self.chain_balances[chain]
			for token in token_balances:
				total_balance += get_token_price(token) * token_balances[token]

	def get_balance(self, chain_name, token):
		token_balance = self.chain_balances[chain_name][token]
		usd_balance = token_balance * get_token_price(token)
		return (token_balance, usd_balance)

	def filter_by_chains(self, chain_names):
		balance = 0
		for chain in chain_names:
			balance += self.get_chain_balance(chain)

	def filter_by_tokens(self, tokens):
		balance = 0
		for token in tokens:
			balance += self.get_token_balance(token)
		return balance
			


