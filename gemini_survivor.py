import pygame
import random
import math

# --- 常量 ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
PLAYER_SIZE = 40
ENEMY_SIZE = 30
TANK_ENEMY_SIZE = 50
BOSS_ENEMY_SIZE = 100 # 新增：Boss敌人尺寸
ORBIT_WEAPON_SIZE = 20
XP_GEM_SIZE = 15
PROJECTILE_SIZE = 10
BEAM_WIDTH = 20 # 新增：光束武器宽度
BEAM_LENGTH = SCREEN_WIDTH # 新增：光束武器长度

# --- 玩家初始属性 ---
PLAYER_INITIAL_SPEED = 5
PLAYER_INITIAL_HEALTH = 100

# --- 敌人初始属性 ---
ENEMY_INITIAL_SPEED = 2
ENEMY_SPAWN_RATE = 1000

# --- 武器初始属性 ---
ORBIT_WEAPON_INITIAL_RADIUS = 100
ORBIT_WEAPON_INITIAL_SPEED = 0.1
PROJECTILE_WEAPON_INITIAL_COOLDOWN = 1200
PROJECTILE_SPEED = 10
BEAM_WEAPON_INITIAL_COOLDOWN = 5000 # 新增：光束武器初始冷却时间

# --- 颜色 ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
GREY = (100, 100, 100)
CYAN = (0, 255, 255)
PURPLE = (128, 0, 128)
DARK_GREEN = (0, 100, 0)
ORANGE = (255, 165, 0) # 新增：Boss敌人颜色
GOLD = (255, 215, 0) # 新增：宝箱颜色

# --- 玩家类 ---
class Player(pygame.sprite.Sprite):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.image = pygame.Surface([PLAYER_SIZE, PLAYER_SIZE])
        self.image.fill(BLUE)
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        
        self.speed = PLAYER_INITIAL_SPEED
        self.max_health = PLAYER_INITIAL_HEALTH
        self.health = self.max_health
        self.level = 1
        self.experience = 0
        self.experience_to_next_level = 10
        self.last_move_dir = pygame.math.Vector2(0, -1) # 新增：用于光束武器

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.game.game_over = True

    def heal(self, amount):
        self.health += amount
        if self.health > self.max_health: self.health = self.max_health

    def gain_experience(self, amount):
        self.experience += amount
        while self.experience >= self.experience_to_next_level:
            self.level_up()
    
    def gain_levels(self, amount):
        """ 用于宝箱奖励，直接提升多个等级 """
        for _ in range(amount):
            self.level_up()

    def level_up(self):
        self.level += 1
        self.experience -= self.experience_to_next_level
        self.experience_to_next_level = int(self.experience_to_next_level * 1.5)
        self.game.level_up_state = True

    def update(self):
        move_dir = pygame.math.Vector2(0, 0)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: move_dir.x = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: move_dir.x = 1
        if keys[pygame.K_UP] or keys[pygame.K_w]: move_dir.y = -1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: move_dir.y = 1

        if move_dir.length_squared() > 0:
            move_dir.normalize_ip()
            self.last_move_dir = move_dir.copy()
            self.rect.move_ip(move_dir * self.speed)

        if self.rect.left < 0: self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH: self.rect.right = SCREEN_WIDTH
        if self.rect.top < 0: self.rect.top = 0
        if self.rect.bottom > SCREEN_HEIGHT: self.rect.bottom = SCREEN_HEIGHT

# --- 敌人基类 ---
class Enemy(pygame.sprite.Sprite):
    def __init__(self, player, speed):
        super().__init__()
        self.player = player
        self.speed = speed
        self.health = 1
        self.damage = 10
        self.xp_value = 5
        self.image = pygame.Surface([ENEMY_SIZE, ENEMY_SIZE])
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.spawn_at_edge()

    def spawn_at_edge(self):
        side = random.choice(['top', 'bottom', 'left', 'right'])
        if side == 'top': self.rect.midbottom = (random.randint(0, SCREEN_WIDTH), 0)
        elif side == 'bottom': self.rect.midtop = (random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT)
        elif side == 'left': self.rect.midright = (0, random.randint(0, SCREEN_HEIGHT))
        else: self.rect.midleft = (SCREEN_WIDTH, random.randint(0, SCREEN_HEIGHT))

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.kill()
            return True
        return False

    def update(self):
        direction = pygame.math.Vector2(self.player.rect.center) - self.rect.center
        if direction.length_squared() > 0:
            direction.normalize_ip()
            self.rect.move_ip(direction * self.speed)

