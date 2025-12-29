#!/usr/bin/env python3
"""
System Core Worker
시뮬레이션 전체 프로세스를 조율하는 핵심 워커
"""

import redis
import json
import time
import logging
import os
import requests
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Redis 연결
REDIS_HOST = os.getenv('REDIS_HOST', 'redis-service.queue-system.svc.cluster.local')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
STORAGE_SERVICE_URL = "http://storage-service.storage-pool.svc.cluster.local:8080"

# Queue 이름
SIMULATION_QUEUE = "simulation_queue"
CHANNEL_QUEUE = "channel_queue"
PDP_QUEUE = "pdp_queue"

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
    exit(1)

def get_scenario(scenario_id):
    """Storage에서 시나리오 데이터 로드"""
    try:
        response = requests.get(
            f"{STORAGE_SERVICE_URL}/scenarios/{scenario_id}",
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to load scenario: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error loading scenario: {str(e)}")
        return None

def save_result(simulation_id, result_data):
    """결과를 Storage에 저장"""
    try:
        response = requests.post(
            f"{STORAGE_SERVICE_URL}/results/{simulation_id}",
            json=result_data,
            timeout=5
        )
        return response.status_code == 201
    except Exception as e:
        logger.error(f"Error saving result: {str(e)}")
        return False

def process_simulation(job_data):
    """시뮬레이션 처리"""
    simulation_id = job_data['simulation_id']
    scenario_id = job_data['scenario_id']
    
    logger.info(f"Processing simulation {simulation_id} with scenario {scenario_id}")
    
    # 1. 시나리오 로드
    scenario = get_scenario(scenario_id)
    if not scenario:
        logger.error(f"Scenario {scenario_id} not found")
        return False
    
    num_users = len(scenario['users'])
    num_steps = scenario['simulation_config']['total_steps']
    
    logger.info(f"Simulation config: {num_users} users, {num_steps} time steps")
    
    # 2. Channel Generation 작업 큐에 추가
    channel_job = {
        'job_type': 'channel_generation',
        'simulation_id': simulation_id,
        'scenario': scenario,
        'timestamp': datetime.now().isoformat()
    }
    redis_client.lpush(CHANNEL_QUEUE, json.dumps(channel_job))
    logger.info(f"Enqueued channel generation job for {simulation_id}")
    
    # 3. PDP Interpolation 작업 큐에 추가
    pdp_job = {
        'job_type': 'pdp_interpolation',
        'simulation_id': simulation_id,
        'scenario': scenario,
        'timestamp': datetime.now().isoformat()
    }
    redis_client.lpush(PDP_QUEUE, json.dumps(pdp_job))
    logger.info(f"Enqueued PDP interpolation job for {simulation_id}")
    
    # 4. 초기 결과 저장 (진행 상태 추적용)
    initial_result = {
        'simulation_id': simulation_id,
        'scenario_id': scenario_id,
        'status': 'processing',
        'start_time': datetime.now().isoformat(),
        'progress': 0.0,
        'num_users': num_users,
        'num_steps': num_steps
    }
    
    save_result(simulation_id, initial_result)
    
    return True

def main():
    """메인 워커 루프"""
    logger.info("System Core Worker started")
    logger.info(f"Listening on queue: {SIMULATION_QUEUE}")
    
    while True:
        try:
            # BRPOP: Blocking Right POP (타임아웃 1초)
            result = redis_client.brpop(SIMULATION_QUEUE, timeout=1)
            
            if result:
                queue_name, job_json = result
                job_data = json.loads(job_json)
                
                logger.info(f"Received job: {job_data.get('simulation_id', 'unknown')}")
                
                # 작업 처리
                success = process_simulation(job_data)
                
                if success:
                    logger.info(f"Job completed successfully")
                else:
                    logger.error(f"Job failed")
            
            # CPU 사용량 제한
            time.sleep(0.1)
            
        except KeyboardInterrupt:
            logger.info("Worker stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in worker loop: {str(e)}")
            time.sleep(1)

if __name__ == '__main__':
    main()
