import pygame
from pygame.locals import *

import time

from common.Config import Config
from common.Button import Button

CONFIG_FILENAME = 'assets/config/config.json'

from ft5406 import Touchscreen, TS_PRESS, TS_RELEASE, TS_MOVE

class Leonardo:
	def __init__(self):
		pass

	def start(self):
		self.blitCursor = True
		self.config = Config(CONFIG_FILENAME)

		self.touchScreenBounds = (self.config.getTouchScreenMaxX(), self.config.getTouchScreenMaxY())

		pygame.mixer.pre_init(44100, -16, 1, 512)
		pygame.init()
		pygame.mouse.set_visible(False)

		self.screen = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN)
		self.cursor = pygame.image.load('assets/images/cursor.png').convert_alpha()
		self.magnifier = pygame.image.load('assets/images/magnifier.png').convert_alpha()
		self.magnifierPosition = (0,0)
		self.dragStartPos = None

		if self.config.isTouch():
			print("Loading touch screen...")
			self.ts = Touchscreen(self.config.getTouchDevice())

			for touch in self.ts.touches:
			    touch.on_press = self.onMouseDown
			    touch.on_release = self.onMouseUp
			    touch.on_move = self.onMouseMove

			self.ts.run()

		self.totalImagesNum = 21
		self.currIndex = 0
		self.loadImage()

		self.buttons = []

		self.prevButton = Button(self.screen, pygame.Rect(70, 1080 // 2 - 102 // 2, 56, 102), 
			pygame.image.load('assets/images/left_regular.png'), pygame.image.load('assets/images/left_selected.png'), 
			None, None, None, None, self.onPrevClick)
		self.buttons.append(self.prevButton)

		self.nextButton = Button(self.screen, pygame.Rect(1800, 1080 // 2 - 102 // 2, 56, 102), 
			pygame.image.load('assets/images/right_regular.png'), pygame.image.load('assets/images/right_selected.png'), 
			None, None, None, None, self.onNextClick)
		self.buttons.append(self.nextButton)

		self.loop()

	def loadImage(self):
		self.currImage = pygame.image.load('assets/images/' + str(self.currIndex + 1) + '.png')
		self.currZoomImage = pygame.image.load('assets/images/' + str(self.currIndex + 1) + '-big.png')

	def onNextClick(self):
		self.currIndex = (self.currIndex + 1) % self.totalImagesNum
		self.loadImage()

	def onPrevClick(self):
		self.currIndex = (self.currIndex - 1) % self.totalImagesNum
		self.loadImage()

	def onMouseDown(self, pos):
		for button in self.buttons:
			button.onMouseDown(pos)

		if Rect(self.magnifierPosition[0], self.magnifierPosition[1], self.magnifier.get_width(), self.magnifier.get_height()).collidepoint(pos):
			self.dragStartPos = pos
			self.magnifierStartPos = self.magnifierPosition

	def onMouseUp(self, pos):
		for button in self.buttons:
			button.onMouseUp(pos)

		self.dragStartPos = None

	def onMouseMove(self, pos):
		if self.dragStartPos is not None:
			self.magnifierPosition = (pos[0] - self.dragStartPos[0] + self.magnifierStartPos[0], pos[1] - self.dragStartPos[1] + self.magnifierStartPos[1])

	def draw(self, dt):
		self.screen.blit(self.currImage, (0, 0))

		factor = 2.0
		magnifierMidPos = (self.magnifierPosition[0] + 210, self.magnifierPosition[1] + 210)
		midZoomPos = (magnifierMidPos[0] * factor, magnifierMidPos[1] * factor)
		self.screen.blit(self.currZoomImage, self.magnifierPosition, Rect(midZoomPos[0] - 210, midZoomPos[1] - 210, 420, 420))

		self.screen.blit(self.magnifier, self.magnifierPosition)

		for button in self.buttons:
			button.draw()

	def loop(self):
		isGameRunning = True
		clock = pygame.time.Clock()
		lastTime = pygame.time.get_ticks()

		while isGameRunning:
			for event in pygame.event.get():
				if event.type == MOUSEBUTTONDOWN:
					if not self.config.isTouch():
						self.onMouseDown(event.pos)
				elif event.type == MOUSEBUTTONUP:
					if not self.config.isTouch():
						self.onMouseUp(event.pos)
				elif event.type == MOUSEMOTION:
					if not self.config.isTouch():
						self.onMouseMove(event.pos)
				elif event.type == KEYDOWN:
					if event.key == K_ESCAPE:
						isGameRunning = False

			self.screen.fill([0,0,0])
			currTime = pygame.time.get_ticks()
			dt = currTime - lastTime
			lastTime = currTime

			self.draw(dt / 1000)

			if not self.config.isTouch() and self.blitCursor:
				self.screen.blit(self.cursor, (pygame.mouse.get_pos()))

			pygame.display.flip()
			clock.tick(60)

		pygame.quit()

		if self.config.isTouch():
			self.ts.stop()

if __name__ == '__main__':
	Leonardo().start()
