import pygame
from pygame.locals import *

import time

import platform

if platform.system() == 'Linux':
	import evdev
	from evdev import InputDevice, categorize, ecodes

from threading import Thread

from common.Config import Config
from common.Button import Button
from common.Timer import Timer
from common.TouchScreen import TouchScreen
from common.Log import Log

CONFIG_FILENAME = 'assets/config/config.json'
MAGNIFIER_BUTTON_POSITION = (42, 857)
IDLE_TIME = 300

LOG_FILE_PATH = 'browser.log'

class Leonardo:
	def __init__(self):
		self.touchPos = (0,0)

	def start(self):
		Log.init(LOG_FILE_PATH)
		Log.getLogger().info('START')

		self.idleTimer = Timer(IDLE_TIME, self.onIdle)
		self.blitCursor = True
		self.isMagnifying = False
		self.config = Config(CONFIG_FILENAME)

		pygame.mixer.pre_init(44100, -16, 1, 512)
		pygame.init()
		pygame.mouse.set_visible(False)

		self.screen = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN)
		self.zoomRenderSurface = pygame.Surface(self.config.getMagnifierSize()).convert_alpha()
		self.cursor = pygame.image.load('assets/images/cursor.png').convert_alpha()
		self.magnifier = pygame.image.load('assets/images/magnifier.png').convert_alpha()
		self.magnifierPosition = self.config.getMagnifierInitialPosition()
		self.dragStartPos = None

		self.touchScreen = None
		if self.config.isTouch():
			print("Loading touch screen...")
			self.touchScreen = TouchScreen(self.config.getTouchDevicePartialName(), (self.config.getTouchScreenMaxX(), self.config.getTouchScreenMaxY()))

			if not self.touchScreen.setup():
				self.config.setTouch(False)

		self.totalImagesNum = 21
		self.images = []
		self.zoomImages = []
		for i in range(self.totalImagesNum):
			self.images.append(pygame.image.load('assets/images/' + str(i + 1) + '.png').convert())
			self.zoomImages.append(pygame.image.load('assets/images/' + str(i + 1) + '-big.png').convert())

		self.currIndex = 0
		self.loadImage()

		self.buttons = []

		leftRegular = pygame.image.load('assets/images/left_regular.png')
		self.prevButton = Button(self.screen, pygame.Rect(70, 1080 // 2 - leftRegular.get_height() // 2, leftRegular.get_width(), leftRegular.get_height()), 
			leftRegular, pygame.image.load('assets/images/left_selected.png'), 
			None, None, None, None, self.onPrevClick, 2.0)
		self.buttons.append(self.prevButton)

		rightRegular = pygame.image.load('assets/images/right_regular.png')
		self.nextButton = Button(self.screen, pygame.Rect(1760, 1080 // 2 - rightRegular.get_height() // 2, rightRegular.get_width(), rightRegular.get_height()), 
			rightRegular, pygame.image.load('assets/images/right_selected.png'), 
			None, None, None, None, self.onNextClick, 2.0)
		self.buttons.append(self.nextButton)

		self.magnifierOff = pygame.image.load('assets/images/magnifier_off.png')
		self.magnifierOn = pygame.image.load('assets/images/magnifier_on.png')
		self.magnifierButton = self.magnifierOff

		Log.getLogger().info('INIT')

		self.loop()

	def onIdle(self):
		Log.getLogger().info('IDLE')
		self.magnifierPosition = self.config.getMagnifierInitialPosition()
		self.isMagnifying = False
		self.updateMagnifierButton()
		self.currIndex = 0
		self.loadImage()

	def loadImage(self):
		self.currImage = self.images[self.currIndex]
		self.currZoomImage = self.zoomImages[self.currIndex]
		self.zoomFactor = self.currZoomImage.get_width() / self.currImage.get_width()

	def onNextClick(self):
		self.idleTimer = Timer(IDLE_TIME, self.onIdle)
		self.currIndex = (self.currIndex + 1) % self.totalImagesNum
		self.loadImage()
		Log.getLogger().info('NEXT,' + str(self.currIndex + 1))

	def onPrevClick(self):
		self.idleTimer = Timer(IDLE_TIME, self.onIdle)
		self.currIndex = (self.currIndex - 1) % self.totalImagesNum
		self.loadImage()
		Log.getLogger().info('PREV,' + str(self.currIndex + 1))

	def toggleMagnifier(self):
		self.idleTimer = Timer(IDLE_TIME, self.onIdle)
		self.isMagnifying = not self.isMagnifying
		Log.getLogger().info('MAGNIFIER_ON' if self.isMagnifying else 'MAGNIFIER_OFF')
		self.updateMagnifierButton()
	
	def updateMagnifierButton(self):
		self.magnifierButton = self.magnifierOn if self.isMagnifying else self.magnifierOff

	def onMouseDown(self, pos):
		for button in self.buttons:
			button.onMouseDown(pos)

		if Rect(MAGNIFIER_BUTTON_POSITION[0] - self.magnifierButton.get_width() // 4, MAGNIFIER_BUTTON_POSITION[1] - self.magnifierButton.get_height() // 4, self.magnifierButton.get_width() * 1.5, self.magnifierButton.get_height() * 1.5).collidepoint(pos):
			self.toggleMagnifier()

		if Rect(self.magnifierPosition[0], self.magnifierPosition[1], self.magnifier.get_width(), self.magnifier.get_height()).collidepoint(pos):
			self.idleTimer = Timer(IDLE_TIME, self.onIdle)
			self.dragStartPos = pos
			self.magnifierStartPos = self.magnifierPosition
			Log.getLogger().info('MAGNIFIER_MOVE_START,' + str(pos[0]) + ',' + str(pos[1]))

	def onMouseUp(self, pos):
		for button in self.buttons:
			button.onMouseUp(pos)

		if self.dragStartPos is not None:
			Log.getLogger().info('MAGNIFIER_MOVE_END,' + str(pos[0]) + ',' + str(pos[1]))
		self.dragStartPos = None

	def onMouseMove(self, pos):
		if self.dragStartPos is not None:
			self.idleTimer = Timer(IDLE_TIME, self.onIdle)

			newMagnifierPositionX = pos[0] - self.dragStartPos[0] + self.magnifierStartPos[0]
			newMagnifierPositionY = pos[1] - self.dragStartPos[1] + self.magnifierStartPos[1]

			magnifierCenterPos = self.config.getMagnifierImageCenterPos()

			if newMagnifierPositionX + magnifierCenterPos[0] > self.screen.get_width():
				newMagnifierPositionX = self.screen.get_width() - magnifierCenterPos[0]
			if newMagnifierPositionX + magnifierCenterPos[0] < 0:
				newMagnifierPositionX = -magnifierCenterPos[0]

			if newMagnifierPositionY + magnifierCenterPos[1] > self.screen.get_height():
				newMagnifierPositionY = self.screen.get_height() - magnifierCenterPos[1]
			if newMagnifierPositionY + magnifierCenterPos[1] < 0:
				newMagnifierPositionY = -magnifierCenterPos[1]

			self.magnifierPosition = (newMagnifierPositionX, newMagnifierPositionY)

	def draw(self, dt):
		self.screen.blit(self.currImage, (0, 0))

		if self.isMagnifying:
			magnifierCenterPos = self.config.getMagnifierImageCenterPos()
			magnifierMidPos = (self.magnifierPosition[0] + magnifierCenterPos[0], self.magnifierPosition[1] + magnifierCenterPos[1])
			midZoomPos = (magnifierMidPos[0] * self.zoomFactor, magnifierMidPos[1] * self.zoomFactor)
			magnifierSize = self.config.getMagnifierSize()

			self.zoomRenderSurface.blit(self.currZoomImage, 
				(0, 0),
				Rect(midZoomPos[0] - magnifierSize[0] // 2, midZoomPos[1] - magnifierSize[1] // 2, magnifierSize[0], magnifierSize[1]))

			transparent = pygame.Color(0,0,0,0)
			for i in range(125):
				for j in range(125 - i):
					self.zoomRenderSurface.set_at((i,j), transparent)
					self.zoomRenderSurface.set_at((magnifierSize[0] - i,j), transparent)
					self.zoomRenderSurface.set_at((i,magnifierSize[1] - j), transparent)
					self.zoomRenderSurface.set_at((magnifierSize[0] - i,magnifierSize[1] - j), transparent)

			self.screen.blit(self.zoomRenderSurface, 
				(self.magnifierPosition[0] + magnifierCenterPos[0] - magnifierSize[0] // 2, self.magnifierPosition[1] + magnifierCenterPos[1] - magnifierSize[1] // 2))

			self.screen.blit(self.magnifier, self.magnifierPosition)

		for button in self.buttons:
			button.draw()

		self.screen.blit(self.magnifierButton, MAGNIFIER_BUTTON_POSITION)

	def loop(self):
		isGameRunning = True
		clock = pygame.time.Clock()
		lastTime = pygame.time.get_ticks()
		font = pygame.font.Font(None, 30)

		while isGameRunning:
			for event in pygame.event.get():
				if event.type == MOUSEBUTTONDOWN:
					if not self.config.isTouch():
						self.onMouseDown(event.pos)
				elif event.type == MOUSEBUTTONUP:
					if not self.config.isTouch():
						self.onMouseUp(event.pos)
				elif event.type == KEYDOWN:
					if event.key == K_ESCAPE:
						isGameRunning = False

			if self.config.isTouch():
				event = self.touchScreen.readUpDownEvent()
				while event is not None:
					if event['type'] == TouchScreen.DOWN_EVENT:
						self.onMouseDown(event['pos'])
					elif event['type'] == TouchScreen.UP_EVENT:
						self.onMouseUp(event['pos'])
					event = self.touchScreen.readUpDownEvent()

			if not self.config.isTouch():
				self.onMouseMove(pygame.mouse.get_pos())
			else:
				pos = self.touchScreen.getPosition()
				self.onMouseMove(pos)

			self.screen.fill([0,0,0])
			currTime = pygame.time.get_ticks()
			dt = currTime - lastTime
			lastTime = currTime

			self.draw(dt / 1000)
			self.idleTimer.tick(dt / 1000)

			if not self.config.isTouch() and self.blitCursor:
				self.screen.blit(self.cursor, (pygame.mouse.get_pos()))

			if self.config.showFPS():
				fps = font.render(str(int(clock.get_fps())), True, Color('white'))
				self.screen.blit(fps, (50, 50))

			pygame.display.flip()
			clock.tick(60)

		pygame.quit()

if __name__ == '__main__':
	Leonardo().start()
