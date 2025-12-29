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


def calculate_path_loss(distance, frequency_hz):
    """
    3GPP Urban Micro (UMi) 간소화 Path Loss 모델
    더 현실적인 SNR 값을 위해 조정된 모델

    참고: 실제 3GPP 모델은 더 복잡하지만, 시뮬레이션용으로 간소화
    PL(dB) = 32.4 + 20*log10(f_GHz) + 21*log10(d)
    """
    if distance < 1:
        distance = 1

    frequency_ghz = frequency_hz / 1e9  # Hz -> GHz

    # 간소화된 Urban Micro 모델 (LOS 가정)
    path_loss = 32.4 + 20 * np.log10(frequency_ghz) + 21 * np.log10(distance)

    # Shadow fading 추가 (4 dB 표준편차)
    shadow_fading = np.random.normal(0, 4)

    return path_loss + shadow_fading


def calculate_snr(tx_power_dbm, path_loss_db, bandwidth_hz=20e6, noise_figure_db=9):
    """
    현실적인 SNR 계산

    Args:
        tx_power_dbm: 송신 전력 (dBm)
        path_loss_db: 경로 손실 (dB)
        bandwidth_hz: 대역폭 (Hz), 기본 20 MHz
        noise_figure_db: 수신기 노이즈 피규어 (dB)

    Returns:
        SNR in dB
    """
    # 수신 전력
    rx_power_dbm = tx_power_dbm - path_loss_db

    # 열잡음 전력: N = kTB
    # -174 dBm/Hz @ 290K (thermal noise floor)
    thermal_noise_dbm_hz = -174
    noise_power_dbm = (
        thermal_noise_dbm_hz + 10 * np.log10(bandwidth_hz) + noise_figure_db
    )

    # SNR = 수신 전력 - 노이즈 전력
    snr_db = rx_power_dbm - noise_power_dbm

    return snr_db


def generate_channel_response(user, base_station):
    """사용자-기지국 간 채널 응답 생성"""
    # 거리 계산
    dx = user["position"]["x"] - base_station["position"]["x"]
    dy = user["position"]["y"] - base_station["position"]["y"]
    dz = user["position"]["z"] - base_station["position"]["z"]
    distance = np.sqrt(dx**2 + dy**2 + dz**2)

    # Path Loss 계산
    path_loss = calculate_path_loss(distance, base_station["frequency"])

    # 현실적인 SNR 계산
    snr_db = calculate_snr(base_station["tx_power"], path_loss)

    # 간단한 채널 모델 (Rayleigh Fading 시뮬레이션)
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
        "snr_db": snr_db,
    }


def process_channel_generation(job_data):
    """채널 생성 및 실시간 시뮬레이션 처리"""
    simulation_id = job_data["simulation_id"]
    scenario = job_data["scenario"]
    duration = scenario.get("duration", 60)  # 기본 60초
    update_interval = 1.0  # 1초마다 업데이트

    logger.info(f"Starting realtime simulation {simulation_id} for {duration}s")

    users = scenario["users"]
    base_stations = scenario["base_stations"]

    # 시뮬레이션 루프: duration 동안 실시간 업데이트 전송
    num_steps = int(duration / update_interval)

    for time_step in range(num_steps):
        # 사용자 위치 업데이트 (속도 기반 이동)
        for user in users:
            # 속도가 없으면 랜덤 속도 생성
            if "velocity" not in user:
                user["velocity"] = {
                    "x": round(np.random.uniform(-2, 2), 2),
                    "y": round(np.random.uniform(-2, 2), 2),
                    "z": 0,
                }

            # 위치 업데이트
            user["position"]["x"] += user["velocity"]["x"] * update_interval
            user["position"]["y"] += user["velocity"]["y"] * update_interval

            # 경계 처리 (반사)
            for axis in ["x", "y"]:
                if user["position"][axis] < 0 or user["position"][axis] > 500:
                    user["velocity"][axis] *= -1
                    user["position"][axis] = max(0, min(500, user["position"][axis]))

        # 모든 사용자-기지국 쌍에 대한 채널 생성
        all_snr_values = []
        user_states = []

        for user in users:
            best_snr = -999
            best_bs = None

            for bs in base_stations:
                channel = generate_channel_response(user, bs)
                snr = channel["snr_db"]
                all_snr_values.append(snr)

                if snr > best_snr:
                    best_snr = snr
                    best_bs = bs["bs_id"]

            # 사용자 상태 저장
            user_states.append(
                {
                    "user_id": user["user_id"],
                    "position": {
                        "x": round(user["position"]["x"], 1),
                        "y": round(user["position"]["y"], 1),
                    },
                    "velocity": {
                        "x": round(user["velocity"]["x"], 2),
                        "y": round(user["velocity"]["y"], 2),
                    },
                    "snr_db": round(best_snr, 2),
                    "best_bs": best_bs,
                }
            )

        # Monitor Pool로 실시간 업데이트 전송
        monitor_update = {
            "update_type": "realtime_update",
            "simulation_id": simulation_id,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "time_step": time_step,
                "num_users": len(users),
                "num_base_stations": len(base_stations),
                "user_states": user_states,
                "statistics": {
                    "avg_snr_db": round(float(np.mean(all_snr_values)), 2),
                    "max_snr_db": round(float(np.max(all_snr_values)), 2),
                    "min_snr_db": round(float(np.min(all_snr_values)), 2),
                },
            },
        }

        redis_client.lpush(MONITOR_UPDATE_QUEUE, json.dumps(monitor_update))
        logger.info(
            f"Step {time_step}/{num_steps}: Avg SNR = {monitor_update['data']['statistics']['avg_snr_db']} dB"
        )

        # 다음 업데이트까지 대기
        time.sleep(update_interval)

    logger.info(f"Simulation {simulation_id} completed after {num_steps} steps")
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
