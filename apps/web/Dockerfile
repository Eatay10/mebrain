# Web: Vite build -> nginx (aynı origin'den /api proxy)
FROM node:lts-alpine AS build
WORKDIR /repo
RUN npm install -g pnpm@12.21.0
COPY pnpm-workspace.yaml package.json pnpm-lock.yaml ./
COPY packages/api-client/package.json packages/api-client/
COPY apps/web/package.json apps/web/
RUN pnpm install --frozen-lockfile --filter @cth/web...
COPY packages/api-client packages/api-client
COPY apps/web apps/web
RUN pnpm -C apps/web build

FROM nginx:1.27-alpine
COPY apps/web/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=build /repo/apps/web/dist /usr/share/nginx/html
EXPOSE 8080
