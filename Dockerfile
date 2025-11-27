# Use a tiny version of Linux with Python pre-installed
FROM python:3.9-slim

# Create a folder inside the container called /app
WORKDIR /app

# This container will just stay alive waiting for commands
CMD ["tail", "-f", "/dev/null"]