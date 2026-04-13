# Stage 1: build React app
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json .
RUN npm ci --quiet
COPY . .
RUN npm run build

# Stage 2: serve with nginx (also proxies API to backend)
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
# nginx.conf is mounted by docker-compose.prod.yml
