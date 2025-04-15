# Voice Conversation Agent

A real-time voice conversation agent powered by LiveKit, Supabase, and AI services.

## Overview

This project implements a real-time voice conversation agent that allows users to have natural voice conversations with an AI assistant. The application uses LiveKit for voice communication and Supabase for backend services including authentication, database, and storage.

![Voice Conversation Agent](https://placeholder-for-diagram.com/voice-agent-diagram.png)

## Features

- **Real-time Voice Communication**
  - WebRTC-based audio streaming using LiveKit
  - Low-latency, high-quality voice capture and playback
  - Voice activity detection and audio preprocessing

- **User Authentication**
  - Secure registration and login with Supabase Auth
  - Role-based access control (regular users and admins)
  - Profile management
  - JWT token revocation and blacklisting
  - Configurable token expiration and automatic refresh

- **Conversation Management**
  - Create, retrieve, and manage conversations
  - Conversation history with search and filtering
  - Export conversations as text or audio

- **Admin Functionality**
  - System prompt management
  - User management
  - Analytics and reporting
  - Security monitoring and alerts

- **Modern UI**
  - Responsive design for desktop and mobile
  - Accessibility compliance
  - Streamlit-based interface

- **Security Features**
  - Centralized API key and secret management
  - Input validation for LiveKit room and participant names
  - Rate limiting for token generation and subscriptions
  - Subscription limits per user
  - Audit logging for security events
  - Resource usage monitoring

## Technologies Used

- **Frontend**
  - Python with Streamlit
  - LiveKit WebRTC SDK
  - Streamlit WebRTC for audio streaming

- **Backend**
  - Supabase for authentication, database, and storage
  - LiveKit for real-time communication
  - AI services for speech processing and language model integration
  - Security monitoring and audit logging

- **Infrastructure**
  - PostgreSQL database (via Supabase)
  - LiveKit cloud or self-hosted server
  - Railway for deployment
  - Secure environment configuration management

## Quick Start Guide

### Prerequisites

- Python 3.8 or higher
- Supabase account
- LiveKit account
- API keys for AI services (speech-to-text, text-to-speech, language model)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/voice-agent.git
   cd voice-agent
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory with your configuration (see `.env.example` for required variables).

4. Run the application:
   ```bash
   python -m src.app
   ```

5. Open your browser and navigate to `http://localhost:8000`.

## Development Setup

### Environment Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   - Copy `.env.example` to `.env.development`
   - Fill in the required values for your development environment

### Running Tests

```bash
pytest src/tests
```

### Development Workflow

1. Start the application in development mode:
   ```bash
   python -m src.app
   ```

2. Make changes to the code
3. Test your changes
4. Commit your changes with descriptive commit messages

## Deployment on Railway

### Prerequisites

- Railway account
- Supabase project
- LiveKit project

### Deployment Steps

1. Fork this repository to your GitHub account

2. Create a new project on Railway and connect it to your GitHub repository

3. Configure the following environment variables in Railway:
   - All variables from your `.env.production` file

4. Deploy the application:
   - Railway will automatically build and deploy the application
   - The application will be available at the URL provided by Railway

5. Configure the domain (optional):
   - Set up a custom domain in the Railway project settings
   - Update DNS records for your domain

## Documentation

For more detailed documentation, see:

- [User Guide](./docs/user_guide.md) - How to use the application
- [Admin Guide](./docs/admin_guide.md) - Administration tasks
- [Developer Documentation](./docs/developer_documentation.md) - Architecture and development
- [Deployment Guide](./docs/deployment_guide.md) - Detailed deployment instructions
- [Security Documentation](./docs/security_documentation.md) - Security features and best practices
- [Monitoring Documentation](./docs/monitoring_documentation.md) - Monitoring and alerting

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please see the [Contributing Guidelines](CONTRIBUTING.md) for more information.