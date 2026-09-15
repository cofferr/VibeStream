# Etapa 1: Build del frontend
FROM node:18 AS build
WORKDIR /frontend
COPY package*.json ./
RUN npm install
COPY . .
# Usar archivo de producción para Docker
RUN npm run build -- --mode production

# Etapa 2: Servir con Nginx
FROM nginx:stable-alpine
COPY --from=build /frontend/dist /usr/share/nginx/html

# Opcional: configura Nginx (para SPA/Vite)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
