#!/usr/bin/env python3
"""
Scenario Pool Service
시뮬레이션 시나리오 생성 및 관리 서비스
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import uuid
import random
import os
from datetime import datetime
import logging

app = Flask(__name__)
CORS(app)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Storage Service URL (환경변수 우선, K3s DNS는 fallback)
STORAGE_SERVICE_URL = os.getenv(
    'STORAGE_SERVICE_URL',
    "http://storage-service.storage-pool.svc.cluster.local:8080"
)

# ========== Helper Functions ==========

def generate_user_positions(num_users, area_size):
    """사용자 초기 위치 생성"""
    users = []
    for i in range(num_users):
        user = {
            'user_id': f'user_{i:04d}',
            'position': {
                'x': random.uniform(0, area_size[0]),
                'y': random.uniform(0, area_size[1]),
                'z': random.uniform(1.5, 2.0)  # 사람 높이
            },
            'velocity': {
                'x': random.uniform(-5, 5),
                'y': random.uniform(-5, 5),
                'z': 0
            },
            'device_type': random.choice(['smartphone', 'tablet', 'laptop'])
        }
        users.append(user)
    return users

def generate_base_stations(area_size, num_bs=4):
    """기지국 위치 생성"""
    base_stations = []
    # 균등 분포로 기지국 배치
    grid_size = int(num_bs ** 0.5)
    for i in range(grid_size):
        for j in range(grid_size):
            bs = {
                'bs_id': f'bs_{len(base_stations):02d}',
                'position': {
                    'x': (i + 0.5) * area_size[0] / grid_size,
                    'y': (j + 0.5) * area_size[1] / grid_size,
                    'z': 25.0  # 기지국 높이
                },
                'frequency': 3.5e9,  # 3.5 GHz
                'bandwidth': 100e6,   # 100 MHz
                'tx_power': 43        # dBm
            }
            base_stations.append(bs)
    return base_stations

# ========== Health Check ==========

@app.route('/health', methods=['GET'])
def health_check():
    """헬스체크 엔드포인트"""
    return jsonify({
        'status': 'healthy',
        'service': 'scenario-pool',
        'timestamp': datetime.now().isoformat()
    }), 200

# ========== Scenario Generation ==========

@app.route('/generate', methods=['POST'])
def generate_scenario():
    """새 시나리오 생성"""
    try:
        data = request.get_json()
        
        # 파라미터 추출
        scenario_name = data.get('name', 'unnamed_scenario')
        num_users = data.get('num_users', 10)
        area_size = data.get('area_size', [1000, 1000])  # meters
        duration = data.get('duration', 60)  # seconds
        scenario_type = data.get('type', 'urban_mobility')
        
        # 시나리오 ID 생성
        scenario_id = f"scenario_{uuid.uuid4().hex[:12]}"
        
        # 시나리오 데이터 생성
        scenario_data = {
            'scenario_id': scenario_id,
            'name': scenario_name,
            'type': scenario_type,
            'created_at': datetime.now().isoformat(),
            'parameters': {
                'num_users': num_users,
                'area_size': area_size,
                'duration': duration
            },
            'environment': {
                'area_size': area_size,
                'terrain': 'urban',
                'weather': 'clear'
            },
            'users': generate_user_positions(num_users, area_size),
            'base_stations': generate_base_stations(area_size),
            'simulation_config': {
                'time_step': 0.1,  # seconds
                'total_steps': int(duration / 0.1),
                'channel_model': 'ray_tracing',
                'mobility_model': 'random_waypoint'
            }
        }
        
        # Storage Service에 저장
        try:
            response = requests.post(
                f"{STORAGE_SERVICE_URL}/scenarios/{scenario_id}",
                json=scenario_data,
                timeout=5
            )
            
            if response.status_code == 201:
                logger.info(f"Scenario created and stored: {scenario_id}")
                return jsonify({
                    'status': 'success',
                    'scenario_id': scenario_id,
                    'scenario_name': scenario_name,
                    'num_users': num_users,
                    'message': 'Scenario generated successfully'
                }), 201
            else:
                logger.error(f"Failed to store scenario: {response.text}")
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to store scenario'
                }), 500
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Storage service error: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f'Storage service error: {str(e)}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in generate_scenario: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/templates', methods=['GET'])
def get_templates():
    """시나리오 템플릿 목록"""
    templates = [
        {
            'type': 'urban_mobility',
            'name': 'Urban Mobility',
            'description': '도심 환경에서 이동하는 사용자',
            'default_params': {
                'num_users': 20,
                'area_size': [1000, 1000],
                'duration': 60
            }
        },
        {
            'type': 'highway',
            'name': 'Highway Scenario',
            'description': '고속도로 이동 시나리오',
            'default_params': {
                'num_users': 50,
                'area_size': [5000, 100],
                'duration': 120
            }
        },
        {
            'type': 'indoor',
            'name': 'Indoor Environment',
            'description': '실내 환경 (건물, 사무실)',
            'default_params': {
                'num_users': 10,
                'area_size': [50, 50],
                'duration': 30
            }
        }
    ]
    
    return jsonify({
        'templates': templates,
        'count': len(templates)
    }), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    logger.info(f"Starting Scenario Pool Service on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
