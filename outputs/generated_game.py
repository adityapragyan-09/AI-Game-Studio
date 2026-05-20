import pygame
import random
import sys
import math
import os


pygame.init()


AUDIO_ENABLED = False
try:
    pygame.mixer.init()
    AUDIO_ENABLED = True
except Exception:
    AUDIO_ENABLED = False


WIDTH, HEIGHT = 1000, 600
FPS = 60
TARGET_FRAME_TIME_MS = 1000.0 / FPS # Ideal time per frame in milliseconds


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 200, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 100, 0)
PURPLE = (150, 0, 150)
CYAN = (0, 200, 200)
DARK_GREEN = (0, 100, 0)
LIGHT_BLUE = (173, 216, 230)
GREY = (150, 150, 150)
DARK_GREY = (50, 50, 50)
BROWN = (139, 69, 19)
SWAMP_GREEN = (50, 70, 40)
MURKY_BLUE = (80, 100, 120)
JUNGLE_GREEN = (30, 120, 30)
DEEP_BLUE = (50, 50, 150)
ROCKY_GREY = (80, 80, 80)
DARK_PURPLISH_BLUE = (60, 40, 80)


GRAVITY = 0.8
PLAYER_X = 100
PLAYER_HEAD_RADIUS = 20
PLAYER_BODY_WIDTH = 30
PLAYER_BODY_HEIGHT = 40
PLAYER_LIMB_LENGTH = 25
PLAYER_HEIGHT_TOTAL = PLAYER_HEAD_RADIUS * 2 + PLAYER_BODY_HEIGHT # Approximate total player height
GROUND_HEIGHT = 50
PLAYER_START_Y = HEIGHT - GROUND_HEIGHT - PLAYER_HEIGHT_TOTAL # Ground height - player height
BASE_SCROLL_SPEED = 6 # Pixels per frame
JUMP_VELOCITY = -14 # Base jump strength
MAX_JUMP_CHARGE_TIME = 30 # Frames (will implicitly be affected by dt, but animation is still frame-based)
JUMP_CHARGE_MULTIPLIER = 0.6 # How much holding SPACE adds to jump
BOOST_JUMP_MULTIPLIER = 1.8 # Multiplier for boost pad jump


MIN_OBSTACLE_GAP = 250
MAX_OBSTACLE_GAP = 450
OBSTACLE_SPAWN_INTERVAL = 100 # How far the last obstacle must be before spawning next
MIN_OBSTACLE_HEIGHT = 40
MAX_OBSTACLE_HEIGHT = 150
MIN_OBSTACLE_WIDTH = 30
MAX_OBSTACLE_WIDTH = 120
PIT_MIN_WIDTH = 80
PIT_MAX_WIDTH = 200
BOUNCY_BLOB_RADIUS = 25
BOUNCY_BLOB_HEIGHT_RANGE = 40
BOUNCY_BLOB_SPEED = 0.08 # Multiplier for sine wave, time-based, so less direct dt scaling needed
GLIDER_HEIGHT_OFFSET = 100 # How high above ground gliders appear
GLIDER_WIDTH = 80
GLIDER_HEIGHT = 40
FALLING_PLATFORM_WIDTH = 80
FALLING_PLATFORM_HEIGHT = 20
FALLING_PLATFORM_DISAPPEAR_TIME = 500 # ms


TIME_SCORE_INTERVAL_MS = 100
OBSTACLE_CLEAR_BONUS = 5
PERFECT_JUMP_BONUS = 15
PERFECT_JUMP_THRESHOLD = 15 # Pixels below obstacle to count as perfect


GAME_STATE_PLAYING = 0
GAME_STATE_GAME_OVER = 1


ZONE_1_SCORE = 0
ZONE_2_SCORE = 500
ZONE_3_SCORE = 1500
ZONE_4_SCORE = 3000


screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Sir Wigglebottom's Wobbly Warp")
clock = pygame.time.Clock()


current_score = 0
high_score = 0
game_state = GAME_STATE_PLAYING
scroll_speed = BASE_SCROLL_SPEED # This will be the base speed, actual scroll amount derived from dt
obstacles = []
background_elements = []
ground_y = HEIGHT - GROUND_HEIGHT
player_death_particles = [] # For the "pop" animation


ZONE_DATA = {} # Will be populated after Player class


player = None # Initialize player to None, will be set in main()


