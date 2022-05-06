import pygame as pg
import os
from random import randint
from .. import tool
from .. import constants as c


class Zombie(pg.sprite.Sprite):
    def __init__(self, x, y, name, head_group=None, helmetHealth=0, helmetType2Health=0, bodyHealth=c.NORMAL_HEALTH + c.LOSTHEAD_HEALTH, damage=c.ZOMBIE_ATTACK_DAMAGE, canSwim=False):
        pg.sprite.Sprite.__init__(self)

        self.name = name
        self.frames = []
        self.frame_index = 0
        self.loadImages()
        self.frame_num = len(self.frames)

        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y

        self.helmetHealth = helmetHealth
        self.helmetType2Health = helmetType2Health
        self.health = bodyHealth
        self.damage = damage
        self.dead = False
        self.lostHead = False
        self.canSwim = canSwim
        self.swimming = False
        self.helmet = (self.helmetHealth > 0)
        self.helmetType2 = (self.helmetType2Health > 0)
        self.head_group = head_group

        self.walk_timer = 0
        self.animate_timer = 0
        self.attack_timer = 0
        self.state = c.WALK
        self.animate_interval = 150
        self.walk_animate_interval = 180
        self.attack_animate_interval = 100
        self.lostHead_animate_interval = 180
        self.die_animate_interval = 50
        self.boomDie_animate_interval = 100
        self.ice_slow_ratio = 1
        self.ice_slow_timer = 0
        self.hit_timer = 0
        self.speed = 1
        self.freeze_timer = 0
        self.losthead_timer = 0
        self.is_hypno = False  # the zombie is hypo and attack other zombies when it ate a HypnoShroom

    def loadFrames(self, frames, name, colorkey=c.BLACK):
        frame_list = tool.GFX[name]
        rect = frame_list[0].get_rect()
        width, height = rect.w, rect.h
        if name in tool.ZOMBIE_RECT:
            data = tool.ZOMBIE_RECT[name]
            x, width = data['x'], data['width']
        else:
            x = 0
        for frame in frame_list:
            frames.append(tool.get_image(frame, x, 0, width, height, colorkey))

    def update(self, game_info):
        self.current_time = game_info[c.CURRENT_TIME]
        self.handleState()
        self.updateIceSlow()
        self.animation()

    def handleState(self):
        if self.state == c.WALK:
            self.walking()
        elif self.state == c.ATTACK:
            self.attacking()
        elif self.state == c.DIE:
            self.dying()
        elif self.state == c.FREEZE:
            self.freezing()

    # 濒死状态用函数
    def checkToDie(self, framesKind):
        if self.health <= 0:
            self.setDie()
            return True
        elif self.health <= c.LOSTHEAD_HEALTH:
            if not self.lostHead:
                self.changeFrames(framesKind)
                self.setLostHead()
                return True
            else:
                self.health -= (self.current_time - self.losthead_timer) / 40
                self.losthead_timer = self.current_time
                return False
        else:
            return False

    def walking(self):
        if self.checkToDie(self.losthead_walk_frames):
            return

        # 能游泳的僵尸
        if self.canSwim:
            # 在水池范围内
            # 在右侧岸左
            if self.rect.right <= c.MAP_POOL_FRONT_X:
                # 在左侧岸右，左侧岸位置为预估
                if self.rect.right - 25 >= c.MAP_POOL_OFFSET_X:
                    # 还未进入游泳状态
                    if not self.swimming:
                        self.swimming = True
                        self.changeFrames(self.swim_frames)
                        # 播放入水音效
                        pg.mixer.Sound(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))) ,"resources", "sound", "zombieEnteringWater.ogg")).play()
                        # 同样没有兼容双防具
                        if self.helmet:
                            if self.helmetHealth <= 0:
                                self.helmet = False
                            else:
                                self.changeFrames(self.helmet_swim_frames)
                        if self.helmetType2:
                            if self.helmetType2Health <= 0:
                                self.helmetType2 = False
                            else:
                                self.changeFrames(self.helmet_swim_frames)
                    # 已经进入游泳状态
                    else:
                        if self.helmet:
                            if self.helmetHealth <= 0:
                                self.changeFrames(self.swim_frames)
                                self.helmet = False
                        if self.helmetType2:
                            if self.helmetType2Health <= 0:
                                self.changeFrames(self.swim_frames)
                                self.helmetType2 = False
                # 水生僵尸已经接近家门口并且上岸
                else:
                    if self.swimming:
                        self.changeFrames(self.walk_frames)
                        self.swimming = False
                    # 同样没有兼容双防具
                    if self.helmet:
                        if self.helmetHealth <= 0:
                            self.helmet = False
                        else:
                            self.changeFrames(self.helmet_walk_frames)
                    if self.helmetType2:
                        if self.helmetType2Health <= 0:
                            self.helmetType2 = False
                        else:
                            self.changeFrames(self.helmet_walk_frames)
            elif self.is_hypno and self.rect.right > c.MAP_POOL_FRONT_X + 55:   # 常数拟合暂时缺乏检验
                if self.swimming:
                    self.changeFrames(self.walk_frames)
                if self.helmet:
                    if self.helmetHealth <= 0:
                        self.changeFrames(self.walk_frames)
                        self.helmet = False
                    elif self.swimming: # 游泳状态需要改为步行
                        self.changeFrames(self.helmet_walk_frames)
                if self.helmetType2:
                    if self.helmetType2Health <= 0:
                        self.changeFrames(self.walk_frames)
                        self.helmetType2 = False
                    elif self.swimming: # 游泳状态需要改为步行
                        self.changeFrames(self.helmet_walk_frames)
                self.swimming = False
            # 尚未进入水池
            else:
                if self.helmetHealth <= 0 and self.helmet:
                    self.changeFrames(self.walk_frames)
                    self.helmet = False
                if self.helmetType2Health <= 0 and self.helmetType2:
                    self.changeFrames(self.walk_frames)
                    self.helmetType2 = False
        # 不能游泳的一般僵尸
        else:
            if self.helmetHealth <= 0 and self.helmet:
                self.changeFrames(self.walk_frames)
                self.helmet = False
            if self.helmetType2Health <= 0 and self.helmetType2:
                self.changeFrames(self.walk_frames)
                self.helmetType2 = False
                if self.name == c.NEWSPAPER_ZOMBIE:
                    self.speed = 2.5
                    # 触发报纸僵尸暴走音效
                    pg.mixer.Sound(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))) ,"resources", "sound", "newspaperZombieAngry.ogg")).play()
        if (self.current_time - self.walk_timer) > (c.ZOMBIE_WALK_INTERVAL * self.getTimeRatio()):
            self.walk_timer = self.current_time
            if self.is_hypno:
                self.rect.x += 1
            else:
                self.rect.x -= 1

    def attacking(self):
        if self.checkToDie(self.losthead_attack_frames):
            return
        
        if self.helmetHealth <= 0 and self.helmet:
            self.changeFrames(self.attack_frames)
            self.helmet = False
        if self.helmetType2Health <= 0 and self.helmetType2:
            self.changeFrames(self.attack_frames)
            self.helmetType2 = False
            if self.name == c.NEWSPAPER_ZOMBIE:
                self.speed = 2.5
        if ((self.current_time - self.attack_timer) > (c.ATTACK_INTERVAL * self.getAttackTimeRatio())) and (not self.lostHead):
            if self.prey.health > 0:
                if self.prey_is_plant:
                    self.prey.setDamage(self.damage, self)
                else:
                    self.prey.setDamage(self.damage)
                
                # 播放啃咬音效
                pg.mixer.Sound(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))) ,"resources", "sound", "zombieAttack.ogg")).play()
            self.attack_timer = self.current_time

        if self.prey.health <= 0:
            self.prey = None
            self.setWalk()

    def dying(self):
        pass

    def freezing(self):
        if self.old_state == c.WALK:
            if self.checkToDie(self.losthead_walk_frames):
                return
        else:
            if self.checkToDie(self.losthead_attack_frames):
                return

        if (self.current_time - self.freeze_timer) >= c.MIN_FREEZE_TIME + randint(0, 2000):
            self.setWalk()
            # 注意寒冰菇解冻后还有减速
            self.ice_slow_timer = self.freeze_timer + 10000 # 每次冰冻冻结 + 减速时间为20 s，而减速有10 s计时，故这里+10 s
            self.ice_slow_ratio = 2

    def setLostHead(self):
        self.losthead_timer = self.current_time
        self.lostHead = True
        self.speed = 0.5
        self.animate_interval = self.lostHead_animate_interval
        if self.head_group is not None:
            self.head_group.add(ZombieHead(self.rect.centerx, self.rect.bottom))

    def changeFrames(self, frames):
        '''change image frames and modify rect position'''
        self.frames = frames
        self.frame_num = len(self.frames)
        self.frame_index = 0

        bottom = self.rect.bottom
        centerx = self.rect.centerx
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.bottom = bottom
        self.rect.centerx = centerx

    def animation(self):
        if self.state == c.FREEZE:
            self.image.set_alpha(192)
            return

        if (self.current_time - self.animate_timer) > (self.animate_interval * self.getTimeRatio()):
            self.frame_index += 1
            if self.frame_index >= self.frame_num:
                if self.state == c.DIE:
                    self.kill()
                    return
                self.frame_index = 0
            self.animate_timer = self.current_time

        self.image = self.frames[self.frame_index]
        if self.is_hypno:
            self.image = pg.transform.flip(self.image, True, False)
        if (self.current_time - self.hit_timer) >= 200:
            self.image.set_alpha(255)
        else:
            self.image.set_alpha(192)

    def getTimeRatio(self):
        return (self.ice_slow_ratio / self.speed)   # 目前的机制为：冰冻减速状态与自身速度共同决定行走的时间间隔

    def getAttackTimeRatio(self):
        return self.ice_slow_ratio  # 攻击速度只取决于冰冻状态

    def setIceSlow(self):
        # 在转入冰冻减速状态时播放冰冻音效
        if self.ice_slow_ratio == 1:
            pg.mixer.Sound(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))) ,"resources", "sound", "freeze.ogg")).play()

        # when get a ice bullet damage, slow the attack or walk speed of the zombie
        self.ice_slow_timer = self.current_time
        self.ice_slow_ratio = 2

    def updateIceSlow(self):
        if self.ice_slow_ratio > 1:
            if (self.current_time - self.ice_slow_timer) > c.ICE_SLOW_TIME:
                self.ice_slow_ratio = 1

    def setDamage(self, damage, effect=False, damageType=c.ZOMBIE_COMMON_DAMAGE):
        # 冰冻减速效果
        if effect == c.BULLET_EFFECT_ICE:
            if damageType == c.ZOMBIE_DEAFULT_DAMAGE:   # 寒冰射手不能穿透二类防具进行减速
                if not self.helmetType2:
                    self.setIceSlow()
            else:
                self.setIceSlow()
        # 解冻
        elif effect == c.BULLET_EFFECT_UNICE:
            if damageType == c.ZOMBIE_DEAFULT_DAMAGE:   # 寒冰射手不能穿透二类防具进行减速
                if not self.helmetType2:
                    self.ice_slow_ratio = 1
            else:
                self.ice_slow_ratio = 1

        if damageType == c.ZOMBIE_DEAFULT_DAMAGE:   # 不穿透二类防具的攻击
            # 从第二类防具开始逐级传递
            if self.helmetType2:
                self.helmetType2Health -= damage
                if self.helmetType2Health <= 0:
                    if self.helmet:
                        self.helmetHealth += self.helmetType2Health # 注意self.helmetType2Health已经带有正负
                        self.helmetType2Health = 0  # 注意合并后清零
                        if self.helmetHealth <= 0:
                            self.health += self.helmetHealth
                            self.helmetHealth = 0   # 注意合并后清零
                    else:
                        self.health += self.helmetType2Health
                        self.helmetType2Health = 0
            elif self.helmet:   # 不存在二类防具，但是存在一类防具
                self.helmetHealth -= damage
                if self.helmetHealth <= 0:
                    self.health += self.helmetHealth
                    self.helmetHealth = 0   # 注意合并后清零
            else:   # 没有防具
                self.health -= damage
        elif damageType == c.ZOMBIE_COMMON_DAMAGE:  # 无视二类防具，将攻击一类防具与本体视为整体的攻击
            if self.helmet:   # 存在一类防具
                self.helmetHealth -= damage
                if self.helmetHealth <= 0:
                    self.health += self.helmetHealth
                    self.helmetHealth = 0   # 注意合并后清零
            else:   # 没有一类防具
                self.health -= damage
        elif damageType == c.ZOMBIE_RANGE_DAMAGE:
            # 从第二类防具开始逐级传递
            if self.helmetType2:
                self.helmetType2Health -= damage
                if self.helmetType2Health <= 0:
                    if self.helmet:
                        self.helmetHealth -= damage # 注意范围伤害中这里还有一个攻击
                        self.helmetHealth += self.helmetType2Health # 注意self.helmetType2Health已经带有正负
                        self.helmetType2Health = 0  # 注意合并后清零
                        if self.helmetHealth <= 0:
                            self.health += self.helmetHealth
                            self.helmetHealth = 0   # 注意合并后清零
                    else:
                        self.health -= damage   # 注意范围伤害中这里还有一个攻击
                        self.health += self.helmetType2Health
                        self.helmetType2Health = 0
            elif self.helmet:   # 不存在二类防具，但是存在一类防具
                self.helmetHealth -= damage
                if self.helmetHealth <= 0:
                    self.health += self.helmetHealth
                    self.helmetHealth = 0   # 注意合并后清零
            else:   # 没有防具
                self.health -= damage
        elif damageType == c.ZOMBIE_ASH_DAMAGE:
            self.health -= damage   # 无视任何防具
        elif damageType == c.ZOMBIE_WALLNUT_BOWLING_DANMAGE:
            # 逻辑：对防具的多余伤害不传递
            # 以后增设铁门后可能需要设置侧面冲撞特殊性
            if self.helmetType2:
                self.helmetType2Health -= damage
            elif self.helmet:   # 不存在二类防具，但是存在一类防具
                self.helmetHealth -= damage
            else:   # 没有防具
                self.health -= damage
        else:
            print('警告：植物攻击类型错误，现在默认进行类豌豆射手型攻击')
            setDamage(damage, effect=effect, damageType=c.ZOMBIE_DEAFULT_DAMAGE)
        
        # 记录攻击时间              
        self.hit_timer = self.current_time

    def setWalk(self):
        self.state = c.WALK
        self.animate_interval = self.walk_animate_interval

        if self.helmet or self.helmetType2: # 这里暂时没有考虑同时有两种防具的僵尸
            self.changeFrames(self.helmet_walk_frames)
        elif self.lostHead:
            self.changeFrames(self.losthead_walk_frames)
        else:
            self.changeFrames(self.walk_frames)

        if self.canSwim:
            if self.rect.right <= c.MAP_POOL_FRONT_X:
                self.swimming = True
                self.changeFrames(self.swim_frames)
                # 同样没有兼容双防具
                if self.helmet:
                    if self.helmetHealth <= 0:
                        self.changeFrames(self.swim_frames)
                        self.helmet = False
                    else:
                        self.changeFrames(self.helmet_swim_frames)
                if self.helmetType2:
                    if self.helmetType2Health <= 0:
                        self.changeFrames(self.swim_frames)
                        self.helmetType2 = False
                    else:
                        self.changeFrames(self.helmet_swim_frames)

    def setAttack(self, prey, is_plant=True):
        self.prey = prey  # prey can be plant or other zombies
        self.prey_is_plant = is_plant
        self.state = c.ATTACK
        self.attack_timer = self.current_time
        self.animate_interval = self.attack_animate_interval

        if self.helmet or self.helmetType2: # 这里暂时没有考虑同时有两种防具的僵尸
            self.changeFrames(self.helmet_attack_frames)
        elif self.lostHead:
            self.changeFrames(self.losthead_attack_frames)
        else:
            self.changeFrames(self.attack_frames)

    def setDie(self):
        self.state = c.DIE
        self.animate_interval = self.die_animate_interval
        self.changeFrames(self.die_frames)

    def setBoomDie(self):
        self.health = 0
        self.state = c.DIE
        self.animate_interval = self.boomDie_animate_interval
        self.changeFrames(self.boomdie_frames)

    def setFreeze(self, ice_trap_image):
        self.old_state = self.state
        self.state = c.FREEZE
        self.freeze_timer = self.current_time
        self.ice_trap_image = ice_trap_image
        self.ice_trap_rect = ice_trap_image.get_rect()
        self.ice_trap_rect.centerx = self.rect.centerx
        self.ice_trap_rect.bottom = self.rect.bottom

    def drawFreezeTrap(self, surface):
        if self.state == c.FREEZE:
            surface.blit(self.ice_trap_image, self.ice_trap_rect)

    def setHypno(self):
        self.is_hypno = True
        self.setWalk()
        # 播放魅惑音效
        pg.mixer.Sound(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))) ,"resources", "sound", "hypnoed.ogg")).play()


