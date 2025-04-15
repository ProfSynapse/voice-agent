# Environment Variables Structure

## 1. Overview

This document outlines the environment variables required for the voice conversation agent application. These variables should be stored in a `.env` file in the root directory of the project and should never be committed to version control.

## 2. Environment Variable Categories

### 2.1 Supabase Configuration

| Variable Name | Description | Example Value | Required |
|---------------|-------------|--------------|----------|
| SUPABASE_URL | URL of the Supabase instance | https://example.supabase.co | Yes |
| SUPABASE_ANON_KEY | Anonymous API key for Supabase | eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... | Yes |
| SUPABASE_SERVICE_KEY | Service role API key for admin operations | eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... | Yes |

### 2.2 LiveKit Configuration

| Variable Name | Description | Example Value | Required |
|---------------|-------------|--------------|----------|
| LIVEKIT_API_KEY | API key for LiveKit | API_KEY_HERE | Yes |
| LIVEKIT_API_SECRET | API secret for LiveKit | API_SECRET_HERE | Yes |
| LIVEKIT_URL | URL of the LiveKit server | wss://example.livekit.cloud | Yes |

### 2.3 AI Service Configuration

| Variable Name | Description | Example Value | Required |
|---------------|-------------|--------------|----------|
| AI_API_KEY | API key for the language model service | sk-... | Yes |
| AI_API_URL | URL of the language model API | https://api.openai.com/v1 | Yes |
| AI_MODEL_NAME | Name of the language model to use | gpt-4 | Yes |
| STT_API_KEY | API key for speech-to-text service | KEY_HERE | Yes |
| STT_API_URL | URL of the speech-to-text API | https://api.speech.example.com | Yes |
| TTS_API_KEY | API key for text-to-speech service | KEY_HERE | Yes |
| TTS_API_URL | URL of the text-to-speech API | https://api.tts.example.com | Yes |

### 2.4 Application Configuration

| Variable Name | Description | Example Value | Required |
|---------------|-------------|--------------|----------|
| APP_ENV | Application environment | development, production, testing | Yes |
| APP_DEBUG | Enable debug mode | true, false | No (defaults to false) |
| APP_PORT | Port for the application to run on | 8000 | No (defaults to 8000) |
| APP_SECRET_KEY | Secret key for session encryption | RANDOM_STRING_HERE | Yes |
| APP_CORS_ORIGINS | Allowed CORS origins | https://example.com,https://app.example.com | No (defaults to *) |

### 2.5 Storage Configuration

| Variable Name | Description | Example Value | Required |
|---------------|-------------|--------------|----------|
| STORAGE_PROVIDER | Storage provider for audio files | supabase, s3, local | No (defaults to supabase) |
| S3_BUCKET_NAME | S3 bucket name (if using S3) | my-app-audio-files | Only if STORAGE_PROVIDER=s3 |
| S3_REGION | S3 region (if using S3) | us-west-2 | Only if STORAGE_PROVIDER=s3 |
| S3_ACCESS_KEY | S3 access key (if using S3) | ACCESS_KEY_HERE | Only if STORAGE_PROVIDER=s3 |
| S3_SECRET_KEY | S3 secret key (if using S3) | SECRET_KEY_HERE | Only if STORAGE_PROVIDER=s3 |
| LOCAL_STORAGE_PATH | Path for local storage (if using local) | ./storage | Only if STORAGE_PROVIDER=local |

### 2.6 Logging Configuration

| Variable Name | Description | Example Value | Required |
|---------------|-------------|--------------|----------|
| LOG_LEVEL | Minimum log level | debug, info, warning, error | No (defaults to info) |
| LOG_FORMAT | Log format | json, text | No (defaults to json) |
| LOG_FILE | Log file path | ./logs/app.log | No (defaults to stdout) |

### 2.7 Secrets Manager Configuration

| Variable Name | Description | Example Value | Required |
|---------------|-------------|--------------|----------|
| SECRETS_MASTER_KEY | Master key for secrets encryption | random_secure_string | No (defaults to development key in non-production) |
| SECRETS_DIR | Directory for storing encrypted secrets | ~/.config/voice_agent | No (defaults to ~/.config/voice_agent) |

## 3. Environment Setup

### 3.1 Development Environment

For local development, create a `.env.development` file with the following template:

```
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# LiveKit Configuration
LIVEKIT_API_KEY=your-livekit-api-key
LIVEKIT_API_SECRET=your-livekit-api-secret
LIVEKIT_URL=wss://your-livekit-server.com

# AI Service Configuration
AI_API_KEY=your-ai-api-key
AI_API_URL=https://api.openai.com/v1
AI_MODEL_NAME=gpt-4
STT_API_KEY=your-stt-api-key
STT_API_URL=https://api.speech.example.com
TTS_API_KEY=your-tts-api-key
TTS_API_URL=https://api.tts.example.com

# Application Configuration
APP_ENV=development
APP_DEBUG=true
APP_PORT=8000
APP_SECRET_KEY=your-secret-key
APP_CORS_ORIGINS=*

# Storage Configuration
STORAGE_PROVIDER=supabase

# Logging Configuration
LOG_LEVEL=debug
LOG_FORMAT=text

# Secrets Manager Configuration
# SECRETS_MASTER_KEY=your-master-key-for-secrets-encryption
# SECRETS_DIR=~/.config/voice_agent
```

### 3.2 Production Environment

For production deployment, create a `.env.production` file with more restrictive settings:

```
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# LiveKit Configuration
LIVEKIT_API_KEY=your-livekit-api-key
LIVEKIT_API_SECRET=your-livekit-api-secret
LIVEKIT_URL=wss://your-livekit-server.com

# AI Service Configuration
AI_API_KEY=your-ai-api-key
AI_API_URL=https://api.openai.com/v1
AI_MODEL_NAME=gpt-4
STT_API_KEY=your-stt-api-key
STT_API_URL=https://api.speech.example.com
TTS_API_KEY=your-tts-api-key
TTS_API_URL=https://api.tts.example.com

# Application Configuration
APP_ENV=production
APP_DEBUG=false
APP_PORT=8000
APP_SECRET_KEY=your-secret-key
APP_CORS_ORIGINS=https://your-domain.com

# Storage Configuration
STORAGE_PROVIDER=s3
S3_BUCKET_NAME=your-bucket-name
S3_REGION=your-region
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key

# Logging Configuration
LOG_LEVEL=info
LOG_FORMAT=json
LOG_FILE=./logs/app.log

# Secrets Manager Configuration
SECRETS_MASTER_KEY=your-secure-production-master-key
SECRETS_DIR=/etc/voice_agent/secrets
```

## 4. Environment Variable Loading

The application should load environment variables in the following order of precedence:

1. Runtime environment variables
2. `.env.{APP_ENV}.local` file (not committed to version control)
3. `.env.{APP_ENV}` file
4. `.env.local` file (not committed to version control)
5. `.env` file

This allows for environment-specific configurations and local overrides.

## 5. Security Considerations

- Never commit `.env` files or any files containing secrets to version control
- Use different API keys for development and production environments
- Rotate API keys periodically
- Limit the permissions of service accounts to only what is necessary
- Store production secrets in a secure vault or environment variable management system
- Implement proper access controls for environment variables in CI/CD pipelines
- Use a strong, randomly generated SECRETS_MASTER_KEY in production
- Store the SECRETS_MASTER_KEY in a secure location separate from the application code
- Ensure the SECRETS_DIR has appropriate file system permissions (readable only by the application user)
- Regularly back up encrypted secrets but maintain their security during backup