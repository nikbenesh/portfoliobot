class Logger:
	def __init__(self, filename, mode='w'):
		self.file = open(filename, mode)

	def log(self, msg):
		self.file.write(msg)