class ZombieHead(Zombie):
    def __init__(self, x, y):
        Zombie.__init__(self, x, y, c.ZOMBIE_HEAD, 0)
        self.state = c.DIE

    def loadImages(self):
        self.die_frames = []
        die_name = self.name
        self.loadFrames(self.die_frames, die_name)
        self.frames = self.die_frames

    def setWalk(self):
        self.animate_interval = 100


class NormalZombie(Zombie):
    def __init__(self, x, y, head_group):
        Zombie.__init__(self, x, y, c.NORMAL_ZOMBIE, head_group)

    def loadImages(self):
        self.walk_frames = []
        self.attack_frames = []
        self.losthead_walk_frames = []
        self.losthead_attack_frames = []
        self.die_frames = []
        self.boomdie_frames = []

        walk_name = self.name
        attack_name = self.name + 'Attack'
        losthead_walk_name = self.name + 'LostHead'
        losthead_attack_name = self.name + 'LostHeadAttack'
        die_name = self.name + 'Die'
        boomdie_name = c.BOOMDIE

        frame_list = [self.walk_frames, self.attack_frames, self.losthead_walk_frames,
                      self.losthead_attack_frames, self.die_frames, self.boomdie_frames]
        name_list = [walk_name, attack_name, losthead_walk_name,
                     losthead_attack_name, die_name, boomdie_name]

        for i, name in enumerate(name_list):
            self.loadFrames(frame_list[i], name)

        self.frames = self.walk_frames

