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

WIDTH, HEIGHT = 1000, 600
FPS = 60
TARGET_FRAME_TIME_MS = 1000.0 / FPS

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
NEON_BLUE = (0, 255, 255)
NEON_PINK = (255, 20, 147)
NEON_GREEN = (57, 255, 20)
NEON_ORANGE = (255, 165, 0)
NEON_PURPLE = (191, 0, 255)
NEON_YELLOW = (255, 255, 0)
DARK_BG = (10, 10, 30)
GRID_COLOR = (30, 30, 80)

PLAYER_SIZE = 30
PLAYER_SPEED = 5
OBSTACLE_WIDTH = 60
OBSTACLE_GAP = 200
OBSTACLE_SPEED = 6
SPAWN_INTERVAL = 1500
GRAVITY = 0.5
JUMP_FORCE = -12

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Neon Runner")
clock = pygame.time.Clock()

font_large = pygame.font.Font(None, 72)
font_medium = pygame.font.Font(None, 48)
font_small = pygame.font.Font(None, 32)

class Player:
    def __init__(self):
        self.x = 150
        self.y = HEIGHT // 2
        self.vel_y = 0
        self.rect = pygame.Rect(self.x, self.y, PLAYER_SIZE, PLAYER_SIZE)
        self.color = NEON_BLUE
        self.glow_phase = 0

    def update(self, dt):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] and self.y >= HEIGHT - 100 - PLAYER_SIZE:
            self.vel_y = JUMP_FORCE
        if keys[pygame.K_UP] and self.y > 50:
            self.y -= PLAYER_SPEED * dt / 16
        if keys[pygame.K_DOWN] and self.y < HEIGHT - 100 - PLAYER_SIZE:
            self.y += PLAYER_SPEED * dt / 16

        self.vel_y += GRAVITY * dt / 16
        self.y += self.vel_y * dt / 16

        if self.y >= HEIGHT - 100 - PLAYER_SIZE:
            self.y = HEIGHT - 100 - PLAYER_SIZE
            self.vel_y = 0

        self.rect.y = int(self.y)
        self.glow_phase += 0.1

    def draw(self, surface):
        glow = int(20 + 15 * math.sin(self.glow_phase))
        # Glow effect
        for i in range(3):
            alpha = 50 - i * 15
            glow_rect = pygame.Rect(self.rect.x - i * 2, self.rect.y - i * 2,
                                   PLAYER_SIZE + i * 4, PLAYER_SIZE + i * 4)
            pygame.draw.rect(surface, (*self.color[:3], alpha), glow_rect, border_radius=5)
        # Main body
        pygame.draw.rect(surface, self.color, self.rect, border_radius=5)
        # Core
        core_rect = pygame.Rect(self.rect.x + 5, self.rect.y + 5, PLAYER_SIZE - 10, PLAYER_SIZE - 10)
        pygame.draw.rect(surface, WHITE, core_rect, border_radius=3)

class Obstacle:
    def __init__(self, x, gap_y):
        self.x = x
        self.gap_y = gap_y
        self.width = OBSTACLE_WIDTH
        self.top_height = gap_y
        self.bottom_y = gap_y + OBSTACLE_GAP
        self.bottom_height = HEIGHT - 100 - self.bottom_y
        self.color = random.choice([NEON_PINK, NEON_GREEN, NEON_ORANGE, NEON_PURPLE])
        self.passed = False

    def update(self, dt):
        self.x -= OBSTACLE_SPEED * dt / 16

    def draw(self, surface):
        # Top obstacle
        top_rect = pygame.Rect(int(self.x), 0, self.width, self.top_height)
        pygame.draw.rect(surface, self.color, top_rect)
        # Neon glow on edges
        pygame.draw.rect(surface, WHITE, top_rect, 2)

        # Bottom obstacle
        bottom_rect = pygame.Rect(int(self.x), self.bottom_y, self.width, self.bottom_height)
        pygame.draw.rect(surface, self.color, bottom_rect)
        pygame.draw.rect(surface, WHITE, bottom_rect, 2)

    def is_offscreen(self):
        return self.x + self.width < 0

    def check_collision(self, player_rect):
        top_rect = pygame.Rect(int(self.x), 0, self.width, self.top_height)
        bottom_rect = pygame.Rect(int(self.x), self.bottom_y, self.width, self.bottom_height)
        return player_rect.colliderect(top_rect) or player_rect.colliderect(bottom_rect)

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(3, 8)
        self.vel_x = random.uniform(-3, 3)
        self.vel_y = random.uniform(-5, 5)
        self.life = 1.0
        self.decay = random.uniform(0.02, 0.05)

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

