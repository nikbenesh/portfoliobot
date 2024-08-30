from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import time


class CGParser:
	def __init__(self, contracts_filename='token_contracts_cg.json', chains_filename='chains2.json'):
		self.session = Session()
		self.contracts = {}
		self.contracts_filename = contracts_filename
		self.chains_filename = chains_filename
		self.cg_chain_dict = {}
		self.chains_with_contracts = {}
		self.log_filename = 'logs'
		self.blockings = 0
		self.large_block = False

	def log(self, msg):
			with open(self.log_filename, 'w+') as log_file:
				log_file.write(msg)

	def load_cg_chains(self):
		url = 'https://api.coingecko.com/api/v3/asset_platforms'
		response = self.session.get(url)
		data = response.json()
		for cg_chain in data:
			self.cg_chain_dict[cg_chain['chain_identifier']] = cg_chain
		return self.cg_chain_dict

	def get_cg_contracts(self, cg_chain_id):
		url = f'https://tokens.coingecko.com/{cg_chain_id}/all.json'
		response = self.session.get(url)

		if 'access denied' in response.text.lower() or 'Error 1015' in response.text:
			if self.large_block:
				self.large_block = False
				return None
			if self.blockings >= 7:
				print('7 blockings. waiting 120 seconds...')
				time.sleep(120)
				self.blockings = 0
				self.large_block = True
			else:
				print(f'coingecko blocked me. Waiting 10 seconds... [blocking #{self.blockings}]')
				time.sleep(10)
			self.session.close()
			self.session = Session()
			self.blockings += 1
			return self.get_cg_contracts(cg_chain_id)

		if response.text[0] not in '{[':
			self.log(response.text)

		data = response.json()
		return data['tokens']

	def parse_contracts(self, chains_list=None):
		if chains_list is None:
			with open(self.chains_filename, 'r') as chains_file:
				chains_list = json.load(chains_file)
		
		for chain in chains_list:
			chain_id = chain['chainId']
			chain_name = chain['name']
			if chain_id in self.cg_chain_dict:
				cg_chain = self.cg_chain_dict[chain_id]
				self.chains_with_contracts[chain_name] = self.get_cg_contracts(cg_chain['id'])
				print('Successfully loaded contracts for the following chain:', chain_name, chain_id)
			else:
				print('Chain not found in coingecko:', chain_name, chain_id)
		return self.chains_with_contracts

	def dump_contracts(self):
		with open(self.contracts_filename, 'w') as contracts_file:
			json.dump(self.chains_with_contracts, contracts_file)

	def __del__(self):
		self.session.close()



def main():
	# TESTS
	parser = CGParser()
	parser.load_cg_chains()
	parser.parse_contracts()
	parser.dump_contracts()


if __name__ == '__main__':
	main()