# 路障僵尸
class ConeHeadZombie(Zombie):
    def __init__(self, x, y, head_group):
        Zombie.__init__(self, x, y, c.CONEHEAD_ZOMBIE, head_group, helmetHealth=c.CONEHEAD_HEALTH)

    def loadImages(self):
        self.helmet_walk_frames = []
        self.helmet_attack_frames = []
        self.walk_frames = []
        self.attack_frames = []
        self.losthead_walk_frames = []
        self.losthead_attack_frames = []
        self.die_frames = []
        self.boomdie_frames = []

        helmet_walk_name = self.name
        helmet_attack_name = self.name + 'Attack'
        walk_name = c.NORMAL_ZOMBIE
        attack_name = c.NORMAL_ZOMBIE + 'Attack'
        losthead_walk_name = c.NORMAL_ZOMBIE + 'LostHead'
        losthead_attack_name = c.NORMAL_ZOMBIE + 'LostHeadAttack'
        die_name = c.NORMAL_ZOMBIE + 'Die'
        boomdie_name = c.BOOMDIE

        frame_list = [self.helmet_walk_frames, self.helmet_attack_frames,
                      self.walk_frames, self.attack_frames, self.losthead_walk_frames,
                      self.losthead_attack_frames, self.die_frames, self.boomdie_frames]
        name_list = [helmet_walk_name, helmet_attack_name,
                     walk_name, attack_name, losthead_walk_name,
                     losthead_attack_name, die_name, boomdie_name]

        for i, name in enumerate(name_list):
            self.loadFrames(frame_list[i], name)

        self.frames = self.helmet_walk_frames


