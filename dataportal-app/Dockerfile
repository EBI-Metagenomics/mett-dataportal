# Build stage
FROM node:22.13.0-alpine3.19 as build

WORKDIR /app

ARG VITE_BASENAME=/
ENV PUBLIC_URL=$VITE_BASENAME

COPY dataportal-app/package.json /app/
COPY dataportal-app/package-lock.json /app/
RUN npm install

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

RUN echo 'server { \
    listen 80; \
    server_name localhost; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD /bin/sh -c "\
    find /usr/share/nginx/html/static/js -type f -name '*.js' -exec sed -i 's|VITE_API_BASE_URL_PLACEHOLDER|'\"\$VITE_API_BASE_URL\"'|g' {} + && \
    find /usr/share/nginx/html/static/js -type f -name '*.js' -exec sed -i 's|VITE_ASSEMBLY_INDEXES_PATH_PLACEHOLDER|'\"\$VITE_ASSEMBLY_INDEXES_PATH\"'|g' {} + && \
    find /usr/share/nginx/html/static/js -type f -name '*.js' -exec sed -i 's|VITE_GFF_INDEXES_PATH_PLACEHOLDER|'\"\$VITE_GFF_INDEXES_PATH\"'|g' {} + && \
    find /usr/share/nginx/html/static/js -type f -name '*.js' -exec sed -i 's|VITE_BACINTERACTOME_SHINY_APP_URL_PLACEHOLDER|'\"\$VITE_BACINTERACTOME_SHINY_APP_URL\"'|g' {} + && \
    nginx -g 'daemon off;'"
