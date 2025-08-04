# main.py

if __name__ == '__main__':
    # Muốn GUI thì chạy:
    from visual.gui import WumpusGUI
    app = WumpusGUI(N=4, K=2, p=0.2, seed=42)
    app.mainloop()

    # Nếu muốn console test:
    # from env.environment import Environment
    # from agent.agent import Agent
    # from agent.random_agent import RandomAgent
    # 
    # # Test Intelligent Agent
    # env = Environment(N=4, K=1, p=0.2, seed=42)
    # agent = Agent(N=4)
    # 
    # # Test Random Agent
    # env2 = Environment(N=4, K=1, p=0.2, seed=42)
    # random_agent = RandomAgent(N=4)
    # 
    # # So sánh performance
    # print("Testing Intelligent Agent...")
    # # ... test logic
    # 
    # print("Testing Random Agent...")
    # # ... test logic