class BucketHeadZombie(Zombie):
    def __init__(self, x, y, head_group):
        Zombie.__init__(self, x, y, c.BUCKETHEAD_ZOMBIE, head_group, helmetHealth=c.BUCKETHEAD_HEALTH)

    def loadImages(self):
        self.helmet_walk_frames = []
        self.helmet_attack_frames = []
        self.walk_frames = []
        self.attack_frames = []
        self.losthead_walk_frames = []
        self.losthead_attack_frames = []
        self.die_frames = []
        self.boomdie_frames = []

        helmet_walk_name = self.name
        helmet_attack_name = self.name + 'Attack'
        walk_name = c.NORMAL_ZOMBIE
        attack_name = c.NORMAL_ZOMBIE + 'Attack'
        losthead_walk_name = c.NORMAL_ZOMBIE + 'LostHead'
        losthead_attack_name = c.NORMAL_ZOMBIE + 'LostHeadAttack'
        die_name = c.NORMAL_ZOMBIE + 'Die'
        boomdie_name = c.BOOMDIE

        frame_list = [self.helmet_walk_frames, self.helmet_attack_frames,
                      self.walk_frames, self.attack_frames, self.losthead_walk_frames,
                      self.losthead_attack_frames, self.die_frames, self.boomdie_frames]
        name_list = [helmet_walk_name, helmet_attack_name,
                     walk_name, attack_name, losthead_walk_name,
                     losthead_attack_name, die_name, boomdie_name]

        for i, name in enumerate(name_list):
            self.loadFrames(frame_list[i], name)

        self.frames = self.helmet_walk_frames


