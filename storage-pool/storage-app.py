#!/usr/bin/env python3
"""
Storage Pool Service
시뮬레이션 결과 및 데이터 저장/조회 서비스
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
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

# 저장 디렉토리 설정
RESULTS_DIR = os.getenv('RESULTS_DIR', '/app/results')
SCENARIOS_DIR = os.getenv('SCENARIOS_DIR', '/app/scenarios')

os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(SCENARIOS_DIR, exist_ok=True)

# ========== Helper Functions ==========

def save_json_file(directory, filename, data):
    """JSON 파일 저장"""
    filepath = os.path.join(directory, f"{filename}.json")
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved file: {filepath}")
        return True
    except Exception as e:
        logger.error(f"Error saving file {filepath}: {str(e)}")
        return False

def load_json_file(directory, filename):
    """JSON 파일 로드"""
    filepath = os.path.join(directory, f"{filename}.json")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        logger.warning(f"File not found: {filepath}")
        return None
    except Exception as e:
        logger.error(f"Error loading file {filepath}: {str(e)}")
        return None

def list_files(directory):
    """디렉토리의 JSON 파일 목록 반환"""
    try:
        files = [f.replace('.json', '') for f in os.listdir(directory) if f.endswith('.json')]
        return files
    except Exception as e:
        logger.error(f"Error listing files in {directory}: {str(e)}")
        return []

# ========== Health Check ==========

@app.route('/health', methods=['GET'])
def health_check():
    """헬스체크 엔드포인트"""
    return jsonify({
        'status': 'healthy',
        'service': 'storage-pool',
        'timestamp': datetime.now().isoformat()
    }), 200

# ========== Scenario Storage ==========

@app.route('/scenarios/<scenario_id>', methods=['POST'])
def save_scenario(scenario_id):
    """시나리오 데이터 저장"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # 메타데이터 추가
        data['scenario_id'] = scenario_id
        data['created_at'] = datetime.now().isoformat()
        
        if save_json_file(SCENARIOS_DIR, scenario_id, data):
            logger.info(f"Scenario saved: {scenario_id}")
            return jsonify({
                'status': 'success',
                'scenario_id': scenario_id,
                'message': 'Scenario saved successfully'
            }), 201
        else:
            return jsonify({'error': 'Failed to save scenario'}), 500
            
    except Exception as e:
        logger.error(f"Error in save_scenario: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/scenarios/<scenario_id>', methods=['GET'])
def get_scenario(scenario_id):
    """시나리오 데이터 조회"""
    try:
        data = load_json_file(SCENARIOS_DIR, scenario_id)
        if data:
            return jsonify(data), 200
        else:
            return jsonify({'error': 'Scenario not found'}), 404
    except Exception as e:
        logger.error(f"Error in get_scenario: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/scenarios', methods=['GET'])
def list_scenarios():
    """시나리오 목록 조회"""
    try:
        scenarios = list_files(SCENARIOS_DIR)
        return jsonify({
            'scenarios': scenarios,
            'count': len(scenarios)
        }), 200
    except Exception as e:
        logger.error(f"Error in list_scenarios: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ========== Simulation Results Storage ==========

@app.route('/results/<simulation_id>', methods=['POST'])
def save_result(simulation_id):
    """시뮬레이션 결과 저장"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # 메타데이터 추가
        data['simulation_id'] = simulation_id
        data['stored_at'] = datetime.now().isoformat()
        
        if save_json_file(RESULTS_DIR, simulation_id, data):
            logger.info(f"Result saved: {simulation_id}")
            return jsonify({
                'status': 'success',
                'simulation_id': simulation_id,
                'message': 'Result saved successfully'
            }), 201
        else:
            return jsonify({'error': 'Failed to save result'}), 500
            
    except Exception as e:
        logger.error(f"Error in save_result: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/results/<simulation_id>', methods=['GET'])
def get_result(simulation_id):
    """시뮬레이션 결과 조회"""
    try:
        data = load_json_file(RESULTS_DIR, simulation_id)
        if data:
            return jsonify(data), 200
        else:
            return jsonify({'error': 'Result not found'}), 404
    except Exception as e:
        logger.error(f"Error in get_result: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/results', methods=['GET'])
def list_results():
    """결과 목록 조회"""
    try:
        results = list_files(RESULTS_DIR)
        return jsonify({
            'results': results,
            'count': len(results)
        }), 200
    except Exception as e:
        logger.error(f"Error in list_results: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ========== Statistics ==========

@app.route('/stats', methods=['GET'])
def get_stats():
    """스토리지 통계"""
    try:
        scenario_count = len(list_files(SCENARIOS_DIR))
        result_count = len(list_files(RESULTS_DIR))
        
        return jsonify({
            'scenarios': scenario_count,
            'results': result_count,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error in get_stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    logger.info(f"Starting Storage Pool Service on port {port}")
    logger.info(f"Results directory: {RESULTS_DIR}")
    logger.info(f"Scenarios directory: {SCENARIOS_DIR}")
    app.run(host='0.0.0.0', port=port, debug=False)
