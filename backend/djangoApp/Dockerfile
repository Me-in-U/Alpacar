# Python 3.11 베이스 이미지 사용
FROM python:3.11-slim-bookworm

# 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=djangoApp.settings

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ gfortran pkg-config curl wget \
    # OpenCV 런타임 의존성
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender1 libgomp1 libgtk-3-0 \
    # 영상/코덱
    libavcodec-dev libavformat-dev libswscale-dev libv4l-dev libxvidcore-dev libx264-dev \
    # 이미지 코덱
    libjpeg62-turbo-dev libpng-dev libtiff5-dev \
    # BLAS: ATLAS 대신 OpenBLAS
    libopenblas-dev \
    # DB
    default-libmysqlclient-dev \
 && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN python -m pip install --upgrade pip
#  && pip install --no-cache-dir -r requirements.txt
RUN pip install -r requirements.txt

# 프로젝트 파일 복사
COPY . .

# 정적 파일 수집을 위한 디렉토리 생성
RUN mkdir -p /app/staticfiles

# 포트 노출
EXPOSE 8000

# 실행 명령어
CMD ["uvicorn", "djangoApp.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "debug", "--access-log"]