class FlagZombie(Zombie):
    def __init__(self, x, y, head_group):
        Zombie.__init__(self, x, y, c.FLAG_ZOMBIE, head_group)
        self.speed = 1.25

    def loadImages(self):
        self.walk_frames = []
        self.attack_frames = []
        self.losthead_walk_frames = []
        self.losthead_attack_frames = []
        self.die_frames = []
        self.boomdie_frames = []

        walk_name = self.name
        attack_name = self.name + 'Attack'
        losthead_walk_name = self.name + 'LostHead'
        losthead_attack_name = self.name + 'LostHeadAttack'
        die_name = c.NORMAL_ZOMBIE + 'Die'
        boomdie_name = c.BOOMDIE

        frame_list = [self.walk_frames, self.attack_frames, self.losthead_walk_frames,
                      self.losthead_attack_frames, self.die_frames, self.boomdie_frames]
        name_list = [walk_name, attack_name, losthead_walk_name,
                     losthead_attack_name, die_name, boomdie_name]

        for i, name in enumerate(name_list):
            self.loadFrames(frame_list[i], name)

        self.frames = self.walk_frames


class NewspaperZombie(Zombie):
    def __init__(self, x, y, head_group):
        Zombie.__init__(self, x, y, c.NEWSPAPER_ZOMBIE, head_group, helmetType2Health=c.NEWSPAPER_HEALTH)

    def loadImages(self):
        self.helmet_walk_frames = []
        self.helmet_attack_frames = []
        self.walk_frames = []
        self.attack_frames = []
        self.losthead_walk_frames = []
        self.losthead_attack_frames = []
        self.die_frames = []
        self.boomdie_frames = []

        helmet_walk_name = self.name
        helmet_attack_name = self.name + 'Attack'
        walk_name = self.name + 'NoPaper'
        attack_name = self.name + 'NoPaperAttack'
        losthead_walk_name = self.name + 'LostHead'
        losthead_attack_name = self.name + 'LostHeadAttack'
        die_name = self.name + 'Die'
        boomdie_name = c.BOOMDIE

        frame_list = [self.helmet_walk_frames, self.helmet_attack_frames,
                      self.walk_frames, self.attack_frames, self.losthead_walk_frames,
                      self.losthead_attack_frames, self.die_frames, self.boomdie_frames]
        name_list = [helmet_walk_name, helmet_attack_name,
                     walk_name, attack_name, losthead_walk_name,
                     losthead_attack_name, die_name, boomdie_name]

        for i, name in enumerate(name_list):
            if name == c.BOOMDIE:
                color = c.BLACK
            else:
                color = c.WHITE
            self.loadFrames(frame_list[i], name, color)

        self.frames = self.helmet_walk_frames

