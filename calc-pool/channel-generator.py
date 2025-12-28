#!/usr/bin/env python3
"""
Channel Generator Worker
Ray Tracing 기반 채널 생성 시뮬레이터
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
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Redis 연결
REDIS_HOST = os.getenv("REDIS_HOST", "redis-service.queue-system.svc.cluster.local")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

CHANNEL_QUEUE = "channel_queue"
MONITOR_UPDATE_QUEUE = "monitor_update_queue"

try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
        socket_connect_timeout=5,
    )
    redis_client.ping()
    logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
except Exception as e:
    logger.error(f"Failed to connect to Redis: {str(e)}")
    exit(1)


def calculate_path_loss(distance, frequency):
    """
    간단한 Path Loss 계산 (Free Space Path Loss)
    FSPL(dB) = 20*log10(d) + 20*log10(f) + 32.45
    """
    if distance < 1:
        distance = 1
    fspl = 20 * np.log10(distance) + 20 * np.log10(frequency / 1e6) + 32.45
    return fspl


def generate_channel_response(user, base_station):
    """사용자-기지국 간 채널 응답 생성"""
    # 거리 계산
    dx = user["position"]["x"] - base_station["position"]["x"]
    dy = user["position"]["y"] - base_station["position"]["y"]
    dz = user["position"]["z"] - base_station["position"]["z"]
    distance = np.sqrt(dx**2 + dy**2 + dz**2)

    # Path Loss 계산
    path_loss = calculate_path_loss(distance, base_station["frequency"])

    # 간단한 채널 모델 (여기서는 Rayleigh Fading 시뮬레이션)
    # 실제로는 Ray Tracing을 사용하지만, 샘플에서는 간소화
    num_paths = 5  # 다중 경로
    channel_taps = []

    for i in range(num_paths):
        # 각 경로의 복소 채널 계수
        real_part = np.random.randn()
        imag_part = np.random.randn()
        magnitude = np.sqrt(real_part**2 + imag_part**2)
        phase = np.arctan2(imag_part, real_part)

        # 경로 지연 (나노초)
        delay = i * 10 + distance / 3e8 * 1e9  # 빛의 속도 기반

        channel_taps.append(
            {
                "delay_ns": delay,
                "magnitude": magnitude,
                "phase": phase,
                "power_db": -path_loss - i * 3,  # 각 경로마다 3dB 감쇠
            }
        )

    return {
        "user_id": user["user_id"],
        "bs_id": base_station["bs_id"],
        "distance": distance,
        "path_loss_db": path_loss,
        "channel_taps": channel_taps,
        "snr_db": base_station["tx_power"] - path_loss - 10,  # 간단한 SNR 계산
    }


def process_channel_generation(job_data):
    """채널 생성 처리"""
    simulation_id = job_data["simulation_id"]
    scenario = job_data["scenario"]

    logger.info(f"Generating channels for simulation {simulation_id}")

    users = scenario["users"]
    base_stations = scenario["base_stations"]

    # 모든 사용자-기지국 쌍에 대한 채널 생성
    channel_matrix = []

    for user in users:
        user_channels = []
        for bs in base_stations:
            channel = generate_channel_response(user, bs)
            user_channels.append(channel)
        channel_matrix.append({"user_id": user["user_id"], "channels": user_channels})

    logger.info(
        f"Generated {len(channel_matrix)} user channels with {len(base_stations)} BS each"
    )

    # Monitor Pool로 업데이트 전송
    monitor_update = {
        "update_type": "channel_generated",
        "simulation_id": simulation_id,
        "timestamp": datetime.now().isoformat(),
        "data": {
            "num_users": len(users),
            "num_base_stations": len(base_stations),
            "channel_matrix_summary": {
                "avg_snr": np.mean(
                    [ch["snr_db"] for uc in channel_matrix for ch in uc["channels"]]
                )
            },
        },
    }

    redis_client.lpush(MONITOR_UPDATE_QUEUE, json.dumps(monitor_update))

    return True


def main():
    """메인 워커 루프"""
    logger.info("Channel Generator Worker started")
    logger.info(f"Listening on queue: {CHANNEL_QUEUE}")

    while True:
        try:
            result = redis_client.brpop(CHANNEL_QUEUE, timeout=1)

            if result:
                queue_name, job_json = result
                job_data = json.loads(job_json)

                logger.info(
                    f"Received channel job: {job_data.get('simulation_id', 'unknown')}"
                )

                success = process_channel_generation(job_data)

                if success:
                    logger.info(f"Channel generation completed")
                else:
                    logger.error(f"Channel generation failed")

            time.sleep(0.1)

        except KeyboardInterrupt:
            logger.info("Worker stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in worker loop: {str(e)}")
            time.sleep(1)


if __name__ == "__main__":
    main()
