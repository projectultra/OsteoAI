# Stage 1: Build React app
FROM node:18 AS build

# Set the working directory for React
WORKDIR /app

# Copy package.json and package-lock.json first for dependency installation
COPY package.json package-lock.json ./
# Install Node.js dependencies
RUN npm install

# Copy the rest of the project, including the public folder containing index.html
COPY . .

# Run the React build
RUN npm run build

# Stage 2: Setup Python environment and copy React build
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy Flask dependencies and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p src/upload

# Copy the Flask app and other files
COPY . .

# Copy the built React app from the previous stage
COPY --from=build /app/build /app/build

# Expose port for Flask
EXPOSE 8000

# Command to run Flask
CMD ["python", "app.py"]