class Player:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = PLAYER_X
        self.y = float(PLAYER_START_Y) # Use float for smooth movement
        self.vel_y = 0.0 # Use float for smooth movement
        self.is_jumping = False
        self.on_ground = True
        self.jump_charge_timer = 0
        self.wobble_offset = 0 # Visual wobble
        self.wobble_direction = 1
        self.wobble_timer = 0
        self.squash_stretch_timer = 0
        self.squash_stretch_duration = 10 # frames for animation
        self.body_color = BLUE
        self.boosted_jump = False
        self.is_dead = False
        self.death_flash_timer = 0.0 # Use float for dt scaling

    def start_jump(self):
        if self.on_ground and not self.is_dead:
            self.is_jumping = True
            self.jump_charge_timer = 0
            self.on_ground = False # No longer on ground once jump initiated

    def end_jump(self):
        # Only apply jump if it was an active jump (not just letting go of space when airborne)
        # or if max charge reached and space was subsequently released.
        if self.is_jumping or (self.jump_charge_timer > 0 and not self.on_ground):
            jump_power = 1.0 + (self.jump_charge_timer / MAX_JUMP_CHARGE_TIME) * JUMP_CHARGE_MULTIPLIER
            if self.boosted_jump:
                jump_power *= BOOST_JUMP_MULTIPLIER
                self.boosted_jump = False # Use boost once
            self.vel_y = JUMP_VELOCITY * jump_power
            self.is_jumping = False # Ensure jump state is reset immediately after applying velocity
            self.squash_stretch_timer = self.squash_stretch_duration # Start stretch animation

    def update(self, dt):
        if self.is_dead:
            # Player flashes red for a brief moment after dying
            if self.death_flash_timer > 0:
                self.death_flash_timer -= dt
                if self.death_flash_timer <= 0:
                    self.body_color = BLUE # Reset color after flash
            return

        # Handle jump charge (frame-based for consistency with jump mechanic feel)
        if self.is_jumping and pygame.key.get_pressed()[pygame.K_SPACE]:
            self.jump_charge_timer = min(self.jump_charge_timer + 1, MAX_JUMP_CHARGE_TIME)
        else:
            if self.is_jumping: # Space was released or max charge reached
                self.end_jump()

        # Apply gravity and velocity, scaled by dt
        dt_factor = dt / TARGET_FRAME_TIME_MS # How many "ideal frames" have passed
        self.vel_y += GRAVITY * dt_factor
        self.y += self.vel_y * dt_factor

        # Ground collision
        if self.y >= PLAYER_START_Y:
            self.y = float(PLAYER_START_Y)
            self.vel_y = 0.0
            if not self.on_ground: # Just landed
                self.on_ground = True
                self.squash_stretch_timer = -self.squash_stretch_duration # Start squash animation
                self.is_jumping = False # Ensure jump state is reset, even if space was held

        # Wobble animation (frame-based for visual consistency)
        if self.on_ground:
            self.wobble_timer += 1
            if self.wobble_timer % 5 == 0: # Change wobble every few frames
                self.wobble_offset += self.wobble_direction * random.randint(0, 2)
                if abs(self.wobble_offset) > 5:
                    self.wobble_direction *= -1
            self.wobble_offset = max(-5, min(5, self.wobble_offset)) # Clamp wobble
        else:
            self.wobble_offset = 0 # No wobble in air

        # Squash and stretch animation (frame-based for visual consistency)
        if self.squash_stretch_timer > 0: # Stretching up
            self.squash_stretch_timer -= 1
        elif self.squash_stretch_timer < 0: # Squashing down
            self.squash_stretch_timer += 1
            if self.squash_stretch_timer == 0: # Finished squash, reset
                self.squash_stretch_timer = 0

    def get_rect(self):
        # Approximate player bounding box for collision
        # Adjust y and height based on squash/stretch for more accurate collision
        body_width_adj = float(PLAYER_BODY_WIDTH)
        body_height_adj = float(PLAYER_BODY_HEIGHT)
        
        if self.squash_stretch_timer > 0: # Stretching upwards
            stretch_factor = self.squash_stretch_timer / self.squash_stretch_duration
            body_height_adj *= (1 + stretch_factor * 0.5)
            body_width_adj *= (1 - stretch_factor * 0.2)
        elif self.squash_stretch_timer < 0: # Squashing downwards
            squash_factor = abs(self.squash_stretch_timer) / self.squash_stretch_duration
            body_height_adj *= (1 - squash_factor * 0.3)
            body_width_adj *= (1 + squash_factor * 0.3)
        
        # Ensure minimum dimensions
        body_width_adj = max(PLAYER_BODY_WIDTH * 0.8, body_width_adj)
        body_height_adj = max(PLAYER_BODY_HEIGHT * 0.8, body_height_adj)

        # Player's total height, including head
        current_total_height = PLAYER_HEAD_RADIUS * 2 + body_height_adj

        # The rect should originate from the top of the head
        return pygame.Rect(self.x - body_width_adj / 2, self.y, body_width_adj, current_total_height)


    def draw(self, screen):
        if self.is_dead and self.death_flash_timer <= 0:
            return # Don't draw player if dead and flash is over

        body_width = PLAYER_BODY_WIDTH + self.wobble_offset
        body_height = PLAYER_BODY_HEIGHT - abs(self.wobble_offset) / 2

        # Apply squash/stretch
        if self.squash_stretch_timer > 0: # Stretching upwards
            stretch_factor = self.squash_stretch_timer / self.squash_stretch_duration
            body_height *= (1 + stretch_factor * 0.5)
            body_width *= (1 - stretch_factor * 0.2)
        elif self.squash_stretch_timer < 0: # Squashing downwards
            squash_factor = abs(self.squash_stretch_timer) / self.squash_stretch_duration
            body_height *= (1 - squash_factor * 0.3)
            body_width *= (1 + squash_factor * 0.3)

        # Ensure minimum dimensions
        body_width = max(PLAYER_BODY_WIDTH * 0.8, body_width)
        body_height = max(PLAYER_BODY_HEIGHT * 0.8, body_height)

        # Body
        body_x = self.x - body_width / 2
        body_y = self.y + PLAYER_HEAD_RADIUS * 2 # Body starts below head
        body_rect = pygame.Rect(int(body_x), int(body_y), int(body_width), int(body_height))
        
        # Flash red if just died
        draw_body_color = RED if self.is_dead and (int(self.death_flash_timer / 100) % 2 == 0) else self.body_color
        pygame.draw.rect(screen, draw_body_color, body_rect)

        # Head
        head_center_x = self.x + self.wobble_offset / 2 # Head can wobble slightly
        head_center_y = self.y + PLAYER_HEAD_RADIUS
        pygame.draw.circle(screen, YELLOW, (int(head_center_x), int(head_center_y)), PLAYER_HEAD_RADIUS)

        # Eyes (slightly off-center for goofy look)
        eye_offset = PLAYER_HEAD_RADIUS * 0.3
        eye_y_offset = -PLAYER_HEAD_RADIUS * 0.1
        left_eye_center = (int(head_center_x - eye_offset), int(head_center_y + eye_y_offset))
        right_eye_center = (int(head_center_x + eye_offset), int(head_center_y + eye_y_offset))
        pygame.draw.circle(screen, WHITE, left_eye_center, 8)
        pygame.draw.circle(screen, WHITE, right_eye_center, 8)
        pygame.draw.circle(screen, BLACK, (left_eye_center[0] + 3, left_eye_center[1]), 4) # Pupils
        pygame.draw.circle(screen, BLACK, (right_eye_center[0] + 3, right_eye_center[1]), 4)

        # Mouth (simple red rect)
        mouth_width = 12
        mouth_height = 5
        mouth_x = int(head_center_x - mouth_width / 2)
        mouth_y = int(head_center_y + PLAYER_HEAD_RADIUS * 0.5)
        pygame.draw.rect(screen, RED, (mouth_x, mouth_y, mouth_width, mouth_height))

        # Limbs (stick-figure style)
        arm_offset_x = body_width / 2 + 5
        arm_y_start = body_y + body_height / 4
        leg_offset_x = body_width / 4
        leg_y_start = body_y + body_height

        # Arms
        pygame.draw.line(screen, BLACK, (int(body_x - 5), int(arm_y_start)), (int(body_x - arm_offset_x), int(arm_y_start + PLAYER_LIMB_LENGTH)), 3)
        pygame.draw.line(screen, BLACK, (int(body_x + body_width + 5), int(arm_y_start)), (int(body_x + body_width + arm_offset_x), int(arm_y_start + PLAYER_LIMB_LENGTH)), 3)

        # Legs
        pygame.draw.line(screen, BLACK, (int(body_x + leg_offset_x), int(leg_y_start)), (int(body_x + leg_offset_x - 5), int(leg_y_start + PLAYER_LIMB_LENGTH)), 3)
        pygame.draw.line(screen, BLACK, (int(body_x + body_width - leg_offset_x), int(leg_y_start)), (int(body_x + body_width - leg_offset_x + 5), int(leg_y_start + PLAYER_LIMB_LENGTH)), 3)

    def die(self):
        global player_death_particles
        if self.is_dead: # Prevent multiple death calls
            return
        self.is_dead = True
        self.death_flash_timer = 200.0 # Flash for 200ms

        # Create death particles
        player_rect = self.get_rect()
        for _ in range(10): # Spawn a few particles
            particle_size = random.randint(5, 15)
            particle_x = random.uniform(player_rect.left, player_rect.right)
            particle_y = random.uniform(player_rect.top, player_rect.bottom)
            particle_color = random.choice([self.body_color, YELLOW, RED])
            particle_vel_x = random.uniform(-3, 3)
            particle_vel_y = random.uniform(-5, -1)
            particle_type = random.choice(['rect', 'circle'])
            player_death_particles.append(DeathParticle(particle_x, particle_y, particle_size, particle_color, particle_vel_x, particle_vel_y, particle_type))
            
    def apply_boost(self):
        self.boosted_jump = True

