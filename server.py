import asyncio
import websockets
import json
from agent import TicTacToeAgent
import http.server
import socketserver
import threading
import random
import numpy as np
import random
import pickle

agent = TicTacToeAgent()

# WebSocket 服务器
async def game_server(websocket, path="/"):
    print(f"New client connected on path: {path}")
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                print(f"Received message: {data}")
                
                if data['action'] == 'move':
                    # 获取当前棋盘状态
                    board_state = data['board']
                    player_position = data['position']
                    
                    # 让 AI 决策下一步
                    ai_move = agent.get_action(board_state)
                    print(f"AI chose move: {ai_move}")
                    
                    # 发送 AI 的移动
                    response = {
                        'action': 'move',
                        'position': ai_move
                    }
                    await websocket.send(json.dumps(response))
                    
                elif data['action'] == 'reset':
                    # 重置 AI 状态
                    agent.reset()
                    print("Game reset")
                
                elif data['action'] == 'start':
                    # 随机决定先手
                    first_player = random.choice(['AI', 'Player'])
                    response = {
                        'action': 'start',
                        'first_player': first_player
                    }
                    await websocket.send(json.dumps(response))
                    print(f"Game starting with {first_player} first")
                    
                    # 如果 AI 先手，立即进行第一步
                    if first_player == 'AI':
                        ai_move = agent.get_action([''] * 9)  # 空棋盘
                        await websocket.send(json.dumps({
                            'action': 'move',
                            'position': ai_move
                        }))
                    
            except json.JSONDecodeError:
                print("Invalid JSON received")
            except Exception as e:
                print(f"Error processing message: {e}")
                
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
    except Exception as e:
        print(f"Unexpected error: {e}")

# HTTP 服务器
class HttpHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

def run_http_server():
    with socketserver.TCPServer(("", 8000), HttpHandler) as httpd:
        print("HTTP server started on http://localhost:8000")
        httpd.serve_forever()

async def main():
    # 启动 HTTP 服务器
    http_thread = threading.Thread(target=run_http_server)
    http_thread.daemon = True
    http_thread.start()

    # 启动 WebSocket 服务器
    server = await websockets.serve(game_server, "localhost", 8765)
    print("WebSocket server started on ws://localhost:8765")
    await asyncio.Future()  # 保持服务器运行





class TicTacToe:
    def __init__(self):
        self.board = [' ' for _ in range(9)]  # 初始化空棋盘
        self.current_winner = None  # 追踪赢家

    def make_move(self, square, letter):
        if self.board[square] == ' ':  
            self.board[square] = letter
            if self.winner(square, letter):
                self.current_winner = letter
            return True
        return False

    def winner(self, square, letter):
        row_ind = square // 3
        row = self.board[row_ind * 3:(row_ind + 1) * 3]
        if all([s == letter for s in row]):
            return True
        
        col_ind = square % 3
        column = [self.board[col_ind + i * 3] for i in range(3)]
        if all([s == letter for s in column]):
            return True
        
        if square % 2 == 0:
            diagonal1 = [self.board[i] for i in [0, 4, 8]]
            if all([s == letter for s in diagonal1]):
                return True
            diagonal2 = [self.board[i] for i in [2, 4, 6]]
            if all([s == letter for s in diagonal2]):
                return True
        
        return False

    def empty_squares(self):
        return ' ' in self.board

    def get_empty_squares(self):
        return [i for i, x in enumerate(self.board) if x == ' ']

    def num_empty_squares(self):
        return len(self.get_empty_squares())

    def reset(self):
        self.board = [' ' for _ in range(9)]
        self.current_winner = None


