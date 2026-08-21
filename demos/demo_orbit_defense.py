import pygame
import random
import sys
import math

pygame.init()

AUDIO_ENABLED = False
try:
    pygame.mixer.init()
    AUDIO_ENABLED = True
except Exception:
    AUDIO_ENABLED = False

WIDTH, HEIGHT = 800, 800
FPS = 60
CENTER = (WIDTH // 2, HEIGHT // 2)

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 100)
BLUE = (50, 150, 255)
YELLOW = (255, 255, 50)
ORANGE = (255, 165, 0)
PURPLE = (200, 50, 255)
CYAN = (50, 255, 255)
DARK_BG = (15, 15, 35)

PLANET_RADIUS = 80
ORBIT_RADIUS = 200
PLAYER_SIZE = 20
ENEMY_SIZE = 15
PROJECTILE_SIZE = 5

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Orbit Defense")
clock = pygame.time.Clock()

font_large = pygame.font.Font(None, 72)
font_medium = pygame.font.Font(None, 48)
font_small = pygame.font.Font(None, 28)

class Player:
    def __init__(self):
        self.angle = 0
        self.orbit_radius = ORBIT_RADIUS
        self.size = PLAYER_SIZE
        self.color = CYAN
        self.cooldown = 0
        self.update_position()

    def update_position(self):
        self.x = CENTER[0] + self.orbit_radius * math.cos(self.angle)
        self.y = CENTER[1] + self.orbit_radius * math.sin(self.angle)
        self.rect = pygame.Rect(self.x - self.size // 2, self.y - self.size // 2, self.size, self.size)

    def update(self, dt, keys):
        speed = 2.0 * dt / 16
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.angle -= speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.angle += speed

        self.update_position()

        if self.cooldown > 0:
            self.cooldown -= dt

    def draw(self, surface):
        # Orbit path
        pygame.draw.circle(surface, (40, 40, 80), CENTER, self.orbit_radius, 1)
        # Player
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size // 2)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.size // 4)
        # Direction indicator
        tip_x = self.x + (self.size // 2 + 5) * math.cos(self.angle)
        tip_y = self.y + (self.size // 2 + 5) * math.sin(self.angle)
        pygame.draw.line(surface, WHITE, (int(self.x), int(self.y)), (int(tip_x), int(tip_y)), 2)

    def shoot(self):
        if self.cooldown <= 0:
            self.cooldown = 200
            return Projectile(self.x, self.y, self.angle)
        return None

class Projectile:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 8
        self.size = PROJECTILE_SIZE
        self.color = YELLOW
        self.life = 60

    def update(self):
        self.x += self.speed * math.cos(self.angle)
        self.y += self.speed * math.sin(self.angle)
        self.life -= 1

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)
        # Trail
        trail_x = self.x - self.speed * 3 * math.cos(self.angle)
        trail_y = self.y - self.speed * 3 * math.sin(self.angle)
        pygame.draw.line(surface, self.color, (int(self.x), int(self.y)), (int(trail_x), int(trail_y)), 2)

    def is_alive(self):
        return self.life > 0 and 0 <= self.x <= WIDTH and 0 <= self.y <= HEIGHT

    def get_rect(self):
        return pygame.Rect(self.x - self.size, self.y - self.size, self.size * 2, self.size * 2)

class Enemy:
    def __init__(self, wave):
        self.angle = random.uniform(0, 2 * math.pi)
        self.orbit_radius = random.randint(PLANET_RADIUS + 50, ORBIT_RADIUS - 50)
        self.size = ENEMY_SIZE
        self.color = random.choice([RED, ORANGE, PURPLE])
        self.speed = 0.5 + wave * 0.1
        self.health = 1 + wave // 3
        self.max_health = self.health
        self.update_position()

    def update_position(self):
        self.x = CENTER[0] + self.orbit_radius * math.cos(self.angle)
        self.y = CENTER[1] + self.orbit_radius * math.sin(self.angle)
        self.rect = pygame.Rect(self.x - self.size // 2, self.y - self.size // 2, self.size, self.size)

    def update(self):
        self.angle += self.speed * 0.01
        self.orbit_radius -= 0.1  # Spiral inward
        self.update_position()

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size // 2)
        # Health indicator
        if self.health < self.max_health:
            pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.size // 2, 1)

    def is_dead(self):
        return self.health <= 0 or self.orbit_radius <= PLANET_RADIUS + 20

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(2, 6)
        self.vel_x = random.uniform(-3, 3)
        self.vel_y = random.uniform(-3, 3)
        self.life = 1.0
        self.decay = random.uniform(0.03, 0.08)

    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.life -= self.decay
        self.size = max(0, self.size * self.life)

    def draw(self, surface):
        if self.life > 0:
            alpha = int(255 * self.life)
            color = (*self.color[:3], alpha)
            surf = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (int(self.size), int(self.size)), int(self.size))
            surface.blit(surf, (int(self.x - self.size), int(self.y - self.size)))

def draw_planet(surface):
    """Draw the central planet."""
    # Planet base
    pygame.draw.circle(surface, (40, 40, 80), CENTER, PLANET_RADIUS)
    # Atmosphere glow
    for i in range(3):
        alpha = 30 - i * 10
        pygame.draw.circle(surface, (*BLUE[:3], alpha), CENTER, PLANET_RADIUS + i * 5)
    # Surface details
    for _ in range(20):
        angle = random.uniform(0, 2 * math.pi)
        r = random.uniform(0, PLANET_RADIUS * 0.8)
        x = CENTER[0] + r * math.cos(angle)
        y = CENTER[1] + r * math.sin(angle)
        pygame.draw.circle(surface, (60, 60, 120), (int(x), int(y)), random.randint(2, 8))

def draw_stars(surface):
    """Draw background stars."""
    random.seed(42)  # Consistent stars
    for _ in range(100):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        size = random.randint(1, 3)
        brightness = random.randint(100, 255)
        pygame.draw.circle(surface, (brightness, brightness, brightness), (x, y), size)

def main():
    player = Player()
    enemies = []
    projectiles = []
    particles = []
    score = 0
    high_score = 0
    wave = 1
    enemies_spawned = 0
    enemies_per_wave = 5
    spawn_timer = 0
    game_over = False

    try:
        with open("highscore.txt", "r") as f:
            high_score = int(f.read())
    except:
        pass

    running = True
    while running:
        dt = clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    proj = player.shoot()
                    if proj:
                        projectiles.append(proj)
                if event.key == pygame.K_r and game_over:
                    if score > high_score:
                        high_score = score
                        try:
                            with open("highscore.txt", "w") as f:
                                f.write(str(high_score))
                        except:
                            pass
                    player = Player()
                    enemies.clear()
                    projectiles.clear()
                    particles.clear()
                    score = 0
                    wave = 1
                    enemies_spawned = 0
                    spawn_timer = 0
                    game_over = False
                if event.key == pygame.K_ESCAPE:
                    running = False

        keys = pygame.key.get_pressed()

        if not game_over:
            player.update(dt, keys)

            # Spawn enemies
            spawn_timer += dt
            if enemies_spawned < enemies_per_wave and spawn_timer > 1000:
                enemies.append(Enemy(wave))
                enemies_spawned += 1
                spawn_timer = 0

            # Check wave complete
            if enemies_spawned >= enemies_per_wave and len(enemies) == 0:
                wave += 1
                enemies_spawned = 0
                enemies_per_wave = min(5 + wave * 2, 25)

            # Update projectiles
            for proj in projectiles[:]:
                proj.update()
                if not proj.is_alive():
                    projectiles.remove(proj)
                    continue

                # Check collisions with enemies
                for enemy in enemies[:]:
                    if proj.get_rect().colliderect(enemy.rect):
                        enemy.health -= 1
                        projectiles.remove(proj)
                        if enemy.is_dead():
                            # Explosion particles
                            for _ in range(10):
                                particles.append(Particle(enemy.x, enemy.y, enemy.color))
                            score += 100 * wave
                            enemies.remove(enemy)
                        break

            # Update enemies
            for enemy in enemies[:]:
                enemy.update()
                # Check collision with planet
                dist = math.hypot(enemy.x - CENTER[0], enemy.y - CENTER[1])
                if dist <= PLANET_RADIUS + enemy.size // 2:
                    game_over = True
                # Check collision with player
                if math.hypot(enemy.x - player.x, enemy.y - player.y) <= (enemy.size + player.size) // 2:
                    game_over = True

            # Update particles
            for p in particles[:]:
                p.update()
                if p.life <= 0:
                    particles.remove(p)

        # Draw
        screen.fill(DARK_BG)
        draw_stars(screen)
        draw_planet(screen)

        for proj in projectiles:
            proj.draw(screen)

        for enemy in enemies:
            enemy.draw(screen)

        player.draw(screen)

        for p in particles:
            p.draw(screen)

        # UI
        score_text = font_medium.render(f"SCORE: {score}", True, WHITE)
        wave_text = font_small.render(f"WAVE: {wave}", True, YELLOW)
        high_text = font_small.render(f"HIGH: {high_score}", True, CYAN)
        screen.blit(score_text, (20, 20))
        screen.blit(wave_text, (20, 70))
        screen.blit(high_text, (WIDTH - 150, 20))

        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            over_text = font_large.render("GAME OVER", True, RED)
            final_text = font_medium.render(f"FINAL SCORE: {score}", True, WHITE)
            wave_text = font_medium.render(f"WAVES SURVIVED: {wave - 1}", True, YELLOW)
            high_text = font_medium.render(f"HIGH SCORE: {high_score}", True, CYAN)
            restart_text = font_small.render("Press R to Restart | ESC to Quit", True, WHITE)

            screen.blit(over_text, (WIDTH // 2 - over_text.get_width() // 2, HEIGHT // 2 - 120))
            screen.blit(final_text, (WIDTH // 2 - final_text.get_width() // 2, HEIGHT // 2 - 40))
            screen.blit(wave_text, (WIDTH // 2 - wave_text.get_width() // 2, HEIGHT // 2 + 20))
            screen.blit(high_text, (WIDTH // 2 - high_text.get_width() // 2, HEIGHT // 2 + 80))
            screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 140))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()