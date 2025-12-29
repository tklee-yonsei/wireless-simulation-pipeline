#!/usr/bin/env python3
"""
PDP (Power Delay Profile) Interpolator Worker
시간에 따른 전력 지연 프로파일 보간 처리
"""

import redis
import json
import time
import logging
import os
import numpy as np
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

PDP_QUEUE = "pdp_queue"
MONITOR_UPDATE_QUEUE = "monitor_update_queue"

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

def interpolate_pdp(user_positions, time_steps):
    """
    PDP 보간 처리
    시간에 따른 사용자 위치 변화를 고려한 전력 지연 프로파일 계산
    """
    pdp_profiles = []
    
    for t in range(time_steps):
        time_pdp = []
        
        for user_idx, user in enumerate(user_positions):
            # 사용자 이동 시뮬레이션 (간단한 선형 이동)
            current_pos = {
                'x': user['position']['x'] + user['velocity']['x'] * t * 0.1,
                'y': user['position']['y'] + user['velocity']['y'] * t * 0.1,
                'z': user['position']['z']
            }
            
            # PDP 계산 (실제로는 채널 응답으로부터 계산하지만 여기서는 간소화)
            num_delays = 10
            delays = np.linspace(0, 1000, num_delays)  # 0-1000 ns
            powers = np.exp(-delays / 200) * (1 + 0.1 * np.random.randn(num_delays))
            
            time_pdp.append({
                'user_id': user['user_id'],
                'time_step': t,
                'position': current_pos,
                'pdp': {
                    'delays_ns': delays.tolist(),
                    'powers_linear': powers.tolist(),
                    'rms_delay': np.sqrt(np.sum(delays**2 * powers) / np.sum(powers))
                }
            })
        
        pdp_profiles.append(time_pdp)
    
    return pdp_profiles

def process_pdp_interpolation(job_data):
    """PDP 보간 처리"""
    simulation_id = job_data['simulation_id']
    scenario = job_data['scenario']
    
    logger.info(f"Processing PDP interpolation for simulation {simulation_id}")
    
    users = scenario['users']
    time_steps = min(scenario['simulation_config']['total_steps'], 100)  # 샘플에서는 최대 100 스텝
    
    # PDP 보간 수행
    pdp_profiles = interpolate_pdp(users, time_steps)
    
    logger.info(f"Generated PDP profiles for {len(users)} users over {time_steps} time steps")
    
    # 통계 계산
    all_rms_delays = [
        p['pdp']['rms_delay']
        for time_pdp in pdp_profiles
        for p in time_pdp
    ]
    
    # Monitor Pool로 업데이트 전송
    monitor_update = {
        'update_type': 'pdp_interpolated',
        'simulation_id': simulation_id,
        'timestamp': datetime.now().isoformat(),
        'data': {
            'num_users': len(users),
            'time_steps': time_steps,
            'pdp_statistics': {
                'avg_rms_delay_ns': np.mean(all_rms_delays),
                'max_rms_delay_ns': np.max(all_rms_delays),
                'min_rms_delay_ns': np.min(all_rms_delays)
            }
        }
    }
    
    redis_client.lpush(MONITOR_UPDATE_QUEUE, json.dumps(monitor_update))
    
    return True

def main():
    """메인 워커 루프"""
    logger.info("PDP Interpolator Worker started")
    logger.info(f"Listening on queue: {PDP_QUEUE}")
    
    while True:
        try:
            result = redis_client.brpop(PDP_QUEUE, timeout=1)
            
            if result:
                queue_name, job_json = result
                job_data = json.loads(job_json)
                
                logger.info(f"Received PDP job: {job_data.get('simulation_id', 'unknown')}")
                
                success = process_pdp_interpolation(job_data)
                
                if success:
                    logger.info(f"PDP interpolation completed")
                else:
                    logger.error(f"PDP interpolation failed")
            
            time.sleep(0.1)
            
        except KeyboardInterrupt:
            logger.info("Worker stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in worker loop: {str(e)}")
            time.sleep(1)

if __name__ == '__main__':
    main()