class FootballZombie(Zombie):
    def __init__(self, x, y, head_group):
        Zombie.__init__(self, x, y, c.FOOTBALL_ZOMBIE, head_group, helmetHealth=c.FOOTBALL_HELMET_HEALTH)
        self.speed = 1.88
        self.animate_interval = 50
        self.walk_animate_interval = 50
        self.attack_animate_interval = 60
        self.lostHead_animate_interval = 50
        self.die_animate_interval = 50

    def loadImages(self):
        self.helmet_walk_frames = []
        self.helmet_attack_frames = []
        self.walk_frames = []
        self.attack_frames = []
        self.losthead_walk_frames = []
        self.losthead_attack_frames = []
        self.die_frames = []
        self.boomdie_frames = []

        helmet_walk_name = self.name
        helmet_attack_name = self.name + 'Attack'
        walk_name = self.name + 'LostHelmet'
        attack_name = self.name + 'LostHelmetAttack'
        losthead_walk_name = self.name + 'LostHead'
        losthead_attack_name = self.name + 'LostHeadAttack'
        die_name = self.name + 'Die'
        boomdie_name = c.BOOMDIE

        frame_list = [self.helmet_walk_frames, self.helmet_attack_frames,
                      self.walk_frames, self.attack_frames, self.losthead_walk_frames,
                      self.losthead_attack_frames, self.die_frames, self.boomdie_frames]
        name_list = [helmet_walk_name, helmet_attack_name,
                     walk_name, attack_name, losthead_walk_name,
                     losthead_attack_name, die_name, boomdie_name]

        for i, name in enumerate(name_list):
            self.loadFrames(frame_list[i], name)

        self.frames = self.helmet_walk_frames

