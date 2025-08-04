import tkinter as tk
from tkinter import ttk
import threading
import time
import os
from env.environment import Environment
from agent.agent import Agent

class WumpusGUI(tk.Tk):
    CELL_SIZE = 60
    COLORS = {
        'agent': '#3A72E6',
        'gold': '#FFD700',
        'pit': '#FF3A3A',        # đỏ
        'wumpus': '#990000',     # đỏ đậm
        'warn': '#FFB347',       # cam (Ô nguy cơ)
        'danger': '#FF3A3A',     # đỏ (Ô chắc chắn nguy hiểm)
        'safe': '#9CF59A',       # xanh lá
        'visited': '#D0E9FF',    # xanh nhạt
        'unknown': '#ECECEC',    # xám
        'border': '#AAAAAA'
    }
    DIR_ARROW = ['↑', '→', '↓', '←']

    def __init__(self, N=4, K=1, p=0.2, seed=42):
        super().__init__()
        self.title("Wumpus World GUI")
        self.N = N
        self.K = K
        self.p = p
        self.seed = seed
        self.selected_map = None
        self.env = None
        self.agent = None
        self.running = False
        self.delay = 0.5
        self.map_files = self.scan_maps()
        self.create_widgets()
        self.set_default_map()
        self.new_game()

    def scan_maps(self):
        testcases_dir = "testcases"
        files = []
        if os.path.exists(testcases_dir):
            for fname in os.listdir(testcases_dir):
                if fname.endswith(".json"):
                    files.append(fname)
        files.sort()
        return files

    def set_default_map(self):
        # Mặc định là map1.json nếu có
        if "map1.json" in self.map_files:
            idx = self.map_files.index("map1.json")
            self.cmb_map.current(idx)
            self.selected_map = self.map_files[idx]
        else:
            self.cmb_map.current(0)
            self.selected_map = self.map_files[0]

    def create_widgets(self):
        top_frame = tk.Frame(self)
        top_frame.pack(side=tk.TOP, fill=tk.X)

        tk.Label(top_frame, text="Select Map: ").pack(side=tk.LEFT)
        self.cmb_map = ttk.Combobox(top_frame, values=self.map_files, state="readonly", width=18)
        self.cmb_map.pack(side=tk.LEFT, padx=5)
        self.cmb_map.bind("<<ComboboxSelected>>", self.on_map_selected)

        self.btn_start = tk.Button(top_frame, text="Start", command=self.new_game)
        self.btn_start.pack(side=tk.LEFT, padx=5)

        self.btn_next = tk.Button(top_frame, text="Next Step", command=self.next_step)
        self.btn_next.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_auto = tk.Button(top_frame, text="Auto Run", command=self.start_auto)
        self.btn_auto.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_stop = tk.Button(top_frame, text="Pause", command=self.stop_auto, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=5, pady=5)

        self.log_text = tk.Text(self, height=8, width=55, bg="#21252b", fg="#C9D1D9")
        self.log_text.pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas = tk.Canvas(self, width=self.N*self.CELL_SIZE, height=self.N*self.CELL_SIZE, bg='white')
        self.canvas.pack(side=tk.TOP, padx=10, pady=10)

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def on_map_selected(self, event=None):
        val = self.cmb_map.get()
        self.selected_map = val
        self.new_game()

    def new_game(self):
        val = self.cmb_map.get() if hasattr(self, 'cmb_map') else self.map_files[0]
        self.selected_map = val

        mapfile = os.path.join("testcases", self.selected_map)
        # Auto size detection based on map file
        try:
            import json
            with open(mapfile, 'r') as f:
                data = json.load(f)
            if "agent" in data:
                size = max(
                    [max(pos) for k in ["pit", "wumpus", "gold"] for pos in data.get(k, [])] +
                    data["agent"]["pos"]
                ) + 1
                self.N = size
            else:
                self.N = len(data)
        except:
            self.N = 4

        self.env = Environment(N=self.N, K=self.K, p=self.p, mapfile=mapfile)
        self.agent = Agent(N=self.N)
        self.running = False
        self.btn_next['state'] = tk.NORMAL
        self.btn_auto['state'] = tk.NORMAL
        self.btn_stop['state'] = tk.DISABLED
        self.log_text.delete('1.0', tk.END)
        self.log(f"Đã tải map từ file: {self.selected_map}")
        self.update_board()

    def update_board(self):
        self.canvas.config(width=self.N*self.CELL_SIZE, height=self.N*self.CELL_SIZE)
        self.canvas.delete('all')
        kb = self.agent.get_kb()
        for i in range(self.N):
            for j in range(self.N):
                x1 = i * self.CELL_SIZE
                y1 = (self.N-1-j) * self.CELL_SIZE
                x2 = x1 + self.CELL_SIZE
                y2 = y1 + self.CELL_SIZE
                state = kb[j][i]
                # Hiện đúng màu theo knowledge
                fill = self.COLORS['unknown']
                if state == 'safe':
                    fill = self.COLORS['safe']
                elif state == 'warn':
                    fill = self.COLORS['warn']
                elif state == 'danger':
                    fill = self.COLORS['danger']
                elif state == 'visited':
                    fill = self.COLORS['visited']
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline=self.COLORS['border'])
                # Symbol trực quan
                if state == 'warn':
                    self.canvas.create_text(x1+30, y1+30, text="!", font=('Arial', 16, 'bold'), fill='orange')
                elif state == 'danger':
                    self.canvas.create_text(x1+30, y1+30, text="X", font=('Arial', 16, 'bold'), fill='red')
                elif state == 'safe':
                    self.canvas.create_text(x1+30, y1+30, text="S", font=('Arial', 14), fill='green')
                elif state == 'visited':
                    self.canvas.create_text(x1+30, y1+30, text="•", font=('Arial', 10), fill='gray')
        # Vẽ item thật
        for i in range(self.N):
            for j in range(self.N):
                cell = self.env.map[i][j]
                x1 = i * self.CELL_SIZE
                y1 = (self.N-1-j) * self.CELL_SIZE
                if cell.has_pit:
                    self.canvas.create_oval(x1+10, y1+35, x1+25, y1+50, fill=self.COLORS['pit'])
                if cell.has_gold and not self.env.gold_grabbed:
                    self.canvas.create_oval(x1+38, y1+10, x1+55, y1+25, fill=self.COLORS['gold'])
                if cell.has_wumpus and getattr(self.env, "wumpus_alive", [True])[getattr(self.env, "wumpus_idx_at", lambda x, y: 0)(i, j)]:
                    self.canvas.create_rectangle(x1+38, y1+35, x1+55, y1+52, fill=self.COLORS['wumpus'])
        # Agent
        x, y = self.env.agent_pos
        x1 = x * self.CELL_SIZE
        y1 = (self.N-1-y) * self.CELL_SIZE
        self.canvas.create_oval(x1+12, y1+12, x1+48, y1+48, fill=self.COLORS['agent'])
        self.canvas.create_text(x1+30, y1+30, text=self.DIR_ARROW[self.env.agent_dir], font=('Arial', 16), fill='white')

    def next_step(self):
        if not self.env.agent_alive:
            self.log("Agent đã chết! Không thể đi tiếp.")
            return
        percepts = self.env.get_percepts()
        action = self.agent.next_action(percepts)
        self.env.step(action)
        self.agent.update_agent_state(action, percepts)
        self.log(f"Percepts: {percepts} | Action: {action}")
        self.update_board()
        # END GAME nếu lấy được vàng
        if action == 'grab':
            self.log("🎉 Agent đã lấy được vàng!")
            self.btn_next['state'] = tk.DISABLED
            self.btn_auto['state'] = tk.DISABLED
            self.btn_stop['state'] = tk.DISABLED
        elif not self.env.agent_alive:
            self.log("Agent đã chết! Game Over.")
            self.btn_next['state'] = tk.DISABLED
            self.btn_auto['state'] = tk.DISABLED
            self.btn_stop['state'] = tk.DISABLED

    def start_auto(self):
        self.running = True
        self.btn_auto['state'] = tk.DISABLED
        self.btn_stop['state'] = tk.NORMAL
        self.btn_next['state'] = tk.DISABLED
        threading.Thread(target=self.auto_loop, daemon=True).start()

    def stop_auto(self):
        self.running = False
        self.btn_auto['state'] = tk.NORMAL
        self.btn_stop['state'] = tk.DISABLED
        self.btn_next['state'] = tk.NORMAL

    def auto_loop(self):
        while self.running and self.env.agent_alive:
            percepts = self.env.get_percepts()
            action = self.agent.next_action(percepts)
            self.env.step(action)
            self.agent.update_agent_state(action, percepts)
            self.log(f"Percepts: {percepts} | Action: {action}")
            self.update_board()
            if action == 'grab':
                self.log("🎉 Agent đã lấy được vàng!")
                self.btn_next['state'] = tk.DISABLED
                self.btn_auto['state'] = tk.DISABLED
                self.btn_stop['state'] = tk.DISABLED
                break
            if not self.env.agent_alive: break
            time.sleep(self.delay)

if __name__ == '__main__':
    app = WumpusGUI()
    app.mainloop()
