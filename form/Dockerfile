FROM node:22-alpine
WORKDIR /app
COPY package.json server.js ./
ENV NODE_ENV=production
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://127.0.0.1:3000/health >/dev/null || exit 1
CMD ["node", "server.js"]
