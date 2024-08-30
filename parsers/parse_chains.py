import wget
import json
from web3 import Web3


# https://chainid.network/chains.jsons

# filename = wget.download('https://chainid.network/chains.json')

with open('chains.json', 'r') as chains_file:
	chains = json.load(chains_file)

eth_rpc = chains[0]['rpc'][3]
print(eth_rpc)
print(chains[0]['explorers'][0])
# print(get_balance(adress, eth_rpc))

sample_address = '0x975580eb2B1473Ac0b9FDF9F5eEc9C26C04A3F76'
save_chains = []
for chain in chains:
	# print(*[key for key in chain.keys()], sep='\n')
	save_chain = {}
	if 'explorers' in chain:
		if len(chain['explorers']) > 0:
			save_chain['explorer'] = chain['explorers'][0]
		else:
			print(chain['explorers'])
			print(chain['name'])
	else:
		print(chain['name'])

	save_chain['nativeCurrency'] = chain['nativeCurrency']
	for rpc in chain['rpc']:
		if 'API_KEY' not in rpc:
			try:
				web3 = Web3(Web3.HTTPProvider(rpc))
				web3.eth.get_balance(Web3.to_checksum_address(sample_address))
				save_chain['rpc'] = rpc
				break
			except:
				continue
	save_chain['name'] = chain['name']
	save_chain['chain'] = chain['chain']
	save_chain['shortName'] = chain['shortName']
	save_chain['chainId'] = chain['chainId']
	if 'faucets' in chain and len(chain['faucets']) > 0:
		save_chain['isTestnet'] = True
		print('Testnet', chain['name'])
	else:
		save_chain['isTestnet'] = False
	save_chains.append(save_chain)

with open('chains2.json', 'w') as f:
	json.dump(save_chains, f)




