import pygame
import random
import math
import numpy

# --- 常量 ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
PLAYER_SIZE = 40
ENEMY_SIZE = 30
TANK_ENEMY_SIZE = 50
BOSS_ENEMY_SIZE = 100
ORBIT_WEAPON_SIZE = 20
XP_GEM_SIZE = 15
PROJECTILE_SIZE = 10
BEAM_WIDTH = 20
BEAM_LENGTH = SCREEN_WIDTH

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
BEAM_WEAPON_INITIAL_COOLDOWN = 5000

# --- 音量设置 ---
MUSIC_VOLUME = 0.3
SFX_VOLUME = 0.5

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
ORANGE = (255, 165, 0)
GOLD = (255, 215, 0)
BROWN = (139, 69, 19)

# --- 声音生成函数 ---
def generate_sound(frequency, duration, sample_rate=44100):
    n_samples = int(sample_rate * duration)
    t = numpy.linspace(0, duration, n_samples, False)
    audio = numpy.sin(frequency * t * 2 * numpy.pi)
    # 添加衰减效果
    decay = numpy.exp(-5 * t)
    audio *= decay
    audio *= 32767 / numpy.max(numpy.abs(audio))
    audio = numpy.repeat(audio[:, numpy.newaxis], 2, axis=1)
    return pygame.sndarray.make_sound(audio.astype(numpy.int16))

