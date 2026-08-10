# syntax=docker/dockerfile:1.7
FROM node:22.18.0-bookworm-slim AS dependencies

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts

FROM node:22.18.0-bookworm-slim AS build

ARG NEXT_PUBLIC_SUPABASE_URL
ARG NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY
ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL \
    NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=$NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY
WORKDIR /app
COPY --from=dependencies /app/node_modules ./node_modules
COPY . .
RUN test -n "$NEXT_PUBLIC_SUPABASE_URL" \
    && test -n "$NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY" \
    && case "$NEXT_PUBLIC_SUPABASE_URL" in https://*) true ;; *) false ;; esac \
    && npm run build \
    && npm prune --omit=dev --ignore-scripts

FROM node:22.18.0-bookworm-slim AS runtime

ENV HOSTNAME=0.0.0.0 \
    NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production \
    PORT=3000

WORKDIR /app
COPY --from=build --chown=node:node /app/package.json ./package.json
COPY --from=build --chown=node:node /app/node_modules ./node_modules
COPY --from=build --chown=node:node /app/.next ./.next
COPY --from=build --chown=node:node /app/public ./public

USER node
EXPOSE 3000
CMD ["npm", "start"]