class DeathParticle:
    def __init__(self, x, y, size, color, vel_x, vel_y, p_type):
        self.x = float(x)
        self.y = float(y)
        self.size = size
        self.color = color
        self.vel_x = float(vel_x)
        self.vel_y = float(vel_y)
        self.alpha = 255.0
        self.p_type = p_type

    def update(self, dt):
        dt_factor = dt / TARGET_FRAME_TIME_MS
        self.x += self.vel_x * dt_factor
        self.y += self.vel_y * dt_factor
        self.vel_y += (GRAVITY / 2) * dt_factor # Apply some gravity, scaled by dt
        self.alpha -= (255.0 / (1000.0 / FPS)) * dt_factor # Fade out proportionally to dt
        if self.alpha < 0:
            self.alpha = 0

    def draw(self, screen):
        if self.alpha > 0:
            # Create a surface with SRCALPHA for transparency
            surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            color_with_alpha = self.color + (int(self.alpha),)
            if self.p_type == 'rect':
                pygame.draw.rect(surf, color_with_alpha, (0, 0, self.size, self.size))
            elif self.p_type == 'circle':
                pygame.draw.circle(surf, color_with_alpha, (self.size // 2, self.size // 2), self.size // 2)
            screen.blit(surf, (int(self.x - self.size/2), int(self.y - self.size/2)))


class Obstacle:
    def __init__(self, x, y, width, height, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.is_cleared = False # For scoring, track if player has passed it
        self.is_falling_platform = False # For specific logic

    def update(self, scroll_amount):
        self.rect.x -= scroll_amount

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)

    def is_offscreen(self):
        return self.rect.right < 0

class ChunkyBlock(Obstacle):
    def __init__(self, x, height):
        width = random.randint(MIN_OBSTACLE_WIDTH, MAX_OBSTACLE_WIDTH)
        y = ground_y - height
        super().__init__(x, y, width, height, ORANGE)

class SpikyPit(Obstacle):
    def __init__(self, x):
        width = random.randint(PIT_MIN_WIDTH, PIT_MAX_WIDTH)
        # Pit itself is a gap, not drawn, but for collision/positioning, use a rect
        # The rect's height covers the ground area for simpler calculation.
        super().__init__(x, ground_y, width, GROUND_HEIGHT, BLACK)
        self.spike_color = RED
        self.spike_height = 10
        self.spike_width = 10

    def draw(self, screen):
        # Draw spikes at the top of the pit.
        spike_count = self.rect.width // self.spike_width
        for i in range(spike_count):
            spike_tip_x = self.rect.x + i * self.spike_width + self.spike_width // 2
            spike_base_left_x = self.rect.x + i * self.spike_width
            spike_base_right_x = self.rect.x + (i + 1) * self.spike_width
            spike_points = [
                (spike_tip_x, self.rect.y - self.spike_height),
                (spike_base_left_x, self.rect.y),
                (spike_base_right_x, self.rect.y)
            ]
            pygame.draw.polygon(screen, self.spike_color, spike_points)

class BouncyBlob(Obstacle):
    def __init__(self, x):
        radius = BOUNCY_BLOB_RADIUS
        width = radius * 2
        height = radius * 2
        # Position relative to ground, accounting for radius and some random height variation
        y_base = ground_y - radius * 2
        y_offset = random.randint(0, BOUNCY_BLOB_HEIGHT_RANGE)
        super().__init__(x, y_base - y_offset, width, height, GREEN)
        self.start_y = float(y_base - y_offset) # Store actual starting y for bobbing
        self.time_offset = random.uniform(0, math.pi * 2) # For varied bobbing
        self.radius_change = 0 # For pulsating effect

    def update(self, scroll_amount):
        super().update(scroll_amount)
        # Bobbing motion is time-based, unaffected by dt factor for visual consistency
        current_y_offset = math.sin(pygame.time.get_ticks() * BOUNCY_BLOB_SPEED + self.time_offset) * (BOUNCY_BLOB_HEIGHT_RANGE / 2)
        self.rect.y = int(self.start_y + current_y_offset)
        # Pulsating effect (slight radius change)
        self.radius_change = math.sin(pygame.time.get_ticks() * BOUNCY_BLOB_SPEED * 2 + self.time_offset) * 2 # Max 2 pixel change

    def draw(self, screen):
        current_radius = BOUNCY_BLOB_RADIUS + self.radius_change
        # Adjust center for drawing as rect.center is based on original rect, but y changes.
        draw_center_x = self.rect.x + self.rect.width // 2
        draw_center_y = self.rect.y + self.rect.height // 2
        pygame.draw.circle(screen, self.color, (int(draw_center_x), int(draw_center_y)), int(current_radius))

class WobblyWall(Obstacle):
    def __init__(self, x, height):
        width = random.randint(20, 40)
        y = ground_y - height
        super().__init__(x, y, width, height, PURPLE)
        self.wobble_magnitude = 5 # Max pixel deviation
        self.wobble_frequency = 0.005 # How fast it wobbles over time and space

    def update(self, scroll_amount):
        super().update(scroll_amount)

    def draw(self, screen):
        # Generate wobbly points dynamically for drawing
        points = []
        base_x = self.rect.x
        base_y = self.rect.y
        width = self.rect.width
        height = self.rect.height

        # Bottom two points (fixed)
        points.append((base_x, base_y + height))
        points.append((base_x + width, base_y + height))

        # Top points with wobble
        num_segments = 5
        for i in range(num_segments + 1):
            t = i / num_segments
            # Apply a sine wave wobble based on global time and current X position
            # This makes the wobble consistent for the wall as it moves
            wobble = math.sin((self.rect.centerx + pygame.time.get_ticks()) * self.wobble_frequency + i * math.pi / num_segments) * self.wobble_magnitude
            points.append((int(base_x + width * t + wobble), int(base_y + random.randint(-3, 3)))) # Random offset for jagged top

        # Reverse order of top points to form a valid polygon
        points[2:] = points[2:][::-1] # Reverse the order of top points for correct polygon
        pygame.draw.polygon(screen, self.color, points)

class HoveringGlider(Obstacle):
    def __init__(self, x):
        width = GLIDER_WIDTH
        height = GLIDER_HEIGHT
        y = ground_y - GLIDER_HEIGHT_OFFSET - random.randint(0, 50) - height # Float mid-air
        super().__init__(x, y, width, height, CYAN)

    def draw(self, screen):
        # Draw as a triangle
        points = [
            (self.rect.x, self.rect.y + self.rect.height),
            (self.rect.x + self.rect.width, self.rect.y + self.rect.height),
            (self.rect.x + self.rect.width // 2, self.rect.y)
        ]
        pygame.draw.polygon(screen, self.color, points)

class BoostPad(Obstacle):
    def __init__(self, x):
        width = 40
        height = 10
        y = ground_y - height
        super().__init__(x, y, width, height, YELLOW)
        self.arrow_color = BLUE

    def draw(self, screen):
        super().draw(screen) # Draw base rectangle
        # Draw upward-pointing triangle (arrow)
        arrow_points = [
            (self.rect.centerx, self.rect.y - 10),
            (self.rect.centerx - 8, self.rect.y + 5),
            (self.rect.centerx + 8, self.rect.y + 5)
        ]
        pygame.draw.polygon(screen, self.arrow_color, arrow_points)

class FallingPlatform(Obstacle):
    def __init__(self, x, height_offset=0):
        width = FALLING_PLATFORM_WIDTH
        height = FALLING_PLATFORM_HEIGHT
        y = ground_y - height - height_offset # Can appear at various heights
        super().__init__(x, y, width, height, GREY)
        self.is_falling_platform = True
        self.landed_on_timer = 0.0 # Use float for dt scaling
        self.landed_on = False
        self.original_color = GREY
        self.disappearing_color = DARK_GREY

    def player_landed(self):
        if not self.landed_on:
            self.landed_on = True
            self.landed_on_timer = FALLING_PLATFORM_DISAPPEAR_TIME

    def update(self, scroll_amount):
        super().update(scroll_amount)
        if self.landed_on:
            self.landed_on_timer -= clock.get_time() # dt is already `clock.get_time()`
            if self.landed_on_timer <= 0:
                self.rect.y += int(scroll_amount * 2) # Simulate falling quickly off screen
                self.color = self.disappearing_color # Change color as it disappears
        
    def draw(self, screen):
        # Flash or change color when about to disappear
        if self.landed_on and self.landed_on_timer > 0:
            if int(self.landed_on_timer / 100) % 2 == 0:
                pygame.draw.rect(screen, self.original_color, self.rect)
            else:
                pygame.draw.rect(screen, self.disappearing_color, self.rect)
        else:
            pygame.draw.rect(screen, self.color, self.rect)


class BackgroundElement:
    def __init__(self, x, y, speed_multiplier, color):
        self.x = float(x) # Ensure float for smooth movement
        self.y = float(y)
        self.speed_multiplier = speed_multiplier
        self.color = color

    def update(self, scroll_amount):
        self.x -= scroll_amount * self.speed_multiplier
    
    def is_offscreen(self):
        return self.x < -200 # A bit generous for large elements

    def draw(self, screen):
        pass # Abstract method


class BackgroundCloud(BackgroundElement):
    def __init__(self):
        x = WIDTH + random.randint(0, WIDTH // 2)
        y = random.randint(50, HEIGHT // 3)
        super().__init__(x, y, random.uniform(0.1, 0.3), WHITE)
        self.radius = random.randint(20, 40)
        self.offset = random.randint(10, 20)

    def draw(self, screen):
        alpha = 100 # Semi-transparent
        s = pygame.Surface((self.radius * 3, self.radius * 2), pygame.SRCALPHA)
        s.fill((0,0,0,0)) # Transparent background
        
        c = self.color + (alpha,)
        
        pygame.draw.circle(s, c, (self.radius, self.radius), self.radius)
        pygame.draw.circle(s, c, (self.radius + self.offset, self.radius - self.offset//2), self.radius * 0.8)
        pygame.draw.circle(s, c, (self.radius - self.offset, self.radius + self.offset//2), self.radius * 0.9)
        # Main body for a more cloud-like shape
        pygame.draw.rect(s, c, (self.radius - self.offset, self.radius - self.offset//2, self.radius + self.offset, self.radius + self.offset))
        screen.blit(s, (int(self.x), int(self.y)))


class BackgroundTree(BackgroundElement):
    def __init__(self, zone_bg_color):
        x = WIDTH + random.randint(0, WIDTH // 2)
        y = ground_y - random.randint(80, 150)
        super().__init__(x, y, random.uniform(0.2, 0.4), zone_bg_color)
        self.width = random.randint(20, 40)
        self.height = ground_y - self.y # Tree grows up from the ground

    def draw(self, screen):
        # Simple green rectangular tree
        pygame.draw.rect(screen, self.color, (int(self.x), int(self.y), self.width, int(self.height)))
        # Brown trunk
        pygame.draw.rect(screen, BROWN, (int(self.x + self.width / 3), int(self.y + self.height * 0.7), int(self.width / 3), int(self.height * 0.3)))


class BackgroundVine(BackgroundElement):
    def __init__(self, zone_bg_color):
        x = WIDTH + random.randint(0, WIDTH // 2)
        y = random.randint(HEIGHT // 2, ground_y - 50)
        super().__init__(x, y, random.uniform(0.3, 0.5), zone_bg_color)
        self.segment_count = random.randint(5, 10)
        self.initial_points = []
        self._generate_vine_points()

    def _generate_vine_points(self):
        self.initial_points = []
        current_x = 0
        current_y = 0
        for i in range(self.segment_count):
            self.initial_points.append((current_x, current_y))
            current_x += random.randint(10, 20)
            current_y += random.randint(-15, 15)
        self.thickness = random.randint(2, 4)

    def update(self, scroll_amount):
        super().update(scroll_amount)

    def draw(self, screen):
        # Draw a twisted line-art vine
        for i in range(len(self.initial_points) - 1):
            start_point_local = self.initial_points[i]
            end_point_local = self.initial_points[i+1]
            pygame.draw.line(screen, self.color, 
                             (int(self.x + start_point_local[0]), int(self.y + start_point_local[1])), 
                             (int(self.x + end_point_local[0]), int(self.y + end_point_local[1])), 
                             self.thickness)


class BackgroundFoliage(BackgroundElement):
    def __init__(self, zone_bg_color):
        x = WIDTH + random.randint(0, WIDTH // 2)
        y = ground_y - random.randint(40, 100)
        super().__init__(x, y, random.uniform(0.4, 0.6), zone_bg_color)
        self.initial_points = [] # Store points relative to self.x, self.y
        self._generate_foliage_points()

    def _generate_foliage_points(self):
        self.initial_points = []
        width = random.randint(50, 100)
        height = random.randint(30, 60)
        
        self.initial_points.append((0, height)) # Bottom-left
        self.initial_points.append((width, height)) # Bottom-right
        # Top irregular points
        self.initial_points.append((width * 0.7 + random.randint(-5,5), height * 0.2 + random.randint(-10,10)))
        self.initial_points.append((width * 0.3 + random.randint(-5,5), height * 0.1 + random.randint(-10,10)))
        self.initial_points.append((random.randint(0,10), height * 0.3 + random.randint(-10,10)))

    def draw(self, screen):
        # Translate initial_points by current self.x and self.y
        current_points = [(int(p[0] + self.x), int(p[1] + self.y)) for p in self.initial_points]
        pygame.draw.polygon(screen, self.color, current_points)


class BackgroundCliff(BackgroundElement):
    def __init__(self, zone_bg_color):
        x = WIDTH + random.randint(0, WIDTH // 2)
        y = ground_y - random.randint(50, 150)
        super().__init__(x, y, random.uniform(0.5, 0.7), zone_bg_color)
        self.initial_points = []
        self._generate_cliff_points()

    def _generate_cliff_points(self):
        self.initial_points = []
        width = random.randint(100, 200)
        height = ground_y - self.y # This height calculation assumes self.y is the top of the cliff
        
        # Bottom two corners (along relative ground)
        self.initial_points.append((0, ground_y - self.y)) # Relative to self.y (top of cliff)
        self.initial_points.append((width, ground_y - self.y))
        # Top jagged edges
        for i in range(random.randint(3, 6)):
            px = random.randint(0, width)
            py = random.randint(0, int(height // 2))
            self.initial_points.append((px, py))
        
        # Sort by x for jagged top, but ensure bottom points remain first
        top_points = sorted(self.initial_points[2:], key=lambda p: p[0])
        self.initial_points = self.initial_points[:2] + top_points

    def draw(self, screen):
        # Translate initial_points by current self.x and self.y
        current_points = [(int(p[0] + self.x), int(p[1] + self.y)) for p in self.initial_points]
        pygame.draw.polygon(screen, self.color, current_points)


ZONE_DATA = {
    0: { # Wobble Woods
        "sky_color": LIGHT_BLUE,
        "ground_color": BROWN,
        "bg_elements_color": (50, 150, 50), # Green for trees
        "speed_multiplier": 1.0,
        "obstacle_types": ["chunky_block", "spiky_pit", "bouncy_blob"],
        "bg_element_func": BackgroundTree,
    },
    1: { # Squiggle Swamps
        "sky_color": MURKY_BLUE,
        "ground_color": SWAMP_GREEN,
        "bg_elements_color": (100, 70, 50), # Darker for twisted vines
        "speed_multiplier": 1.15,
        "obstacle_types": ["chunky_block", "spiky_pit", "bouncy_blob", "wobbly_wall"],
        "bg_element_func": BackgroundVine,
    },
    2: { # Jittery Jungles
        "sky_color": DEEP_BLUE,
        "ground_color": JUNGLE_GREEN,
        "bg_elements_color": (80, 180, 80), # Lighter for foliage
        "speed_multiplier": 1.30,
        "obstacle_types": ["chunky_block", "spiky_pit", "bouncy_blob", "wobbly_wall", "hovering_glider", "boost_pad"],
        "bg_element_func": BackgroundFoliage,
    },
    3: { # Fidgety Falls
        "sky_color": DARK_PURPLISH_BLUE,
        "ground_color": ROCKY_GREY,
        "bg_elements_color": (90, 90, 100), # Cliffs/Canyons
        "speed_multiplier": 1.50, # Initial speed multiplier for this zone, speed continues to accelerate
        "obstacle_types": ["chunky_block", "spiky_pit", "bouncy_blob", "wobbly_wall", "hovering_glider", "boost_pad", "falling_platform"],
        "bg_element_func": BackgroundCliff,
    }
}
current_zone_index = 0
current_zone_data = ZONE_DATA[current_zone_index]


def reset_game():
    global current_score, game_state, obstacles, scroll_speed, background_elements, player_death_particles, current_zone_index, current_zone_data, player, last_score_time

    if player is None: # Initialize player if it's the very first call
        player = Player()
    else:
        player.reset()

    obstacles.clear()
    background_elements.clear()
    player_death_particles.clear()
    current_score = 0
    game_state = GAME_STATE_PLAYING
    scroll_speed = BASE_SCROLL_SPEED # Reset base scroll speed
    current_zone_index = 0
    current_zone_data = ZONE_DATA[current_zone_index]
    last_score_time = pygame.time.get_ticks() # Reset score timer too

    # Spawn initial background elements
    for _ in range(5): # Populate with a few clouds
        background_elements.append(BackgroundCloud())
    if current_zone_data["bg_element_func"]:
        for _ in range(5): # Populate with zone-specific elements
            background_elements.append(current_zone_data["bg_element_func"](current_zone_data["bg_elements_color"]))

def spawn_obstacle():
    # Find the rightmost edge of existing obstacles that are still visible
    rightmost_active_obstacle_edge = 0
    if obstacles:
        rightmost_active_obstacle_edge = max([o.rect.right for o in obstacles])

    # Ensure new obstacle is spawned after a minimum gap from the rightmost active obstacle,
    # and at least WIDTH if no obstacles are present.
    new_obstacle_x = max(WIDTH + 50, rightmost_active_obstacle_edge + random.randint(MIN_OBSTACLE_GAP, MAX_OBSTACLE_GAP))

    # Optimization: Check if there's enough space relative to the last spawned obstacle.
    # This prevents over-spawning, especially after combo obstacles.
    if new_obstacle_x - rightmost_active_obstacle_edge < OBSTACLE_SPAWN_INTERVAL:
         return # Not enough room yet

    obstacle_types = current_zone_data["obstacle_types"]
    
    # Prioritize combination for advanced zones
    if current_zone_index >= 2 and random.random() < 0.4: # 40% chance for a complex combo
        combo_type = random.choice(["block_glider", "pit_glider", "block_wall"])
        if combo_type == "block_glider":
            block_height = random.randint(MIN_OBSTACLE_HEIGHT, MAX_OBSTACLE_HEIGHT // 2)
            obstacles.append(ChunkyBlock(new_obstacle_x, block_height))
            obstacles.append(HoveringGlider(new_obstacle_x + random.randint(block_height + 20, block_height + 50)))
        elif combo_type == "pit_glider":
            obstacles.append(SpikyPit(new_obstacle_x))
            obstacles.append(HoveringGlider(new_obstacle_x + PIT_MIN_WIDTH // 2 + random.randint(20, 50)))
        elif combo_type == "block_wall":
            obstacles.append(ChunkyBlock(new_obstacle_x, random.randint(MIN_OBSTACLE_HEIGHT, MAX_OBSTACLE_HEIGHT // 2)))
            obstacles.append(WobblyWall(new_obstacle_x + random.randint(60, 100), random.randint(MIN_OBSTACLE_HEIGHT, MAX_OBSTACLE_HEIGHT)))
    else: # Normal single obstacle spawn
        chosen_type = random.choice(obstacle_types)

        if chosen_type == "chunky_block":
            height = random.randint(MIN_OBSTACLE_HEIGHT, MAX_OBSTACLE_HEIGHT)
            obstacles.append(ChunkyBlock(new_obstacle_x, height))
        elif chosen_type == "spiky_pit":
            obstacles.append(SpikyPit(new_obstacle_x))
        elif chosen_type == "bouncy_blob":
            obstacles.append(BouncyBlob(new_obstacle_x))
        elif chosen_type == "wobbly_wall":
            height = random.randint(MIN_OBSTACLE_HEIGHT, MAX_OBSTACLE_HEIGHT)
            obstacles.append(WobblyWall(new_obstacle_x, height))
        elif chosen_type == "hovering_glider":
            obstacles.append(HoveringGlider(new_obstacle_x))
        elif chosen_type == "boost_pad":
            obstacles.append(BoostPad(new_obstacle_x))
        elif chosen_type == "falling_platform":
            obstacles.append(FallingPlatform(new_obstacle_x, random.randint(0, 50))) # Vary height slightly


def check_zone_transition():
    global current_zone_index, current_zone_data, scroll_speed, background_elements
    
    new_zone_index = current_zone_index
    if current_zone_index == 0 and current_score >= ZONE_2_SCORE:
        new_zone_index = 1
    elif current_zone_index == 1 and current_score >= ZONE_3_SCORE:
        new_zone_index = 2
    elif current_zone_index == 2 and current_score >= ZONE_4_SCORE:
        new_zone_index = 3
    
    if new_zone_index != current_zone_index:
        current_zone_index = new_zone_index
        current_zone_data = ZONE_DATA[current_zone_index]
        
        # Clear and repopulate some background elements for the new zone
        # Keep some clouds and existing elements that are still on screen for smooth transition
        background_elements = [be for be in background_elements if isinstance(be, BackgroundCloud) and be.x < WIDTH and random.random() < 0.5] # Keep some clouds
        if current_zone_data["bg_element_func"]:
            for _ in range(5): # Add new elements specific to the zone
                background_elements.append(current_zone_data["bg_element_func"](current_zone_data["bg_elements_color"]))


def display_game_over(screen, final_score, high_score_val):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180)) # Semi-transparent black
    screen.blit(overlay, (0, 0))

    font_large = pygame.font.Font(None, 80)
    font_medium = pygame.font.Font(None, 50)

    game_over_text = font_large.render("GAME OVER", True, RED)
    final_score_text = font_medium.render(f"FINAL SCORE: {final_score}", True, WHITE)
    high_score_text = font_medium.render(f"HIGH SCORE: {high_score_val}", True, YELLOW)
    restart_text = font_medium.render("Press R to Restart", True, WHITE)

    screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 100))
    screen.blit(final_score_text, (WIDTH // 2 - final_score_text.get_width() // 2, HEIGHT // 2 - 20))
    screen.blit(high_score_text, (WIDTH // 2 - high_score_text.get_width() // 2, HEIGHT // 2 + 30))
    screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 100))


def main():
    global current_score, high_score, game_state, scroll_speed, background_elements, player_death_particles, player, last_score_time

    # Load high score from a file if needed, otherwise keep in memory
    try:
        with open("highscore.txt", "r") as f:
            high_score = int(f.read())
    except (FileNotFoundError, ValueError):
        high_score = 0

    reset_game() # Initial setup for player, obstacles, score, etc.

    running = True

    while running:
        dt = clock.tick(FPS) # dt is time in milliseconds since last tick

        # Factor to scale per-frame values by delta time
        dt_factor = dt / TARGET_FRAME_TIME_MS
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if game_state == GAME_STATE_PLAYING:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        player.start_jump()
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_SPACE:
                        player.end_jump()
            elif game_state == GAME_STATE_GAME_OVER:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r: # Press R to restart
                        if current_score > high_score:
                            high_score = current_score
                            try:
                                with open("highscore.txt", "w") as f:
                                    f.write(str(high_score))
                            except Exception:
                                pass # Failed to save high score
                        reset_game()

        # --- Update ---
        if game_state == GAME_STATE_PLAYING:
            player.update(dt)

            # Update scroll speed based on zone and time
            zone_speed_multiplier = current_zone_data["speed_multiplier"]
            # Small constant increase over time, scaled by dt_factor for smoothness
            time_based_speed_increase = (pygame.time.get_ticks() / 100000.0)
            scroll_speed = BASE_SCROLL_SPEED * zone_speed_multiplier + time_based_speed_increase
            
            # Calculate actual scroll amount for this frame
            actual_scroll_amount = scroll_speed * dt_factor

            # Score update (time-based)
            if pygame.time.get_ticks() - last_score_time >= TIME_SCORE_INTERVAL_MS:
                current_score += 1
                last_score_time = pygame.time.get_ticks()

            # Update obstacles
            for obstacle in list(obstacles): # Use list() to allow modification during iteration
                obstacle.update(actual_scroll_amount)
                if obstacle.is_offscreen():
                    obstacles.remove(obstacle)

            # Spawn new obstacles
            current_rightmost_obstacle_edge = 0
            if obstacles:
                current_rightmost_obstacle_edge = max([o.rect.right for o in obstacles])
            
            # Spawn if there's enough room between the rightmost obstacle and the edge of the screen
            if current_rightmost_obstacle_edge < WIDTH + OBSTACLE_SPAWN_INTERVAL:
                spawn_obstacle()

            # Update background elements
            for element in list(background_elements): # Use list() to allow modification during iteration
                element.update(actual_scroll_amount)
                if element.is_offscreen():
                    background_elements.remove(element)
                    # Randomly add new background elements when one goes off-screen
                    if isinstance(element, BackgroundCloud):
                        background_elements.append(BackgroundCloud())
                    elif current_zone_data["bg_element_func"]:
                        background_elements.append(current_zone_data["bg_element_func"](current_zone_data["bg_elements_color"]))

            # Check collisions
            player_rect = player.get_rect()
            for obstacle in list(obstacles): # Use list() for safe removal
                # Only check collision if player is alive
                if player.is_dead:
                    break # No need to check further if player is already dead

                # Pit collision: player's horizontal position overlaps pit, AND player's bottom is below top of pit (or spike line)
                if isinstance(obstacle, SpikyPit):
                    # Create a rect for the visible part of the pit including spikes
                    pit_collision_rect_spikes = pygame.Rect(obstacle.rect.x, obstacle.rect.y - obstacle.spike_height, obstacle.rect.width, obstacle.spike_height)
                    if player_rect.colliderect(pit_collision_rect_spikes):
                        if not player.is_dead:
                            player.die()
                            game_state = GAME_STATE_GAME_OVER
                            continue
                    # Check if player falls into the actual gap
                    if player_rect.centerx > obstacle.rect.left and player_rect.centerx < obstacle.rect.right:
                        if player_rect.bottom >= obstacle.rect.y + 1: # Player is over the pit and below ground level
                            if not player.is_dead:
                                player.die()
                                game_state = GAME_STATE_GAME_OVER
                                continue
                    
                    # Score for clearing pit: player has passed the pit horizontally
                    if not obstacle.is_cleared and player_rect.left > obstacle.rect.right: # Player is fully past the pit
                        # Perfect jump over pit: player's lowest point during jump was close to pit's top (spike line)
                        if player_rect.bottom < obstacle.rect.y - obstacle.spike_height + PERFECT_JUMP_THRESHOLD and player_rect.bottom > obstacle.rect.y - obstacle.spike_height - (player_rect.height * 0.5):
                            current_score += PERFECT_JUMP_BONUS
                        else:
                            current_score += OBSTACLE_CLEAR_BONUS
                        obstacle.is_cleared = True
                    continue # Pit handled, skip general rect collision for this obstacle

                # BoostPad collision: only count as landing if player is falling (vel_y > 0)
                if isinstance(obstacle, BoostPad):
                    if player_rect.colliderect(obstacle.rect):
                        # Check if player is landing on top of the pad
                        if player.vel_y > 0 and player_rect.bottom >= obstacle.rect.top and player_rect.top < obstacle.rect.top + (player_rect.height / 2):
                            player.y = obstacle.rect.y - player_rect.height # Place player on top
                            player.vel_y = 0.0
                            player.on_ground = True
                            player.apply_boost()
                            obstacles.remove(obstacle) # Consume boost pad
                            current_score += OBSTACLE_CLEAR_BONUS # Count as clearing
                            continue # BoostPad consumed, move to next obstacle
                        else: # Hit from side or bottom
                            player.die()
                            game_state = GAME_STATE_GAME_OVER
                            continue

                # FallingPlatform collision: similar to BoostPad, must land on top
                if isinstance(obstacle, FallingPlatform):
                    if player_rect.colliderect(obstacle.rect):
                        # Check if player is landing on top
                        if player.vel_y > 0 and player_rect.bottom >= obstacle.rect.top and player_rect.top < obstacle.rect.top + (player_rect.height / 2):
                            player.y = obstacle.rect.y - player_rect.height # Place player on top
                            player.vel_y = 0.0
                            player.on_ground = True
                            obstacle.player_landed()
                            # Check for perfect jump on platform
                            if not obstacle.is_cleared and player_rect.bottom < obstacle.rect.top + PERFECT_JUMP_THRESHOLD:
                                current_score += PERFECT_JUMP_BONUS
                            else:
                                current_score += OBSTACLE_CLEAR_BONUS
                            obstacle.is_cleared = True
                            continue # Platform handled, move to next obstacle
                        else: # Hit from side or bottom
                            player.die()
                            game_state = GAME_STATE_GAME_OVER
                            continue

                # General obstacle collision (for ChunkyBlock, BouncyBlob, WobblyWall, HoveringGlider)
                if player_rect.colliderect(obstacle.rect):
                    if not player.is_dead: # Ensure player isn't already marked dead
                        player.die()
                        game_state = GAME_STATE_GAME_OVER
                        continue # Collision found, no need to check other obstacles

                # Score for clearing general solid obstacles: player has passed the obstacle horizontally
                # This should only trigger once per obstacle
                if not obstacle.is_cleared and player_rect.left > obstacle.rect.right:
                    if player_rect.bottom < obstacle.rect.top + PERFECT_JUMP_THRESHOLD and player_rect.bottom > obstacle.rect.top - (player_rect.height * 0.5): # Not too high
                        current_score += PERFECT_JUMP_BONUS
                    else:
                        current_score += OBSTACLE_CLEAR_BONUS
                    obstacle.is_cleared = True

            # Update and clean up death particles
            for particle in list(player_death_particles):
                particle.update(dt)
                if particle.alpha <= 0:
                    player_death_particles.remove(particle)

            check_zone_transition()


        # --- Draw ---
        # Sky
        screen.fill(current_zone_data["sky_color"])

        # Background elements
        for element in background_elements:
            element.draw(screen)

        # Ground
        pygame.draw.rect(screen, current_zone_data["ground_color"], (0, ground_y, WIDTH, HEIGHT - ground_y))

        # Obstacles
        for obstacle in obstacles:
            obstacle.draw(screen)

        # Player
        if player: # Ensure player object exists before drawing
            player.draw(screen)

        # Death particles
        for particle in player_death_particles:
            particle.draw(screen)

        # UI
        font_score = pygame.font.Font(None, 40)
        score_text = font_score.render(f"SCORE: {current_score}", True, WHITE)
        high_score_text = font_score.render(f"HIGH: {high_score}", True, YELLOW)
        zone_text = font_score.render(f"ZONE: {current_zone_index + 1}", True, WHITE)

        screen.blit(score_text, (20, 20))
        screen.blit(high_score_text, (WIDTH - high_score_text.get_width() - 20, 20))
        screen.blit(zone_text, (WIDTH // 2 - zone_text.get_width() // 2, 20))

        if game_state == GAME_STATE_GAME_OVER:
            display_game_over(screen, current_score, high_score)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()