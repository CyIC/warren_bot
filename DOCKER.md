# Docker Deployment Guide for Warren Bot

This guide covers how to build and run Warren Bot using Docker.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+ (optional, for easier deployment)
- Discord Bot Token

## Quick Start with Docker Compose (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/CyIC/warren_bot.git
   cd warren_bot
   ```

2. **Set up environment variables**
   ```bash
   cp .env.template .env
   # Edit .env file with your Discord bot token
   ```

3. **Prepare configuration files**
   ```bash
   # Copy and customize your club data files
   cp club_info_template.json club_info.json
   cp club_stocks.csv club_stocks.csv  # if you have existing data
   ```

4. **Run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

5. **Check logs**
   ```bash
   docker-compose logs -f warren-bot
   ```

## Manual Docker Build and Run

### Build the Image

```bash
# Build the Docker image
docker build -t warren-bot:latest .
```

### Run the Container

```bash
# Run the container with environment variables
docker run -d \
  --name warren-bot \
  --restart unless-stopped \
  -e DISCORD_TOKEN="your_discord_bot_token_here" \
  -e LOGGING_LEVEL="INFO" \
  -v $(pwd)/club_info.json:/app/club_info.json:ro \
  -v $(pwd)/club_stocks.csv:/app/club_stocks.csv:ro \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  warren-bot:latest
```

## Configuration

### Environment Variables

| Variable             | Required | Default           | Description                                 |
|----------------------|----------|-------------------|---------------------------------------------|
| `DISCORD_TOKEN`      | Yes      | -                 | Discord bot token                           |
| `DISCORD_APP_ID`     | No       | -                 | Discord application ID                      |
| `DISCORD_PUBLIC_KEY` | No       | -                 | Discord public key                          |
| `LOGGING_LEVEL`      | No       | INFO              | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `DEBUG_MODE`         | No       | false             | Enable debug mode                           |
| `CLUB_INFO_FILE`     | No       | ./club_info.json  | Path to club info file                      |
| `CLUB_STOCKS_FILE`   | No       | ./club_stocks.csv | Path to club stocks file                    |

### Volume Mounts

| Host Path           | Container Path         | Purpose                          |
|---------------------|------------------------|----------------------------------|
| `./club_info.json`  | `/app/club_info.json`  | Club configuration (read-only)   |
| `./club_stocks.csv` | `/app/club_stocks.csv` | Stock portfolio data (read-only) |
| `./data`            | `/app/data`            | Persistent data storage          |
| `./logs`            | `/app/logs`            | Log files                        |

## Management Commands

### View Logs

```bash
# Docker Compose
docker-compose logs -f warren-bot

# Docker
docker logs -f warren-bot
```

### Stop the Bot

```bash
# Docker Compose
docker-compose down

# Docker
docker stop warren-bot
docker rm warren-bot
```

### Update the Bot

```bash
# Docker Compose
docker-compose down
docker-compose pull  # if using pre-built image
docker-compose build  # if building locally
docker-compose up -d

# Docker
docker stop warren-bot
docker rm warren-bot
docker build -t warren-bot:latest .
# Run command again
```

### Access Container Shell (for debugging)

```bash
# Docker Compose
docker-compose exec warren-bot /bin/bash

# Docker
docker exec -it warren-bot /bin/bash
```

## Security Considerations

1. **Environment Variables**: Never commit your `.env` file with real tokens
2. **File Permissions**: The container runs as a non-root user for security
3. **Network**: The bot doesn't expose any ports by default
4. **Updates**: Regularly update the base image and dependencies

## Troubleshooting

### Common Issues

1. **Bot won't start**
    - Check Discord token is valid
    - Verify environment variables are set correctly
    - Check logs for specific error messages

2. **Permission errors**
    - Ensure volume mount directories exist and are readable
    - Check file ownership if mounting existing files

3. **Memory issues**
    - Adjust resource limits in docker-compose.yml
    - Monitor container memory usage: `docker stats warren-bot`

### Debug Mode

To run in debug mode:

```bash
# Add to .env file
DEBUG_MODE=true
LOGGING_LEVEL=DEBUG

# Restart container
docker-compose down && docker-compose up -d
```

## Production Deployment

For production deployment, consider:

1. **Resource Limits**: Set appropriate CPU and memory limits
2. **Health Checks**: Configure proper health checks
3. **Monitoring**: Set up log aggregation and monitoring
4. **Backup**: Regular backup of persistent data
5. **Updates**: Automated deployment pipeline

### Example Production docker-compose.yml

```yaml
version: '3.8'
services:
  warren-bot:
    build: .
    restart: unless-stopped
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - LOGGING_LEVEL=INFO
    volumes:
      - ./prod-data:/app/data
      - ./prod-logs:/app/logs
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "5"
```

## Multi-Architecture Support

The Dockerfile supports multiple architectures. To build for different platforms:

```bash
# Build for multiple architectures
docker buildx build --platform linux/amd64,linux/arm64 -t warren-bot:latest .

# Build for Raspberry Pi
docker buildx build --platform linux/arm/v7 -t warren-bot:arm -.