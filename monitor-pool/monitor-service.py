#!/usr/bin/env python3
"""
3D Monitor Service
WebSocket을 통한 실시간 시뮬레이션 모니터링 서비스
"""

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import redis
import json
import threading
import time
import logging
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'wireless-simulation-secret'
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Redis 연결
REDIS_HOST = os.getenv('REDIS_HOST', 'redis-service.queue-system.svc.cluster.local')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))

try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
        socket_connect_timeout=5
    )
    redis_client.ping()
    logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
except Exception as e:
    logger.error(f"Failed to connect to Redis: {str(e)}")

# Delta Buffer - 시뮬레이션별 마지막 상태 저장
delta_buffer = {}
client_subscriptions = {}  # {session_id: simulation_id}

# ========== Helper Functions ==========

def get_delta_update(simulation_id, current_state):
    """현재 상태와 이전 상태를 비교하여 Delta 생성"""
    if simulation_id not in delta_buffer:
        # 첫 업데이트는 Full Update
        delta_buffer[simulation_id] = current_state
        return {
            'type': 'full_update',
            'data': current_state
        }
    
    previous_state = delta_buffer[simulation_id]
    delta = {
        'type': 'delta_update',
        'changes': []
    }
    
    # 간단한 Delta 계산 (실제로는 더 복잡한 diff 알고리즘 사용)
    for key in current_state:
        if key not in previous_state or current_state[key] != previous_state[key]:
            delta['changes'].append({
                'key': key,
                'value': current_state[key]
            })
    
    # 버퍼 업데이트
    delta_buffer[simulation_id] = current_state
    
    return delta

# ========== HTTP Endpoints ==========

@app.route('/health', methods=['GET'])
def health_check():
    """헬스체크"""
    return jsonify({
        'status': 'healthy',
        'service': 'monitor-pool',
        'active_connections': len(client_subscriptions),
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/stats', methods=['GET'])
def get_stats():
    """모니터링 통계"""
    return jsonify({
        'active_simulations': len(delta_buffer),
        'active_connections': len(client_subscriptions),
        'simulations': list(delta_buffer.keys()),
        'timestamp': datetime.now().isoformat()
    }), 200

# ========== WebSocket Events ==========

@socketio.on('connect')
def handle_connect():
    """클라이언트 연결"""
    session_id = request.sid
    logger.info(f"Client connected: {session_id}")
    emit('connection_response', {
        'status': 'connected',
        'session_id': session_id,
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('disconnect')
def handle_disconnect():
    """클라이언트 연결 해제"""
    session_id = request.sid
    if session_id in client_subscriptions:
        simulation_id = client_subscriptions[session_id]
        leave_room(simulation_id)
        del client_subscriptions[session_id]
        logger.info(f"Client disconnected from simulation {simulation_id}: {session_id}")
    else:
        logger.info(f"Client disconnected: {session_id}")

@socketio.on('subscribe')
def handle_subscribe(data):
    """시뮬레이션 구독"""
    session_id = request.sid
    simulation_id = data.get('simulation_id')
    
    if not simulation_id:
        emit('error', {'message': 'simulation_id is required'})
        return
    
    # Room에 참여
    join_room(simulation_id)
    client_subscriptions[session_id] = simulation_id
    
    logger.info(f"Client {session_id} subscribed to simulation {simulation_id}")
    
    # 구독 확인 및 현재 상태 전송
    response = {
        'status': 'subscribed',
        'simulation_id': simulation_id,
        'timestamp': datetime.now().isoformat()
    }
    
    # 기존 상태가 있으면 전송
    if simulation_id in delta_buffer:
        response['current_state'] = delta_buffer[simulation_id]
    
    emit('subscribe_response', response)

@socketio.on('unsubscribe')
def handle_unsubscribe(data):
    """시뮬레이션 구독 해제"""
    session_id = request.sid
    simulation_id = data.get('simulation_id')
    
    if session_id in client_subscriptions:
        leave_room(client_subscriptions[session_id])
        del client_subscriptions[session_id]
        logger.info(f"Client {session_id} unsubscribed from simulation {simulation_id}")
        
        emit('unsubscribe_response', {
            'status': 'unsubscribed',
            'simulation_id': simulation_id
        })

# ========== Background Worker ==========

def monitor_queue_worker():
    """Redis 큐를 모니터링하고 클라이언트에 업데이트 전송"""
    logger.info("Monitor queue worker started")
    MONITOR_UPDATE_QUEUE = "monitor_update_queue"
    
    while True:
        try:
            result = redis_client.brpop(MONITOR_UPDATE_QUEUE, timeout=1)
            
            if result:
                queue_name, update_json = result
                update_data = json.loads(update_json)
                
                simulation_id = update_data.get('simulation_id')
                update_type = update_data.get('update_type')
                
                logger.info(f"Received update: {update_type} for simulation {simulation_id}")
                
                # Delta 계산
                delta = get_delta_update(simulation_id, update_data['data'])
                
                # 해당 시뮬레이션을 구독 중인 모든 클라이언트에게 전송
                payload = {
                    'simulation_id': simulation_id,
                    'update_type': update_type,
                    'timestamp': update_data['timestamp'],
                    'delta': delta
                }
                
                socketio.emit('simulation_update', payload, room=simulation_id)
                logger.info(f"Broadcasted update to room {simulation_id}")
            
            time.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Error in monitor worker: {str(e)}")
            time.sleep(1)

# ========== Main ==========

def start_background_worker():
    """백그라운드 워커 시작"""
    worker_thread = threading.Thread(target=monitor_queue_worker, daemon=True)
    worker_thread.start()
    logger.info("Background worker thread started")

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    
    logger.info(f"Starting Monitor Service")
    logger.info(f"HTTP and WebSocket on port {port}")
    
    # 백그라운드 워커 시작
    start_background_worker()
    
    # Flask-SocketIO 서버 시작 (HTTP와 WebSocket 모두 같은 포트에서 처리)
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
