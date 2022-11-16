class Player:
    COLORS = [(255,100,0), (0,100,255)]
    TRAIL_COLORS = [(255,150,100), (100,150,255)]
    STUN_TIMER = 7
    DAMAGE = 2

    def __init__(self, game, i, x, y):
        self.game = game
        self.i = i
        self.x = x
        self.y = y
        self.stunned = False
        self.stun_start = 0
        self.health = 20
    
    def move(self, dx, dy):
        self.game.trails[self.y, self.x] = self.i
        self.x += dx
        self.y += dy
        self.game.moved = True
        self.game.end_turn()
    
    def hurt(self):
        self.health -= Player.DAMAGE