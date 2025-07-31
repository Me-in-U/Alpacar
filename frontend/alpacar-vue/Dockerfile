FROM node:20-alpine AS build

# Create app directory
WORKDIR app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy all app source
COPY . .

# Assume the container uses port 3000 (change if your code uses a different port)
EXPOSE 5173

# App start command
CMD [ "npm", "run", "dev" ]
