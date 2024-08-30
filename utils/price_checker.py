import requests
from utils.utils import load_json, save_json, _set
import time


class PriceChecker:
	def __init__(self, symbols_filename='parsers/token_symbols.json', prices_filename='token_prices.json'):
		self.headers = {
			'Accepts': 'application/json',
			'X-CMC_PRO_API_KEY': '12345678',
		}
		self.symbols = load_json(symbols_filename)
		self.prices_filename = prices_filename
		self.current_prices = load_json(prices_filename)


	def get_token_price_binance(self, coin : str = 'eth'):
		coin = coin.upper()
		response = requests.get(f'https://api.binance.com/api/v3/depth?limit=1&symbol={coin}USDT')
		if response.status_code != 200:
			print(f'Price Checker got response from binance with code{response.status_code} ; the symbol is: |{coin}|')
			print('JSON:', response.json())
			return False

		result_dict = response.json()
		if 'asks' not in result_dict:
			print('Response contains (no asks):', result_dict)
			return False

		return float(result_dict['asks'][0][0])


	def get_prices_coinmarketcap(self, tokens=[], filename='token_prices.json', save=True):
		url = 'https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest'
		prices = {}

		if len(tokens) < 100:
			result_tokens = list(_set(tokens) | set(self.symbols[:100]))
			if len(result_tokens) > 100:
				final_tokens = []
				for token_symbol in result_tokens:
					if token_symbol in tokens or token_symbol in self.symbols[:100 - len(tokens)]:
						final_tokens.append(token_symbol)
				tokens = final_tokens
			else:
				tokens = result_tokens
		print(f'Sending api request to coinmarketcap for {len(tokens)} tokens... ')
		print('Params:', ','.join(tokens))
		params = {
			'symbol': ','.join(tokens)
		}
		
		r = requests.get(url, params=params, headers=self.headers)

		data = r.json()['data']
		# print(data)
		update_timestamp = time.time()
		# [на будущее] здесь есть еще куча разных других данных по всем монетам: volume, price change 24h, market cap и тд. 
		# А еще там можно получить historical data по монетам -- можно использовать, чтобы следить за имзменением портфеля
		for token_symbol in data:
			if len(data[token_symbol]) < 1:
				print(data[token_symbol])
				continue
			token = data[token_symbol][0]
	
			prices[token['symbol']] = {
			'price': token['quote']['USD']['price'],
			'last updated': update_timestamp
			}
	
		if save:
			# old_prices = load_json(self.prices_filename)
			for token_symbol in prices:
				self.current_prices[token_symbol] = prices[token_symbol]
			save_json(self.current_prices, self.prices_filename)
		return prices

	def get_token_prices(self, token_symbols):
		# old_prices = load_json(self.prices_filename)
		tokens_to_load = []
		result_prices = {}
		print('GETTING PRICES FOR:', token_symbols)
		for token_symbol in token_symbols:
			if token_symbol in self.current_prices and time.time() - self.current_prices[token_symbol]['last updated'] < 5*60:
				result_prices[token_symbol] = self.current_prices[token_symbol]['price']
				print(token_symbol, 'already loaded')
			else:
				tokens_to_load.append(token_symbol)
				print(token_symbol, 'not loaded yet')
		if len(tokens_to_load) > 0:
			print('need to load:', tokens_to_load)
			cmc_prices = self.get_prices_coinmarketcap(tokens=tokens_to_load)
			for token_symbol in cmc_prices:
				result_prices[token_symbol] = cmc_prices[token_symbol]['price']
		return result_prices

	def get_token_usd_value(self, token_symbol):
		price = self.get_token_prices([token_symbol])
		return price[token_symbol]




def main():
	checker = PriceChecker()
	prices = checker.get_token_prices(['WETH', 'USDC', 'AVAX', 'USDB', 'BNB', 'METIS', 'ETH', 'FTM'])
	print(prices)
	# url = "https://pro-api.coingecko.com/api/v3/simple/token_price/bnb"
	
	# headers = {"accept": "application/json"}
	
	# response = requests.get(url, headers=headers)
	
	# print(response.text)


if __name__ == '__main__':
	# TESTS 
	main()
