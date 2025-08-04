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
            "glitter": self.map[x][y].has_gold and not self.gold_grabbed
        }
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
            dx, dy = [(0,1), (1,0), (0,-1), (-1,0)][self.agent_dir]
            nx, ny = self.agent_pos[0]+dx, self.agent_pos[1]+dy
            if 0 <= nx < self.N and 0 <= ny < self.N:
                self.agent_pos = (nx, ny)
                # Kiểm tra pit/wumpus
                if self.map[nx][ny].has_pit:
                    self.agent_alive = False
                elif self.map[nx][ny].has_wumpus and self.wumpus_alive[self.wumpus_idx_at(nx, ny)]:
                    self.agent_alive = False
        elif action == "left":
            self.agent_dir = (self.agent_dir - 1) % 4
        elif action == "right":
            self.agent_dir = (self.agent_dir + 1) % 4
        elif action == "grab":
            x, y = self.agent_pos
            if self.map[x][y].has_gold:
                self.gold_grabbed = True
        elif action == "climb":
            pass

