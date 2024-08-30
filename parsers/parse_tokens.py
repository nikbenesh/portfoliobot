from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import time


# url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/map'

# symbols: 
# https://coinmarketcap.com/tokens/views/all/


# с этим api очень мало токенов реально, это не пойдет 

class ContractsParser:
	def __init__(self, 
		contracts_filename='token_contracts.json', symbols_filename='token_symbols.json'):
		self.headers = {
			'Accepts': 'application/json',
			'X-CMC_PRO_API_KEY': 'd70b787e-869b-441e-8955-afa1c945e63e',
		}
		self.parameters = {
			'symbol': ''
		}
		
		self.session = Session()
		self.session.headers.update(self.headers)
		self.contracts = {}
		self.contracts_filename = contracts_filename
		self.symbols_filename = symbols_filename
		self.token_symbols = []

	def parse_symbols(self):
		url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
		
		symbols = []
		for start in range(1, 20000, 5000):
			params = {
				'start': start,
				'limit': 5000,
			}
		
			r = self.session.get(url, params=params)
			data = r.json()
			
			for number, item in enumerate(data['data']):
				print(f"{start+number:4} | {item['symbol']:5} | {item['date_added'][:10]}")
				symbols.append(item['symbol'])
		
		with open(self.symbols_filename, 'w') as file:
			json.dump(symbols, file)


	def load_symbols(self):
		with open(self.symbols_filename, 'r') as symbols_file:
			self.token_symbols = json.load(symbols_file)

	def get_multiple_token_contracts(self, tokens):

	def reform_tokens_dict(self, token_dict, tokens_str):
		tokens = tokens_str.split(',')
		chains_with_tokens_dict = {}
		for token in tokens:
			token_contracts = token_dict[token][0]['contract_address']
			for contract_data in token_contracts:
				chain_name = contract_data['platform']['name']
				contract_address = contract_data['contract_address']
				if chain_name not in chains_with_tokens_dict:
					chains_with_tokens_dict[chain_name] = {}
				chains_with_tokens_dict[chain_name][token] = contract_address







	def get_contracts(self, token, multiple_tokens=False):
		self.parameters['symbol'] = token
		token_contracts = {}
		url = 'https://pro-api.coinmarketcap.com/v2/cryptocurrency/info'
		print('Getting contract adresses for: ', token)
		try:
			response = self.session.get(url, params=self.parameters)
			r_data = response.json()
			if token == 'USDT':
				print(response.text)
			print('Response status:', r_data['status'], '\n')
			if multiple_tokens:
				return self.reform_tokens_dict(r_data['data'], token) # testing

			if r_data['status']['error_code'] == 1008:
				print('Reached the api requests limit. Waiting 1 minute for them to recover...')
				time.sleep(60) # wait untill the api requests limit recovers 
				return self.get_contracts(token)

			token_adresses = r_data['data'][token][0]['contract_address']
			for contract_data in token_adresses:
				chain_name = contract_data['platform']['name']
				token_contracts[chain_name] = contract_data['contract_address']
			
		except (ConnectionError, Timeout, TooManyRedirects) as e:
			print(e)

		return token_contracts



	def update_contracts(self):
		for token in self.token_symbols:
			self.contracts[token] = self.get_contracts(token)
		return self.contracts

	def dump_contracts(self):
		with open(self.contracts_filename, 'w') as f:
			json.dump(self.contracts, f)

	def __del__(self):
		self.session.close()


def main():
	parser = ContractsParser()
	# parser.parse_symbols()
	parser.load_symbols()
	contracts = parser.get_contracts('BTC,ETH,USDT,BNB,SOL')
	# contracts = parser.update_contracts()
	# parser.dump_contracts()
	with open('contracts_test.json', 'w') as file:
		json.dump(contracts, file)


if __name__ == '__main__':
	main()


# https://docs.cloud.debank.com/en/readme/api-pro-reference/chain 
# use debank api and maybe later arkham api ; it might help a lot. 