class DuckyTubeZombie(Zombie):
    def __init__(self, x, y, head_group):
        Zombie.__init__(self, x, y, c.DUCKY_TUBE_ZOMBIE, head_group, canSwim=True)

    def loadImages(self):
        self.walk_frames = []
        self.swim_frames = []
        self.attack_frames = []
        self.losthead_walk_frames = []
        self.losthead_attack_frames = []
        self.die_frames = []
        self.boomdie_frames = []

        walk_name = self.name
        swim_name = self.name + 'Swim'
        attack_name = self.name + 'Attack'
        losthead_walk_name = self.name + 'LostHead'
        losthead_attack_name = self.name + 'LostHead'
        die_name = self.name + 'Die'
        boomdie_name = c.BOOMDIE

        frame_list = [self.walk_frames, self.swim_frames, self.attack_frames, self.losthead_walk_frames,
                      self.losthead_attack_frames, self.die_frames, self.boomdie_frames]
        name_list = [walk_name, swim_name, attack_name, losthead_walk_name,
                     losthead_attack_name, die_name, boomdie_name]

        for i, name in enumerate(name_list):
            self.loadFrames(frame_list[i], name)

        self.frames = self.walk_frames

class ConeHeadDuckyTubeZombie(Zombie):
    def __init__(self, x, y, head_group):
        Zombie.__init__(self, x, y, c.CONEHEAD_DUCKY_TUBE_ZOMBIE, head_group, helmetHealth=c.CONEHEAD_HEALTH ,canSwim=True)
        
    def loadImages(self):
        self.helmet_walk_frames = []
        self.walk_frames = []
        self.helmet_swim_frames = []
        self.swim_frames = []
        self.helmet_attack_frames = []
        self.attack_frames = []
        self.losthead_walk_frames = []
        self.losthead_attack_frames = []
        self.die_frames = []
        self.boomdie_frames = []

        helmet_walk_name = self.name
        helmet_swim_name = self.name + 'Swim'
        helmet_attack_name = self.name + 'Attack'
        walk_name = c.DUCKY_TUBE_ZOMBIE
        swim_name = c.DUCKY_TUBE_ZOMBIE + 'Swim'
        attack_name = c.DUCKY_TUBE_ZOMBIE + 'Attack'
        losthead_walk_name = c.DUCKY_TUBE_ZOMBIE + 'LostHead'
        losthead_attack_name = c.DUCKY_TUBE_ZOMBIE + 'LostHead'
        die_name = c.DUCKY_TUBE_ZOMBIE + 'Die'
        boomdie_name = c.BOOMDIE

        frame_list = [self.helmet_walk_frames, self.helmet_swim_frames, self.helmet_attack_frames, self.walk_frames, self.swim_frames, self.attack_frames, self.losthead_walk_frames,
                      self.losthead_attack_frames, self.die_frames, self.boomdie_frames]
        name_list = [helmet_walk_name, helmet_swim_name, helmet_attack_name, walk_name, swim_name, attack_name, losthead_walk_name,
                     losthead_attack_name, die_name, boomdie_name]

        for i, name in enumerate(name_list):
            self.loadFrames(frame_list[i], name)

        self.frames = self.helmet_walk_frames


