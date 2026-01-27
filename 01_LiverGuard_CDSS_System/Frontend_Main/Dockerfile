# -------------------------------
# 1) Build Stage (Node)
# -------------------------------
FROM node:20 AS builder

# 작업 디렉토리
WORKDIR /app

# package.json 먼저 복사 → 캐시 최적화
COPY package*.json ./

# dependencies 설치
RUN npm install

# 전체 소스 복사
COPY . .

# 리액트 빌드
RUN npm run build


# -------------------------------
# 2) Production Stage (Nginx)
# -------------------------------
FROM nginx:1.25-alpine

# Nginx 기본 정적 파일 경로: /usr/share/nginx/html
COPY --from=builder /app/dist /usr/share/nginx/html

# 커스텀 nginx.conf 덮어쓰기
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 9000번 포트로 실행
EXPOSE 9000

CMD ["nginx", "-g", "daemon off;"]