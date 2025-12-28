FROM python:3.11-slim

WORKDIR /app

# Python 패키지 설치
RUN pip install --no-cache-dir \
    flask==3.0.0 \
    flask-cors==4.0.0 \
    redis==5.0.1 \
    requests==2.31.0

# 애플리케이션 복사
COPY control-pool/api-gateway.py /app/

# 클라이언트 파일 복사
COPY client /app/client

# 헬스체크
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

EXPOSE 8080

CMD ["python", "-u", "api-gateway.py"]
