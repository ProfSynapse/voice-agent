# Voice Agent Tests

This directory contains comprehensive tests for the LiveKit-powered voice conversation agent. The tests are organized by component and follow the Test-Driven Development (TDD) approach.

## Test Structure

The tests are organized into the following directories:

- `auth/`: Tests for authentication functionality
- `voice/`: Tests for voice processing and LiveKit integration
- `conversation/`: Tests for conversation management
- `admin/`: Tests for admin functionality
- `ui/`: Tests for UI components
- `integration/`: Integration tests for end-to-end flows

## Running Tests

### Prerequisites

- Python 3.8+
- pytest
- pytest-asyncio
- pytest-mock

### Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

### Running All Tests

To run all tests:

```bash
pytest src/tests/
```

### Running Specific Test Categories

To run tests for a specific component:

```bash
# Authentication tests
pytest src/tests/auth/

# Voice processing tests
pytest src/tests/voice/

# Conversation management tests
pytest src/tests/conversation/

# Admin functionality tests
pytest src/tests/admin/

# UI component tests
pytest src/tests/ui/

# Integration tests
pytest src/tests/integration/
```

### Running with Coverage

To run tests with coverage reporting:

```bash
pytest --cov=src src/tests/
```

## Test Coverage

The tests cover the following components and functionality:

### Authentication Tests

- User registration
- User login
- Password validation
- Role-based access control (regular users vs admins)
- Session management
- Password reset functionality

### Voice Processing Tests

- LiveKit connection and session management
- Audio capture and playback
- Voice activity detection
- Audio transcription
- Speech synthesis

### Conversation Management Tests

- Conversation creation and retrieval
- Conversation turn management
- Conversation archiving and deletion
- Supabase integration for storing conversations

### Admin Functionality Tests

- System prompt management
- Admin-only operations
- Default prompt configuration

### UI Component Tests

- UI component rendering
- User interaction handling
- Voice-specific UI components
- Theme management

### Integration Tests

- End-to-end user flows
- System initialization
- Error handling
- Service interaction

## Mocking Strategy

The tests use mocking to isolate components and avoid external dependencies:

- Supabase client is mocked to avoid actual database operations
- LiveKit WebSocket connections are mocked
- Audio devices are mocked to avoid actual audio capture/playback
- HTTP clients are mocked to avoid actual API calls

## Test Fixtures

Common test fixtures are defined in `conftest.py` and include:

- Mock Supabase client
- Mock environment configuration
- Sample user objects
- Event loop for async tests

## Adding New Tests

When adding new tests:

1. Follow the TDD approach: write failing tests first, then implement the code to make them pass
2. Use appropriate mocking to isolate the component being tested
3. Ensure tests are independent and don't rely on external services
4. Keep test files organized by component
5. Use descriptive test names that explain what is being tested