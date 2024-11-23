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

if __name__ == "__main__":
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}") 
