from selenium import webdriver # if without proxy
from seleniumwire import webdriver as proxy_webdriver # for proxy
from fake_useragent import UserAgent
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import json
from lxml import etree
from lxml.etree import fromstring # using this 
from lxml import html
import requests


class MDriver:
	def __init__(self, driver, wait_for = 130, cookies_path='cookies.json'):
		self.driver = driver
		self.wait = WebDriverWait(self.driver, wait_for)
		self.cookies_path = cookies_path

	def check_if_element_exists(self, xpath): # 
		document = html.fromstring(self.driver.page_source)
		el = document.xpath(xpath)
		if el:
			return True
		return False

	def find_by_xpath(self, xpath, wait_it=False, wait_clickable=False, wait_for_text=None):
		if wait_it:
			print('DEBUG: waiting for element', xpath)
			self.wait_until_presence(xpath)
		if wait_clickable:
			self.wiit_until_clickable(xpath)
		if wait_for_text:
			print('DEBUG: waiting for element', xpath, 'and text', wait_for_text)
			self.wait_for_text(xpath, wait_for_text)
		return self.driver.find_element(by=By.XPATH, value=(xpath))

	def click_el(self, xpath, wait_it=False, wait_for_text=None):
		self.find_by_xpath(xpath, wait_it=wait_it, wait_clickable=True, wait_for_text=wait_for_text).click()


	def send_keys(self, xpath, keys):
		self.find_by_xpath(xpath).send_keys(keys)

	def find_element_by_text(self, text):
		return self.find_by_xpath(f'//*[text()="{text}"]')

	def scroll_down(self, y=10, full_height=False):
		if full_height:
			self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
		else:
			self.driver.execute_script(f"window.scrollTo(0, {y});")

	def wait_until_presence(self, xpath):
		self.wait.until(EC.presence_of_element_located((By.XPATH, xpath)))

	def wiit_until_clickable(self, xpath):
		self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))

	def wait_for_text(self, xpath, text):
		self.wait.until(EC.text_to_be_present_in_element((By.XPATH, xpath), text))

	def load_cookies(self):
		with open(self.cookies_path, 'r') as cookies_file:
			for cookie in json.load(cookies_file):
				# if cookie['sameSite'] == 'None':
				# 	cookie['sameSite'] = 'Strict'
				self.driver.add_cookie(cookie)

	def save_cookies(self):
		with open(self.cookies_path, 'w') as cookies_file:
			json.dump(self.driver.get_cookies(), cookies_file)

	def login_discord(self, token, switch_back_to=None):
		self.driver.get("discord.com/login")
		with open('discord_login.js', 'r') as disc_file:
			js_code = disc_file.read().replace('PASTE TOKEN HERE', token)
		self.driver.execute_script(js_code)
		if switch_back_to:
			self.driver.switch_to.window(switch_back_to)


