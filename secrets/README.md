# Secrets Management for Warren Bot

This directory contains sensitive configuration files that should **NEVER** be committed to version control.

## Setup Instructions

### 1. Create Discord Token File
```bash
echo "your_discord_bot_token_here" > secrets/discord_token.txt
chmod 600 secrets/discord_token.txt
```

### 2. Optional: Additional Secrets
```bash
# If you need additional API keys
echo "your_other_api_key" > secrets/other_api_key.txt
chmod 600 secrets/other_api_key.txt
```

## Security Best Practices

1. **File Permissions**: Always set restrictive permissions (600) on secret files
2. **Environment**: Use Docker secrets or external secret management in production
3. **Rotation**: Regularly rotate tokens and keys
4. **Monitoring**: Monitor for unauthorized access to secrets

## Docker Integration

The secure Docker setup reads secrets from files instead of environment variables:

```yaml
# docker-compose.secure.yml
secrets:
  discord_token:
    file: ./secrets/discord_token.txt
```

## Production Recommendations

For production deployments, consider:

- **HashiCorp Vault** for centralized secret management
- **AWS Secrets Manager** or **Azure Key Vault** for cloud deployments
- **Kubernetes Secrets** for K8s deployments
- **Docker Swarm Secrets** for Docker Swarm mode

## Files in This Directory

```
secrets/
├── README.md              # This file
├── .gitkeep              # Keep directory in git
├── discord_token.txt     # Discord bot token (create this)
└── example.env           # Example environment file
```

## Emergency Procedures

If secrets are compromised:

1. **Immediately rotate** all affected tokens/keys
2. **Review logs** for unauthorized access
3. **Update** all secret files and restart services
4. **Audit** access patterns and implement additional security measures