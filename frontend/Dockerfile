FROM node:22-slim

WORKDIR /app

# Only copy package.json to avoid Windows cross-platform lockfile conflicts
COPY package.json ./
RUN npm install

# Copy source code
COPY . .

# Expose Vite's default dev server port
EXPOSE 5173

# Start the development server and bind to all network interfaces
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
