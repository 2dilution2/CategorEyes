# Python 기반 이미지 선택
FROM python:3.10

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# FastAPI 애플리케이션 소스 복사
COPY ./app /app

# Uvicorn으로 FastAPI 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
