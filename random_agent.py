import random

class RandomAgent:
    def __init__(self, N):
        self.N = N
        self.x, self.y = 0, 0  # Start at (0,0)
        self.dir = 1
        self.has_gold = False
        self.action_log = []
        self.visited = set()

    def next_action(self, percepts):
        # Ưu tiên lấy vàng nếu thấy glitter
        if percepts.get('glitter', False):
            self.action_log.append('grab')
            self.has_gold = True
            return 'grab'
            
        # Về nhà nếu đã có vàng và ở (0,0)
        if self.has_gold and (self.x, self.y) == (0, 0):
            self.action_log.append('climb')
            return 'climb'
            
        # Về nhà nếu đã có vàng
        if self.has_gold:
            action = self.move_towards_home()
            self.action_log.append(action)
            return action

        # Random action
        actions = ['forward', 'left', 'right']
        if percepts.get('stench', False):
            # Nếu có stench, có thể bắn tên
            actions.append('shoot')
            
        action = random.choice(actions)
        self.action_log.append(action)
        return action

    def move_towards_home(self):
        """Di chuyển về nhà một cách đơn giản"""
        if self.x > 0:
            if self.dir == 3:  # Đang nhìn trái
                return 'forward'
            elif self.dir == 1:  # Đang nhìn phải
                return 'left'
            else:
                return 'left'
        elif self.y > 0:
            if self.dir == 2:  # Đang nhìn xuống
                return 'forward'
            elif self.dir == 0:  # Đang nhìn lên
                return 'right'
            else:
                return 'right'
        else:
            return 'climb'

    def update_agent_state(self, action, percepts):
        if action == 'forward':
            dx, dy = [(0,1), (1,0), (0,-1), (-1,0)][self.dir]
            self.x += dx
            self.y += dy
            self.visited.add((self.x, self.y))
        elif action == 'left':
            self.dir = (self.dir - 1) % 4
        elif action == 'right':
            self.dir = (self.dir + 1) % 4

    def get_action_log(self):
        return self.action_log 
