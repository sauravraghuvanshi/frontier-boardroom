FROM node:20-alpine AS build
WORKDIR /app

ARG VITE_API_BASE=http://localhost:8000
ARG VITE_WS_BASE=ws://localhost:8000
ARG VITE_ENTRA_AUTH_ENABLED=false
ENV VITE_API_BASE=$VITE_API_BASE
ENV VITE_WS_BASE=$VITE_WS_BASE
ENV VITE_ENTRA_AUTH_ENABLED=$VITE_ENTRA_AUTH_ENABLED

COPY package.json package-lock.json* ./
RUN npm install
COPY . .
RUN chmod -R +x node_modules/.bin && npx vite build

FROM node:20-alpine AS runner
WORKDIR /app
COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./package.json
COPY --from=build /app/vite.config.ts ./vite.config.ts
EXPOSE 5173
CMD ["npx", "vite", "preview", "--host", "0.0.0.0", "--port", "5173"]
