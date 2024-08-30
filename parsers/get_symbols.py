import requests
import json


filename = 'token_symbols.json'

headers = {
			'Accepts': 'application/json',
			'X-CMC_PRO_API_KEY': '12345678',
}

def get_symbols(symbols_filename='token_symbols.json', limit=20000):
	url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
	symbols = []
	for start in range(1, 20000, 5000):
		params = {
			'start': start,
			'limit': 5000,
		}
	
		r = requests.get(url, params=params, headers=headers)
		data = r.json()
		
		for number, item in enumerate(data['data']):
			print(f"{start+number:4} | {item['symbol']:5} | {item['date_added'][:10]}")
			symbols.append(item['symbol'])
	
	with open(symbols_filename, 'w') as file:
		json.dump(symbols, file)
	return symbols



if __name__ == '__main__':
	get_symbols()

