import pygame
import random
import math

# --- 常量 ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
PLAYER_SIZE = 40
PLAYER_SPEED = 5
ENEMY_SIZE = 30
ENEMY_SPEED = 2
ORBIT_WEAPON_SIZE = 20
ORBIT_WEAPON_RADIUS = 100
ORBIT_WEAPON_SPEED = 0.1  # 弧度/帧

# --- 颜色 ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

# --- 玩家类 ---
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # 创建一个代表玩家的图像（一个蓝色的方块）
        self.image = pygame.Surface([PLAYER_SIZE, PLAYER_SIZE])
        self.image.fill(BLUE)
        # 获取玩家图像的矩形区域
        self.rect = self.image.get_rect()
        # 设置玩家的初始位置在屏幕中央
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

    def update(self):
        """ 根据按键输入移动玩家 """
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += PLAYER_SPEED
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.rect.y -= PLAYER_SPEED
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.rect.y += PLAYER_SPEED

        # 确保玩家不会移出屏幕边界
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT

# --- 敌人累 ---
class Enemy(pygame.sprite.Sprite):
    def __init__(self, player):
        super().__init__()
        # 创建一个代表敌人的图像（一个红色的方块）
        self.image = pygame.Surface([ENEMY_SIZE, ENEMY_SIZE])
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.player = player # 保存对玩家对象的引用，以便追踪

        # 在屏幕边缘随机生成敌人
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
        elif side == 'right':
            self.rect.x = SCREEN_WIDTH
            self.rect.y = random.randint(0, SCREEN_HEIGHT - ENEMY_SIZE)

    def update(self):
        """ 移动敌人使其朝向玩家 """
        # 计算玩家方向的向量
        dx = self.player.rect.centerx - self.rect.centerx
        dy = self.player.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)

        # 防止除以零的错误
        if dist != 0:
            # 标准化向量并乘以速度
            dx = dx / dist
            dy = dy / dist
            self.rect.x += dx * ENEMY_SPEED
            self.rect.y += dy * ENEMY_SPEED

# --- 环绕武器类 ---
class OrbitWeapon(pygame.sprite.Sprite):
    def __init__(self, player):
        super().__init__()
        # 创建一个代表武器的图像（一个绿色的方块）
        self.image = pygame.Surface([ORBIT_WEAPON_SIZE, ORBIT_WEAPON_SIZE])
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.player = player
        self.angle = 0 # 初始角度

    def update(self):
        """ 更新武器位置，使其环绕玩家旋转 """
        self.angle += ORBIT_WEAPON_SPEED
        # 根据角度和半径计算武器位置
        self.rect.centerx = self.player.rect.centerx + ORBIT_WEAPON_RADIUS * math.cos(self.angle)
        self.rect.centery = self.player.rect.centery + ORBIT_WEAPON_RADIUS * math.sin(self.angle)

# --- 游戏主类 ---
class Game:
    def __init__(self):
        """ 初始化游戏 """
        pygame.init()
        # 设置屏幕和标题
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("类吸血鬼幸存者游戏")
        # 用于控制帧率的时钟
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 50)
        self.running = True
        self.game_over = False
        self.score = 0
        
        # 创建精灵组
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.weapons = pygame.sprite.Group()

        # 创建游戏对象
        self.player = Player()
        self.weapon = OrbitWeapon(self.player)
        
        # 将对象添加到精灵组
        self.all_sprites.add(self.player)
        self.all_sprites.add(self.weapon)
        self.weapons.add(self.weapon)

        # 设置敌人生成的计时器
        self.enemy_spawn_timer = pygame.USEREVENT + 1
        pygame.time.set_timer(self.enemy_spawn_timer, 1000) # 每1000毫秒（1秒）生成一个敌人

    def run(self):
        """ 游戏主循环 """
        while self.running:
            # 处理事件
            self.events()
            if not self.game_over:
                # 更新游戏状态
                self.update()
            # 绘制画面
            self.draw()
            # 控制帧率
            self.clock.tick(60)
        pygame.quit()

    def events(self):
        """ 处理所有事件 """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            # 根据计时器生成敌人
            if event.type == self.enemy_spawn_timer and not self.game_over:
                enemy = Enemy(self.player)
                self.all_sprites.add(enemy)
                self.enemies.add(enemy)
            # 如果游戏结束，按任意键重新开始
            if event.type == pygame.KEYDOWN and self.game_over:
                self.reset_game()

    def update(self):
        """ 更新所有游戏对象 """
        self.all_sprites.update()

        # 检测武器与敌人的碰撞
        hits = pygame.sprite.groupcollide(self.weapons, self.enemies, False, True)
        if hits:
            self.score += len(hits[self.weapon]) # 增加分数

        # 检测玩家与敌人的碰撞
        if pygame.sprite.spritecollide(self.player, self.enemies, False):
            self.game_over = True

    def draw(self):
        """ 绘制所有内容到屏幕 """
        self.screen.fill(BLACK) # 用黑色填充背景
        self.all_sprites.draw(self.screen) # 绘制所有精灵

        # 显示分数
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))

        if self.game_over:
            self.show_game_over_screen()

        pygame.display.flip() # 更新整个屏幕

    def show_game_over_screen(self):
        """ 显示游戏结束画面 """
        game_over_text = self.font.render("GAME OVER", True, WHITE)
        restart_text = self.font.render("Press any key to restart", True, WHITE)
        
        # 居中显示文本
        text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 30))
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 30))

        self.screen.blit(game_over_text, text_rect)
        self.screen.blit(restart_text, restart_rect)

    def reset_game(self):
        """ 重置游戏状态以重新开始 """
        self.game_over = False
        self.score = 0
        # 清空所有精灵组并重新创建
        self.all_sprites.empty()
        self.enemies.empty()
        self.weapons.empty()

        self.player = Player()
        self.weapon = OrbitWeapon(self.player)
        
        self.all_sprites.add(self.player)
        self.all_sprites.add(self.weapon)
        self.weapons.add(self.weapon)

if __name__ == '__main__':
    game = Game()
    game.run()