class TankEnemy(Enemy):
    def __init__(self, player, speed):
        super().__init__(player, speed)
        self.health = 5
        self.speed = speed * 0.7
        self.xp_value = 20
        self.damage = 25
        self.image = pygame.Surface([TANK_ENEMY_SIZE, TANK_ENEMY_SIZE])
        self.image.fill(PURPLE)
        self.rect = self.image.get_rect()
        self.spawn_at_edge()

class BossEnemy(Enemy):
    def __init__(self, player, speed):
        super().__init__(player, speed)
        self.health = 100
        self.speed = speed * 0.5
        self.xp_value = 200
        self.damage = 50
        self.image = pygame.Surface([BOSS_ENEMY_SIZE, BOSS_ENEMY_SIZE])
        self.image.fill(ORANGE)
        self.rect = self.image.get_rect()
        self.spawn_at_edge()

# --- 武器类 ---
class OrbitWeapon(pygame.sprite.Sprite):
    def __init__(self, player):
        super().__init__()
        self.player = player
        self.image = pygame.Surface([ORBIT_WEAPON_SIZE, ORBIT_WEAPON_SIZE])
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.angle = 0
        self.radius = ORBIT_WEAPON_INITIAL_RADIUS
        self.speed = ORBIT_WEAPON_INITIAL_SPEED
        self.damage = 10

    def update(self):
        self.angle += self.speed
        self.rect.center = self.player.rect.center + pygame.math.Vector2(self.radius, 0).rotate_rad(self.angle)

class ProjectileWeapon(pygame.sprite.Sprite):
    def __init__(self, player, game):
        super().__init__()
        self.player = player
        self.game = game
        self.cooldown = PROJECTILE_WEAPON_INITIAL_COOLDOWN
        self.last_shot_time = pygame.time.get_ticks()
        self.image = pygame.Surface([1, 1], pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=player.rect.center)

    def update(self):
        self.rect.center = self.player.rect.center
        now = pygame.time.get_ticks()
        if now - self.last_shot_time > self.cooldown:
            self.shoot()
            self.last_shot_time = now

    def find_nearest_enemy(self):
        return min(self.game.enemies, key=lambda e: pygame.math.Vector2(e.rect.center).distance_squared_to(self.player.rect.center), default=None)

    def shoot(self):
        target = self.find_nearest_enemy()
        if target:
            self.game.add_sprite(Projectile(self.rect.center, target.rect.center), self.game.projectiles)

class Projectile(pygame.sprite.Sprite):
    def __init__(self, start_pos, target_pos):
        super().__init__()
        self.image = pygame.Surface([PROJECTILE_SIZE, PROJECTILE_SIZE])
        self.image.fill(CYAN)
        self.rect = self.image.get_rect(center=start_pos)
        self.damage = 1
        direction = pygame.math.Vector2(target_pos) - start_pos
        if direction.length_squared() > 0:
            self.velocity = direction.normalize() * PROJECTILE_SPEED
        else:
            self.velocity = pygame.math.Vector2(0, -PROJECTILE_SPEED)

    def update(self):
        self.rect.move_ip(self.velocity)
        if not self.rect.colliderect(self.game.screen.get_rect()): self.kill()

class DirectionalBeamWeapon(pygame.sprite.Sprite):
    def __init__(self, player, game):
        super().__init__()
        self.player = player
        self.game = game
        self.cooldown = BEAM_WEAPON_INITIAL_COOLDOWN
        self.damage = 3
        self.last_shot_time = pygame.time.get_ticks()
        self.image = pygame.Surface([1, 1], pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=player.rect.center)

    def update(self):
        self.rect.center = self.player.rect.center
        now = pygame.time.get_ticks()
        if now - self.last_shot_time > self.cooldown:
            self.shoot()
            self.last_shot_time = now

    def shoot(self):
        self.game.add_sprite(Beam(self.player, self.damage), self.game.beams)

class Beam(pygame.sprite.Sprite):
    def __init__(self, player, damage):
        super().__init__()
        self.player = player
        self.damage = damage
        self.direction = player.last_move_dir.copy()
        angle = self.direction.angle_to(pygame.math.Vector2(1, 0))
        
        self.image = pygame.Surface([BEAM_LENGTH, BEAM_WIDTH], pygame.SRCALPHA)
        self.image.fill(YELLOW)
        self.image = pygame.transform.rotate(self.image, angle)
        
        self.rect = self.image.get_rect(center=player.rect.center)
        self.spawn_time = pygame.time.get_ticks()
        self.duration = 250 # 光束持续时间（毫秒）
        self.hit_enemies = set() # 防止对同一敌人造成多次伤害

    def update(self):
        if pygame.time.get_ticks() - self.spawn_time > self.duration:
            self.kill()

