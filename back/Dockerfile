FROM node:20-alpine

# Instalar dependencias necesarias para compilar modulos nativos como sqlite3 en Alpine
RUN apk add --no-cache python3 make g++

WORKDIR /usr/app

COPY package.json ./

RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
