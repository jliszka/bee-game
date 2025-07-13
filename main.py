import pygame, sys
import pygame.gfxdraw
from pygame.locals import *
import random
import math
from collections import defaultdict
import itertools

FPS = 60

BLACK = (0, 0, 0)
GRAY = (127, 127, 127)
LIGHT_GRAY = (230, 230, 230)
WHITE = (255, 255, 255)
YELLOW_BG = (255, 255, 200)
YELLOW_CELL1 = (230, 230, 150)
YELLOW_CELL2 = (240, 240, 180)
YELLOW_CELL3 = (240, 240, 100)
YELLOW_BEE1 = (255, 255, 100)
YELLOW_BEE2 = (200, 200, 0)

NURSE_BEE_COLOR = (210, 200, 255)
BUILDER_BEE_COLOR = (255, 200, 100)
CLEANER_BEE_COLOR = (120, 180, 255)
FOOD_MAKER_BEE_COLOR = (100, 200, 150)

pygame.init()

display_info = pygame.display.Info()
SCREEN_WIDTH = display_info.current_w
SCREEN_HEIGHT = display_info.current_h
CELL_SIZE = SCREEN_WIDTH / 40
BEE_SIZE = SCREEN_HEIGHT / 30
BEE_SPEED = 4
QB_SPEED = 4

SQRT3 = math.sqrt(3)

font = pygame.font.SysFont("Verdana", 60)
font_medium = pygame.font.SysFont("Verdana", 30)
font_small = pygame.font.SysFont("Verdana", 20)
font_tiny = pygame.font.SysFont("Verdana", 14)
build_text = font.render("+", True, LIGHT_GRAY)

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

def move_point(p, dx, dy):
    return (p[0] + dx, p[1] + dy)

def random_in_rect(rect):
    return (random.randint(rect.left, rect.right), random.randint(rect.top, rect.bottom))

class Task(object):
    def start(self, bee):
        pass
    def update(self):
        pass
    def is_done(self):
        pass

class TravelTo(Task):
    def __init__(self, dest):
        super().__init__()
        self.dest = dest
    
    def start(self, bee):
        self.bee = bee
        dist = distance(bee.center, self.dest)
        self.dx = (self.dest[0] - bee.center[0]) / dist * BEE_SPEED
        self.dy = (self.dest[1] - bee.center[1]) / dist * BEE_SPEED

    def update(self):
        self.bee.center = move_point(self.bee.center, self.dx, self.dy)
    
    def is_done(self):
        return distance(self.bee.center, self.dest) < 10

class Build(Task):
    def __init__(self, cell):
        super().__init__()
        self.cell = cell
    def start(self, bee):
        self.cell.state = "building"
        self.time_remaining = FPS * 3
    def update(self):
        self.time_remaining -= 1
        if self.time_remaining == 0:
            self.cell.state = "ready"
            self.cell.type = "built"
            hive.enable_cells()

    def is_done(self):
        return self.time_remaining == 0

class Nurse(Task):
    def __init__(self, cell):
        super().__init__()
        self.cell = cell
        self.total_time = FPS * 5
        self.elapsed_time = 0
    def start(self, bee):
        self.cell.state = "nursing"
        self.cell.progress = 0
    def update(self):
        self.elapsed_time += 1
        self.cell.progress = self.elapsed_time / self.total_time
        if self.elapsed_time == self.total_time:
            self.cell.state = "cleaner requested"
            hive.request_cleaner(self.cell)
            self.cell.progress = 0
            new_bee = Bee(self.cell.rect.center[0], self.cell.rect.center[1], "unassigned")
            new_bee.add_tasks([
                TravelTo(random_in_rect(job_rect)),
                GetJob(),
            ])
            hive.add_bee(new_bee)
    def is_done(self):
        return self.elapsed_time == self.total_time

class Clean(Task):
    def __init__(self, cell):
        super().__init__()
        self.cell = cell
        self.total_time = FPS * 4
        self.elapsed_time = 0
    def start(self, bee):
        self.cell.state = "cleaning"
        self.cell.progress = 0
    def update(self):
        self.elapsed_time += 1
        if self.elapsed_time == self.total_time:
            self.cell.state = self.cell.type
    def is_done(self):
        return self.elapsed_time == self.total_time

