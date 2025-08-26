import pygame
import random
import math

# --- 常量 ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
PLAYER_SIZE = 40
ENEMY_SIZE = 30
ORBIT_WEAPON_SIZE = 20
XP_GEM_SIZE = 15
PROJECTILE_SIZE = 10

# --- 玩家初始属性 ---
PLAYER_INITIAL_SPEED = 5

# --- 敌人初始属性 ---
ENEMY_INITIAL_SPEED = 2
ENEMY_SPAWN_RATE = 1000 # 初始生成速率（毫秒）

# --- 武器初始属性 ---
ORBIT_WEAPON_INITIAL_RADIUS = 100
ORBIT_WEAPON_INITIAL_SPEED = 0.1  # 弧度/帧
PROJECTILE_WEAPON_INITIAL_COOLDOWN = 1200 # 毫秒
PROJECTILE_SPEED = 10

# --- 颜色 ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
GREY = (100, 100, 100)
CYAN = (0, 255, 255)

# --- 玩家类 ---
class Player(pygame.sprite.Sprite):
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.image = pygame.Surface([PLAYER_SIZE, PLAYER_SIZE])
        self.image.fill(BLUE)
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        
        self.speed = PLAYER_INITIAL_SPEED
        self.level = 1
        self.experience = 0
        self.experience_to_next_level = 10

    def gain_experience(self, amount):
        self.experience += amount
        if self.experience >= self.experience_to_next_level:
            self.level_up()

    def level_up(self):
        self.level += 1
        self.experience -= self.experience_to_next_level
        self.experience_to_next_level = int(self.experience_to_next_level * 1.5)
        self.game.level_up_state = True

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.rect.x += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]: self.rect.y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: self.rect.y += self.speed

        if self.rect.left < 0: self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH: self.rect.right = SCREEN_WIDTH
        if self.rect.top < 0: self.rect.top = 0
        if self.rect.bottom > SCREEN_HEIGHT: self.rect.bottom = SCREEN_HEIGHT

# --- 敌人累 ---
class Enemy(pygame.sprite.Sprite):
    def __init__(self, player, speed):
        super().__init__()
        self.image = pygame.Surface([ENEMY_SIZE, ENEMY_SIZE])
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.player = player
        self.speed = speed
        self.health = 1 # 新增：敌人生命值

        side = random.choice(['top', 'bottom', 'left', 'right'])
        if side == 'top':
            self.rect.x = random.randint(0, SCREEN_WIDTH - ENEMY_SIZE)
            self.rect.y = -ENEMY_SIZE
        elif side == 'bottom':
            self.rect.x = random.randint(0, SCREEN_WIDTH - ENEMY_SIZE)
            self.rect.y = SCREEN_HEIGHT
        elif side == 'left':
            self.rect.x = -ENEMY_SIZE
            self.rect.y = random.randint(0, SCREEN_HEIGHT - ENEMY_SIZE)
        else:
            self.rect.x = SCREEN_WIDTH
            self.rect.y = random.randint(0, SCREEN_HEIGHT - ENEMY_SIZE)

    def take_damage(self, amount):
        """ 敌人受到伤害 """
        self.health -= amount
        if self.health <= 0:
            self.kill()
            return True # 返回True表示敌人已被击败
        return False

    def update(self):
        dx = self.player.rect.centerx - self.rect.centerx
        dy = self.player.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist != 0:
            dx, dy = dx / dist, dy / dist
            self.rect.x += dx * self.speed
            self.rect.y += dy * self.speed

# --- 武器类 ---
class OrbitWeapon(pygame.sprite.Sprite):
    def __init__(self, player):
        super().__init__()
        self.image = pygame.Surface([ORBIT_WEAPON_SIZE, ORBIT_WEAPON_SIZE])
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.player = player
        self.angle = 0
        self.radius = ORBIT_WEAPON_INITIAL_RADIUS
        self.speed = ORBIT_WEAPON_INITIAL_SPEED
        self.damage = 10 # 伤害值很高，可以秒杀普通敌人

    def update(self):
        self.angle += self.speed
        self.rect.centerx = self.player.rect.centerx + self.radius * math.cos(self.angle)
        self.rect.centery = self.player.rect.centery + self.radius * math.sin(self.angle)

