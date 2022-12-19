#Snaildash is a small game created in the scope of a school project
#Copyright (C) 2022  Louis HEREDERO & Mathéo BENEY

import json
import os
import requests
import struct
import time

import pygame

from display_manager import DisplayManager
from game import Game
from gui import GUI
from socket_handler import SocketHandler
from sound_manager import SoundManager
from stage import Stage
from tutorial import Tutorial

class Manager:
    """Main class managing the whole game process, menus and communication"""
    
    WIDTH, HEIGHT = 800, 800 #1920, 1080
    FPS = 30
    
    COUNTDOWN_DUR = 4  # Duration in seconds of the start countdown
    BREAKDOWN_IN_DUR = 2  # Duration in seconds of the game to breakdown transition
    BREAKDOWN_BAR_DUR = 4  # Duration in seconds of the progress bar animation
    BREAKDOWN_BAR_PAUSE = 0.5  # Duration in seconds before the progress bar end fill
    BREAKDOWN_BAR_END_DUR = 0.2  # Duration in seconds of the bar end fill
    BREAKDOWN_INTERVAL = 1  # Interval in seconds between each bonus score reveal

    def __init__(self):
        """Initializes a Manager instance"""
        
        pygame.init()
        pygame.display.set_caption("Snaildash")
        self.clock = pygame.time.Clock()
        self.stage = Stage.MAIN_MENU
        self.socket_handler = SocketHandler(self)
        self.game = Game(self)
        self.gui = GUI()
        self.tutorial = Tutorial(self)
        self.display_manager = DisplayManager(self)
        self._is_host = False
        self.load_config()
        
        self.startup_time = time.time()
        self.last_ping = 0
        self.win = pygame.display.set_mode([self.WIDTH, self.HEIGHT], pygame.RESIZABLE)#, pygame.FULLSCREEN)
    
    def is_host(self):
        """Returns whether this instance is the host or not

        Returns:
            bool: True if host, False if guest
        """
        return self._is_host
    
    def init_host(self):
        """Initializes this instance as the host"""
        self._is_host = True
        self.game.init_host()
    
    def init_guest(self):
        """Initializes this instance as the guest"""
        self._is_host = False
        self.game.init_guest()
    
    def quit(self, send=False):
        """Exits the game and closes the main window

        Args:
            send (bool, optional): Whether the command should be sent to the other device. Defaults to False.
        """
        
        if send:
            self.socket_handler.send(b"quit")
        self.socket_handler.quit()
        self.stage = Stage.STOP
    
    def quit_game(self):
        """Quits a running game and returns to main menu"""
        
        self.socket_handler.quit()
        self.gui.set_menu("main")
        self.gui.visible = True
        self.stage = Stage.MAIN_MENU
    
    def mainloop(self):
        """Main loop, calls logic and rendering related methods"""
        
        while self.stage != Stage.STOP:
            pygame.display.set_caption(f"Snaildash - {self.clock.get_fps():.2f}fps")
            events = pygame.event.get()
            self.handle_events(events)
            self.display_manager.render(self.win)
            pygame.display.flip()
            self.clock.tick(self.FPS)
    
    def time(self):
        """Returns the relative time since game start"""
        return time.time()-self.time_origin
    
    def handle_events(self, events):
        """Handles pygame events

        Args:
            events (list[pygame.Event]): list of pygame events
        """
        
        for event in events:
            if event.type == pygame.QUIT:
                self.quit(True)
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_0 and event.mod & pygame.KMOD_CTRL:
                    self.quit(True)
                
                if self.stage == Stage.IN_GAME:
                    self.game.handle_key(event)
                else:
                    self.gui.on_key_down(event)
            
            elif event.type == pygame.VIDEORESIZE:
                self.WIDTH, self.HEIGHT = event.w, event.h
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.on_mouse_down(event)
            
            elif event.type == pygame.MOUSEBUTTONUP:
                self.on_mouse_up(event)
            
            elif event.type == pygame.USEREVENT:
                self.game.start_turn()
            
            elif event.type == pygame.USEREVENT+1:
                SoundManager.get(["click.wav"]).play()
                
                name = event.name
                if name == "main.play":
                    self.gui.set_menu("nameinput")
                    self.stage = Stage.NAMEINPUT
                
                elif name == "nameinput.connect":
                    self.username = self.gui.get_menu().components[1].txt
                    if self.username == "":
                        continue
                    self.socket_handler.connect()
                    self.gui.set_menu("waiting")
                    self.stage = Stage.WAITING_OPPONENT
                
                elif name == "main.tutorial":
                    self.tutorial.start_time = time.time()
                    self.tutorial.slide = 0
                    self.gui.set_menu("tutorial")
                    self.gui.get_menu().components[1].visible = False
                    self.gui.get_menu().components[2].visible = True
                    self.stage = Stage.TUTORIAL
                
                elif name == "main.credits":
                    self.gui.set_menu("credits")
                    self.stage = Stage.CREDITS
                
                elif name in ["waiting.main", "credits.main", "breakdown.main", "tutorial.main"]:
                    self.gui.set_menu("main")
                    self.stage = Stage.MAIN_MENU
                    if name == "waiting.main":
                        self.socket_handler.running = False
                    
                    elif name == "breakdown.main":
                        self.socket_handler.quit()
                
                elif name == "tutorial.prev":
                    self.tutorial.prev_slide()
                
                elif name == "tutorial.next":
                    self.tutorial.next_slide()
        
        if self.stage == Stage.COUNTDOWN:
            cur_time = time.time()
            rem = self.countdown_start+self.COUNTDOWN_DUR-cur_time
            
            if cur_time-self.last_ping > 0.1:
                self.socket_handler.send(b"ping")  # keep tunnel open
                self.last_ping = cur_time
                
            if rem <= 0:
                self.stage = Stage.IN_GAME
                #pygame.mixer.music.play()
                self.game.start_time = self.time()
                self.game.start_turn()

        elif self.stage == Stage.IN_GAME:
            self.game.loop()
            rem = self.game.start_time+self.game.DURATION-self.time()
            if rem <= 0:
                self.send_score()
                self.stage = Stage.GAME_TO_BREAKDOWN
                self.game_to_breakdown_start = self.time()
        
        elif self.stage == Stage.GAME_TO_BREAKDOWN:
            rem = self.game_to_breakdown_start+self.BREAKDOWN_IN_DUR-self.time()
            if rem <= 0:
                self.stage = Stage.BREAKDOWN_BAR
                self.breakdown_bar_start = self.time()
        
        elif self.stage == Stage.BREAKDOWN_BAR:
            rem = self.breakdown_bar_start+self.BREAKDOWN_BAR_DUR-self.time()
            if rem <= 0:
                self.stage = Stage.BREAKDOWN_BONUSES
                self.breakdown_start = self.time()
    
    def on_mouse_down(self, event):
        """Handles a pygame.MOUSEBUTTONDOWN event

        Args:
            event (pygame.Event): pygame event
        """
        self.gui.on_mouse_down(event)
    
    def on_mouse_up(self, event):
        """Handles a pygame.MOUSEBUTTONUP event

        Args:
            event (pygame.Event): pygame event
        """
        self.gui.on_mouse_up(event)
    
    def on_connected(self):
        """Starts game when an opponent is found and the connection is established"""
        
        if self.stage == Stage.WAITING_OPPONENT:
            self.play()
    
    def on_receive(self, data):
        """Processes data received from the other device

        Args:
            data (bytes): received data
        """
        
        if data == b"quit":
            self.quit_game()
            return

        if self.stage == Stage.IN_GAME:
            if data.startswith(b"turnEnd"):
                if data.startswith(b"turnEndHost"):
                    x1, y1, d1, ds1, x2, y2, d2, ds2, trails_count, bonus_count = struct.unpack(">BBBBBBBBBB", data[11:21])
                    data = data[21:]
                    trails = []
                    for j in range(trails_count):
                        x, y, i = struct.unpack(">BBB", data[3*j:3*j+3])
                        trails.append((x, y, i))

                    data = data[3*trails_count:]
                    
                    bonus_dict = {}
                    for j in range(bonus_count):
                        x, y, i = struct.unpack(">BBB", data[3*j:3*j+3])
                        bonus_dict[(x, y)] = i
                    
                    data = data[3*bonus_count:]
                    col_start, col_x, col_y, bonus_scores_count = struct.unpack(">dBBB", data[:11])
                    data = data[11:]
                    bonus_scores = []
                    for i in range(bonus_scores_count):
                        r, b = struct.unpack(">II", data[8*i:8*i+8])
                        bonus_scores.append([r,b])
                    
                    for i in range(2):
                        self.game.players[i].reinforced_placed = bonus_scores[1][i]
                        self.game.players[i].dashed_count = bonus_scores[2][i]
                        self.game.players[i].used_bonus = bonus_scores[3][i]

                else:
                    x1, y1, d1, ds1, x2, y2, d2, ds2 = struct.unpack(">BBBBBBBB", data[7:])
                    trails = None
                    bonus_dict = None
                    col_start, col_x, col_y = 0, 0, 0
                
                self.game.sync(x1, y1, d1, ds1, x2, y2, d2, ds2, trails, bonus_dict, col_start, col_x, col_y)
                if self.is_host():
                    self.game.end_turn()
                
                else:
                    pygame.event.post(pygame.event.Event(pygame.USEREVENT))
    
    def play(self, send=False):
        """Starts the game

        Args:
            send (bool, optional): Whether the command should be sent to the other device. Defaults to False.
        """
        
        if send:
            self.socket_handler.send(b"start")
        
        self.game.reset()
        
        self.countdown_start = time.time()
        self.stage = Stage.COUNTDOWN
        self.time_origin = time.time()
        self.gui.visible = False
    
    def get_bonus_scores(self):
        """Returns a list of bonus scores for each player

        Returns:
            list[list[str, int, int]]: list of bonus scores
        """
        
        p1, p2 = self.game.players
        scores = [
            ["Zone couverte", *self.game.get_trail_count()],
            ["Bave renforcée", p1.reinforced_placed, p2.reinforced_placed],
            ["Dash", p1.dashed_count, p2.dashed_count],
            ["Bonus", p1.used_bonus, p2.used_bonus]
        ]

        scores.append(["Total", sum(map(lambda s: s[1], scores)), sum(map(lambda s: s[2], scores))])
        return scores
    
    def load_config(self):
        if not os.path.exists("config.json"):
            print("#"*80)
            print("You are missing config.json")
            print("Please contact the developers")
            print("if you have no idea what this is about !")
            print("#"*80)
            exit()
        with open("config.json", encoding="utf-8") as conffile:
            self.config = json.load(conffile)
    
    def send_score(self):
        data = {
            "name": self.username,
            "score": self.get_bonus_scores()[-1][self.game.player.i + 1]
        }
        requests.post(self.config["score_url"], data)