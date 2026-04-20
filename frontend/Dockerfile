# # Stage 1: Build React app
# FROM node:20-alpine AS build

# WORKDIR /app

# # Copy package.json first
# COPY package.json ./

# # Generate package-lock.json inside the container
# RUN npm install --package-lock-only

# # Install dependencies using the generated lock file
# RUN npm install

# # Copy the rest of the source code
# COPY . .

# # Build optimized production files
# RUN npm run build

# # Stage 2: Serve using nginx
# FROM nginx:alpine

# # Copy built React app to nginx html folder
# COPY --from=build /app/dist /usr/share/nginx/html

# EXPOSE 80

# CMD ["nginx", "-g", "daemon off;"]

# --- STAGE 1: Build the Application ---
FROM node:20-alpine AS build
WORKDIR /app

# Copy package files and install dependencies first (leverages Docker cache)
# IMPORTANT: Using --legacy-peer-deps to fix ERESOLVE error.
COPY package.json package-lock.json* ./
RUN npm install --legacy-peer-deps

# Copy the rest of the source code and configuration files
COPY . .

# Run the build command (Vite builds the static assets into 'dist')
RUN npm run build

# --- STAGE 2: Serve the Static Files (Lightweight Production Server) ---
# We use node:20-alpine again, but you could use a smaller nginx image here if preferred
FROM node:20-alpine AS runner

# Install 'serve' globally to serve the static content
RUN npm install -g serve

WORKDIR /usr/app

# Copy the build output from the build stage
COPY --from=build /app/dist ./dist

# Expose the port where 'serve' will run (must match docker-compose.yml)
EXPOSE 3000

# Command to run the static file server, serving the 'dist' directory
CMD ["serve", "-s", "dist", "-l", "3000"]