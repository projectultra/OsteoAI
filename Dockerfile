# Stage 1: Build React app
FROM node:16-alpine AS build

# Set the working directory for React
WORKDIR /app

# Install Node.js dependencies
COPY package.json package-lock.json ./
RUN npm install

# Build the React app
COPY . .
RUN npm run build

# Stage 2: Setup Python environment and copy React build
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy Flask dependencies and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Flask and React code
COPY . .

# Copy the built React app from the previous stage
COPY --from=build /app/build /app/build

# Expose ports for Flask and React
EXPOSE 5000 3000

# Ensure the shell script is executable
RUN chmod +x start.sh

# Command to run both Flask and React
CMD ["bash", "start.sh"]
