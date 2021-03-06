"""
The Client is slave: 
- it sends only the player inputs to the server.
- every frame, it displays the server's last received data
Pros: the server is the only component with game logic, 
so all clients see the same game at the same time (consistency, no rollbacks).
Cons: lag between player input and screen display (one round-trip).
But the client can smooth the lag by interpolating the position of the boxes. 
"""
import sys
from network import Handler, poll

from pygame import Rect, init as init_pygame
from pygame.display import set_mode, update as update_pygame_display
from pygame.draw import rect as draw_rect
from pygame.event import get as get_pygame_events
from pygame.locals import KEYDOWN, QUIT, K_ESCAPE, K_UP, K_DOWN, K_LEFT, K_RIGHT
from pygame.time import Clock


borders = []
pellets = []
players = {}  # map player name to rectangle
myname = None
dx, dy = 0, 1 # Down
delta_time = 1 / 50.0
     
init_pygame()
screen = set_mode((400, 300))
clock = Clock()

def make_rect(quad):  # make a pygame.Rect from a list of 4 integers
    x, y, w, h = quad
    return Rect(x, y, w, h)
    
class Client(Handler):
            
    def on_msg(self, data):
        global borders, pellets, players, myname, dx, dy
        sys.stdout.flush()
        if data['msg_type'] == 'state':
            borders = [make_rect(b) for b in data['borders']]
            pellets = [make_rect(p) for p in data['pellets']]
            players = {name: make_rect(p) for name, p in data['players'].items()}
            myname = data['myname']
        elif data['msg_type'] == 'die':
            dx, dy = 0, 1
        
client = Client('localhost', 8888)  # connect asynchronously

valid_inputs = {K_UP: 'up', K_DOWN: 'down', K_LEFT: 'left', K_RIGHT: 'right'}

counter = 0
while 1:
    
    poll()  # push and pull network messages

    # send valid inputs to the server
    for event in get_pygame_events():  
        if event.type == QUIT:
            exit()
        if event.type == KEYDOWN:
            key = event.key
            if key == K_ESCAPE:
                exit()
            elif key in valid_inputs:
                if key == K_UP:
                    dx, dy = 0, -1
                elif key == K_DOWN:
                    dx, dy = 0, 1
                elif key == K_LEFT:
                    dx, dy = -1, 0
                elif key == K_RIGHT:
                    dx, dy = 1, 0
                msg = {'input': valid_inputs[key]}
                client.do_send(msg)
    
    # draw everything
    screen.fill((0, 0, 64))  # dark blue
    [draw_rect(screen, (0, 191, 255), b) for b in borders]  # deep sky blue 
    [draw_rect(screen, (255, 192, 203), p) for p in pellets]  # shrimp
    for name, p in players.items():
        if name != myname:
            draw_rect(screen, (255, 0, 0), p)  # red
    if myname and myname in players.keys():
        if counter % 2 == 0:
            players[myname].move_ip(dx, dy)  # update position
        draw_rect(screen, (0, 191, 255), players[myname])  # deep sky blue
    
    update_pygame_display()
    
    counter += 1
    clock.tick(50)  # frames per second, independent of server frame rate
