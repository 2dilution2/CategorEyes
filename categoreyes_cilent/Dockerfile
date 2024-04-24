# 베이스 이미지 선택
FROM node:18

# 작업 디렉토리 생성
WORKDIR /app

# 의존성 파일 복사 및 설치
COPY package.json .
COPY package-lock.json .
RUN npm install

# 애플리케이션 소스 복사
COPY . .

# 빌드 실행
RUN npm run build

# 정적 파일을 서비스하기 위한 베이스 이미지
FROM nginx:1.25

# 빌드된 애플리케이션 복사
COPY --from=0 /app/build /usr/share/nginx/html

# Nginx 실행
CMD ["nginx", "-g", "daemon off;"]
