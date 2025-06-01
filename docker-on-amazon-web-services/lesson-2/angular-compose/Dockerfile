FROM node:14-alpine AS build
WORKDIR /app
COPY package*.json .
RUN npm install
COPY . .
RUN npm run build

FROM nginx:1.13.12-alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY /app/nginx.conf /etc/nginx/conf.d/default.conf
