FROM node:22-alpine3.19

# Set work directory
WORKDIR /app

# Install dependencies
COPY dataportal-app/package.json /app/
COPY dataportal-app/package-lock.json /app/
RUN npm install

COPY dataportal-app /app

# Build React app
RUN npm run build

EXPOSE 3000
CMD ["npx", "serve", "-s", "build"]
