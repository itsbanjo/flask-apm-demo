FROM node:14

WORKDIR /usr/src/app

COPY package*.json ./

RUN npm install

COPY . .

EXPOSE 5004

CMD ["node", "--trace-warnings", "--unhandled-rejections=strict", "app.js"]
