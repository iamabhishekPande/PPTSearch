# Use a Debian "bookworm" or higher base image
FROM debian:bookworm-slim

# Update the package lists and install libsqlite3-dev
RUN apt-get update && apt-get install -y libsqlite3-dev

# Set the working directory
WORKDIR /app

# Copy your application code into the container
COPY . /app

# Install Python and create a virtual environment
RUN apt-get install -y python3 python3-venv && \
    python3 -m venv venv

# Install Python dependencies within the virtual environment
RUN /bin/bash -c "source venv/bin/activate && pip install -r requirements.txt"

# Specify the command to run your application
CMD ["venv/bin/python", "app.py"]

