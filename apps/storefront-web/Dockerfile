FROM node:22-alpine AS base

WORKDIR /app

COPY package.json package-lock.json* ./
COPY packages/ ./packages/
COPY apps/storefront-web/ ./apps/storefront-web/

RUN npm install

WORKDIR /app/apps/storefront-web
RUN npm run build

EXPOSE 3001
ENV PORT=3001
CMD ["npm", "run", "start"]
