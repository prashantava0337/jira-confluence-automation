# simple Dockerfile for Vite dev (not for production)
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev"]