class MakeFood(Task):
    def __init__(self, cell):
        super().__init__()
        self.cell = cell
        self.total_time = FPS * 5
        self.elapsed_time = 0
    def start(self, bee):
        self.cell.state = "making food"
        self.cell.progress = 0
    def update(self):
        self.elapsed_time += 1
        self.cell.progress = self.elapsed_time / self.total_time
        if self.elapsed_time == self.total_time:
            if self.cell.type == "honey":
                hive.honey = min(100, hive.honey + 4)
            elif self.cell.type == "bee bread":
                hive.bee_bread = min(20, hive.bee_bread + 1)
            self.cell.state = "cleaner requested"
            hive.request_cleaner(self.cell)
            self.cell.progress = 0
    def is_done(self):
        return self.elapsed_time == self.total_time

class Die(Task):
    def __init__(self):
        super().__init__()
        self.total_time = FPS * 2
        self.elapsed_time = 0
    def start(self, bee):
        self.bee = bee
        bee.job = "dying"
    def update(self):
        self.elapsed_time += 1
        if self.elapsed_time == self.total_time:
            hive.remove_bee(self.bee)
    def is_done(self):
        return self.elapsed_time == self.total_time


class GetJob(Task):
    def __init__(self):
        super().__init__()
    def start(self, bee):
        hive.bees_needing_jobs.append(bee)
    def update(self):
        pass
    def is_done(self):
        return True


def center_text(surface, rect):
    w = surface.get_width()
    h = surface.get_height()
    return move_point(rect.center, -w/2, -h/2)

def center_text1(surface, rect):
    w = surface.get_width()
    h = surface.get_height()
    return move_point(rect.center, -w/2, -h)

def center_text2(surface, rect):
    w = surface.get_width()
    return move_point(rect.center, -w/2, 0)


class Button(object):
    def __init__(self, parent, text, color, x, y, fn, font = font_tiny):
        self.parent = parent
        self.fn = fn
        self.pos = (x, y)
        self.rendered_text = font.render(text, True, GRAY)
        w = self.rendered_text.get_width() + 16
        h = self.rendered_text.get_height() + 8
        self.button_surface = pygame.Surface((w, h))
        pygame.draw.rect(self.button_surface, color, self.button_surface.get_rect())
        self.button_surface.blit(self.rendered_text, center_text(self.rendered_text, self.button_surface.get_rect()))

    def draw(self, surface):
        surface.blit(self.button_surface, self.get_rect().topleft)

    def get_rect(self):
        rect = self.button_surface.get_rect()
        rect.midtop = move_point(self.parent.rect.midtop, self.pos[0], self.pos[1])
        return rect

    def handle_click(self):
        self.fn()