def draw_grid(surface):
    """Draw cyberpunk grid background."""
    for x in range(0, WIDTH, 50):
        pygame.draw.line(surface, GRID_COLOR, (x, 0), (x, HEIGHT - 100))
    for y in range(0, HEIGHT - 100, 50):
        pygame.draw.line(surface, GRID_COLOR, (0, y), (WIDTH, y))

def draw_ground(surface):
    """Draw neon ground line."""
    pygame.draw.rect(surface, NEON_BLUE, (0, HEIGHT - 100, WIDTH, 100))
    pygame.draw.line(surface, WHITE, (0, HEIGHT - 100), (WIDTH, HEIGHT - 100), 3)
    # Grid on ground
    for x in range(0, WIDTH, 50):
        pygame.draw.line(surface, GRID_COLOR, (x, HEIGHT - 100), (x, HEIGHT))

def main():
    player = Player()
    obstacles = []
    particles = []
    score = 0
    high_score = 0
    game_over = False
    last_spawn = pygame.time.get_ticks()

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
                if event.key == pygame.K_r and game_over:
                    if score > high_score:
                        high_score = score
                        try:
                            with open("highscore.txt", "w") as f:
                                f.write(str(high_score))
                        except:
                            pass
                    player = Player()
                    obstacles.clear()
                    particles.clear()
                    score = 0
                    game_over = False
                    last_spawn = pygame.time.get_ticks()
                if event.key == pygame.K_ESCAPE:
                    running = False

        if not game_over:
            player.update(dt)

            # Spawn obstacles
            now = pygame.time.get_ticks()
            if now - last_spawn > SPAWN_INTERVAL:
                gap_y = random.randint(100, HEIGHT - 100 - OBSTACLE_GAP - 100)
                obstacles.append(Obstacle(WIDTH, gap_y))
                last_spawn = now

            # Update obstacles
            for obs in obstacles[:]:
                obs.update(dt)
                if obs.check_collision(player.rect):
                    game_over = True
                    # Explosion particles
                    for _ in range(20):
                        particles.append(Particle(player.rect.centerx, player.rect.centery, player.color))
                if not obs.passed and obs.x + obs.width < player.x:
                    obs.passed = True
                    score += 10
                if obs.is_offscreen():
                    obstacles.remove(obs)

            # Update particles
            for p in particles[:]:
                p.update()
                if p.life <= 0:
                    particles.remove(p)

        # Draw
        screen.fill(DARK_BG)
        draw_grid(screen)
        draw_ground(screen)

        for obs in obstacles:
            obs.draw(screen)

        player.draw(screen)

        for p in particles:
            p.draw(screen)

        # UI
        score_text = font_medium.render(f"SCORE: {score}", True, WHITE)
        high_text = font_small.render(f"HIGH: {high_score}", True, NEON_YELLOW)
        screen.blit(score_text, (20, HEIGHT - 80))
        screen.blit(high_text, (WIDTH - 150, HEIGHT - 80))

        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            over_text = font_large.render("GAME OVER", True, NEON_PINK)
            final_text = font_medium.render(f"FINAL SCORE: {score}", True, WHITE)
            high_text = font_medium.render(f"HIGH SCORE: {high_score}", True, NEON_YELLOW)
            restart_text = font_small.render("Press R to Restart | ESC to Quit", True, WHITE)

            screen.blit(over_text, (WIDTH // 2 - over_text.get_width() // 2, HEIGHT // 2 - 100))
            screen.blit(final_text, (WIDTH // 2 - final_text.get_width() // 2, HEIGHT // 2 - 20))
            screen.blit(high_text, (WIDTH // 2 - high_text.get_width() // 2, HEIGHT // 2 + 40))
            screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 100))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()