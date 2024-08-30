# using selemnium and chainlist.org 
from selenium import webdriver 
from fake_useragent import UserAgent
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException 
from selenium.common.exceptions import TimeoutException


import time
import json
import os
import sys
from mdriver import MDriver
from web3 import Web3
import sys
sys.path.insert(0, '..')

from utils.utils import load_json, save_json


class RPCLoader:
	def __init__(self, chains_filename = 'chains2.json'):
		self.chains_filename = chains_filename
		self.log_filename = 'rpcs_test.csv'
		self.chains_list = load_json(chains_filename)

	def log_rpc(chain_name, rpc=None):
		with open(self.log_filename, 'a') as rpc_log_file:
			rpc_log_file.write(f'{chain_name},{rpc}')

	def launch_driver(self, include_testnets = False):
		# 1 -- user agent
		options = Options()
		options.add_argument(f"user-agent={UserAgent.random}")
		options.add_argument("--disable-blink-features=AutomationControlled")	
		
		self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options) # without proxy
		self.mdriver = MDriver(self.driver, wait_for=60)
		
		
		self.driver.get('https://chainlist.org')
		
		self.driver.implicitly_wait(10)
		if include_testnets:
			self.mdriver.click_el('//*[@id="__next"]/div/div[2]/div[1]/header/div/div[2]/label/input') # include testnets checkbutton 
		time.sleep(2)
	
	# 1527 total chains on chain list (including testnets)
	def load_rpcs(self, top_chains=60):
		chain_rpcs = {}
		for i in range(1, top_chains):
			if not self.mdriver.check_if_element_exists(f'//*[@id="__next"]/div/div[2]/div[2]/div[{i}]/a/span'):
				print('Reached the end of the chains,', i, '; breaking...')
				break
			chain_name = self.mdriver.find_by_xpath(f'//*[@id="__next"]/div/div[2]/div[2]/div[{i}]/a/span', wait_it=True).text
		
			self.mdriver.click_el(f'//*[@id="__next"]/div/div[2]/div[2]/div[{i}]/button[2]', wait_it=True) # click the arrow button to unfold RPCs table
			time.sleep(0.3)
		
			if self.mdriver.check_if_element_exists(f'//*[@id="__next"]/div/div[2]/div[2]/div[{i+1}]/table/tbody/tr[1]/td[1]'):
				rpc = self.mdriver.find_by_xpath(f'//*[@id="__next"]/div/div[2]/div[2]/div[{i+1}]/table/tbody/tr[1]/td[1]', wait_it=True, wait_for_text=':').text
				print('RPC for', chain_name, ':', rpc)
				self.log_rpc(chain_name, rpc)
				chain_rpcs[chain_name] = rpc
			elif self.mdriver.check_if_element_exists(f'//*[@id="__next"]/div/div[2]/div[2]/div[{i+1}]/table/tbody/tr/td[1]'):
				rpc = self.mdriver.find_by_xpath(f'//*[@id="__next"]/div/div[2]/div[2]/div[{i+1}]/table/tbody/tr/td[1]', wait_it=True, wait_for_text=':').text
				print('RPC for', chain_name, ':', rpc)
				self.log_rpc(chain_name, rpc)
				chain_rpcs[chain_name] = rpc
			else:
				print('No rpc found for', chain_name)
				self.log_rpc(chain_name)
			time.sleep(0.3)
			self.mdriver.click_el(f'//*[@id="__next"]/div/div[2]/div[2]/div[{i}]/button[2]', wait_it=True)
		return chain_rpcs
	
	def find_rpc(self, chain_name):
		print('Looking for RPC for', chain_name)
		time.sleep(0.5)
		self.mdriver.find_by_xpath('//*[@id="__next"]/div/div[2]/div[1]/header/div/div[1]/label/input', wait_it=True).clear()
		time.sleep(0.5)
		self.mdriver.send_keys('//*[@id="__next"]/div/div[2]/div[1]/header/div/div[1]/label/input', chain_name) # send the chain name to search input
		time.sleep(1)
	
		if self.mdriver.check_if_element_exists('//*[@id="__next"]/div/div[2]/div[2]/div/button[2]'):
			self.mdriver.click_el('//*[@id="__next"]/div/div[2]/div[2]/div/button[2]') # click the arrow button to unfold RPCs
			time.sleep(1)
			if self.mdriver.check_if_element_exists('//*[@id="__next"]/div/div[2]/div[2]/div[2]/table/tbody/tr[1]/td[1]'):
				rpc = self.mdriver.find_by_xpath('//*[@id="__next"]/div/div[2]/div[2]/div[2]/table/tbody/tr[1]/td[1]', wait_for_text=':').text
				print('RPC for', chain_name, ':', rpc)
				return rpc
			elif self.mdriver.check_if_element_exists('//*[@id="__next"]/div/div[2]/div[2]/div[2]/table/tbody/tr/td[1]'):
				rpc = self.mdriver.find_by_xpath('//*[@id="__next"]/div/div[2]/div[2]/div[2]/table/tbody/tr[1]/td[1]', wait_for_text=':').text
				print('RPC for', chain_name, ':', rpc)
				return rpc
		print('No RPC for', chain_name)
		return None

	def fetch_rpc(self, top_chains=60, save=True):
		for index, chain in enumerate(self.chains_list[:top_chains]):
			if 'rpc' not in chain or chain['rpc'] is None:
				self.chains_list[index]['rpc'] = self.find_rpc(chain['name'])

		if save:
			# save_json(self.chains_list, 'chains_new_rpcs.json')
			save_json(self.chains_list, self.chains_filename)
		return self.chains_list



def main():
	loader = RPCLoader()
	loader.launch_driver()
	loader.fetch_rpc()


if __name__ == '__main__':
	main()

