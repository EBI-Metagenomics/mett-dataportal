# Build stage
FROM node:22-alpine3.19 as build

WORKDIR /app

COPY dataportal-app/package.json /app/
COPY dataportal-app/package-lock.json /app/
RUN npm install

ARG REACT_APP_API_BASE_URL
ENV REACT_APP_API_BASE_URL=${REACT_APP_API_BASE_URL}

COPY dataportal-app /app
RUN npm run build

# Production stage
FROM nginx:stable-alpine

COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 80