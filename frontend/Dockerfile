# Stage 1: Build React app
FROM node:20-alpine AS build

WORKDIR /app

# Copy package.json first
COPY package.json ./

# Generate package-lock.json inside the container
RUN npm install --package-lock-only

# Install dependencies using the generated lock file
RUN npm install

# Copy the rest of the source code
COPY . .

# Build optimized production files
RUN npm run build

# Stage 2: Serve using nginx
FROM nginx:alpine

# Copy built React app to nginx html folder
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
