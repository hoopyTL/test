import heapq

class Agent:
    def __init__(self, N):
        self.N = N
        self.x, self.y = 0, 0  # Start at (0,0)
        self.dir = 1
        self.kb = [['unknown' for _ in range(N)] for _ in range(N)]
        self.visited = set()
        self.has_gold = False
        self.action_log = []
        self.percept_history = {}  # {(x, y): percepts dict}

    def get_neighbors(self, x, y):
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = x+dx, y+dy
            if 0 <= nx < self.N and 0 <= ny < self.N:
                yield (nx, ny)

    def update_percepts(self, percepts):
        x, y = self.x, self.y
        self.visited.add((x, y))
        self.kb[y][x] = 'visited'
        self.percept_history[(x, y)] = dict(percepts)

        # Xử lý scream percept - Wumpus bị giết
        if percepts.get('scream', False):
            # Cập nhật KB: tất cả ô có stench giờ có thể an toàn
            for i in range(self.N):
                for j in range(self.N):
                    if self.kb[j][i] == 'warn':
                        # Kiểm tra xem ô này có còn stench không
                        has_stench = False
                        for nx, ny in self.get_neighbors(i, j):
                            if (nx, ny) in self.visited:
                                p = self.percept_history.get((nx, ny), {})
                                if p.get('stench', False):
                                    has_stench = True
                                    break
                        if not has_stench:
                            self.kb[j][i] = 'safe'
        
        # 1. Mark all neighbors safe if NO warn
        if not percepts.get('breeze', False) and not percepts.get('stench', False):
            for nx, ny in self.get_neighbors(x, y):
                if self.kb[ny][nx] == 'unknown':
                    self.kb[ny][nx] = 'safe'

        # 2. Classic warn inference: mark warn/danger if enough warn sources
        for i in range(self.N):
            for j in range(self.N):
                if self.kb[j][i] in ['unknown', 'warn']:
                    warn_sources = 0
                    neighbors_visited = 0
                    for nx, ny in self.get_neighbors(i, j):
                        if (nx, ny) in self.visited:
                            neighbors_visited += 1
                            p = self.percept_history.get((nx, ny), {})
                            if p.get('breeze', False) or p.get('stench', False):
                                warn_sources += 1
                    if warn_sources > 0:
                        self.kb[j][i] = 'warn'
                    if neighbors_visited >= 2 and warn_sources == neighbors_visited:
                        self.kb[j][i] = 'danger'

        # 3. Nâng cao: Chỉ mark danger nếu SỐ WARN Ở PERCEPT HIỆN TẠI == SỐ Ô ĐI MỚI
        for i in range(self.N):
            for j in range(self.N):
                if (i, j) in self.visited:
                    new_cells = [(nx, ny) for nx, ny in self.get_neighbors(i, j) if (nx, ny) not in self.visited]
                    if not new_cells:
                        continue
                    percept = self.percept_history.get((i, j), {})
                    n_warn = int(percept.get('breeze', False)) + int(percept.get('stench', False))
                    if n_warn == len(new_cells) and n_warn > 0:
                        for nx, ny in new_cells:
                            self.kb[ny][nx] = 'danger'

        # 4. Backward inference: nếu đã mark warn nhưng neighbor không còn warn thì chuyển safe
        for i in range(self.N):
            for j in range(self.N):
                if self.kb[j][i] == 'warn':
                    has_no_warn_neighbor = False
                    for nx, ny in self.get_neighbors(i, j):
                        if (nx, ny) in self.visited:
                            p = self.percept_history.get((nx, ny), {})
                            if not p.get('breeze', False) and not p.get('stench', False):
                                has_no_warn_neighbor = True
                                break
                    if has_no_warn_neighbor:
                        self.kb[j][i] = 'safe'

    def next_action(self, percepts):
        self.update_percepts(percepts)
        x, y = self.x, self.y
        # Ưu tiên lấy vàng nếu thấy glitter
        if percepts.get('glitter'):
            self.action_log.append('grab')
            return 'grab'
        # Về nhà nếu đã có vàng và ở (0,0)
        if getattr(self, 'has_gold', False) and (x, y) == (0, 0):
            self.action_log.append('climb')
            return 'climb'
        # Về nhà nếu đã có vàng
        if getattr(self, 'has_gold', False):
            action = self.move_towards(0, 0)
            self.action_log.append(action)
            return action

        # Logic bắn tên: nếu có stench và có tên thì bắn
        if percepts.get('stench', False) and hasattr(self, 'agent_arrows') and self.agent_arrows > 0:
            # Tìm Wumpus để bắn
            wumpus_target = self.find_wumpus_to_shoot()
            if wumpus_target:
                # Xoay hướng về phía Wumpus
                action = self.turn_towards(wumpus_target)
                if action != 'forward':
                    self.action_log.append(action)
                    return action
                else:
                    # Đã hướng đúng, bắn tên
                    self.action_log.append('shoot')
                    return 'shoot'
                    
        # Ưu tiên đi safe chưa đi
        target = self.find_unvisited(['safe'])
        if target:
            action = self.move_towards(*target)
            self.action_log.append(action)
            return action

        # Hết safe thì đi warn chưa đi (liều)
        target = self.find_unvisited(['warn'])
        if target:
            action = self.move_towards(*target)
            self.action_log.append(action)
            return action

        # Không còn đường đi, về cửa ra
        if (x, y) == (0, 0):
            self.action_log.append('climb')
            return 'climb'
        else:
            action = self.move_towards(0, 0)
            self.action_log.append(action)
            return action

    def find_unvisited(self, types):
        for i in range(self.N):
            for j in range(self.N):
                if self.kb[j][i] in types and (i, j) not in self.visited:
                    return (i, j)
        return None

    def move_towards(self, tx, ty):
        path = self.astar((self.x, self.y), (tx, ty))
        if len(path) <= 1:
            return 'climb' if (self.x, self.y) == (0, 0) else 'forward'
        next_pos = path[1]
        nx, ny = next_pos
        dx, dy = nx - self.x, ny - self.y
        new_dir = None
        if dx == 1: new_dir = 1
        elif dx == -1: new_dir = 3
        elif dy == 1: new_dir = 0
        elif dy == -1: new_dir = 2
        if new_dir is not None and new_dir != self.dir:
            if (new_dir - self.dir) % 4 == 1:
                return 'right'
            else:
                return 'left'
        else:
            return 'forward'

    def astar(self, start, goal):
        frontier = []
        heapq.heappush(frontier, (0, start))
        came_from = {}
        cost_so_far = {start: 0}
        while frontier:
            _, current = heapq.heappop(frontier)
            if current == goal:
                break
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                nx, ny = current[0]+dx, current[1]+dy
                if 0 <= nx < self.N and 0 <= ny < self.N:
                    status = self.kb[ny][nx]
                    if status not in ['danger']:
                        if status in ['safe', 'visited', 'warn', 'unknown'] or (nx, ny) == goal:
                            new_cost = cost_so_far[current] + 1
                            if (nx, ny) not in cost_so_far or new_cost < cost_so_far[(nx, ny)]:
                                cost_so_far[(nx, ny)] = new_cost
                                priority = new_cost + abs(nx - goal[0]) + abs(ny - goal[1])
                                heapq.heappush(frontier, (priority, (nx, ny)))
                                came_from[(nx, ny)] = current
        if goal not in came_from and start != goal:
            return [start]
        path = [goal]
        while path[-1] != start:
            path.append(came_from[path[-1]])
        path.reverse()
        return path

    def update_agent_state(self, action, percepts):
        if action == 'forward':
            dx, dy = [(0,1), (1,0), (0,-1), (-1,0)][self.dir]
            self.x += dx
            self.y += dy
        elif action == 'left':
            self.dir = (self.dir - 1) % 4
        elif action == 'right':
            self.dir = (self.dir + 1) % 4
        elif action == 'grab':
            # Cập nhật trạng thái khi lấy vàng
            self.has_gold = True

    def get_kb(self):
        return self.kb

    def get_action_log(self):
        return self.action_log

    def find_wumpus_to_shoot(self):
        """Tìm Wumpus để bắn tên"""
        for i in range(self.N):
            for j in range(self.N):
                if self.kb[j][i] == 'warn' and (i, j) not in self.visited:
                    # Kiểm tra xem có thể bắn được không
                    if self.can_shoot_at(i, j):
                        return (i, j)
        return None

    def can_shoot_at(self, target_x, target_y):
        """Kiểm tra có thể bắn tên vào ô target không"""
        # Kiểm tra xem target có nằm trên đường thẳng từ agent không
        dx = target_x - self.x
        dy = target_y - self.y
        
        # Chỉ bắn được theo hướng agent đang nhìn
        if self.dir == 0 and dy > 0:  # Nhìn lên
            return dx == 0
        elif self.dir == 1 and dx > 0:  # Nhìn phải
            return dy == 0
        elif self.dir == 2 and dy < 0:  # Nhìn xuống
            return dx == 0
        elif self.dir == 3 and dx < 0:  # Nhìn trái
            return dy == 0
        return False

    def turn_towards(self, target):
        """Xoay hướng về phía target"""
        target_x, target_y = target
        dx = target_x - self.x
        dy = target_y - self.y
        
        # Xác định hướng cần xoay
        if dx > 0:  # Cần nhìn phải
            target_dir = 1
        elif dx < 0:  # Cần nhìn trái
            target_dir = 3
        elif dy > 0:  # Cần nhìn lên
            target_dir = 0
        elif dy < 0:  # Cần nhìn xuống
            target_dir = 2
        else:
            return 'forward'  # Đã ở đúng hướng
            
        # Xoay về hướng target
        if target_dir == self.dir:
            return 'forward'
        elif (target_dir - self.dir) % 4 == 1:
            return 'right'
        else:
            return 'left'
