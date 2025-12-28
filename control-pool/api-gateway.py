#!/usr/bin/env python3
"""
API Gateway
모든 API 엔드포인트를 통합하고 WebSocket 프록시 역할 수행
"""

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path

import redis
import requests
from flask import Flask, jsonify, redirect, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder=None)
CORS(app)

# 클라이언트 파일 경로
CLIENT_DIR = Path("/app/client")

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Service URLs (환경변수 우선, K3s DNS는 fallback)
SCENARIO_SERVICE_URL = os.getenv(
    "SCENARIO_SERVICE_URL",
    "http://scenario-service.scenario-pool.svc.cluster.local:8080",
)
STORAGE_SERVICE_URL = os.getenv(
    "STORAGE_SERVICE_URL", "http://storage-service.storage-pool.svc.cluster.local:8080"
)
MONITOR_SERVICE_URL = os.getenv(
    "MONITOR_SERVICE_URL", "http://monitor-service.monitor-pool.svc.cluster.local:8080"
)

# Redis 연결
REDIS_HOST = os.getenv("REDIS_HOST", "redis-service.queue-system.svc.cluster.local")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

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

SIMULATION_QUEUE = "simulation_queue"

# ========== Static File Serving ==========


@app.route("/", methods=["GET"])
def index():
    """API Gateway 루트 - API 정보"""
    return redirect("/api", code=302)


@app.route("/web_client", methods=["GET"])
@app.route("/web_client/", methods=["GET"])
def web_client():
    """웹 클라이언트 메인 페이지"""
    client_file = CLIENT_DIR / "web-client.html"
    if client_file.exists():
        return send_from_directory(str(CLIENT_DIR), "web-client.html")
    else:
        return jsonify({"error": "Web client not found"}), 404


# ========== Health Check ==========


@app.route("/health", methods=["GET"])
def health_check():
    """헬스체크"""
    return (
        jsonify(
            {
                "status": "healthy",
                "service": "api-gateway",
                "timestamp": datetime.now().isoformat(),
            }
        ),
        200,
    )


@app.route("/api", methods=["GET"])
def api_info():
    """API 정보"""
    return (
        jsonify(
            {
                "service": "Wireless Simulation Pipeline API Gateway",
                "version": "1.0.0",
                "endpoints": {
                    "scenarios": "/api/scenario/*",
                    "simulations": "/api/simulation/*",
                    "results": "/api/results/*",
                    "monitoring": "/api/monitor/*",
                    "websocket": "ws://<host>:30082/",
                },
                "timestamp": datetime.now().isoformat(),
            }
        ),
        200,
    )


# ========== Scenario Management ==========


@app.route("/api/scenario/create", methods=["POST"])
def create_scenario():
    """새 시나리오 생성"""
    try:
        data = request.get_json()

        # Scenario Service로 전달
        response = requests.post(
            f"{SCENARIO_SERVICE_URL}/generate", json=data, timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as e:
        logger.error(f"Scenario service error: {str(e)}")
        return jsonify({"error": f"Scenario service error: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Error in create_scenario: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/scenario/templates", methods=["GET"])
def get_scenario_templates():
    """시나리오 템플릿 목록"""
    try:
        response = requests.get(f"{SCENARIO_SERVICE_URL}/templates", timeout=5)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Error in get_scenario_templates: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/scenario/list", methods=["GET"])
def list_scenarios():
    """시나리오 목록 조회"""
    try:
        response = requests.get(f"{STORAGE_SERVICE_URL}/scenarios", timeout=5)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Error in list_scenarios: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/scenario/<scenario_id>", methods=["GET"])
def get_scenario(scenario_id):
    """특정 시나리오 조회"""
    try:
        response = requests.get(
            f"{STORAGE_SERVICE_URL}/scenarios/{scenario_id}", timeout=5
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Error in get_scenario: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ========== Simulation Control ==========


@app.route("/api/simulation/start", methods=["POST"])
def start_simulation():
    """시뮬레이션 시작"""
    try:
        data = request.get_json()
        scenario_id = data.get("scenario_id")

        if not scenario_id:
            return jsonify({"error": "scenario_id is required"}), 400

        # 시뮬레이션 ID 생성
        simulation_id = f"sim_{uuid.uuid4().hex[:12]}"

        # 시뮬레이션 작업을 큐에 추가
        job_data = {
            "simulation_id": simulation_id,
            "scenario_id": scenario_id,
            "timestamp": datetime.now().isoformat(),
        }

        redis_client.lpush(SIMULATION_QUEUE, json.dumps(job_data))

        logger.info(f"Simulation started: {simulation_id} with scenario {scenario_id}")

        return (
            jsonify(
                {
                    "status": "started",
                    "simulation_id": simulation_id,
                    "scenario_id": scenario_id,
                    "message": "Simulation queued successfully",
                    "websocket_url": "ws://<host>:30082/",
                }
            ),
            202,
        )

    except Exception as e:
        logger.error(f"Error in start_simulation: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/simulation/status/<simulation_id>", methods=["GET"])
def get_simulation_status(simulation_id):
    """시뮬레이션 상태 조회"""
    try:
        # Storage에서 결과 조회
        response = requests.get(
            f"{STORAGE_SERVICE_URL}/results/{simulation_id}", timeout=5
        )

        if response.status_code == 200:
            result_data = response.json()
            return (
                jsonify(
                    {
                        "simulation_id": simulation_id,
                        "status": result_data.get("status", "unknown"),
                        "progress": result_data.get("progress", 0.0),
                        "data": result_data,
                    }
                ),
                200,
            )
        elif response.status_code == 404:
            return (
                jsonify(
                    {
                        "simulation_id": simulation_id,
                        "status": "not_found",
                        "message": "Simulation not found or not started yet",
                    }
                ),
                404,
            )
        else:
            return jsonify(response.json()), response.status_code

    except Exception as e:
        logger.error(f"Error in get_simulation_status: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ========== Results Management ==========


@app.route("/api/results/list", methods=["GET"])
def list_results():
    """결과 목록 조회"""
    try:
        response = requests.get(f"{STORAGE_SERVICE_URL}/results", timeout=5)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Error in list_results: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/results/<simulation_id>", methods=["GET"])
def get_result(simulation_id):
    """특정 결과 조회"""
    try:
        response = requests.get(
            f"{STORAGE_SERVICE_URL}/results/{simulation_id}", timeout=5
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Error in get_result: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ========== Monitoring ==========


@app.route("/api/monitor/stats", methods=["GET"])
def get_monitor_stats():
    """모니터링 통계"""
    try:
        response = requests.get(f"{MONITOR_SERVICE_URL}/stats", timeout=5)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Error in get_monitor_stats: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ========== Queue Statistics ==========


@app.route("/api/queue/stats", methods=["GET"])
def get_queue_stats():
    """큐 통계"""
    try:
        stats = {
            "simulation_queue": redis_client.llen(SIMULATION_QUEUE),
            "channel_queue": redis_client.llen("channel_queue"),
            "pdp_queue": redis_client.llen("pdp_queue"),
            "monitor_update_queue": redis_client.llen("monitor_update_queue"),
            "timestamp": datetime.now().isoformat(),
        }
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Error in get_queue_stats: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Starting API Gateway on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