class ProjectileWeapon(pygame.sprite.Sprite):
    """ 新增：一把自动向最近敌人发射子弹的武器 """
    def __init__(self, player, game):
        super().__init__()
        self.player = player
        self.game = game
        self.cooldown = PROJECTILE_WEAPON_INITIAL_COOLDOWN
        self.last_shot_time = pygame.time.get_ticks()
        # 这个武器本身不可见，所以我们给它一个1x1的透明图像
        self.image = pygame.Surface([1, 1], pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=player.rect.center)

    def update(self):
        # 将武器位置始终对准玩家
        self.rect.center = self.player.rect.center
        now = pygame.time.get_ticks()
        if now - self.last_shot_time > self.cooldown:
            self.shoot()
            self.last_shot_time = now

    def find_nearest_enemy(self):
        """ 找到距离玩家最近的敌人 """
        nearest_enemy = None
        min_dist = float('inf')
        for enemy in self.game.enemies:
            dist = math.hypot(self.player.rect.centerx - enemy.rect.centerx,
                              self.player.rect.centery - enemy.rect.centery)
            if dist < min_dist:
                min_dist = dist
                nearest_enemy = enemy
        return nearest_enemy

    def shoot(self):
        target = self.find_nearest_enemy()
        if target:
            projectile = Projectile(self.rect.center, target.rect.center)
            self.game.all_sprites.add(projectile)
            self.game.projectiles.add(projectile)

class Projectile(pygame.sprite.Sprite):
    """ 新增：子弹类 """
    def __init__(self, start_pos, target_pos):
        super().__init__()
        self.image = pygame.Surface([PROJECTILE_SIZE, PROJECTILE_SIZE])
        self.image.fill(CYAN)
        self.rect = self.image.get_rect(center=start_pos)
        self.damage = 1

        # 计算朝向目标的向量
        dx = target_pos[0] - start_pos[0]
        dy = target_pos[1] - start_pos[1]
        dist = math.hypot(dx, dy)
        if dist != 0:
            self.vel_x = (dx / dist) * PROJECTILE_SPEED
            self.vel_y = (dy / dist) * PROJECTILE_SPEED
        else:
            self.vel_x, self.vel_y = 0, -PROJECTILE_SPEED

    def update(self):
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        # 如果子弹飞出屏幕，则销毁它
        if not self.rect.colliderect(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)):
            self.kill()

