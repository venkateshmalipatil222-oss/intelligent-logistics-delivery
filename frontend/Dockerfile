# Stage 1: Build Frontend Assets
FROM node:20-alpine AS build-stage

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci || npm install

# Copy application source
COPY . .

# Build production bundle
RUN npm run build

# Stage 2: Production Nginx Server
FROM nginx:1.27-alpine AS production-stage

# Copy compiled assets from builder
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy custom nginx configuration with SPA routing and WebSocket proxy
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose standard HTTP port
EXPOSE 80

# Run Nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