class BucketHeadDuckyTubeZombie(Zombie):
    def __init__(self, x, y, head_group):
        Zombie.__init__(self, x, y, c.BUCKETHEAD_DUCKY_TUBE_ZOMBIE, head_group, helmetHealth=c.BUCKETHEAD_HEALTH ,canSwim=True)
        
    def loadImages(self):
        self.helmet_walk_frames = []
        self.walk_frames = []
        self.helmet_swim_frames = []
        self.swim_frames = []
        self.helmet_attack_frames = []
        self.attack_frames = []
        self.losthead_walk_frames = []
        self.losthead_attack_frames = []
        self.die_frames = []
        self.boomdie_frames = []

        helmet_walk_name = self.name
        helmet_swim_name = self.name + 'Swim'
        helmet_attack_name = self.name + 'Attack'
        walk_name = c.DUCKY_TUBE_ZOMBIE
        swim_name = c.DUCKY_TUBE_ZOMBIE + 'Swim'
        attack_name = c.DUCKY_TUBE_ZOMBIE + 'Attack'
        losthead_walk_name = c.DUCKY_TUBE_ZOMBIE + 'LostHead'
        losthead_attack_name = c.DUCKY_TUBE_ZOMBIE + 'LostHead'
        die_name = c.DUCKY_TUBE_ZOMBIE + 'Die'
        boomdie_name = c.BOOMDIE

        frame_list = [self.helmet_walk_frames, self.helmet_swim_frames, self.helmet_attack_frames, self.walk_frames, self.swim_frames, self.attack_frames, self.losthead_walk_frames,
                      self.losthead_attack_frames, self.die_frames, self.boomdie_frames]
        name_list = [helmet_walk_name, helmet_swim_name, helmet_attack_name, walk_name, swim_name, attack_name, losthead_walk_name,
                     losthead_attack_name, die_name, boomdie_name]

        for i, name in enumerate(name_list):
            self.loadFrames(frame_list[i], name)

        self.frames = self.helmet_walk_frames


class ScreenDoorZombie(Zombie):
    def __init__(self, x, y, head_group):
        Zombie.__init__(self, x, y, c.SCREEN_DOOR_ZOMBIE, head_group, helmetType2Health=c.SCREEN_DOOR_HEALTH)

    def loadImages(self):
        self.helmet_walk_frames = []
        self.helmet_attack_frames = []
        self.walk_frames = []
        self.attack_frames = []
        self.losthead_walk_frames = []
        self.losthead_attack_frames = []
        self.die_frames = []
        self.boomdie_frames = []

        helmet_walk_name = self.name
        helmet_attack_name = self.name + 'Attack'
        walk_name = c.NORMAL_ZOMBIE
        attack_name = c.NORMAL_ZOMBIE + 'Attack'
        losthead_walk_name = c.NORMAL_ZOMBIE + 'LostHead'
        losthead_attack_name = c.NORMAL_ZOMBIE + 'LostHeadAttack'
        die_name = c.NORMAL_ZOMBIE + 'Die'
        boomdie_name = c.BOOMDIE

        frame_list = [self.helmet_walk_frames, self.helmet_attack_frames,
                      self.walk_frames, self.attack_frames, self.losthead_walk_frames,
                      self.losthead_attack_frames, self.die_frames, self.boomdie_frames]
        name_list = [helmet_walk_name, helmet_attack_name,
                     walk_name, attack_name, losthead_walk_name,
                     losthead_attack_name, die_name, boomdie_name]

        for i, name in enumerate(name_list):
            self.loadFrames(frame_list[i], name)

        self.frames = self.helmet_walk_frames