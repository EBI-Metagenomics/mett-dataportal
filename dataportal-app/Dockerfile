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

# custom nginx.conf
COPY ./dataportal-app/nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

# Replace placeholder values and start Nginx
CMD /bin/sh -c "\
    sed -i 's|REACT_APP_API_BASE_URL_PLACEHOLDER|$REACT_APP_API_BASE_URL|g' /usr/share/nginx/html/static/js/*.js && \
    sed -i 's|REACT_APP_ASSEMBLY_INDEXES_PATH_PLACEHOLDER|$REACT_APP_ASSEMBLY_INDEXES_PATH|g' /usr/share/nginx/html/static/js/*.js && \
    sed -i 's|REACT_APP_GFF_INDEXES_PATH_PLACEHOLDER|$REACT_APP_GFF_INDEXES_PATH|g' /usr/share/nginx/html/static/js/*.js && \
    nginx -g 'daemon off;'"