class Hive(object):
    def __init__(self, bees = [], cells = []):
        pass
        self.honey = 20
        self.bee_bread = 5
        self.bees = bees
        self.cells = cells
        self.cells_needing_builder = []
        self.cells_needing_food_maker = []
        self.cells_needing_nurse = []
        self.cells_needing_cleaner = []
        self.bees_needing_jobs = []
        self.debug = False
        self.paused = False
        self.next_id = 1
        self.cell_dict = defaultdict(lambda: defaultdict(None))
        self.rect = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        for bee in bees:
            self.assign_id(bee)
        for cell in cells:
            self.cell_dict[cell.row][cell.col] = cell

    def get_cell(self, r, c):
        if r in self.cell_dict:
            if c in self.cell_dict[r]:
                return self.cell_dict[r][c]
        return None

    def assign_id(self, bee):
        bee.id = self.next_id
        self.next_id += 1

    def add_bee(self, bee):
        self.assign_id(bee)
        self.bees.append(bee)
        self.bee_bread -= 1

    def remove_bee(self, bee):
        self.bees = [ b for b in self.bees if b.id != bee.id ]

    def is_first_bee_waiting_for_job(self, bee):
        return len(self.bees_needing_jobs) > 0 and bee.id == self.bees_needing_jobs[0].id

    def assign_job(self, job):
        if len(self.bees_needing_jobs) > 0:
            bee = self.bees_needing_jobs[0]
            if (bee.job == "unassigned" and job in ["nurse", "cleaner"]) or (bee.job == "unassigned2" and job in ["food maker", "builder"]):
                bee.job = job
                self.bees_needing_jobs = self.bees_needing_jobs[1:]

    def request_job(self, bee):
        if bee.job == "builder" and len(self.cells_needing_builder) > 0:
            cell = self.cells_needing_builder[0]
            self.cells_needing_builder = self.cells_needing_builder[1:]
            self.assign_builder(cell, bee)
        elif bee.job == "nurse" and len(self.cells_needing_nurse) > 0:
            cell = self.cells_needing_nurse[0]
            self.cells_needing_nurse = self.cells_needing_nurse[1:]
            self.assign_nurse(cell, bee)
        elif bee.job == "food maker" and len(self.cells_needing_food_maker) > 0:
            cell = self.cells_needing_food_maker[0]
            self.cells_needing_food_maker = self.cells_needing_food_maker[1:]
            self.assign_food_maker(cell, bee)
        elif bee.job == "cleaner" and len(self.cells_needing_cleaner) > 0:
            cell = self.cells_needing_cleaner[0]
            self.cells_needing_cleaner = self.cells_needing_cleaner[1:]
            self.assign_cleaner(cell, bee)

    def request_builder(self, cell):
        cell.state = "build requested"
        builder = self.get_bee("builder")
        if builder is not None:
            self.assign_builder(cell, builder)
        else:
            self.cells_needing_builder.append(cell)
    
    def assign_builder(self, cell, bee):
        bee.add_tasks([
            TravelTo(cell.rect.center),
            Build(cell),
        ])

    def request_nurse(self, cell):
        cell.state = "nurse requested"
        nurse = self.get_bee("nurse")
        if nurse is not None:
            self.assign_nurse(cell, nurse)
        else:
            self.cells_needing_nurse.append(cell)
    
    def assign_nurse(self, cell, bee):
        bee.add_tasks([
            TravelTo(cell.rect.center),
            Nurse(cell),
        ])

    def request_food_maker(self, cell):
        cell.state = "food maker requested"
        food_maker = self.get_bee("food maker")
        if food_maker is not None:
            self.assign_food_maker(cell, food_maker)
        else:
            self.cells_needing_food_maker.append(cell)

    def assign_food_maker(self, cell, bee):
        bee.add_tasks([
            TravelTo(cell.rect.center),
            MakeFood(cell),
        ])

    def request_cleaner(self, cell):
        cell.state = "cleaner requested"
        cleaner = self.get_bee("cleaner")
        if cleaner is not None:
            self.assign_cleaner(cell, cleaner)
        else:
            self.cells_needing_cleaner.append(cell)

    def assign_cleaner(self, cell, bee):
        bee.add_tasks([
            TravelTo(cell.rect.center),
            Clean(cell),
        ])

    def get_bee(self, job):
        qualified_bees = [ bee for bee in self.bees if bee.job == job and not bee.is_busy() ]
        if len(qualified_bees) > 0:
            return qualified_bees[0]
        return None

    def enable_cells(self):
        for cell in self.cells:
            if cell.type == "none":
                neighbors = [(-1, -1), (-1, 0), (0, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]
                for (r1, c1), (r2, c2) in itertools.pairwise(neighbors):
                    a1 = 0 if r1 == 0 else cell.row % 2
                    a2 = 0 if r2 == 0 else cell.row % 2
                    n1 = self.get_cell(cell.row + r1, cell.col + c1 + a1)
                    n2 = self.get_cell(cell.row + r2, cell.col + c2 + a2)
                    if n1 is not None and n2 is not None:
                        if n1.type not in ["none", "unbuilt"] and n2.type not in ["none", "unbuilt"]:
                            cell.type = "unbuilt"
                            cell.state = "unbuilt"
                            break

    def draw(self, surface):
        honey_text = font_small.render("Honey: %d/100" % self.honey, True, GRAY)
        bee_bread_text = font_small.render("Bee bread: %d/20" % self.bee_bread, True, GRAY)
        surface.blit(honey_text, (SCREEN_WIDTH - honey_text.get_width() - honey_text.get_height()/2, honey_text.get_height()/2))
        surface.blit(bee_bread_text, (SCREEN_WIDTH - bee_bread_text.get_width() - bee_bread_text.get_height()/2, honey_text.get_height() + bee_bread_text.get_height()))
        
        total_bee_text = font_medium.render("Total bees", True, GRAY)
        surface.blit(total_bee_text, ((SCREEN_WIDTH - total_bee_text.get_width()) / 2, 0))
        bee_count_text = font.render(str(len(self.bees)), True, GRAY)
        surface.blit(bee_count_text, ((SCREEN_WIDTH - bee_count_text.get_width()) / 2, total_bee_text.get_height()))

        nurse_bee_text = font_small.render("Nurse bees", True, GRAY)
        cleaner_bee_text = font_small.render("Cleaner bees", True, GRAY)
        food_maker_bee_text = font_small.render("Food maker bees", True, GRAY)
        builder_bee_text = font_small.render("Builder bees", True, GRAY)
        surface.blit(nurse_bee_text, (SCREEN_WIDTH / 6 - nurse_bee_text.get_width() / 2, 0))
        surface.blit(cleaner_bee_text, (SCREEN_WIDTH * 2 / 6 - cleaner_bee_text.get_width() / 2, 0))
        surface.blit(food_maker_bee_text, (SCREEN_WIDTH * 4 / 6 - food_maker_bee_text.get_width() / 2, 0))
        surface.blit(builder_bee_text, (SCREEN_WIDTH * 5 / 6 - builder_bee_text.get_width() / 2, 0))
        
        nurse_bee_count_text = font_medium.render(str(sum(1 for bee in self.bees if bee.job == "nurse")), True, NURSE_BEE_COLOR)
        cleaner_bee_count_text = font_medium.render(str(sum(1 for bee in self.bees if bee.job == "cleaner")), True, CLEANER_BEE_COLOR)
        food_maker_bee_count_text = font_medium.render(str(sum(1 for bee in self.bees if bee.job == "food maker")), True, FOOD_MAKER_BEE_COLOR)
        builder_bee_count_text = font_medium.render(str(sum(1 for bee in self.bees if bee.job == "builder")), True, BUILDER_BEE_COLOR)
        surface.blit(nurse_bee_count_text, (SCREEN_WIDTH / 6 - nurse_bee_count_text.get_width() / 2, nurse_bee_text.get_height()))
        surface.blit(cleaner_bee_count_text, (SCREEN_WIDTH * 2 / 6 - cleaner_bee_count_text.get_width() / 2, cleaner_bee_text.get_height()))
        surface.blit(food_maker_bee_count_text, (SCREEN_WIDTH * 4 / 6 - food_maker_bee_count_text.get_width() / 2, food_maker_bee_text.get_height()))
        surface.blit(builder_bee_count_text, (SCREEN_WIDTH * 5 / 6 - builder_bee_count_text.get_width() / 2, builder_bee_text.get_height()))

class Cell(pygame.sprite.Sprite):
    def __init__(self, row, col, typ = "none"):
        super().__init__()
        self.row = row
        self.col = col
        y = SCREEN_HEIGHT / 2 + row * CELL_SIZE * 3 
        x = SCREEN_WIDTH / 2 + (col * 2 + row % 2) * CELL_SIZE * SQRT3
        self.rect = pygame.Rect(0, 0, CELL_SIZE * SQRT3 * 2, CELL_SIZE * 2)
        self.rect.center = (x, y)
        self.type = typ
        self.state = typ
        self.progress = 0
        self.buttons = [
            Button(self, "Nursery", NURSE_BEE_COLOR, 0, 0, self.make_nursery),
            Button(self, "Bee bread", FOOD_MAKER_BEE_COLOR, 0, 30, self.request_bee_bread),
            Button(self, "Honey", BUILDER_BEE_COLOR, 0, 60, self.request_honey),
        ]
 
    def update(self):
        if self.type == "bee bread" and self.state == "bee bread":
            hive.request_food_maker(self)
        if self.type == "honey" and self.state == "honey":
            hive.request_food_maker(self)

    def make_nursery(self):
        self.type = "nursery"
        self.state = "nursery"
 
    def request_honey(self):
        self.type = "honey"
        hive.request_food_maker(self)

    def request_bee_bread(self):
        self.type = "bee bread"
        hive.request_food_maker(self)

    def draw(self, surface):
        if hive.debug:
            rc_text = font_small.render("%d, %d" % (self.row, self.col), True, GRAY)
            surface.blit(rc_text, self.rect.center)
        if self.type == "none":
            return
        if self.type == "unbuilt":
            if self.state == "building":
                border_color = YELLOW_CELL2
                bg_color = YELLOW_CELL1
            elif self.state == "build requested":
                border_color = YELLOW_CELL1
                bg_color = YELLOW_CELL2
            else:
                border_color = YELLOW_BG
                bg_color = YELLOW_BG
        elif self.type == "nursery":
            border_color = NURSE_BEE_COLOR
            bg_color = YELLOW_CELL3
        elif self.type == "bee bread":
            border_color = FOOD_MAKER_BEE_COLOR
            bg_color = YELLOW_CELL3
        elif self.type == "honey":
            border_color = BUILDER_BEE_COLOR
            bg_color = YELLOW_CELL3
        else:
            border_color = BUILDER_BEE_COLOR
            bg_color = YELLOW_CELL1
        if self.state == "cleaner requested" or self.state == "cleaning":
            bg_color = LIGHT_GRAY

        points = hexagon(self.rect.center, CELL_SIZE)
        pygame.draw.polygon(surface, bg_color, points)
        inner_points = hexagon(self.rect.center, CELL_SIZE-2)
        pygame.draw.polygon(surface, border_color, inner_points, width=7)
        pygame.draw.aalines(surface, BLACK, closed=True, points=points)
        if self.type == "unbuilt":
            if self.state == "unbuilt" and self.rect.collidepoint(pygame.mouse.get_pos()):
                surface.blit(build_text, center_text(build_text, self.rect))
        elif self.state == "ready" and self.rect.collidepoint(pygame.mouse.get_pos()):
            for button in self.buttons:
                button.draw(surface)
        if self.state in ["nursery with egg", "nurse requested", "nursing"]:
            pygame.draw.circle(surface, WHITE, move_point(self.rect.center, 0, CELL_SIZE), CELL_SIZE / 4 * (1 + self.progress))
        if self.type == "bee bread" and self.state == "making food":
            size = CELL_SIZE / 4 * (1 + self.progress)
            rect = pygame.Rect(0, 0, size, size)
            rect.center = move_point(self.rect.center, 0, CELL_SIZE)
            pygame.draw.rect(surface, FOOD_MAKER_BEE_COLOR, rect)
        elif self.type == "honey" and self.state == "making food":
            size = CELL_SIZE / 8 * (1 + self.progress)
            hex = hexagon(move_point(self.rect.center, 0, CELL_SIZE), size)
            pygame.draw.polygon(surface, BUILDER_BEE_COLOR, hex)
        if hive.debug:
            pygame.draw.rect(surface, BLACK, self.rect, 1)

    def handle_click(self):
        if self.state == "unbuilt":
            hive.request_builder(self)
        elif self.state == "ready":
            for button in self.buttons:
                if button.get_rect().collidepoint(pygame.mouse.get_pos()):
                    button.handle_click()


class Bee(pygame.sprite.Sprite):
    def __init__(self, x, y, job):
        super().__init__()
        self.rect = pygame.Rect(0, 0, BEE_SIZE, BEE_SIZE)
        self.center = (x, y)
        self.job = job
        self.tasks = []
        self.task = None
        self.is_idle = True
        self.buttons = {
            "unassigned": [
                Button(self, "(N)urse", NURSE_BEE_COLOR, 0, 20, self.make_nurse),
                Button(self, "(C)leaner", CLEANER_BEE_COLOR, 0, 50, self.make_cleaner),
            ],
            "unassigned2": [
                Button(self, "(F)ood Maker", FOOD_MAKER_BEE_COLOR, 0, 20, self.make_food_maker),
                Button(self, "(B)uilder", YELLOW_BEE1, 0, 50, self.make_builder),
            ]
        }
        self.time_since_last_meal = 0
        self.meals = 0

    def make_nurse(self):
        self.job = "nurse"
    
    def make_cleaner(self):
        self.job = "cleaner"

    def make_food_maker(self):
        self.job = "food_maker"

    def make_builder(self):
        self.job = "builder"

    def update(self):
        self.time_since_last_meal += 1
        if self.time_since_last_meal > 20 * FPS:
            hive.honey -= 1
            self.meals += 1
            self.time_since_last_meal = 0

        if self.task is None or self.task.is_done():
            if self.meals == 3 and self.job in ["nurse", "cleaner"]:
                self.job = "unassigned2"
                self.add_tasks([
                    TravelTo(random_in_rect(job_rect)),
                    GetJob(),
                ])
            elif self.meals == 6:
                self.add_tasks([
                    TravelTo(random_in_rect(die_rect)),
                    Die(),
                ])

            if len(self.tasks) == 0:
                if self.job in ["unassigned", "unassigned2"]:
                    self.task = None
                    self.is_idle = True
                else:
                    hive.request_job(self)
                    if len(self.tasks) == 0:
                        self.task = TravelTo(random_in_rect(idle_rect))
                        self.task.start(self)
                        self.is_idle = True
            else:
                self.task = self.tasks[0]
                self.tasks = self.tasks[1:]
                self.task.start(self)
        else:
            self.task.update()

    def add_task(self, task):
        self.is_idle = False
        self.tasks.append(task)
    
    def add_tasks(self, tasks):
        self.is_idle = False
        for task in tasks:
            self.tasks.append(task)
    
    def is_busy(self):
        return not self.is_idle
    
    def handle_click(self):
        if self.job in ["unassigned", "unassigned2"]:
            for button in self.buttons:
                if button.get_rect().collidepoint(pygame.mouse.get_pos()):
                    button.handle_click()

    def draw(self, surface):
        size = BEE_SIZE
        bee_color = GRAY
        if self.job == "nurse":            
            bee_color = NURSE_BEE_COLOR
        elif self.job == "builder":
            bee_color = BUILDER_BEE_COLOR
            size *= 1.2
        elif self.job == "cleaner":
            bee_color = CLEANER_BEE_COLOR
        elif self.job == "food maker":
            bee_color = FOOD_MAKER_BEE_COLOR
            size *= 1.2
        elif self.job == "unassigned2":
            size *= 1.2
        elif self.job == "dying":
            size *= 1.2
            bee_color = LIGHT_GRAY

        pygame.draw.circle(surface, YELLOW_BEE1, self.center, size)
        pygame.draw.circle(surface, bee_color, self.center, size / 2)
        pygame.gfxdraw.aacircle(surface, int(self.center[0]), int(self.center[1]), int(size), BLACK)
        if hive.debug:
            id_text = font_small.render(str(self.id), True, BLACK)
            surface.blit(id_text, self.center)
        if self.job in ["unassigned", "unassigned2"]:
            self.rect = pygame.Rect(0, 0, BEE_SIZE * 2, BEE_SIZE * 4)
            self.rect.midbottom = self.center
            if hive.is_first_bee_waiting_for_job(self):
                for button in self.buttons[self.job]:
                    button.draw(surface)


class QueenBee(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.center = (x, y)

    def update(self):
        pressed_keys = pygame.key.get_pressed()
        if pressed_keys[K_UP] and self.center[1] > 0:
            self.center = move_point(self.center, 0, -QB_SPEED)
        if pressed_keys[K_DOWN] and self.center[1] < SCREEN_HEIGHT:
            self.center = move_point(self.center, 0, QB_SPEED)
        if pressed_keys[K_LEFT] and self.center[0] > 0:
            self.center = move_point(self.center, -QB_SPEED, 0)
        if pressed_keys[K_RIGHT] and self.center[0] < SCREEN_WIDTH:
            self.center = move_point(self.center, QB_SPEED, 0)
        if pressed_keys[K_RETURN]:
            for cell in hive.cells:
                if cell.state == "nursery" and cell.rect.collidepoint(self.center):
                    cell.state = "nursery with egg"
                    hive.request_nurse(cell)
                    break
    
    def draw(self, surface):
        size = BEE_SIZE * 1.5
        pygame.draw.circle(surface, YELLOW_BEE1, self.center, size)
        pygame.draw.circle(surface, BLACK, self.center, size / 2)
        pygame.gfxdraw.aacircle(surface, int(self.center[0]), int(self.center[1]), int(size), BLACK)


hive = None
def init():
    global hive
    cells = []
    row_indexes = {
        -3: range (-2, 3),
        -2: range(-3, 5),
        -1: range(-4, 5),
        0: range(-3, 6),
        1: range(-3, 5),
        2: range(-2, 4),
        3: range(-2, 3),
    }
    for r, cell_range in row_indexes.items():
        for c in cell_range:
            typ = "unbuilt" if (r == 0 and c == 0) or (r == 1 and c in [-1, 0]) else "none"
            cells.append(Cell(r, c, typ))

    hive = Hive(
        cells = cells,
        bees = [Bee(100, 100, "nurse"), Bee(200, 100, "builder"), Bee(300, 100, "cleaner"), Bee(400, 100, "food maker")]
    )
init()

def pause():
    hive.paused = not hive.paused

qb = QueenBee(SCREEN_WIDTH - 200, 200)
job_rect = pygame.Rect(50, SCREEN_HEIGHT * 2 / 3, SCREEN_HEIGHT / 3, SCREEN_HEIGHT / 3 - 50)
die_rect = pygame.Rect(SCREEN_WIDTH * 3 / 4, SCREEN_HEIGHT * 2 / 3, SCREEN_HEIGHT / 3, SCREEN_HEIGHT / 3 - 50)
idle_rect = pygame.Rect(100, 100, 400, 300)
start_over_button = Button(hive, "Start Over", NURSE_BEE_COLOR, 0, SCREEN_HEIGHT / 2 + 40, init, font)
pause_button = Button(hive, "Pause", NURSE_BEE_COLOR, SCREEN_WIDTH / 2 - 50, 90, pause, font_small)

def main():
    FramePerSec = pygame.time.Clock()
    pygame.display.set_caption("Bee Game")

    surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    while True:
        game_over = hive.honey == 0 or hive.bee_bread == 0 or len(hive.bees) == 0

        # Events
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == MOUSEBUTTONUP:
                if game_over:
                    if start_over_button.get_rect().collidepoint(pygame.mouse.get_pos()):
                        start_over_button.handle_click()
                if pause_button.get_rect().collidepoint(pygame.mouse.get_pos()):
                    pause_button.handle_click()
                for cell in hive.cells:
                    if cell.rect.collidepoint(pygame.mouse.get_pos()):
                        cell.handle_click()
                        break
                else:
                    for bee in hive.bees:
                        if bee.rect.collidepoint(pygame.mouse.get_pos()):
                            bee.handle_click()
                            break
            elif event.type == KEYUP:
                if event.key == K_n:
                    hive.assign_job("nurse")
                elif event.key == K_c:
                    hive.assign_job("cleaner")
                elif event.key == K_f:
                    hive.assign_job("food maker")
                elif event.key == K_b:
                    hive.assign_job("builder")
                elif event.key == K_d:
                    hive.debug = not hive.debug

        # Update
        if not game_over and not hive.paused:
            for bee in hive.bees:
                bee.update()
            for cell in hive.cells:
                cell.update()
            qb.update()

        # Draw
        surface.fill(YELLOW_BG)
        pygame.draw.circle(surface, BUILDER_BEE_COLOR, (0, SCREEN_HEIGHT), SCREEN_HEIGHT / 2)
        if hive.debug:
            pygame.draw.rect(surface, BLACK, job_rect, 1)
            pygame.draw.rect(surface, BLACK, die_rect, 1)
        for c in hive.cells:
            c.draw(surface)
        for b in hive.bees:
            b.draw(surface)
        qb.draw(surface)
        hive.draw(surface)
        pause_button.draw(surface)
        
        if game_over:
            game_over_text = font.render("COLONY COLLAPSE", True, BLACK)
            surface.blit(game_over_text, (SCREEN_WIDTH / 2 - game_over_text.get_width() / 2, SCREEN_HEIGHT / 2 - game_over_text.get_height() / 2))
            start_over_button.draw(surface)

        pygame.display.update()
        FramePerSec.tick(FPS)

if __name__ == "__main__":
    main()
