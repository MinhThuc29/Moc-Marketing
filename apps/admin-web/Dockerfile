FROM node:22-alpine AS base

WORKDIR /app

# Install dependencies based on package manager
COPY package.json package-lock.json* ./
COPY packages/ ./packages/
COPY apps/admin-web/ ./apps/admin-web/

RUN npm install

WORKDIR /app/apps/admin-web
RUN npm run build

EXPOSE 3000
ENV PORT=3000
CMD ["npm", "run", "start"]
