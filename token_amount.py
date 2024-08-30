class TokenAmount:
	Wei: int
	Ether: float # amount of token itself (not always eth)
	decimals: int

	def __init__(self, amount, decimals:int = 18, wei:bool = False):
		if wei:
			self.Wei = int(amount)
			self.Ether = float(amount) / (10 ** decimals)

		else:
			self.Ether = float(amount)
			self.Wei = int(self.Ether * (10 ** decimals))

		self.decimals = decimals

	def __str__(self):
		return "Wei: " + str(self.Wei) + " Ether: " + str(self.Ether)

	def set_amount(self, amount, wei:bool = False):
		if wei:
			self.Wei = int(amount)
			self.Ether = float(amount) / (10 ** decimals)

		else:
			self.Ether = float(amount)
			self.Wei = int(self.Ether * (10 ** decimals))
