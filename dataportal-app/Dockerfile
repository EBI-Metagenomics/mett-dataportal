# Build stage
FROM node:22-alpine3.19 as build

WORKDIR /app

COPY dataportal-app/package.json /app/
COPY dataportal-app/package-lock.json /app/
RUN npm install

COPY dataportal-app /app
RUN REACT_APP_API_BASE_URL="REACT_APP_API_BASE_URL_PLACEHOLDER" \
    REACT_APP_ASSEMBLY_INDEXES_PATH="REACT_APP_ASSEMBLY_INDEXES_PATH_PLACEHOLDER" \
    REACT_APP_GFF_INDEXES_PATH="REACT_APP_GFF_INDEXES_PATH_PLACEHOLDER" npm run build

# Production stage
FROM nginx:stable-alpine

COPY --from=build /app/build /usr/share/nginx/html

RUN echo 'server { \
    listen 80; \
    server_name localhost; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
        add_header Access-Control-Allow-Origin * always; \
        add_header Accept-Ranges bytes; \
        add_header Access-Control-Allow-Methods "GET, OPTIONS"; \
        add_header Access-Control-Allow-Headers "*"; \
    } \
    location ~* \.(fa|fa\.gz|gff|gff3|gff3\.gz|json|txt)$ { \
        add_header Access-Control-Allow-Origin * always; \
        add_header Accept-Ranges bytes; \
    } \
    location /health { \
        return 200 "healthy"; \
        add_header Content-Type text/plain; \
    } \
}' > /etc/nginx/conf.d/default.conf


EXPOSE 80

CMD /bin/sh -c "\
    sed -i 's|REACT_APP_API_BASE_URL_PLACEHOLDER|$REACT_APP_API_BASE_URL|g' /usr/share/nginx/html/static/js/*.js && \
    sed -i 's|REACT_APP_ASSEMBLY_INDEXES_PATH_PLACEHOLDER|$REACT_APP_ASSEMBLY_INDEXES_PATH|g' /usr/share/nginx/html/static/js/*.js && \
    sed -i 's|REACT_APP_GFF_INDEXES_PATH_PLACEHOLDER|$REACT_APP_GFF_INDEXES_PATH|g' /usr/share/nginx/html/static/js/*.js && \
    nginx -g 'daemon off;'"
