FROM node:20-alpine AS build

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
# 빌드 산출물은 /app/dist 에 생성됨
