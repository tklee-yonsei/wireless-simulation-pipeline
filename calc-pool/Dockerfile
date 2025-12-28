FROM python:3.11-slim

WORKDIR /app

# Python 패키지 설치
RUN pip install --no-cache-dir \
    redis==5.0.1 \
    requests==2.31.0 \
    numpy==1.26.0

# 모든 워커 스크립트 복사
COPY system-core.py /app/
COPY channel-generator.py /app/
COPY pdp-interpolator.py /app/

# 실행 권한 부여
RUN chmod +x /app/*.py

# 기본 실행 명령 (실제로는 deployment에서 오버라이드)
CMD ["python", "-u", "system-core.py"]
