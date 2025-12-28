#!/usr/bin/env python3
"""
Blender 3D Viewer Sample
실시간 시뮬레이션 데이터를 3D로 시각화하는 Blender 스크립트 샘플

사용법:
1. Blender에서 Scripting 탭 열기
2. 이 스크립트를 새 텍스트 블록으로 로드
3. WebSocket URL 설정 후 실행

참고: 이것은 샘플 코드이며, 실제 Blender 환경에서 실행 시 추가 설정이 필요합니다.
"""

import socketio
import json
import threading
import time

# WebSocket 클라이언트 설정
WEBSOCKET_URL = "http://localhost:30082"
SIMULATION_ID = "sim_xxxxxxxxxxxx"  # 실제 시뮬레이션 ID로 변경

class SimulationViewer:
    def __init__(self):
        self.sio = socketio.Client()
        self.is_connected = False
        self.latest_data = None
        
        # Event handlers
        self.sio.on('connect', self.on_connect)
        self.sio.on('disconnect', self.on_disconnect)
        self.sio.on('simulation_update', self.on_update)
        
    def on_connect(self):
        print("Connected to simulation server")
        self.is_connected = True
        
        # Subscribe to simulation
        self.sio.emit('subscribe', {'simulation_id': SIMULATION_ID})
        print(f"Subscribed to simulation: {SIMULATION_ID}")
    
    def on_disconnect(self):
        print("Disconnected from server")
        self.is_connected = False
    
    def on_update(self, data):
        """시뮬레이션 업데이트 수신"""
        print(f"Update received: {data['update_type']}")
        self.latest_data = data
        
        # Delta 업데이트 처리
        if data.get('delta'):
            self.process_delta(data['delta'])
    
    def process_delta(self, delta):
        """
        Delta 업데이트를 처리하여 3D 시각화
        
        이 함수에서는 실제 Blender API를 사용하여:
        - 사용자 위치 업데이트 (블루 구체)
        - 기지국 위치 표시 (붉은 원뿔)
        - 채널 상태를 선으로 표시 (강도에 따라 색상 변경)
        """
        print(f"Processing delta: {delta.get('type')}")
        
        if delta.get('type') == 'full_update':
            print("Full update - initializing scene")
            # 전체 씬 초기화
            self.initialize_scene(delta['data'])
        elif delta.get('type') == 'delta_update':
            print("Delta update - updating objects")
            # 변경된 부분만 업데이트
            for change in delta.get('changes', []):
                self.update_object(change)
    
    def initialize_scene(self, data):
        """전체 씬 초기화"""
        print("Scene initialization")
        print(f"Data keys: {data.keys() if data else 'None'}")
        
        # 실제 Blender 구현에서는 여기서:
        # 1. 모든 기존 오브젝트 삭제
        # 2. 사용자 오브젝트 생성
        # 3. 기지국 오브젝트 생성
        # 4. 환경 설정
    
    def update_object(self, change):
        """오브젝트 업데이트"""
        print(f"Updating: {change.get('key')}")
        
        # 실제 Blender 구현에서는 여기서:
        # 1. 해당 오브젝트 찾기
        # 2. 위치/상태 업데이트
        # 3. 머티리얼/색상 변경
    
    def connect(self):
        """서버에 연결"""
        try:
            print(f"Connecting to {WEBSOCKET_URL}...")
            self.sio.connect(WEBSOCKET_URL)
        except Exception as e:
            print(f"Connection error: {e}")
    
    def disconnect(self):
        """연결 종료"""
        if self.is_connected:
            self.sio.disconnect()

# ===== Blender에서 실행할 때 사용할 코드 =====

# 뷰어 인스턴스 생성
viewer = SimulationViewer()

# 별도 스레드에서 WebSocket 실행
def run_websocket():
    viewer.connect()

thread = threading.Thread(target=run_websocket, daemon=True)
thread.start()

print("Blender Viewer Started")
print(f"Connecting to: {WEBSOCKET_URL}")
print(f"Simulation ID: {SIMULATION_ID}")
print("Wait for connection...")

# Blender 타이머 콜백 (실제 Blender에서 사용)
def update_timer():
    """프레임마다 호출되는 업데이트 함수"""
    if viewer.latest_data:
        # 최신 데이터로 씬 업데이트
        # 실제 Blender API 호출은 여기서
        pass
    return 0.1  # 0.1초마다 업데이트

# ===== 실제 Blender용 구현 예시 (주석 처리됨) =====
"""
import bpy

def create_user_object(user_id, position):
    '''사용자를 나타내는 구체 생성'''
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=0.3,
        location=(position['x']/100, position['y']/100, position['z'])
    )
    obj = bpy.context.object
    obj.name = f"User_{user_id}"
    
    # 파란색 머티리얼
    mat = bpy.data.materials.new(name=f"Mat_{user_id}")
    mat.diffuse_color = (0.2, 0.5, 1.0, 1.0)
    obj.data.materials.append(mat)
    
    return obj

def create_base_station(bs_id, position):
    '''기지국을 나타내는 원뿔 생성'''
    bpy.ops.mesh.primitive_cone_add(
        radius1=0.5,
        radius2=0,
        depth=2,
        location=(position['x']/100, position['y']/100, position['z'])
    )
    obj = bpy.context.object
    obj.name = f"BS_{bs_id}"
    
    # 빨간색 머티리얼
    mat = bpy.data.materials.new(name=f"Mat_{bs_id}")
    mat.diffuse_color = (1.0, 0.2, 0.2, 1.0)
    obj.data.materials.append(mat)
    
    return obj

def update_user_position(user_id, new_position):
    '''사용자 위치 업데이트'''
    obj = bpy.data.objects.get(f"User_{user_id}")
    if obj:
        obj.location = (
            new_position['x']/100,
            new_position['y']/100,
            new_position['z']
        )

# Blender 타이머 등록
bpy.app.timers.register(update_timer)
"""

print("\n" + "="*60)
print("Blender 3D Viewer Sample")
print("="*60)
print("\n이 스크립트는 샘플입니다.")
print("실제 Blender에서 사용하려면 위의 주석 처리된 코드를 참고하세요.")
print("\n필요한 패키지:")
print("  pip install python-socketio[client]")
print("\n사용법:")
print("  1. SIMULATION_ID를 실제 시뮬레이션 ID로 변경")
print("  2. Blender Scripting 탭에서 실행")
print("  3. 실시간 업데이트 확인")
print("="*60)
