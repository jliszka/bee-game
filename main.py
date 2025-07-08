import pygame, sys
import pygame.gfxdraw
from pygame.locals import *
import math

FPS = 60

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW_BG = (255, 255, 200)
YELLOW_CELL1 = (230, 230, 150)
YELLOW_CELL2 = (240, 240, 180)
YELLOW_BEE1 = (255, 255, 100)
YELLOW_BEE2 = (200, 200, 0)

NURSE_BEE_COLOR = (210, 200, 255)
BUILDER_BEE_COLOR = (255, 200, 100)
CLEANER_BEE_COLOR = (120, 180, 255)
FOOD_MAKER_BEE_COLOR = (100, 200, 150)

SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900
CELL_SIZE = 40
BEE_SIZE = 30
BEE_SPEED = 4

SQRT3 = math.sqrt(3)

def hexagon(center, size):
    return [
            (center[0], center[1] + 2 * size),
            (center[0] - SQRT3 * size, center[1] + size),
            (center[0] - SQRT3 * size, center[1] - size),
            (center[0], center[1] - 2 * size),
            (center[0] + SQRT3 * size, center[1] - size),
            (center[0] + SQRT3 * size, center[1] + size),
        ]

def distance(a, b):
    return math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2)

class Task(object):
    pass

class TravelTo(Task):
    def __init__(self, bee, dest):
        super().__init__()
        self.bee = bee
        self.dest = dest
        dist = distance(bee.center, dest)
        self.dx = (dest[0] - bee.center[0]) / dist * BEE_SPEED
        self.dy = (dest[1] - bee.center[1]) / dist * BEE_SPEED
    
    def update(self):
        self.bee.center = (self.bee.center[0] + self.dx, self.bee.center[1] + self.dy)
    
    def is_done(self):
        return distance(self.bee.center, self.dest) < 2


class Cell(pygame.sprite.Sprite):
    def __init__(self, row, col):
        super().__init__()
        y = SCREEN_HEIGHT / 2 + row * CELL_SIZE * 3 
        x = SCREEN_WIDTH / 2 + (col * 2 + row % 2) * CELL_SIZE * SQRT3
        self.rect = pygame.Rect(0, 0, CELL_SIZE * SQRT3 * 2, 2)
        self.rect.center = (x, y)
 
    def update(self):
        pass
 
    def draw(self, surface):
        points = hexagon(self.rect.center, CELL_SIZE)
        pygame.draw.polygon(surface, YELLOW_CELL1, points)
        inner_points = hexagon(self.rect.center, CELL_SIZE-5)
        pygame.draw.polygon(surface, YELLOW_CELL2, inner_points, width=10)
        pygame.draw.aalines(surface, BLACK, closed=True, points=points)


class Bee(pygame.sprite.Sprite):
    def __init__(self, x, y, job):
        super().__init__() 
        self.center = (x, y)
        self.job = job
        self.tasks = []

    def update(self):
        if len(self.tasks) == 0:
            return
        if self.tasks[0].is_done():
            self.tasks = self.tasks[1:]
        else:
            self.tasks[0].update()

    def add_task(self, task):
        self.tasks.append(task)
    
    def add_tasks(self, tasks):
        for task in tasks:
            self.tasks.append(task)
    
    def draw(self, surface):
        pygame.draw.circle(surface, YELLOW_BEE1, self.center, BEE_SIZE)
        bee_color = YELLOW_BEE1
        if self.job == "nurse":            
            bee_color = NURSE_BEE_COLOR
        elif self.job == "builder":
            bee_color = BUILDER_BEE_COLOR
        elif self.job == "cleaner":
            bee_color = CLEANER_BEE_COLOR
        elif self.job == "food maker":
            bee_color = FOOD_MAKER_BEE_COLOR
        pygame.draw.circle(surface, bee_color, self.center, BEE_SIZE / 2)
        pygame.gfxdraw.aacircle(surface, int(self.center[0]), int(self.center[1]), BEE_SIZE, BLACK)


def main():
    pygame.init()
    FramePerSec = pygame.time.Clock()
    pygame.display.set_caption("Bee Game")

    surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    cells = [Cell(0, 0), Cell(1, -1), Cell(1, 0)]
    bees = [Bee(100, 100, "nurse"), Bee(200, 100, "builder"), Bee(300, 100, "cleaner"), Bee(400, 100, "food maker")]
    bees[0].add_task(TravelTo(bees[0], cells[0].rect.center))

    while True:
        # Events
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
    
        # Update
        for b in bees:
            b.update()

        # Draw
        surface.fill(YELLOW_BG)
        for c in cells:
            c.draw(surface)
        for b in bees:
            b.draw(surface)
        
        pygame.display.update()
        FramePerSec.tick(FPS)

if __name__ == "__main__":
    main()
