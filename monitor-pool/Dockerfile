FROM python:3.11-slim

WORKDIR /app

# Python 패키지 설치
RUN pip install --no-cache-dir \
    flask==3.0.0 \
    flask-socketio==5.3.5 \
    flask-cors==4.0.0 \
    redis==5.0.1 \
    python-socketio==5.10.0 \
    eventlet==0.33.3

# 애플리케이션 복사
COPY monitor-service.py /app/

# 헬스체크
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

EXPOSE 8080 8081

CMD ["python", "-u", "monitor-service.py"]
