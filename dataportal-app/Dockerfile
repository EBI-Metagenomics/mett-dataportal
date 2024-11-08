# Build stage
FROM node:22-alpine3.19 as build

WORKDIR /app

COPY dataportal-app/package.json /app/
COPY dataportal-app/package-lock.json /app/
RUN npm install

COPY dataportal-app /app
RUN npm run build

# Production stage
FROM nginx:stable-alpine

# Copy build files to NGINX's default public directory
COPY --from=build /app/build /usr/share/nginx/html

# Expose port 80
EXPOSE 80