# --- 玩家类 ---
class Player(pygame.sprite.Sprite):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.image = pygame.Surface([PLAYER_SIZE, PLAYER_SIZE], pygame.SRCALPHA)
        pygame.draw.rect(self.image, BLUE, (5, 15, PLAYER_SIZE - 10, PLAYER_SIZE - 15))
        pygame.draw.circle(self.image, WHITE, (PLAYER_SIZE // 2, 10), 8)
        
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        
        self.speed = PLAYER_INITIAL_SPEED
        self.max_health = PLAYER_INITIAL_HEALTH
        self.health = self.max_health
        self.level = 1
        self.experience = 0
        self.experience_to_next_level = 10
        self.last_move_dir = pygame.math.Vector2(0, -1)
        self.magnet_radius = 0
        self.damage_multiplier = 1.0 # 新增：伤害乘数

        # 升级追踪
        self.upgrades = {
            "speed": 1, "projectile_cooldown": 1, "beam_cooldown": 1,
            "max_health": 1, "magnet": 0, "spinach": 0
        }

    def take_damage(self, amount):
        self.health -= amount
        self.game.sounds['player_hit'].play()
        if self.health <= 0:
            self.health = 0
            self.game.game_over = True

    def heal(self, amount):
        self.health += amount
        if self.health > self.max_health: self.health = self.max_health

    def gain_experience(self, amount):
        self.experience += amount
        self.game.sounds['gem_pickup'].play()
        while self.experience >= self.experience_to_next_level:
            self.level_up()
    
    def gain_levels(self, amount):
        for _ in range(amount):
            self.level_up()

    def level_up(self):
        self.level += 1
        self.experience -= self.experience_to_next_level
        self.experience_to_next_level = int(self.experience_to_next_level * 1.5)
        self.game.prepare_level_up_choices()
        self.game.sounds['level_up'].play()

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
        self.image = pygame.Surface([ENEMY_SIZE, ENEMY_SIZE], pygame.SRCALPHA)
        pygame.draw.circle(self.image, RED, (ENEMY_SIZE // 2, ENEMY_SIZE // 2), ENEMY_SIZE // 2)
        pygame.draw.circle(self.image, BLACK, (ENEMY_SIZE // 2 - 5, ENEMY_SIZE // 2 - 5), 3)
        pygame.draw.circle(self.image, BLACK, (ENEMY_SIZE // 2 + 5, ENEMY_SIZE // 2 - 5), 3)
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
        self.game.sounds['enemy_hit'].play()
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
        self.image = pygame.Surface([TANK_ENEMY_SIZE, TANK_ENEMY_SIZE], pygame.SRCALPHA)
        pygame.draw.rect(self.image, PURPLE, (0, 0, TANK_ENEMY_SIZE, TANK_ENEMY_SIZE), border_radius=8)
        pygame.draw.rect(self.image, BLACK, (10, 10, 10, 10))
        self.rect = self.image.get_rect()
        self.spawn_at_edge()

class BossEnemy(Enemy):
    def __init__(self, player, speed):
        super().__init__(player, speed)
        self.health = 100
        self.speed = speed * 0.5
        self.xp_value = 200
        self.damage = 50
        self.image = pygame.Surface([BOSS_ENEMY_SIZE, BOSS_ENEMY_SIZE], pygame.SRCALPHA)
        pygame.draw.circle(self.image, ORANGE, (BOSS_ENEMY_SIZE // 2, BOSS_ENEMY_SIZE // 2), BOSS_ENEMY_SIZE // 2)
        pygame.draw.polygon(self.image, BLACK, [(30, 30), (40, 20), (50, 30)])
        pygame.draw.polygon(self.image, BLACK, [(BOSS_ENEMY_SIZE - 30, 30), (BOSS_ENEMY_SIZE - 40, 20), (BOSS_ENEMY_SIZE - 50, 30)])
        self.rect = self.image.get_rect()
        self.spawn_at_edge()

# --- 武器类 ---
class Weapon(pygame.sprite.Sprite):
    """ 武器基类，用于追踪等级 """
    def __init__(self, player, game):
        super().__init__()
        self.player = player
        self.game = game
        self.level = 1
        self.max_level = 5
        self.name = "Unnamed Weapon"
        self.image = pygame.Surface([1, 1], pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=player.rect.center)

class OrbitWeapon(Weapon):
    def __init__(self, player, game):
        super().__init__(player, game)
        self.name = "orbit_weapon"
        self.image = pygame.Surface([ORBIT_WEAPON_SIZE, ORBIT_WEAPON_SIZE], pygame.SRCALPHA)
        pygame.draw.circle(self.image, GREEN, (ORBIT_WEAPON_SIZE // 2, ORBIT_WEAPON_SIZE // 2), ORBIT_WEAPON_SIZE // 2)
        self.rect = self.image.get_rect()
        self.angle = 0
        self.radius = ORBIT_WEAPON_INITIAL_RADIUS
        self.speed = ORBIT_WEAPON_INITIAL_SPEED
        self.damage = 10

    def update(self):
        self.angle += self.speed
        self.rect.center = self.player.rect.center + pygame.math.Vector2(self.radius, 0).rotate_rad(self.angle)

class ProjectileWeapon(Weapon):
    def __init__(self, player, game):
        super().__init__(player, game)
        self.name = "projectile_weapon"
        self.cooldown = PROJECTILE_WEAPON_INITIAL_COOLDOWN
        self.last_shot_time = pygame.time.get_ticks()

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
            self.game.sounds['shoot'].play()
            self.game.add_sprite(Projectile(self.rect.center, target.rect.center, self.player.damage_multiplier), self.game.projectiles)

class SuperProjectileWeapon(ProjectileWeapon):
    """ 新增：进化后的武器 """
    def __init__(self, player, game):
        super().__init__(player, game)
        self.name = "super_projectile_weapon"
        self.cooldown = PROJECTILE_WEAPON_INITIAL_COOLDOWN * 0.5 # 射速更快

    def shoot(self):
        target = self.find_nearest_enemy()
        if target:
            self.game.sounds['shoot'].play()
            # 计算主方向
            direction = pygame.math.Vector2(target.rect.center) - self.rect.center
            # 发射三枚弹幕
            for angle in [-20, 0, 20]:
                rotated_dir = direction.rotate(angle)
                target_pos = self.rect.center + rotated_dir
                self.game.add_sprite(Projectile(self.rect.center, target_pos, self.player.damage_multiplier), self.game.projectiles)

class Projectile(pygame.sprite.Sprite):
    def __init__(self, start_pos, target_pos, damage_multiplier):
        super().__init__()
        self.image = pygame.Surface([PROJECTILE_SIZE, PROJECTILE_SIZE], pygame.SRCALPHA)
        pygame.draw.circle(self.image, CYAN, (PROJECTILE_SIZE // 2, PROJECTILE_SIZE // 2), PROJECTILE_SIZE // 2)
        self.rect = self.image.get_rect(center=start_pos)
        self.damage = 1 * damage_multiplier
        direction = pygame.math.Vector2(target_pos) - start_pos
        if direction.length_squared() > 0:
            self.velocity = direction.normalize() * PROJECTILE_SPEED
        else:
            self.velocity = pygame.math.Vector2(0, -PROJECTILE_SPEED)

    def update(self):
        self.rect.move_ip(self.velocity)
        if not self.rect.colliderect(self.game.screen.get_rect()): self.kill()

class DirectionalBeamWeapon(Weapon):
    def __init__(self, player, game):
        super().__init__(player, game)
        self.name = "beam_weapon"
        self.cooldown = BEAM_WEAPON_INITIAL_COOLDOWN
        self.damage = 3
        self.last_shot_time = pygame.time.get_ticks()

    def update(self):
        self.rect.center = self.player.rect.center
        now = pygame.time.get_ticks()
        if now - self.last_shot_time > self.cooldown:
            self.shoot()
            self.last_shot_time = now

    def shoot(self):
        self.game.add_sprite(Beam(self.player, self.damage * self.player.damage_multiplier), self.game.beams)

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
        self.duration = 250
        self.hit_enemies = set()

    def update(self):
        if pygame.time.get_ticks() - self.spawn_time > self.duration:
            self.kill()

# --- 掉落物类 ---
class ExperienceGem(pygame.sprite.Sprite):
    def __init__(self, pos, value):
        super().__init__()
        self.image = pygame.Surface([XP_GEM_SIZE, XP_GEM_SIZE], pygame.SRCALPHA)
        points = [(XP_GEM_SIZE // 2, 0), (XP_GEM_SIZE, XP_GEM_SIZE // 2), (XP_GEM_SIZE // 2, XP_GEM_SIZE), (0, XP_GEM_SIZE // 2)]
        pygame.draw.polygon(self.image, YELLOW, points)
        self.rect = self.image.get_rect(center=pos)
        self.xp_value = value

    def update(self):
        if self.game.player.magnet_radius > 0:
            player_pos = pygame.math.Vector2(self.game.player.rect.center)
            gem_pos = pygame.math.Vector2(self.rect.center)
            dist = player_pos.distance_to(gem_pos)
            if dist < self.game.player.magnet_radius:
                direction = (player_pos - gem_pos).normalize()
                self.rect.move_ip(direction * 8)

class TreasureChest(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface([40, 40], pygame.SRCALPHA)
        pygame.draw.rect(self.image, BROWN, (0, 10, 40, 30))
        pygame.draw.rect(self.image, GOLD, (0, 10, 40, 10))
        pygame.draw.rect(self.image, BLACK, (18, 20, 4, 8))
        self.rect = self.image.get_rect(center=pos)

# --- 游戏主类 ---
class Game:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("类吸血鬼幸存者游戏 - 武器进化")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 50)
        self.small_font = pygame.font.Font(None, 36)
        self.running = True
        self.load_sounds()
        self.setup_game()

    def load_sounds(self):
        self.sounds = {
            'shoot': generate_sound(880, 0.1),
            'enemy_hit': generate_sound(220, 0.1),
            'player_hit': generate_sound(110, 0.3),
            'level_up': generate_sound(1320, 0.5),
            'gem_pickup': generate_sound(1760, 0.05),
            'evolve': generate_sound(1500, 1.0) # 新增：进化音效
        }
        for sound in self.sounds.values():
            sound.set_volume(SFX_VOLUME)
        
        self.music_channel = pygame.mixer.Channel(0)
        self.bgm = generate_sound(110, 2.0)
        self.bgm.set_volume(MUSIC_VOLUME)

    def add_sprite(self, sprite, *groups):
        sprite.game = self
        self.all_sprites.add(sprite)
        for group in groups:
            group.add(sprite)

    def setup_game(self):
        self.game_over = False
        self.level_up_state = False
        self.paused = False
        self.score = 0
        self.start_time = pygame.time.get_ticks()
        self.enemy_current_speed = ENEMY_INITIAL_SPEED
        self.enemy_current_spawn_rate = ENEMY_SPAWN_RATE
        
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.active_weapons = pygame.sprite.Group() # 主武器组
        self.projectiles = pygame.sprite.Group()
        self.beams = pygame.sprite.Group()
        self.experience_gems = pygame.sprite.Group()
        self.treasure_chests = pygame.sprite.Group()

        self.player = Player(self)
        self.add_sprite(self.player)
        
        # 武器实例
        self.weapon_instances = {
            "orbit_weapon": OrbitWeapon(self.player, self),
            "projectile_weapon": ProjectileWeapon(self.player, self),
            "beam_weapon": DirectionalBeamWeapon(self.player, self)
        }
        for weapon in self.weapon_instances.values():
            self.add_sprite(weapon, self.active_weapons)
        
        self.enemy_spawn_timer = pygame.USEREVENT + 1
        pygame.time.set_timer(self.enemy_spawn_timer, self.enemy_current_spawn_rate)
        self.difficulty_timer = pygame.USEREVENT + 2
        pygame.time.set_timer(self.difficulty_timer, 20000)
        self.boss_spawn_timer = pygame.USEREVENT + 3
        pygame.time.set_timer(self.boss_spawn_timer, 120000)

        self.music_channel.play(self.bgm, loops=-1)

    def run(self):
        while self.running:
            self.events()
            if not self.game_over and not self.level_up_state and not self.paused:
                self.update()
            self.draw()
            self.clock.tick(60)
        pygame.quit()

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    self.paused = not self.paused
                    if self.paused: self.music_channel.pause()
                    else: self.music_channel.unpause()
            
            if self.game_over:
                if event.type == pygame.KEYDOWN: self.setup_game()
                continue
            if self.level_up_state:
                if event.type == pygame.KEYDOWN:
                    for i in range(len(self.level_up_choices)):
                        if event.key == getattr(pygame, f"K_{i+1}") or event.key == getattr(pygame, f"K_KP{i+1}"):
                            self.apply_upgrade(self.level_up_choices[i])
                            break
                continue
            if self.paused: continue

            if event.type == self.enemy_spawn_timer:
                if random.random() < 0.2: self.add_sprite(TankEnemy(self.player, self.enemy_current_speed), self.enemies)
                else: self.add_sprite(Enemy(self.player, self.enemy_current_speed), self.enemies)
            if event.type == self.difficulty_timer: self.increase_difficulty()
            if event.type == self.boss_spawn_timer: self.add_sprite(BossEnemy(self.player, self.enemy_current_speed), self.enemies)

    def increase_difficulty(self):
        self.enemy_current_speed *= 1.1
        self.enemy_current_spawn_rate = max(200, int(self.enemy_current_spawn_rate * 0.9))
        pygame.time.set_timer(self.enemy_spawn_timer, self.enemy_current_spawn_rate)
    
    def prepare_level_up_choices(self):
        """ 新增：准备动态升级选项 """
        self.level_up_state = True
        
        # 定义所有可能的升级
        possible_upgrades = {
            "projectile_weapon": ("Projectile Fire Rate", 5),
            "beam_weapon": ("Beam Cooldown", 5),
            "spinach": ("Damage Up", 5),
            "speed": ("Player Speed", 5),
            "max_health": ("Max Health", 5),
            "magnet": ("Magnet Radius", 5),
            "heal": ("Restore 30% Health", -1) # -1 表示无等级限制
        }
        
        # 筛选出可以升级的选项
        available_choices = []
        for key, (text, max_level) in possible_upgrades.items():
            if key == "heal":
                available_choices.append({"key": key, "text": text, "level": 0})
                continue
            
            # 检查武器是否存在且未满级
            if key in self.weapon_instances:
                if self.weapon_instances[key].level < max_level:
                    available_choices.append({"key": key, "text": text, "level": self.weapon_instances[key].level})
            # 检查被动道具是否未满级
            elif key in self.player.upgrades:
                 if self.player.upgrades[key] < max_level:
                    available_choices.append({"key": key, "text": text, "level": self.player.upgrades[key]})

        # 随机选择最多4个选项
        self.level_up_choices = random.sample(available_choices, min(len(available_choices), 4))

    def apply_upgrade(self, choice):
        key = choice["key"]
        if key == "speed": self.player.speed += 1; self.player.upgrades[key] += 1
        elif key == "projectile_weapon": 
            weapon = self.weapon_instances[key]
            weapon.cooldown = max(100, int(weapon.cooldown * 0.85)); weapon.level += 1
        elif key == "beam_weapon": 
            weapon = self.weapon_instances[key]
            weapon.cooldown = max(1000, int(weapon.cooldown * 0.9)); weapon.level += 1
        elif key == "max_health": self.player.max_health += 20; self.player.heal(20); self.player.upgrades[key] += 1
        elif key == "magnet": self.player.magnet_radius += 60; self.player.upgrades[key] += 1
        elif key == "spinach": self.player.damage_multiplier += 0.1; self.player.upgrades[key] += 1
        elif key == "heal": self.player.heal(self.player.max_health * 0.3)
        
        self.level_up_state = False
        self.check_for_evolutions()

    def check_for_evolutions(self):
        """ 新增：检查是否满足武器进化条件 """
        proj_weapon = self.weapon_instances.get("projectile_weapon")
        if proj_weapon and proj_weapon.level >= proj_weapon.max_level and self.player.upgrades["spinach"] >= 5:
            # 进化！
            proj_weapon.kill() # 移除旧武器
            new_weapon = SuperProjectileWeapon(self.player, self)
            self.weapon_instances["projectile_weapon"] = new_weapon # 替换实例
            self.add_sprite(new_weapon, self.active_weapons)
            self.sounds['evolve'].play()
            # 可以在这里添加一个视觉效果
            self.game_over_text = self.font.render("WEAPON EVOLVED!", True, GOLD) # 借用一下变量名
            self.game_over_text_timer = pygame.time.get_ticks()

    def handle_enemy_death(self, enemy):
        self.score += 1
        if isinstance(enemy, BossEnemy):
            self.add_sprite(TreasureChest(enemy.rect.center), self.treasure_chests)
        else:
            self.add_sprite(ExperienceGem(enemy.rect.center, enemy.xp_value), self.experience_gems)

    def update(self):
        self.all_sprites.update()
        
        # 碰撞检测
        for weapon in self.active_weapons:
            if isinstance(weapon, OrbitWeapon):
                for enemy in pygame.sprite.spritecollide(weapon, self.enemies, False):
                    if enemy.take_damage(weapon.damage * self.player.damage_multiplier): self.handle_enemy_death(enemy)
        
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
        if self.paused: self.show_pause_screen()
        
        # 显示进化提示
        if hasattr(self, 'game_over_text_timer') and pygame.time.get_ticks() - self.game_over_text_timer < 2000:
             self.screen.blit(self.game_over_text, self.game_over_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2)))
        else:
            if hasattr(self, 'game_over_text_timer'): delattr(self, 'game_over_text_timer')

        pygame.display.flip()

    def draw_ui(self):
        score_text = self.small_font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        level_text = self.small_font.render(f"Level: {self.player.level}", True, WHITE)
        self.screen.blit(level_text, (10, 40))

        survival_time = (pygame.time.get_ticks() - self.start_time) // 1000
        time_text = self.font.render(f"{survival_time//60:02}:{survival_time%60:02}", True, WHITE)
        self.screen.blit(time_text, time_text.get_rect(midtop=(SCREEN_WIDTH/2, 10)))

        hp_rect = pygame.Rect((SCREEN_WIDTH - 200) / 2, SCREEN_HEIGHT - 70, 200, 25)
        pygame.draw.rect(self.screen, RED, hp_rect)
        pygame.draw.rect(self.screen, DARK_GREEN, (hp_rect.x, hp_rect.y, hp_rect.width * (self.player.health / self.player.max_health), hp_rect.height))
        
        xp_rect = pygame.Rect(10, SCREEN_HEIGHT - 30, SCREEN_WIDTH - 20, 20)
        pygame.draw.rect(self.screen, GREY, xp_rect)
        pygame.draw.rect(self.screen, YELLOW, (xp_rect.x, xp_rect.y, xp_rect.width * (self.player.experience / self.player.experience_to_next_level), xp_rect.height))

    def show_level_up_screen(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        title = self.font.render("LEVEL UP! CHOOSE AN UPGRADE:", True, WHITE)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 150)))
        
        for i, choice in enumerate(self.level_up_choices):
            text = f"{i+1}: {choice['text']}"
            if choice['level'] > 0:
                text += f" (Lvl {choice['level']})"
            
            color = YELLOW if choice['key'] == 'heal' else GREEN
            option_text = self.small_font.render(text, True, color)
            self.screen.blit(option_text, option_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 60 + i * 40)))

    def show_game_over_screen(self):
        game_over_text = self.font.render("GAME OVER", True, WHITE)
        restart_text = self.font.render("Press any key to restart", True, WHITE)
        self.screen.blit(game_over_text, game_over_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 30)))
        self.screen.blit(restart_text, restart_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 30)))

    def show_pause_screen(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        pause_text = self.font.render("PAUSED", True, WHITE)
        self.screen.blit(pause_text, pause_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2)))

if __name__ == '__main__':
    game = Game()
    game.run()