# --- 经验宝石类 ---
class ExperienceGem(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface([XP_GEM_SIZE, XP_GEM_SIZE])
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect(center=pos)
        self.xp_value = 5

# --- 游戏主类 ---
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("类吸血鬼幸存者游戏 - 武器与难度")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 50)
        self.small_font = pygame.font.Font(None, 36)
        self.running = True
        self.setup_game()

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
        self.projectiles = pygame.sprite.Group() # 新增：子弹精灵组
        self.experience_gems = pygame.sprite.Group()

        self.player = Player(self)
        self.orbit_weapon = OrbitWeapon(self.player)
        self.projectile_weapon = ProjectileWeapon(self.player, self)
        
        self.all_sprites.add(self.player, self.orbit_weapon, self.projectile_weapon)
        self.weapons.add(self.orbit_weapon) # 子弹武器不可见，但子弹本身会造成伤害

        # 敌人生成计时器
        self.enemy_spawn_timer = pygame.USEREVENT + 1
        pygame.time.set_timer(self.enemy_spawn_timer, self.enemy_current_spawn_rate)
        # 难度增加计时器
        self.difficulty_timer = pygame.USEREVENT + 2
        pygame.time.set_timer(self.difficulty_timer, 20000) # 每20秒增加一次难度

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
            if event.type == pygame.QUIT:
                self.running = False
            
            if self.game_over:
                if event.type == pygame.KEYDOWN: self.setup_game()
                continue

            if self.level_up_state:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1: self.apply_upgrade(1)
                    elif event.key == pygame.K_2: self.apply_upgrade(2)
                    elif event.key == pygame.K_3: self.apply_upgrade(3)
                continue

            if event.type == self.enemy_spawn_timer:
                enemy = Enemy(self.player, self.enemy_current_speed)
                self.all_sprites.add(enemy)
                self.enemies.add(enemy)
            
            if event.type == self.difficulty_timer:
                self.increase_difficulty()

    def increase_difficulty(self):
        """ 增加游戏难度 """
        self.enemy_current_speed *= 1.1 # 敌人速度增加10%
        self.enemy_current_spawn_rate = max(200, int(self.enemy_current_spawn_rate * 0.9)) # 生成速度加快10%，最快200ms
        pygame.time.set_timer(self.enemy_spawn_timer, self.enemy_current_spawn_rate)

    def apply_upgrade(self, choice):
        if choice == 1: self.player.speed += 1
        elif choice == 2: self.orbit_weapon.speed += 0.02
        elif choice == 3: self.projectile_weapon.cooldown = max(100, int(self.projectile_weapon.cooldown * 0.85)) # 射速提高15%
        self.level_up_state = False

    def update(self):
        self.all_sprites.update()

        # 检测环绕武器与敌人的碰撞
        hits_orbit = pygame.sprite.groupcollide(self.weapons, self.enemies, False, False)
        for weapon, hit_enemies in hits_orbit.items():
            for enemy in hit_enemies:
                if enemy.take_damage(weapon.damage):
                    self.score += 1
                    gem = ExperienceGem(enemy.rect.center)
                    self.all_sprites.add(gem)
                    self.experience_gems.add(gem)
        
        # 检测子弹与敌人的碰撞
        hits_projectile = pygame.sprite.groupcollide(self.projectiles, self.enemies, True, False)
        for projectile, hit_enemies in hits_projectile.items():
            for enemy in hit_enemies:
                if enemy.take_damage(projectile.damage):
                    self.score += 1
                    gem = ExperienceGem(enemy.rect.center)
                    self.all_sprites.add(gem)
                    self.experience_gems.add(gem)

        # 检测玩家与经验宝石的碰撞
        gem_hits = pygame.sprite.spritecollide(self.player, self.experience_gems, True)
        for gem in gem_hits:
            self.player.gain_experience(gem.xp_value)

        # 检测玩家与敌人的碰撞
        if pygame.sprite.spritecollide(self.player, self.enemies, False):
            self.game_over = True

    def draw(self):
        self.screen.fill(BLACK)
        self.all_sprites.draw(self.screen)
        self.draw_ui()
        if self.level_up_state: self.show_level_up_screen()
        if self.game_over: self.show_game_over_screen()
        pygame.display.flip()

    def draw_ui(self):
        # 分数
        score_text = self.small_font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        
        # 等级
        level_text = self.small_font.render(f"Level: {self.player.level}", True, WHITE)
        self.screen.blit(level_text, (10, 40))

        # 生存时间
        survival_time = (pygame.time.get_ticks() - self.start_time) // 1000
        minutes = survival_time // 60
        seconds = survival_time % 60
        time_text = self.font.render(f"{minutes:02}:{seconds:02}", True, WHITE)
        self.screen.blit(time_text, time_text.get_rect(midtop=(SCREEN_WIDTH/2, 10)))

        # 经验条
        xp_bar_width = SCREEN_WIDTH - 20
        xp_bar_height = 20
        xp_percentage = self.player.experience / self.player.experience_to_next_level
        pygame.draw.rect(self.screen, GREY, (10, SCREEN_HEIGHT - 30, xp_bar_width, xp_bar_height))
        pygame.draw.rect(self.screen, YELLOW, (10, SCREEN_HEIGHT - 30, xp_bar_width * xp_percentage, xp_bar_height))

    def show_level_up_screen(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        title_text = self.font.render("LEVEL UP! CHOOSE AN UPGRADE:", True, WHITE)
        option1_text = self.small_font.render("1: Increase Player Speed", True, GREEN)
        option2_text = self.small_font.render("2: Increase Orbit Weapon Speed", True, GREEN)
        option3_text = self.small_font.render("3: Increase Projectile Fire Rate", True, GREEN)
        
        self.screen.blit(title_text, title_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 150)))
        self.screen.blit(option1_text, option1_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 50)))
        self.screen.blit(option2_text, option2_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 10)))
        self.screen.blit(option3_text, option3_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 70)))

    def show_game_over_screen(self):
        game_over_text = self.font.render("GAME OVER", True, WHITE)
        restart_text = self.font.render("Press any key to restart", True, WHITE)
        self.screen.blit(game_over_text, game_over_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 30)))
        self.screen.blit(restart_text, restart_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 30)))

if __name__ == '__main__':
    game = Game()
    game.run()
