FROM python:3.11-slim

WORKDIR /app

# Python 패키지 설치
RUN pip install --no-cache-dir \
    flask==3.0.0 \
    flask-cors==4.0.0 \
    redis==5.0.1

# 애플리케이션 복사
COPY storage-app.py /app/

# 저장 디렉토리 생성
RUN mkdir -p /app/results /app/scenarios

# 헬스체크
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

EXPOSE 8080

CMD ["python", "-u", "storage-app.py"]
