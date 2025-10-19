import pygame

import random

import math

from enum import Enum

from collections import deque



# --- Ustawienia Główne ---

SCREEN_WIDTH = 1200

SCREEN_HEIGHT = 800

FPS = 60



# --- Ustawienia Scenariusza ---

BORDER_Y = 250

CAMERA_COUNT = 5

CAMERA_DETECTION_RANGE = 200

INTERCEPTOR_COUNT = 5

ENEMY_SPAWN_RATE = 100

BASE_POSITION = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)





# --- Stany Drona Obrońcy ---

class DroneState(Enum):

    IDLE = 1

    EN_ROUTE_TO_INVESTIGATE = 2

    SEARCH_PATROLLING = 3

    LOCKED_ON = 4

    RETURNING_TO_BASE = 5





# --- Kolory ---

WHITE = (255, 255, 255);

BLACK = (0, 0, 0);

RED = (255, 50, 50)

BLUE = (100, 149, 237);

GREEN = (50, 205, 50);

YELLOW = (255, 255, 0)

GRAY = (40, 40, 40);

DARK_GRAY = (20, 20, 20);

CAMERA_COLOR = (180, 180, 180)

CAMERA_ALERT_COLOR = (255, 100, 100);

FOV_COLOR = (100, 149, 237, 50)

LOCK_ON_COLOR = (255, 255, 0)





# --- Klasa Kamery (bez zmian) ---

class Camera(pygame.sprite.Sprite):

    def __init__(self, x, y):

        super().__init__()

        self.image = pygame.Surface([15, 15])

        self.rect = self.image.get_rect(center=(x, y))

        self.is_alerted = False



    def update(self, enemies):

        self.is_alerted = False

        for enemy in enemies:

            if enemy.rect.centery < BORDER_Y:

                distance = math.hypot(self.rect.centerx - enemy.rect.centerx, self.rect.centery - enemy.rect.centery)

                if distance < CAMERA_DETECTION_RANGE:

                    self.is_alerted = True

                    return



    def draw_range(self, surface):

        color = CAMERA_ALERT_COLOR if self.is_alerted else GRAY

        self.image.fill(color)

        pygame.draw.circle(surface, color, self.rect.center, CAMERA_DETECTION_RANGE, 1)





# --- Klasa Wrogi Dron ---

class EnemyDrone(pygame.sprite.Sprite):

    def __init__(self):

        super().__init__()

        self.image = pygame.Surface([10, 10]);

        self.image.fill(RED)

        self.rect = self.image.get_rect(x=random.randint(0, SCREEN_WIDTH), y=random.randint(-50, 0))

        self.speed = random.uniform(1.0, 2.5)

        target_x, target_y = random.randint(0, SCREEN_WIDTH), random.randint(BORDER_Y + 50, SCREEN_HEIGHT)

        angle = math.atan2(target_y - self.rect.y, target_x - self.rect.x)

        self.vx = math.cos(angle) * self.speed

        self.vy = math.sin(angle) * self.speed

        self.crossed_border = False

        # --- NOWY ATRYBUT ---

        self.is_targeted_by = None  # Przechowuje, który dron go namierza



    def update(self):

        self.rect.x += self.vx;

        self.rect.y += self.vy

        if not (-100 < self.rect.x < SCREEN_WIDTH + 100 and -100 < self.rect.y < SCREEN_HEIGHT + 100):

            self.kill()





# --- Klasa Drona Obrońcy ---

