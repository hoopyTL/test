import json
import random

class Cell:
    def __init__(self):
        self.has_pit = False
        self.has_wumpus = False
        self.has_gold = False

class Environment:
    def __init__(self, N=4, K=1, p=0.2, seed=42, mapfile=None):
        self.N = N
        self.K = K
        self.p = p
        self.mapfile = mapfile
        self.agent_alive = True
        self.gold_grabbed = False

        # Thêm scoring system
        self.score = 0
        self.agent_arrows = 1  # 1 cung tên như yêu cầu
        
        # Thêm wumpus movement
        self.wumpus_move_counter = 0
        self.wumpus_move_interval = 5  # Wumpus di chuyển sau mỗi 5 bước
        
        # Thêm arrow tracking
        self.arrow_in_flight = False
        self.arrow_target = None
        self.arrow_direction = None
        
        self.map = [[Cell() for _ in range(N)] for _ in range(N)]

        self.agent_pos = (0, 0)
        self.agent_dir = 1  # 0: up, 1: right, 2: down, 3: left
        self.wumpus_alive = []
        if mapfile:
            self.load_from_json(mapfile)
        else:
            self.random_map(seed=seed)
        # Wumpus alive flags (support multi-wumpus)
        if not self.wumpus_alive:
            # Count wumpus
            cnt = sum(self.map[i][j].has_wumpus for i in range(N) for j in range(N))
            self.wumpus_alive = [True] * cnt

    def random_map(self, seed=42):
        random.seed(seed)
        self.map = [[Cell() for _ in range(self.N)] for _ in range(self.N)]
        self.agent_pos = (0, 0)
        self.agent_dir = 1
        # Random pit
        for i in range(self.N):
            for j in range(self.N):
                if (i, j) == (0, 0): continue
                if random.random() < self.p:
                    self.map[i][j].has_pit = True
        # Wumpus
        wumpus_cnt = 0
        while wumpus_cnt < self.K:
            x, y = random.randint(0, self.N-1), random.randint(0, self.N-1)
            if (x, y) != (0, 0) and not self.map[x][y].has_pit and not self.map[x][y].has_wumpus:
                self.map[x][y].has_wumpus = True
                wumpus_cnt += 1
        # Gold
        while True:
            x, y = random.randint(0, self.N-1), random.randint(0, self.N-1)
            if (x, y) != (0, 0) and not self.map[x][y].has_pit and not self.map[x][y].has_wumpus and not self.map[x][y].has_gold:
                self.map[x][y].has_gold = True
                break
        # Wumpus alive
        self.wumpus_alive = [True] * self.K

    def load_from_json(self, filename):
        with open(filename, 'r') as f:
            data = json.load(f)
        if isinstance(data, list):
            self.N = len(data)
            self.map = [[Cell() for _ in range(self.N)] for _ in range(self.N)]
            for i in range(self.N):
                for j in range(self.N):
                    c = data[i][j]
                    self.map[i][j].has_pit = c.get("pit", False)
                    self.map[i][j].has_wumpus = c.get("wumpus", False)
                    self.map[i][j].has_gold = c.get("gold", False)
            self.agent_pos = (0, 0)
            self.agent_dir = 1
        else:
            # Lấy N lớn nhất từ các phần tử
            coords = []
            for k in ["pit", "wumpus", "gold"]:
                coords.extend(data.get(k, []))
            if "agent" in data and "pos" in data["agent"]:
                coords.append(data["agent"]["pos"])
            self.N = max(max(coord) for coord in coords) + 1 if coords else 4
            self.map = [[Cell() for _ in range(self.N)] for _ in range(self.N)]
            # Agent
            self.agent_pos = tuple(data["agent"]["pos"])
            self.agent_dir = data["agent"].get("dir", 1)
            # Wumpus
            for xy in data.get("wumpus", []):
                self.map[xy[0]][xy[1]].has_wumpus = True
            # Pit
            for xy in data.get("pit", []):
                self.map[xy[0]][xy[1]].has_pit = True
            # Gold
            for xy in data.get("gold", []):
                self.map[xy[0]][xy[1]].has_gold = True
            # Wumpus alive (nếu nhiều wumpus)
            self.wumpus_alive = [True] * len(data.get("wumpus", []))

    def get_percepts(self):
        x, y = self.agent_pos
        percepts = {
            "breeze": False,
            "stench": False,
            "glitter": self.map[x][y].has_gold and not self.gold_grabbed,
            "scream": False  # Thêm scream percept
        }
        # Kiểm tra arrow hit (turn sau khi bắn)
        if self.arrow_in_flight:
            self.check_arrow_hit()
            self.arrow_in_flight = False
        
        # Xử lý scream percept
        if hasattr(self, 'scream_this_turn') and self.scream_this_turn:
            percepts["scream"] = True
            self.scream_this_turn = False
            
        # Breeze: có pit kề
        for nx, ny in self.get_neighbors(x, y):
            if self.map[nx][ny].has_pit:
                percepts["breeze"] = True
            if self.map[nx][ny].has_wumpus and self.wumpus_alive[self.wumpus_idx_at(nx, ny)]:
                percepts["stench"] = True
        return percepts

    def get_neighbors(self, x, y):
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = x+dx, y+dy
            if 0 <= nx < self.N and 0 <= ny < self.N:
                yield (nx, ny)

    def wumpus_idx_at(self, x, y):
        # Trả về thứ tự wumpus tại vị trí (x, y)
        idx = 0
        for i in range(self.N):
            for j in range(self.N):
                if self.map[i][j].has_wumpus:
                    if (i, j) == (x, y):
                        return idx
                    idx += 1
        return 0

    def step(self, action):
        if not self.agent_alive:
            return
        if action == "forward":
            self.score -= 1
            dx, dy = [(0,1), (1,0), (0,-1), (-1,0)][self.agent_dir]
            nx, ny = self.agent_pos[0]+dx, self.agent_pos[1]+dy
            if 0 <= nx < self.N and 0 <= ny < self.N:
                self.agent_pos = (nx, ny)
                # Kiểm tra pit/wumpus
                if self.map[nx][ny].has_pit:
                    self.agent_alive = False
                    self.score -= 1000  # Die penalty
                elif self.map[nx][ny].has_wumpus and self.wumpus_alive[self.wumpus_idx_at(nx, ny)]:
                    self.agent_alive = False
                    self.score -= 1000  # Die penalty
        elif action == "left":
            self.score -= 1
            self.agent_dir = (self.agent_dir - 1) % 4
        elif action == "right":
            self.score -= 1
            self.agent_dir = (self.agent_dir + 1) % 4
        elif action == "grab":
            self.score -= 1
            x, y = self.agent_pos
            if self.map[x][y].has_gold:
                self.gold_grabbed = True
                self.score += 1000  # Gold bonus
        elif action == "climb":
            self.score -= 1
            pass
        elif action == "shoot":
            # Xử lý bắn tên
            if self.agent_arrows > 0:
                self.agent_arrows -= 1
                self.score -= 10  # Arrow cost
                
                # Tính hướng bắn
                dx, dy = [(0,1), (1,0), (0,-1), (-1,0)][self.agent_dir]
                arrow_x, arrow_y = self.agent_pos[0] + dx, self.agent_pos[1] + dy
                
                # Kiểm tra mũi tên có bay ra ngoài map không
                if 0 <= arrow_x < self.N and 0 <= arrow_y < self.N:
                    self.arrow_in_flight = True
                    self.arrow_target = (arrow_x, arrow_y)
                    self.arrow_direction = self.agent_dir
        
        # Di chuyển Wumpus sau mỗi bước
        self.move_wumpus()

    def check_arrow_hit(self):
        """Kiểm tra mũi tên có trúng Wumpus không"""
        if not self.arrow_target:
            return
            
        x, y = self.arrow_target
        if self.map[x][y].has_wumpus and self.wumpus_alive[self.wumpus_idx_at(x, y)]:
            # Wumpus bị giết
            self.wumpus_alive[self.wumpus_idx_at(x, y)] = False
            # Tạo scream percept cho turn tiếp theo
            self.scream_this_turn = True
            self.score -= 10  # Trừ điểm cho việc bắn tên

    def move_wumpus(self):
        """Di chuyển Wumpus ngẫu nhiên"""
        self.wumpus_move_counter += 1
        if self.wumpus_move_counter >= self.wumpus_move_interval:
            self.wumpus_move_counter = 0
            
            # Tìm tất cả Wumpus còn sống
            for i in range(self.N):
                for j in range(self.N):
                    if self.map[i][j].has_wumpus and self.wumpus_alive[self.wumpus_idx_at(i, j)]:
                        # Di chuyển Wumpus này
                        self.move_single_wumpus(i, j)

    def move_single_wumpus(self, x, y):
        """Di chuyển một Wumpus từ vị trí (x,y)"""
        import random
        
        # Tìm các ô kề có thể di chuyển
        possible_moves = []
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.N and 0 <= ny < self.N:
                # Wumpus có thể đi vào ô có gold
                if not self.map[nx][ny].has_pit:
                    possible_moves.append((nx, ny))
        
        if possible_moves:
            # Chọn ngẫu nhiên một ô để di chuyển
            new_x, new_y = random.choice(possible_moves)
            
            # Di chuyển Wumpus
            self.map[x][y].has_wumpus = False
            self.map[new_x][new_y].has_wumpus = True

