import sys
sys.path.insert(0, '..')

from utils.utils import load_json, save_json


def index_in_list(arr, el):
	if el in arr:
		return arr.index(el)
	else:
		return len(arr) + 1

def len_(arr):
	if arr is None:
		return 0
	return len(arr)

class Sorter:
	def __init__(self, symbols_filename='token_symbols.json', chains_tokens_filename = 'token_contracts_cg.json',
	 chains_filename='chains2.json'):
		self.symbols_filename = symbols_filename
		self.chains_tokens_filename = chains_tokens_filename
		self.chains_filename = chains_filename
		self.symbols = load_json(symbols_filename)
		self.chains_tokens = load_json(chains_tokens_filename)
		self.chains_arr = load_json(chains_filename)

	def sort(self):
		for chain_name in self.chains_tokens:
			tokens = self.chains_tokens[chain_name]
			if tokens != None:
				self.chains_tokens[chain_name] = sorted(tokens, key=lambda token: index_in_list(self.symbols, token['symbol']))
		sorted_chain_names = sorted(self.chains_tokens.keys(), key=lambda chain_name: len_(self.chains_tokens[chain_name]), reverse=True)

		self.chains_arr = sorted(self.chains_arr, key=lambda chain: index_in_list(sorted_chain_names, chain['name']))

	def save(self):
		save_json(self.chains_arr, self.chains_filename)
		save_json(self.chains_tokens, self.chains_tokens_filename)



if __name__ == '__main__':
	sorter = Sorter()
	sorter.sort()
	sorter.save()
