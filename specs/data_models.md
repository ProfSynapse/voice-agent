# Data Models for Supabase

## 1. Overview

The application uses Supabase as its backend service, which provides PostgreSQL database capabilities. The following data models define the structure of the database tables and their relationships.

## 2. Entity Relationship Diagram

```
┌─────────────┐       ┌────────────────┐       ┌─────────────────┐
│   users     │       │  conversations  │       │  conversation_  │
│             │       │                │       │     turns       │
├─────────────┤       ├────────────────┤       ├─────────────────┤
│ id          │       │ id             │       │ id              │
│ email       │       │ user_id        │──┐    │ conversation_id │──┐
│ password    │       │ title          │  │    │ role            │  │
│ full_name   │       │ created_at     │  │    │ content         │  │
│ avatar_url  │       │ updated_at     │  │    │ audio_url       │  │
│ role        │───┐   │ system_prompt_id│──┼────│ created_at      │  │
│ created_at  │   │   │ is_archived    │  │    └─────────────────┘  │
│ updated_at  │   │   └────────────────┘  │                         │
└─────────────┘   │                       │                         │
                  │                       │                         │
                  │   ┌────────────────┐  │                         │
                  │   │ system_prompts │  │                         │
                  │   │                │  │                         │
                  │   ├────────────────┤  │                         │
                  │   │ id             │  │                         │
                  └───│ created_by     │  │                         │
                      │ name           │  │                         │
                      │ content        │  │                         │
                      │ category       │  │                         │
                      │ is_default     │  │                         │
                      │ created_at     │  │                         │
                      │ updated_at     │  │                         │
                      └────────────────┘  │                         │
                                          │                         │
                                          │                         │
                      ┌────────────────┐  │                         │
                      │  user_settings │  │                         │
                      │                │  │                         │
                      ├────────────────┤  │                         │
                      │ id             │  │                         │
                      │ user_id        │──┘                         │
                      │ theme          │                            │
                      │ voice_id       │                            │
                      │ language       │                            │
                      │ created_at     │                            │
                      │ updated_at     │                            │
                      └────────────────┘                            │
                                                                    │
                                                                    │
                      ┌────────────────┐                            │
                      │  audio_files   │                            │
                      │                │                            │
                      ├────────────────┤                            │
                      │ id             │                            │
                      │ turn_id        │───────────────────────────┘
                      │ file_path      │
                      │ duration       │
                      │ created_at     │
                      └────────────────┘
```

## 3. Table Definitions

### 3.1 users

Stores user account information and authentication details.

| Column      | Type         | Description                               | Constraints                 |
|-------------|--------------|-------------------------------------------|----------------------------|
| id          | uuid         | Unique identifier                         | PK, default: uuid_generate_v4() |
| email       | varchar(255) | User's email address                     | UNIQUE, NOT NULL           |
| password    | varchar(255) | Hashed password (managed by Supabase Auth) | NOT NULL                   |
| full_name   | varchar(255) | User's full name                         | NOT NULL                   |
| avatar_url  | varchar(255) | URL to user's profile picture            | NULL                       |
| role        | varchar(50)  | User role (user, admin)                  | NOT NULL, default: 'user'  |
| created_at  | timestamp    | Account creation timestamp               | NOT NULL, default: now()   |
| updated_at  | timestamp    | Last update timestamp                    | NOT NULL, default: now()   |

**Indexes:**
- Primary Key: id
- Unique Index: email

**RLS Policies:**
- Users can read/update only their own records
- Admins can read all records and update any record
- No one can delete records (soft delete only)

### 3.2 user_settings

Stores user preferences and settings.

| Column      | Type         | Description                               | Constraints                 |
|-------------|--------------|-------------------------------------------|----------------------------|
| id          | uuid         | Unique identifier                         | PK, default: uuid_generate_v4() |
| user_id     | uuid         | Reference to users table                  | FK, NOT NULL               |
| theme       | varchar(50)  | UI theme preference                      | NOT NULL, default: 'light' |
| voice_id    | varchar(100) | Preferred TTS voice identifier           | NULL                       |
| language    | varchar(50)  | Preferred language                       | NOT NULL, default: 'en-US' |
| created_at  | timestamp    | Record creation timestamp                | NOT NULL, default: now()   |
| updated_at  | timestamp    | Last update timestamp                    | NOT NULL, default: now()   |

**Indexes:**
- Primary Key: id
- Foreign Key: user_id references users(id)

**RLS Policies:**
- Users can read/update only their own settings
- Admins can read all settings

### 3.3 system_prompts

Stores system prompts that can be used to configure the AI's behavior.

