# Build stage
FROM node:22-alpine as build

WORKDIR /app

ARG VITE_BASENAME=/
ENV PUBLIC_URL=$VITE_BASENAME
ENV NODE_OPTIONS="--max-old-space-size=8192"

COPY dataportal-app/package.json /app/
COPY dataportal-app/package-lock.json /app/
RUN npm install --legacy-peer-deps

COPY dataportal-app /app
RUN PUBLIC_URL=$PUBLIC_URL \
    VITE_API_BASE_URL="VITE_API_BASE_URL_PLACEHOLDER" \
    VITE_ASSEMBLY_INDEXES_PATH="VITE_ASSEMBLY_INDEXES_PATH_PLACEHOLDER" \
    VITE_BACINTERACTOME_SHINY_APP_URL="VITE_BACINTERACTOME_SHINY_APP_URL_PLACEHOLDER" \
    VITE_GFF_INDEXES_PATH="VITE_GFF_INDEXES_PATH_PLACEHOLDER" \
    npm run build

# Production stage
FROM nginx:stable-alpine

COPY --from=build /app/dist /usr/share/nginx/html

# Create a more comprehensive nginx configuration
RUN echo 'server { \
    listen 80; \
    server_name localhost; \
    root /usr/share/nginx/html; \
    index index.html; \
    \
    # Handle bgzip files properly \
    location ~* \\.(fa\\.gz|gff\\.gz)$ { \
        add_header Content-Type application/octet-stream; \
        add_header Content-Encoding identity; \
        add_header Cache-Control "public, max-age=31536000"; \
    } \
    \
    # Handle other static files \
    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ { \
        expires 1y; \
        add_header Cache-Control "public, immutable"; \
    } \
    \
    # Main location block \
    location / { \
        try_files $uri $uri/ /index.html; \
        add_header Cache-Control "no-cache, no-store, must-revalidate"; \
        add_header Pragma "no-cache"; \
        add_header Expires "0"; \
    } \
    \
    # Security headers \
    add_header X-Frame-Options "SAMEORIGIN" always; \
    add_header X-Content-Type-Options "nosniff" always; \
    add_header X-XSS-Protection "1; mode=block" always; \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD /bin/sh -c "\
    find /usr/share/nginx/html/assets -type f -name '*.js' -exec sed -i 's|VITE_API_BASE_URL_PLACEHOLDER|'\"\$VITE_API_BASE_URL\"'|g' {} + && \
    find /usr/share/nginx/html/assets -type f -name '*.js' -exec sed -i 's|VITE_ASSEMBLY_INDEXES_PATH_PLACEHOLDER|'\"\$VITE_ASSEMBLY_INDEXES_PATH\"'|g' {} + && \
    find /usr/share/nginx/html/assets -type f -name '*.js' -exec sed -i 's|VITE_GFF_INDEXES_PATH_PLACEHOLDER|'\"\$VITE_GFF_INDEXES_PATH\"'|g' {} + && \
    find /usr/share/nginx/html/assets -type f -name '*.js' -exec sed -i 's|VITE_BACINTERACTOME_SHINY_APP_URL_PLACEHOLDER|'\"\$VITE_BACINTERACTOME_SHINY_APP_URL\"'|g' {} + && \
    nginx -g 'daemon off;'"
