// 修改 WebSocket 连接部分
let ws = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 3;

function connectWebSocket() {
    if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
        console.error('达到最大重连次数，请刷新页面重试');
        statusText.innerText = '连接失败，请刷新页面重试';
        return;
    }

    try {
        ws = new WebSocket('ws://localhost:8765');

        ws.onopen = () => {
            console.log('Connected to game server');
            reconnectAttempts = 0;
            statusText.innerText = '轮到你了';
            ws.send(JSON.stringify({action: 'test'}));
        };

        ws.onmessage = (event) => {
            try {
                const response = JSON.parse(event.data);
                console.log('Received message:', response);
                if (response.action === 'move') {
                    handleAIMove(response.position);
                } else if (response.action === 'start') {
                    // 处理先手信息
                    if (response.first_player === 'AI') {
                        gameState = GAME_STATES.WAITING;
                        statusText.innerText = '电脑先手...';
                        cells.forEach(cell => cell.style.pointerEvents = 'none');
                    } else {
                        gameState = GAME_STATES.PLAYING;
                        statusText.innerText = '你先手，轮到你了';
                        cells.forEach(cell => cell.style.pointerEvents = 'auto');
                    }
                }
            } catch (e) {
                console.error('Error processing message:', e);
            }
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        ws.onclose = (event) => {
            console.log('WebSocket connection closed:', event.code, event.reason);
            if (event.code !== 1000) {  // 非正常关闭
                reconnectAttempts++;
                if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                    console.log('Attempting to reconnect...');
                    setTimeout(connectWebSocket, 2000);
                }
            }
        };
    } catch (e) {
        console.error('Error creating WebSocket:', e);
    }
}

// 游戏状态常量
const GAME_STATES = {
  PLAYING: 'playing',
  WIN: 'win',
  DRAW: 'draw',
  WAITING: 'waiting'  // 新增等待 AI 响应状态
};

// DOM 元素
const cells = document.querySelectorAll("[data-cell]");
const board = document.getElementById("board");
const statusText = document.getElementById("status");
const restartButton = document.getElementById("restartButton");

// 游戏变量
let currentPlayer = "X";  // 玩家始终是 X，AI 是 O
let gameState = GAME_STATES.PLAYING;
let boardState = Array(9).fill('');  // 添加棋盘状态数组

// 获胜组合
const winningCombinations = [
  [0, 1, 2], // 横向
  [3, 4, 5],
  [6, 7, 8],
  [0, 3, 6], // 纵向
  [1, 4, 7],
  [2, 5, 8],
  [0, 4, 8], // 对角线
  [2, 4, 6]
];

// 检查是否平局
const checkDraw = () => {
  return [...cells].every(cell => {
    return cell.innerText === "X" || cell.innerText === "O";
  });
};

// 修改 checkWin 函数
const checkWin = (player) => {
  for (let i = 0; i < winningCombinations.length; i++) {
    const combination = winningCombinations[i];
    if (combination.every(index => cells[index].innerText === player)) {
      showWinningLine(i);
      return true;
    }
  }
  return false;
};

// 修改显示胜利线条的函数
const showWinningLine = (combinationIndex) => {
    const line = document.createElement('div');
    line.classList.add('winning-line');
    
    if (combinationIndex < 3) {
        // 横线
        line.classList.add('horizontal-line');
        line.style.top = `${50 + combinationIndex * 100}px`;
    } else if (combinationIndex < 6) {
        // 竖线
        line.classList.add('vertical-line');
        line.style.left = `${50 + (combinationIndex - 3) * 100}px`;
    } else if (combinationIndex === 6) {
        // 左上到右下的对角线
        line.classList.add('diagonal-1');
        line.style.top = '50%';
        line.style.left = '50%';
        line.style.transform = 'translate(-50%, -50%) rotate(45deg)';
    } else {
        // 右上到左下的对角线
        line.classList.add('diagonal-2');
        line.style.top = '50%';
        line.style.left = '50%';
        line.style.transform = 'translate(-50%, -50%) rotate(-45deg)';
    }
    
    board.appendChild(line);
};

// 修改发送移动信息的函数
const sendMove = (position) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            action: 'move',
            position: position,
            board: boardState
        }));
    } else {
        console.error('WebSocket is not connected');
    }
};

// 修改 handleClick 函数
const handleClick = (e) => {
    if (gameState !== GAME_STATES.PLAYING) return;
    
    const cell = e.target;
    const position = Array.from(cells).indexOf(cell);
    
    if (cell.innerText !== '') return;
    
    // 玩家移动
    cell.innerText = 'X';
    cell.classList.add('taken');
    boardState[position] = 'X';
    
    if (checkWin('X')) {
        gameState = GAME_STATES.WIN;
        statusText.innerText = '你赢了！';
        board.classList.add('game-over');
    } else if (checkDraw()) {
        gameState = GAME_STATES.DRAW;
        statusText.innerText = '平局！';
    } else {
        // 设置等待状态，禁止玩家操作
        gameState = GAME_STATES.WAITING;
        statusText.innerText = '等待电脑思考...';
        cells.forEach(cell => cell.style.pointerEvents = 'none'); // 禁用所有格子
        sendMove(position);
    }
};

// 修改 resetGame 函数
const resetGame = () => {
    gameState = GAME_STATES.PLAYING;
    boardState = Array(9).fill('');
    
    const winningLine = board.querySelector('.winning-line');
    if (winningLine) {
        winningLine.remove();
    }
    
    board.classList.remove('game-over');
    cells.forEach(cell => {
        cell.innerText = '';
        cell.classList.remove('taken');
        cell.style.pointerEvents = 'auto';
    });
    
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            action: 'reset'
        }));
        // 请求确定谁先手
        ws.send(JSON.stringify({
            action: 'start'
        }));
        statusText.innerText = '等待确定先手...';
        cells.forEach(cell => cell.style.pointerEvents = 'none');
    }
};

// 在初始化游戏时连接 WebSocket
const initGame = () => {
  cells.forEach(cell => cell.addEventListener("click", handleClick));
  restartButton.addEventListener("click", resetGame);
  connectWebSocket(); // 连接 WebSocket
  resetGame();
};

// 修改 handleAIMove 函数
const handleAIMove = (position) => {
    console.log('AI moving to position:', position);
    if (gameState !== GAME_STATES.WAITING) {
        console.log('Wrong game state:', gameState);
        return;
    }
    
    const cell = cells[position];
    if (!cell) {
        console.error('Invalid position:', position);
        return;
    }

    cell.innerText = 'O';
    cell.classList.add('taken');
    boardState[position] = 'O';
    
    // 重新启用未被占用的格子
    cells.forEach(cell => {
        if (cell.innerText === '') {
            cell.style.pointerEvents = 'auto';
        }
    });
    
    if (checkWin('O')) {
        gameState = GAME_STATES.WIN;
        statusText.innerText = '电脑赢了！';
        board.classList.add('game-over');
    } else if (checkDraw()) {
        gameState = GAME_STATES.DRAW;
        statusText.innerText = '平局！';
    } else {
        gameState = GAME_STATES.PLAYING;
        statusText.innerText = '轮到你了';
    }
};

// 启动游戏
initGame(); 