class InterceptorDrone(pygame.sprite.Sprite):

    def __init__(self, x, y):

        super().__init__()

        self.image = pygame.Surface([12, 12], pygame.SRCALPHA)

        pygame.draw.polygon(self.image, BLUE, [(0, 0), (12, 6), (0, 12)])

        self.original_image = self.image

        self.rect = self.image.get_rect(center=(x, y))

        self.base_pos = (x, y)

        self.speed = 5.0

        self.state = DroneState.IDLE

        self.destination = None

        self.angle = 0

        self.fov_range = CAMERA_DETECTION_RANGE / 2

        self.fov_angle_deg = 60

        self.locked_target = None

        self.lock_on_timer = 0

        self.patrol_center = None

        self.patrol_radius = 60

        self.patrol_angle = 0

        self.patrol_timer = 0

        self.current_task_location = None



    def assign_investigation(self, destination_pos):

        if self.state == DroneState.IDLE:

            self.destination = destination_pos

            self.current_task_location = destination_pos

            self.state = DroneState.EN_ROUTE_TO_INVESTIGATE



    def clear_task(self, pending_locations):

        if self.current_task_location in pending_locations:

            pending_locations.remove(self.current_task_location)

        self.current_task_location = None



    # --- NOWA METODA POMOCNICZA ---

    def release_target(self):

        """Uwalnia roszczenie drona do celu."""

        if self.locked_target and self.locked_target.is_targeted_by == self:

            self.locked_target.is_targeted_by = None

        self.locked_target = None



    # --- ZMODYFIKOWANA METODA is_in_fov ---

    def is_in_fov(self, enemies_group):

        """Sprawdza, czy jakikolwiek *dostępny* wróg jest w polu widzenia."""

        for enemy in enemies_group:

            enemy_vec = pygame.math.Vector2(enemy.rect.center) - pygame.math.Vector2(self.rect.center)

            if 0 < enemy_vec.length() < self.fov_range:

                forward_vec = pygame.math.Vector2(1, 0).rotate(-self.angle)

                angle_between = forward_vec.angle_to(enemy_vec)



                if abs(angle_between) < self.fov_angle_deg / 2:

                    # WARUNEK: Cel jest wolny LUB to nasz obecny cel

                    if enemy.is_targeted_by is None or enemy.is_targeted_by == self:

                        return enemy

        return None



    # --- ZMODYFIKOWANA METODA update ---

    def update(self, enemies, task_queue, pending_locations):

        # Sprawdź, czy cel wciąż żyje

        if self.locked_target and not self.locked_target.alive():

            self.release_target()  # Używamy nowej metody

            self.state = DroneState.SEARCH_PATROLLING

            self.patrol_timer = FPS * 5



            # Skanuj w poszukiwaniu celów (jeśli nie namierzasz)

        if self.state in [DroneState.EN_ROUTE_TO_INVESTIGATE, DroneState.SEARCH_PATROLLING]:

            detected_enemy = self.is_in_fov(enemies)

            if detected_enemy:

                self.locked_target = detected_enemy

                # --- ZAREZERWUJ CEL ---

                self.locked_target.is_targeted_by = self

                self.lock_on_timer = FPS * 3

                self.state = DroneState.LOCKED_ON



        # --- Maszyna Stanów Drona ---

        if self.state == DroneState.EN_ROUTE_TO_INVESTIGATE:

            if self.move_towards(self.destination):

                self.state = DroneState.SEARCH_PATROLLING

                self.patrol_center = self.rect.center

                self.patrol_timer = FPS * 5



        elif self.state == DroneState.SEARCH_PATROLLING:

            self.patrol_timer -= 1

            if self.patrol_timer <= 0:

                self.state = DroneState.RETURNING_TO_BASE

                self.clear_task(pending_locations)

            else:

                self.patrol_angle = (self.patrol_angle + 3) % 360

                patrol_target_x = self.patrol_center[0] + self.patrol_radius * math.cos(math.radians(self.patrol_angle))

                patrol_target_y = self.patrol_center[1] + self.patrol_radius * math.sin(math.radians(self.patrol_angle))

                self.move_towards((patrol_target_x, patrol_target_y))



        elif self.state == DroneState.LOCKED_ON:

            if self.locked_target:

                self.move_towards(self.locked_target.rect.center)

                self.lock_on_timer -= 1

                if self.lock_on_timer <= 0:

                    self.locked_target.kill()

                    self.release_target()  # Używamy nowej metody

                    self.clear_task(pending_locations)



                    if task_queue:

                        new_task = task_queue.popleft()

                        if new_task in pending_locations:

                            pending_locations.remove(new_task)

                        self.assign_investigation(new_task)

                    else:

                        self.state = DroneState.RETURNING_TO_BASE

            else:

                # Cel zniknął (np. zabity przez innego drona)

                self.state = DroneState.SEARCH_PATROLLING



        elif self.state == DroneState.RETURNING_TO_BASE:

            if self.move_towards(self.base_pos):

                self.state = DroneState.IDLE

                self.destination = None

                self.clear_task(pending_locations)



    def move_towards(self, target_pos):

        if not target_pos: return False

        target_vec = pygame.math.Vector2(target_pos)

        current_vec = pygame.math.Vector2(self.rect.center)

        distance = current_vec.distance_to(target_vec)

        if distance < self.speed: return True

        direction_vec = (target_vec - current_vec).normalize()

        self.angle = math.degrees(math.atan2(-direction_vec.y, direction_vec.x))

        self.rect.center += direction_vec * self.speed

        self.image = pygame.transform.rotate(self.original_image, self.angle)

        self.rect = self.image.get_rect(center=self.rect.center)

        return False



    def is_available(self):

        return self.state == DroneState.IDLE



    def draw_fov(self, surface):

        if self.state not in [DroneState.EN_ROUTE_TO_INVESTIGATE, DroneState.SEARCH_PATROLLING, DroneState.LOCKED_ON]:

            return

        fov_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        points = [self.rect.center]

        for n in range(-self.fov_angle_deg // 2, self.fov_angle_deg // 2 + 1, 5):

            angle_rad = math.radians(-self.angle + n)

            end_x = self.rect.centerx + self.fov_range * math.cos(angle_rad)

            end_y = self.rect.centery + self.fov_range * math.sin(angle_rad)

            points.append((end_x, end_y))

        if len(points) > 2: pygame.draw.polygon(fov_surface, FOV_COLOR, points)

        surface.blit(fov_surface, (0, 0))





# --- Główna funkcja gry (bez zmian) ---

def main():

    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    pygame.display.set_caption("SKYGUARD C2 - Target Deconfliction")

    clock = pygame.time.Clock()

    font = pygame.font.SysFont("Consolas", 20)

    indicator_font = pygame.font.SysFont("Consolas", 30, bold=True)

    q_mark_surface = indicator_font.render("?", True, YELLOW)

    ex_mark_surface = indicator_font.render("!", True, RED)



    all_sprites = pygame.sprite.Group();

    enemies = pygame.sprite.Group()

    interceptors = pygame.sprite.Group();

    cameras = pygame.sprite.Group()



    camera_spacing = SCREEN_WIDTH / (CAMERA_COUNT + 1)

    for i in range(CAMERA_COUNT):

        camera = Camera(camera_spacing * (i + 1), BORDER_Y)

        all_sprites.add(camera);

        cameras.add(camera)



    for i in range(INTERCEPTOR_COUNT):

        offset_x = (i - (INTERCEPTOR_COUNT - 1) / 2) * 50

        interceptor = InterceptorDrone(BASE_POSITION[0] + offset_x, BASE_POSITION[1])

        all_sprites.add(interceptor);

        interceptors.add(interceptor)



    task_queue = deque()

    pending_locations = set()

    spawn_timer, border_breaches = 0, 0



    running = True

    while running:

        for event in pygame.event.get():

            if event.type == pygame.QUIT: running = False



        spawn_timer += 1

        if spawn_timer >= ENEMY_SPAWN_RATE:

            spawn_timer = 0

            new_enemy = EnemyDrone();

            all_sprites.add(new_enemy);

            enemies.add(new_enemy)



        cameras.update(enemies)

        for cam in cameras:

            if cam.is_alerted and cam.rect.center not in pending_locations:

                task_queue.append(cam.rect.center)

                pending_locations.add(cam.rect.center)



        if task_queue:

            for drone in interceptors:

                if drone.is_available():

                    task_location = task_queue.popleft()

                    drone.assign_investigation(task_location)

                    break



        for enemy in enemies:

            if not enemy.crossed_border and enemy.rect.centery > BORDER_Y:

                enemy.crossed_border = True;

                border_breaches += 1



        enemies.update()

        interceptors.update(enemies, task_queue, pending_locations)



        # --- Rysowanie ---

        screen.fill(BLACK)

        pygame.draw.rect(screen, DARK_GRAY, (0, 0, SCREEN_WIDTH, BORDER_Y))

        pygame.draw.line(screen, YELLOW, (0, BORDER_Y), (SCREEN_WIDTH, BORDER_Y), 3)

        for cam in cameras: cam.draw_range(screen)

        pygame.draw.rect(screen, GREEN, (BASE_POSITION[0] - 40, BASE_POSITION[1] - 20, 80, 40))



        for drone in interceptors:

            drone.draw_fov(screen)

            if drone.state == DroneState.LOCKED_ON and drone.locked_target:

                pygame.draw.line(screen, LOCK_ON_COLOR, drone.rect.center, drone.locked_target.rect.center, 2)

            elif drone.destination and drone.state not in [DroneState.IDLE, DroneState.RETURNING_TO_BASE]:

                pygame.draw.line(screen, BLUE, drone.rect.center, drone.destination, 1)



        all_sprites.draw(screen)



        for drone in interceptors:

            if drone.state in [DroneState.EN_ROUTE_TO_INVESTIGATE, DroneState.SEARCH_PATROLLING]:

                pos_x = drone.rect.centerx - q_mark_surface.get_width() // 2

                pos_y = drone.rect.top - q_mark_surface.get_height()

                screen.blit(q_mark_surface, (pos_x, pos_y))

            elif drone.state == DroneState.LOCKED_ON:

                pos_x = drone.rect.centerx - ex_mark_surface.get_width() // 2

                pos_y = drone.rect.top - ex_mark_surface.get_height()

                screen.blit(ex_mark_surface, (pos_x, pos_y))



        # --- HUD ---

        available_count = sum(1 for i in interceptors if i.is_available())

        hud_text = f"Naruszenia: {border_breaches} | Zagrożenia: {len(enemies)} | Drony dostępne: {available_count}/{INTERCEPTOR_COUNT} | Zadania w kolejce: {len(task_queue)}"

        text_surface = font.render(hud_text, True, WHITE)

        screen.blit(text_surface, (10, 10))

        border_label = font.render(">>> GRANICA PAŃSTWA <<<", True, YELLOW)

        screen.blit(border_label, (SCREEN_WIDTH / 2 - border_label.get_width() / 2, BORDER_Y - 30))



        pygame.display.flip()

        clock.tick(FPS)



    pygame.quit()





if __name__ == "__main__":

    main()



