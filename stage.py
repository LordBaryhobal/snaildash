#Snaildash is a small game created in the scope of a school project
#Copyright (C) 2022  Louis HEREDERO & Mathéo BENEY

class Stage:
    """Enum representing the game process state"""
    
    STOP = -1
    MAIN_MENU = 0
    WAITING_OPPONENT = 1
    COUNTDOWN = 2
    IN_GAME = 3
    GAME_TO_BREAKDOWN = 4
    BREAKDOWN_BAR = 5
    BREAKDOWN_BONUSES = 6
    TUTORIAL = 7
    CREDITS = 8