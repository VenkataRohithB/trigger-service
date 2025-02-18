# Use an official Python runtime as a parent image
FROM python:3.10

# Set the timezone to Asia/Kolkata (you can change it to your desired timezone)
RUN apt-get update && apt-get install -y tzdata

# Set the environment variable for timezone
ENV TZ=Asia/Kolkata

# Configure the container to use the correct timezone
RUN dpkg-reconfigure -f noninteractive tzdata

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 8989

# Command to run the app
CMD ["python3", "main.py"]
