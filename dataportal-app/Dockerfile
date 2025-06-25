# Build stage
FROM node:22-alpine3.19 as build

WORKDIR /app

ARG REACT_APP_BASENAME=/
ENV PUBLIC_URL=$REACT_APP_BASENAME

COPY dataportal-app/package.json /app/
COPY dataportal-app/package-lock.json /app/
RUN npm install

COPY dataportal-app /app
RUN PUBLIC_URL=$PUBLIC_URL \
    REACT_APP_API_BASE_URL="REACT_APP_API_BASE_URL_PLACEHOLDER" \
    REACT_APP_ASSEMBLY_INDEXES_PATH="REACT_APP_ASSEMBLY_INDEXES_PATH_PLACEHOLDER" \
    REACT_APP_BACINTERACTOME_SHINY_APP_URL="REACT_APP_BACINTERACTOME_SHINY_APP_URL_PLACEHOLDER" \
    REACT_APP_GFF_INDEXES_PATH="REACT_APP_GFF_INDEXES_PATH_PLACEHOLDER" \
    npm run build

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
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

# Replace placeholder values and start Nginx
CMD /bin/sh -c "\
    sed -i 's|REACT_APP_API_BASE_URL_PLACEHOLDER|$REACT_APP_API_BASE_URL|g' /usr/share/nginx/html/static/js/*.js && \
    sed -i 's|REACT_APP_ASSEMBLY_INDEXES_PATH_PLACEHOLDER|$REACT_APP_ASSEMBLY_INDEXES_PATH|g' /usr/share/nginx/html/static/js/*.js && \
    sed -i 's|REACT_APP_GFF_INDEXES_PATH_PLACEHOLDER|$REACT_APP_GFF_INDEXES_PATH|g' /usr/share/nginx/html/static/js/*.js && \
    sed -i 's|REACT_APP_BACINTERACTOME_SHINY_APP_URL_PLACEHOLDER|$REACT_APP_BACINTERACTOME_SHINY_APP_URL|g' /usr/share/nginx/html/static/js/*.js && \
    nginx -g 'daemon off;'"