| Column      | Type         | Description                               | Constraints                 |
|-------------|--------------|-------------------------------------------|----------------------------|
| id          | uuid         | Unique identifier                         | PK, default: uuid_generate_v4() |
| created_by  | uuid         | Reference to users table (admin)          | FK, NOT NULL               |
| name        | varchar(255) | Prompt name/title                        | NOT NULL                   |
| content     | text         | The actual system prompt text            | NOT NULL                   |
| category    | varchar(100) | Category for organization                | NOT NULL                   |
| is_default  | boolean      | Whether this is a default prompt         | NOT NULL, default: false   |
| created_at  | timestamp    | Record creation timestamp                | NOT NULL, default: now()   |
| updated_at  | timestamp    | Last update timestamp                    | NOT NULL, default: now()   |

**Indexes:**
- Primary Key: id
- Foreign Key: created_by references users(id)

**RLS Policies:**
- All authenticated users can read
- Only admins can create/update/delete

### 3.4 conversations

Stores metadata about conversations.

| Column          | Type         | Description                               | Constraints                 |
|-----------------|--------------|-------------------------------------------|----------------------------|
| id              | uuid         | Unique identifier                         | PK, default: uuid_generate_v4() |
| user_id         | uuid         | Reference to users table                  | FK, NOT NULL               |
| title           | varchar(255) | Conversation title                       | NOT NULL                   |
| created_at      | timestamp    | Conversation start timestamp             | NOT NULL, default: now()   |
| updated_at      | timestamp    | Last update timestamp                    | NOT NULL, default: now()   |
| system_prompt_id | uuid         | Reference to system_prompts table        | FK, NULL                   |
| is_archived     | boolean      | Whether conversation is archived         | NOT NULL, default: false   |

**Indexes:**
- Primary Key: id
- Foreign Key: user_id references users(id)
- Foreign Key: system_prompt_id references system_prompts(id)

**RLS Policies:**
- Users can read/update only their own conversations
- Admins can read all conversations

### 3.5 conversation_turns

Stores individual turns in a conversation.

| Column          | Type         | Description                               | Constraints                 |
|-----------------|--------------|-------------------------------------------|----------------------------|
| id              | uuid         | Unique identifier                         | PK, default: uuid_generate_v4() |
| conversation_id | uuid         | Reference to conversations table          | FK, NOT NULL               |
| role            | varchar(50)  | Role (user or assistant)                  | NOT NULL                   |
| content         | text         | Text content of the turn                 | NOT NULL                   |
| audio_url       | varchar(255) | URL to audio file in storage             | NULL                       |
| created_at      | timestamp    | Turn timestamp                           | NOT NULL, default: now()   |

**Indexes:**
- Primary Key: id
- Foreign Key: conversation_id references conversations(id)

**RLS Policies:**
- Users can read only turns from their own conversations
- Users can create turns only in their own conversations
- No updates allowed (immutable)
- Admins can read all turns

### 3.6 audio_files

Stores metadata about audio recordings.

| Column      | Type         | Description                               | Constraints                 |
|-------------|--------------|-------------------------------------------|----------------------------|
| id          | uuid         | Unique identifier                         | PK, default: uuid_generate_v4() |
| turn_id     | uuid         | Reference to conversation_turns table     | FK, NOT NULL               |
| file_path   | varchar(255) | Path to file in storage                  | NOT NULL                   |
| duration    | float        | Audio duration in seconds                | NOT NULL                   |
| created_at  | timestamp    | Record creation timestamp                | NOT NULL, default: now()   |

**Indexes:**
- Primary Key: id
- Foreign Key: turn_id references conversation_turns(id)

**RLS Policies:**
- Users can read only audio files from their own conversations
- No updates or deletes allowed (immutable)

## 4. Database Functions and Triggers

### 4.1 update_updated_at

Trigger function to automatically update the updated_at timestamp when a record is modified.

```sql
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

Applied to:
- users
- user_settings
- system_prompts
- conversations

### 4.2 generate_conversation_title

Function to automatically generate a title for a conversation if one is not provided.

```sql
CREATE OR REPLACE FUNCTION generate_conversation_title()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.title IS NULL OR NEW.title = '' THEN
    NEW.title = 'Conversation ' || to_char(now(), 'YYYY-MM-DD HH24:MI');
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

Applied to:
- conversations (BEFORE INSERT)

## 5. Storage Buckets

### 5.1 avatars

Stores user profile pictures.

- Public access: Read only
- Max file size: 5MB
- Allowed MIME types: image/jpeg, image/png, image/gif

### 5.2 audio_recordings

Stores conversation audio recordings.

- Public access: None (authenticated access only)
- Max file size: 50MB
- Allowed MIME types: audio/mpeg, audio/wav, audio/webm

## 6. Authentication Configuration

### 6.1 Sign-up Settings

- Email confirmation required: Yes
- Password minimum length: 8 characters
- Password strength requirements: At least one uppercase, one lowercase, one number

### 6.2 OAuth Providers (Future Implementation)

- Google
- Microsoft
- GitHub

### 6.3 User Management

- Self-registration allowed: Yes
- Admin invitation required: No (for basic users)
- Password reset: Email-based