import math
import os
import random
import sys
import time
import pygame as pg
from math import atan2, degrees, cos, sin

WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate

def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm

class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 0.9),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 0.9),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 0.9),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 0.9),  # 右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]

        #追加機能1始
        if key_lst[pg.K_LSHIFT]:
            self.speed = 20
        else:
            self.speed = 10
        #追加機能1終

        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rect.move_ip(self.speed*sum_mv[0], self.speed*sum_mv[1])
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-self.speed*sum_mv[0], -self.speed*sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]
        screen.blit(self.image, self.rect)

class Bomb(pg.sprite.Sprite):
    """
    爆弾に関するクラス
    """
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy: "Enemy", bird: Bird):
        """
        爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象のこうかとん
        """
        super().__init__()
        rad = random.randint(10, 50)  # 爆弾円の半径：10以上50以下の乱数
        self.image = pg.Surface((2*rad, 2*rad))
        color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)  
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height//2
        self.speed = 6

        #追加機能3始め
        self.active = True
        #追加機能3終


    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        #追加機能3始
        if not self.active:
            self.rect.move_ip((self.speed/2)*self.vx, (self.speed/2)*self.vy)
        else:
            #追加機能3終
            self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()

class Beam(pg.sprite.Sprite):
    def __init__(self, bird: Bird, angle: float = None):
        super().__init__()
        if angle is None:
            dx, dy = bird.dire
            norm = math.hypot(dx, dy)
            if norm == 0:
                dx, dy = 1, 0
                norm = 1
            angle = math.degrees(math.atan2(-dy, dx))
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        speed = 10
        self.vx *= speed
        self.vy *= speed

        base_img = pg.image.load("fig/beam.png")
        self.image = pg.transform.rotozoom(base_img, angle, 1.0)
        self.rect = self.image.get_rect()
        bird_center = bird.rect.center
        bird_w, bird_h = bird.rect.size
        self.rect.centerx = bird_center[0] + bird_w * self.vx / speed
        self.rect.centery = bird_center[1] + bird_h * self.vy / speed

    def update(self):
        self.rect.move_ip(self.vx, self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()

class NeoBeam:
    def __init__(self, bird: Bird, num: int = 5):
        self.beams = self.gen_beams(bird, num)

    def gen_beams(self, bird: Bird, num: int):
        beams = []
        if num <= 1:
            return [Beam(bird)]
        base_angle = math.degrees(math.atan2(-bird.dire[1], bird.dire[0]))
        step = 100 // (num - 1)
        for i in range(num):
            angle = base_angle - 50 + step * i
            beams.append(Beam(bird, angle))
        return beams

class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "Bomb|Enemy", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load(f"fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()

class Enemy(pg.sprite.Sprite):
    """
    敵機に関するクラス
    """
    imgs = [pg.image.load(f"fig/alien{i}.png") for i in range(1, 4)]
    
    def __init__(self):
        super().__init__()
        self.image = pg.transform.rotozoom(random.choice(__class__.imgs), 0, 0.8)
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        self.vx, self.vy = 0, +6
        self.bound = random.randint(50, HEIGHT//2)  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.interval = random.randint(50, 300)  # 爆弾投下インターバル

    def update(self):
        """
        敵機を速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.move_ip(self.vx, self.vy)

class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 0
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)

#追加機能2始
class Gravity(pg.sprite.Sprite):
    """
    重力場に関するクラス
    """

    def __init__(self, life: int):
        super().__init__()
        self.image = pg.Surface((WIDTH, HEIGHT))
        pg.draw.rect(self.image, (0, 0, 0), (0, 0, WIDTH, HEIGHT))  # 真っ黒な矩形
        self.image.set_alpha(128)  # 半透明
        self.rect = self.image.get_rect()
        self.life = life  # 発動時間
    
    def update(self):
        self.life -= 1
        if self.life <= 0:
            self.kill()  # 時間切れで削除
#追加機能2終

#追加機能3始
class EMP(pg.sprite.Sprite):
    """
    EMPに関するクラス
    """

    def __init__(self, emys: pg.sprite.Group, bombs: pg.sprite.Group, screen: pg.Surface):
        super().__init__()
        # 見た目：黄色半透明スクリーン
        self.image = pg.Surface((WIDTH, HEIGHT))
        self.image.fill((255, 255, 0))
        self.image.set_alpha(128)
        self.rect = self.image.get_rect()

        # 敵機の無効化
        for emy in emys:
            emy.interval = math.inf  # 爆弾を落とさなくする
            emy.image = pg.transform.laplacian(emy.image)  # ラプラシアンフィルタ

        # 爆弾の無効化
        for bomb in bombs:
            bomb.active = False  # ボムスピードダウン

            
        # 表示時間カウンタ
        self.life = 3

    def update(self):
        self.life -= 1
        if self.life <= 0:
            self.kill()
#追加機能3終
class Shield(pg.sprite.Sprite):
    def __init__(self, bird, lifetime=400):
        super().__init__()
        self.lifetime = lifetime

        # Step 1: 空のSurfaceを生成（透明背景）
        surf = pg.Surface((20, 80), pg.SRCALPHA)

        # Step 2: Surfaceにrectを描画
        pg.draw.rect(surf, (0, 0, 255), (0, 0, 20, 80))

        # Step 3: こうかとんの向きを取得（vx, vy）
        vx, vy = bird.dire  # direは向きの単位ベクトル（タプル）

        # Step 4: 角度を計算
        angle = degrees(atan2(-vy, vx))  # yは反転

        # Step 5: Surfaceを回転
        self.image = pg.transform.rotate(surf, angle)

        # Step 6: こうかとんの向きに応じて位置を調整
        offset = pg.math.Vector2(bird.rect.width, 0).rotate(-angle)  # こうかとん1体分ずらす
        self.rect = self.image.get_rect(center=bird.rect.center + offset)

        self.bird = bird
        self.offset = offset
        self.angle = angle

    def update(self):
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()
        # 防御壁を常にこうかとんの前に保つ
        self.rect = self.image.get_rect(center=self.bird.rect.center + self.offset)

def main():
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load(f"fig/pg_bg.jpg")
    score = Score()

    bird = Bird(3, (900, 400))
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()

    #追加機能2始
    gravity_fields = pg.sprite.Group()
    #追加機能2終

     #追加機能3始
    emp_effects = pg.sprite.Group()
    #追加機能3終
    
    shields = pg.sprite.Group()

    tmr = 0
    clock = pg.time.Clock()
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0

            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:
                    if key_lst[pg.K_LSHIFT]:
                        for b in NeoBeam(bird, 5).beams:
                            beams.add(b)
                    else:
                        beams.add(Beam(bird))

                if event.key == pg.K_s and score.value >= 50 and len(shields) == 0:
                    shields.add(Shield(bird, 400))
                    score.value -= 50

            #追加機能2始
            if event.type == pg.KEYDOWN and event.key == pg.K_RETURN and score.value >= 200:
                score.value -= 200
                gravity_fields.add(Gravity(400))
            #追加機能2終

            #追加機能3始
            if event.type == pg.KEYDOWN and event.key == pg.K_e and score.value >= 20:
                score.value -= 20
                emp_effects.add(EMP(emys, bombs, screen))
            #追加機能3終

        screen.blit(bg_img, [0, 0])

        if tmr % 200 == 0:  # 200フレームに1回，敵機を出現させる
            emys.add(Enemy())

        for emy in emys:
            if emy.state == "stop" and tmr % emy.interval == 0:
                bombs.add(Bomb(emy, bird))

        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():
            exps.add(Explosion(emy, 100))
            score.value += 10
            bird.change_img(6, screen)

        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():
            exps.add(Explosion(bomb, 50))
            score.value += 1

        # シールドと爆弾の衝突処理
        for bomb in pg.sprite.groupcollide(bombs, shields, True, False).keys():
            exps.add(Explosion(bomb, 50))

        #追加機能2始
        for gravity in gravity_fields:
            for bomb in pg.sprite.spritecollide(gravity, bombs, True):
                exps.add(Explosion(bomb, 20))
            for emy in pg.sprite.spritecollide(gravity, emys, True):
                exps.add(Explosion(emy, 20))
                bomb.kill()
        #追加機能2終

        for bomb in pg.sprite.spritecollide(bird, bombs, True):  # こうかとんと衝突した爆弾リスト
            if bomb.active:
                bird.change_img(8, screen)  # こうかとん悲しみエフェクト
                score.update(screen)
                pg.display.update()
                time.sleep(2)
                return

        bird.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        emys.update()
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        shields.update()
        shields.draw(screen)
        exps.update()
        exps.draw(screen)
        score.update(screen)

        #追加機能2始
        gravity_fields.update()
        gravity_fields.draw(screen)
        #追加機能2終

        #追加機能3始
        emp_effects.update()
        emp_effects.draw(screen)
        #追加機能3終

        pg.display.update()
        tmr += 1
        clock.tick(50)
    #い

if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()