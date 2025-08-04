# main.py

if __name__ == '__main__':
    # Muốn GUI thì chạy:
    from visual.gui import WumpusGUI
    app = WumpusGUI(N=4, K=2, p=0.2, seed=42)
    app.mainloop()

    # Nếu muốn console:
    # from env.environment import Environment
    # from agent.agent import Agent
    # (viết giống mẫu code ở trên!)