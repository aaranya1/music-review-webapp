# Build the static frontend, then serve it with Caddy (which also proxies /api
# to the backend and handles HTTPS). See ../docker-compose.prod.yml.

FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# Same-origin API: Caddy forwards /api/* to the backend
ENV VITE_API_URL=/api
RUN npm run build

FROM caddy:2-alpine
COPY Caddyfile /etc/caddy/Caddyfile
COPY --from=build /app/dist /srv
