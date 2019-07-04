import json

class Config:

	def __init__(self, filename):
		with open(filename) as file:
			self.config = json.load(file)

	def isTouch(self):
		return self.config['touch']

	def getTouchDevice(self):
		return self.config['touchDevice']

	def getTouchScreenMaxX(self):
		return self.config['touchMaxX']

	def getTouchScreenMaxY(self):
		return self.config['touchMaxY']

	def getMagnifierImageCenterPos(self):
		return (self.config['magnifierImageCenterX'], self.config['magnifierImageCenterY'])

	def getMagnifierSize(self):
		return (self.config['magnifierWidth'], self.config['magnifierHeight'])
