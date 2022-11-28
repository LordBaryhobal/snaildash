import pygame
import random

pygame.init()
S = pygame.Surface([64,64], pygame.SRCALPHA)

for i in range(16):
	S.fill((0,0,0,0))
	for j in range(random.randint(4,7)):
		x, y = random.randint(16,48), random.randint(16,48)
		r = random.randint(6,16)
		pygame.draw.circle(S, (160,160,160), [x,y], r)
	
	for j in range(random.randint(6,12)):
		x, y = random.randint(12,52), random.randint(12,52)
		r = random.randint(3,8)
		pygame.draw.circle(S, (0,0,0,0), [x,y], r)
	
	pygame.image.save(S, f"drool_poison/{i}.png")