class QLearningAgent:
    def __init__(self, alpha=0.5, gamma=0.9, epsilon=0.05):
        self.q_table = {}  # 存储Q值
        self.alpha = alpha  # 学习率
        self.gamma = gamma  # 折扣因子
        self.epsilon = epsilon  # 探索率

    def get_q_value(self, state, action):
        return self.q_table.get((state, action), 0.0)

    def update_q_value(self, state, action, reward, next_state):
        future_rewards = max([self.get_q_value(next_state, a) for a in range(9)], default=0.0)
        current_q = self.get_q_value(state, action)
        self.q_table[(state, action)] = current_q + self.alpha * (reward + self.gamma * future_rewards - current_q)

    def choose_action(self, state, available_actions):
        if random.uniform(0, 1) < self.epsilon:
            return random.choice(available_actions)  # 探索
        q_values = [self.get_q_value(state, a) for a in available_actions]
        max_q = max(q_values)
        return available_actions[q_values.index(max_q)]  # 利用

    def save_q_table(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump(self.q_table, f)

    def load_q_table(self, filename):
        with open(filename, 'rb') as f:
            self.q_table = pickle.load(f)


def train(agent, env, episodes=50000):
    wins = 0
    for episode in range(episodes):
        env.reset()
        state = tuple(env.board)
        while env.empty_squares():
            action = agent.choose_action(state, env.get_empty_squares())
            env.make_move(action, 'X')
            next_state = tuple(env.board)

            if env.current_winner == 'X':
                agent.update_q_value(state, action, 10, next_state)
                wins += 1
                break
            elif not env.empty_squares():
                agent.update_q_value(state, action, 0, next_state)
                break
            else:
                opponent_action = get_opponent_move(env)
                env.make_move(opponent_action, 'O')
                next_state = tuple(env.board)

                if env.current_winner == 'O':
                    agent.update_q_value(state, action, -10, next_state)
                    break
                else:
                    agent.update_q_value(state, action, -0.1, next_state)
            state = next_state
        
        if (episode + 1) % 1000 == 0:
            win_rate = wins / 1000
            wins = 0
            print(f"Episode {episode + 1}/{episodes}, Win Rate: {win_rate:.2%}")

def get_opponent_move(env):
    empty_squares = env.get_empty_squares()
    
    for action in empty_squares:
        env.board[action] = 'O'
        if env.winner(action, 'O'):
            env.board[action] = ' '
            return action
        env.board[action] = ' '
    
    for action in empty_squares:
        env.board[action] = 'X'
        if env.winner(action, 'X'):
            env.board[action] = ' '
            return action
        env.board[action] = ' '
    
    if 4 in empty_squares:
        return 4
    
    corners = [0, 2, 6, 8]
    available_corners = [x for x in corners if x in empty_squares]
    if available_corners:
        return random.choice(available_corners)
    
    return random.choice(empty_squares)

def play(agent, env):
    env.reset()
    state = tuple(env.board)
    while env.empty_squares():
        action = agent.choose_action(state, env.get_empty_squares())
        env.make_move(action, 'X')
        env_display(env)
        if env.current_winner == 'X':
            print("Agent wins!")
            return
        elif not env.empty_squares():
            print("It's a tie!")
            return

        opponent_action = int(input("Enter your move (0-8): "))
        if opponent_action not in env.get_empty_squares():
            print("Invalid move. Try again.")
            continue
        env.make_move(opponent_action, 'O')
        env_display(env)
        if env.current_winner == 'O':
            print("You win!")
            return
        state = tuple(env.board)


def env_display(env):
    board = env.board
    for row in [board[i * 3:(i + 1) * 3] for i in range(3)]:
        print('| ' + ' | '.join(row) + ' |')
    print("\n")


class TicTacToeAgent:
    def __init__(self):
        self.env = TicTacToe()
        self.agent = QLearningAgent()
        try:
            self.agent.load_q_table('q_table.pkl')
            print("Loaded pre-trained model")
        except:
            print("Training new model...")
            train(self.agent, self.env, episodes=50000)
            self.agent.save_q_table('q_table.pkl')
            print("Training completed and saved")

    def get_action(self, board_state):
        self.env.board = [' ' if x == '' else x for x in board_state]
        available_actions = self.env.get_empty_squares()
        if not available_actions:
            return -1
        
        state = tuple(self.env.board)
        if random.uniform(0, 1) < 0.1:
            action = self.agent.choose_action(state, available_actions)
        else:
            action = get_opponent_move(self.env)
        return action

    def reset(self):
        self.env.reset()




if __name__ == "__main__":
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}") 

    env = TicTacToe()
    agent = QLearningAgent()
    print("Training the agent...")
    train(agent, env, episodes=50000)
    agent.save_q_table('q_table.pkl')
    print("Training completed and saved!")