# --- 掉落物类 ---
class ExperienceGem(pygame.sprite.Sprite):
    def __init__(self, pos, value):
        super().__init__()
        self.image = pygame.Surface([XP_GEM_SIZE, XP_GEM_SIZE])
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect(center=pos)
        self.xp_value = value

class TreasureChest(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface([40, 40])
        self.image.fill(GOLD)
        self.rect = self.image.get_rect(center=pos)

# --- 游戏主类 ---
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("类吸血鬼幸存者游戏 - Boss与光束")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 50)
        self.small_font = pygame.font.Font(None, 36)
        self.running = True
        self.setup_game()

    def add_sprite(self, sprite, *groups):
        """ 辅助函数，用于将精灵添加到 all_sprites 和其他组 """
        sprite.game = self # 确保所有精灵都能访问游戏对象
        self.all_sprites.add(sprite)
        for group in groups:
            group.add(sprite)

    def setup_game(self):
        self.game_over = False
        self.level_up_state = False
        self.score = 0
        self.start_time = pygame.time.get_ticks()
        self.enemy_current_speed = ENEMY_INITIAL_SPEED
        self.enemy_current_spawn_rate = ENEMY_SPAWN_RATE
        
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.weapons = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.beams = pygame.sprite.Group() # 新增：光束精灵组
        self.experience_gems = pygame.sprite.Group()
        self.treasure_chests = pygame.sprite.Group() # 新增：宝箱精灵组

        self.player = Player(self)
        self.add_sprite(self.player)
        
        self.orbit_weapon = OrbitWeapon(self.player)
        self.projectile_weapon = ProjectileWeapon(self.player, self)
        self.beam_weapon = DirectionalBeamWeapon(self.player, self)
        self.add_sprite(self.orbit_weapon, self.weapons)
        self.add_sprite(self.projectile_weapon)
        self.add_sprite(self.beam_weapon)

        self.enemy_spawn_timer = pygame.USEREVENT + 1
        pygame.time.set_timer(self.enemy_spawn_timer, self.enemy_current_spawn_rate)
        self.difficulty_timer = pygame.USEREVENT + 2
        pygame.time.set_timer(self.difficulty_timer, 20000)
        self.boss_spawn_timer = pygame.USEREVENT + 3 # 新增：Boss生成计时器
        pygame.time.set_timer(self.boss_spawn_timer, 120000) # 每2分钟

    def run(self):
        while self.running:
            self.events()
            if not self.game_over and not self.level_up_state:
                self.update()
            self.draw()
            self.clock.tick(60)
        pygame.quit()

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False
            if self.game_over:
                if event.type == pygame.KEYDOWN: self.setup_game()
                continue
            if self.level_up_state:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_1, pygame.K_KP_1): self.apply_upgrade(1)
                    elif event.key in (pygame.K_2, pygame.K_KP_2): self.apply_upgrade(2)
                    elif event.key in (pygame.K_3, pygame.K_KP_3): self.apply_upgrade(3)
                    elif event.key in (pygame.K_4, pygame.K_KP_4): self.apply_upgrade(4)
                    elif event.key in (pygame.K_5, pygame.K_KP_5): self.apply_upgrade(5)
                continue

            if event.type == self.enemy_spawn_timer:
                if random.random() < 0.2: self.add_sprite(TankEnemy(self.player, self.enemy_current_speed), self.enemies)
                else: self.add_sprite(Enemy(self.player, self.enemy_current_speed), self.enemies)
            if event.type == self.difficulty_timer: self.increase_difficulty()
            if event.type == self.boss_spawn_timer: self.add_sprite(BossEnemy(self.player, self.enemy_current_speed), self.enemies)

    def increase_difficulty(self):
        self.enemy_current_speed *= 1.1
        self.enemy_current_spawn_rate = max(200, int(self.enemy_current_spawn_rate * 0.9))
        pygame.time.set_timer(self.enemy_spawn_timer, self.enemy_current_spawn_rate)

    def apply_upgrade(self, choice):
        if choice == 1: self.player.speed += 1
        elif choice == 2: self.projectile_weapon.cooldown = max(100, int(self.projectile_weapon.cooldown * 0.85))
        elif choice == 3: self.beam_weapon.cooldown = max(1000, int(self.beam_weapon.cooldown * 0.9))
        elif choice == 4: self.player.max_health += 20; self.player.heal(20)
        elif choice == 5: self.player.heal(self.player.max_health * 0.3)
        self.level_up_state = False

    def handle_enemy_death(self, enemy):
        self.score += 1
        if isinstance(enemy, BossEnemy):
            self.add_sprite(TreasureChest(enemy.rect.center), self.treasure_chests)
        else:
            self.add_sprite(ExperienceGem(enemy.rect.center, enemy.xp_value), self.experience_gems)

    def update(self):
        self.all_sprites.update()
        
        # 碰撞检测
        for weapon in self.weapons:
            for enemy in pygame.sprite.spritecollide(weapon, self.enemies, False):
                if enemy.take_damage(weapon.damage): self.handle_enemy_death(enemy)
        
        for projectile in self.projectiles:
            for enemy in pygame.sprite.spritecollide(projectile, self.enemies, False):
                projectile.kill()
                if enemy.take_damage(projectile.damage): self.handle_enemy_death(enemy)
                break
        
        for beam in self.beams:
            for enemy in pygame.sprite.spritecollide(beam, self.enemies, False):
                if enemy not in beam.hit_enemies:
                    beam.hit_enemies.add(enemy)
                    if enemy.take_damage(beam.damage): self.handle_enemy_death(enemy)

        for gem in pygame.sprite.spritecollide(self.player, self.experience_gems, True):
            self.player.gain_experience(gem.xp_value)
        
        for chest in pygame.sprite.spritecollide(self.player, self.treasure_chests, True):
            self.player.gain_levels(3)

        for enemy in pygame.sprite.spritecollide(self.player, self.enemies, True):
            self.player.take_damage(enemy.damage)

    def draw(self):
        self.screen.fill(BLACK)
        self.all_sprites.draw(self.screen)
        self.draw_ui()
        if self.level_up_state: self.show_level_up_screen()
        if self.game_over: self.show_game_over_screen()
        pygame.display.flip()

    def draw_ui(self):
        score_text = self.small_font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        level_text = self.small_font.render(f"Level: {self.player.level}", True, WHITE)
        self.screen.blit(level_text, (10, 40))

        survival_time = (pygame.time.get_ticks() - self.start_time) // 1000
        time_text = self.font.render(f"{survival_time//60:02}:{survival_time%60:02}", True, WHITE)
        self.screen.blit(time_text, time_text.get_rect(midtop=(SCREEN_WIDTH/2, 10)))

        # 生命条
        hp_rect = pygame.Rect((SCREEN_WIDTH - 200) / 2, SCREEN_HEIGHT - 70, 200, 25)
        pygame.draw.rect(self.screen, RED, hp_rect)
        pygame.draw.rect(self.screen, DARK_GREEN, (hp_rect.x, hp_rect.y, hp_rect.width * (self.player.health / self.player.max_health), hp_rect.height))
        
        # 经验条
        xp_rect = pygame.Rect(10, SCREEN_HEIGHT - 30, SCREEN_WIDTH - 20, 20)
        pygame.draw.rect(self.screen, GREY, xp_rect)
        pygame.draw.rect(self.screen, YELLOW, (xp_rect.x, xp_rect.y, xp_rect.width * (self.player.experience / self.player.experience_to_next_level), xp_rect.height))

    def show_level_up_screen(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        title = self.font.render("LEVEL UP! CHOOSE AN UPGRADE:", True, WHITE)
        options = [
            "1: Increase Player Speed",
            "2: Increase Projectile Fire Rate",
            "3: Decrease Beam Cooldown",
            "4: Increase Max Health (+20)",
            "5: Restore 30% Health"
        ]
        
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 150)))
        for i, text in enumerate(options):
            option_text = self.small_font.render(text, True, GREEN if i < 4 else YELLOW)
            self.screen.blit(option_text, option_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 60 + i * 40)))

    def show_game_over_screen(self):
        game_over_text = self.font.render("GAME OVER", True, WHITE)
        restart_text = self.font.render("Press any key to restart", True, WHITE)
        self.screen.blit(game_over_text, game_over_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 30)))
        self.screen.blit(restart_text, restart_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 30)))

if __name__ == '__main__':
    game = Game()
    game.run()
