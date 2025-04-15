-- Full-Text Search Migrations for Conversations and Turns
-- This file contains SQL statements to set up tsvector columns and indexes
-- for optimized full-text search in Supabase.

-- Add tsvector column to conversations table
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- Add tsvector column to conversation_turns table
ALTER TABLE conversation_turns ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- Create GIN indexes for fast full-text search
CREATE INDEX IF NOT EXISTS idx_conversations_search_vector ON conversations USING GIN (search_vector);
CREATE INDEX IF NOT EXISTS idx_conversation_turns_search_vector ON conversation_turns USING GIN (search_vector);

-- Create function to update conversations search vector
CREATE OR REPLACE FUNCTION update_conversations_search_vector()
RETURNS TRIGGER AS $$
BEGIN
  NEW.search_vector = 
    setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(NEW.metadata->>'tags', '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(NEW.metadata->>'description', '')), 'C');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create function to update conversation_turns search vector
CREATE OR REPLACE FUNCTION update_conversation_turns_search_vector()
RETURNS TRIGGER AS $$
BEGIN
  NEW.search_vector = to_tsvector('english', COALESCE(NEW.content, ''));
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers to automatically update search vectors
DROP TRIGGER IF EXISTS trigger_conversations_search_vector ON conversations;
CREATE TRIGGER trigger_conversations_search_vector
BEFORE INSERT OR UPDATE ON conversations
FOR EACH ROW EXECUTE FUNCTION update_conversations_search_vector();

DROP TRIGGER IF EXISTS trigger_conversation_turns_search_vector ON conversation_turns;
CREATE TRIGGER trigger_conversation_turns_search_vector
BEFORE INSERT OR UPDATE ON conversation_turns
FOR EACH ROW EXECUTE FUNCTION update_conversation_turns_search_vector();

-- Update existing records to populate search vectors
UPDATE conversations SET search_vector = 
  setweight(to_tsvector('english', COALESCE(title, '')), 'A') ||
  setweight(to_tsvector('english', COALESCE(metadata->>'tags', '')), 'B') ||
  setweight(to_tsvector('english', COALESCE(metadata->>'description', '')), 'C');

UPDATE conversation_turns SET search_vector = to_tsvector('english', COALESCE(content, ''));

-- Create a function to search conversations with relevance ranking
CREATE OR REPLACE FUNCTION search_conversations(
  search_query TEXT,
  user_id UUID DEFAULT NULL,
  limit_val INTEGER DEFAULT 10,
  offset_val INTEGER DEFAULT 0,
  min_similarity FLOAT DEFAULT 0.1,
  order_by TEXT DEFAULT 'relevance',
  date_from TIMESTAMP DEFAULT NULL,
  date_to TIMESTAMP DEFAULT NULL
)
RETURNS TABLE (
  id UUID,
  title TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  user_id UUID,
  metadata JSONB,
  relevance FLOAT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    c.id,
    c.title,
    c.created_at,
    c.updated_at,
    c.user_id,
    c.metadata,
    ts_rank(c.search_vector, to_tsquery('english', search_query)) AS relevance
  FROM 
    conversations c
  WHERE 
    ts_rank(c.search_vector, to_tsquery('english', search_query)) > min_similarity
    AND (user_id IS NULL OR c.user_id = search_conversations.user_id)
    AND (date_from IS NULL OR c.created_at >= date_from)
    AND (date_to IS NULL OR c.created_at <= date_to)
  ORDER BY
    CASE WHEN order_by = 'relevance' THEN ts_rank(c.search_vector, to_tsquery('english', search_query)) END DESC,
    CASE WHEN order_by = 'created_at' THEN c.created_at END DESC,
    CASE WHEN order_by = 'updated_at' THEN c.updated_at END DESC
  LIMIT limit_val
  OFFSET offset_val;
END;
$$ LANGUAGE plpgsql;

-- Create a function to search conversation turns with relevance ranking
CREATE OR REPLACE FUNCTION search_conversation_turns(
  search_query TEXT,
  conversation_ids UUID[] DEFAULT NULL,
  user_id UUID DEFAULT NULL,
  limit_val INTEGER DEFAULT 50,
  offset_val INTEGER DEFAULT 0,
  min_similarity FLOAT DEFAULT 0.1,
  order_by TEXT DEFAULT 'relevance',
  role TEXT DEFAULT NULL,
  date_from TIMESTAMP DEFAULT NULL,
  date_to TIMESTAMP DEFAULT NULL
)
RETURNS TABLE (
  id UUID,
  conversation_id UUID,
  role TEXT,
  content TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  metadata JSONB,
  relevance FLOAT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    t.id,
    t.conversation_id,
    t.role,
    t.content,
    t.created_at,
    t.updated_at,
    t.metadata,
    ts_rank(t.search_vector, to_tsquery('english', search_query)) AS relevance
  FROM 
    conversation_turns t
  WHERE 
    ts_rank(t.search_vector, to_tsquery('english', search_query)) > min_similarity
    AND (conversation_ids IS NULL OR t.conversation_id = ANY(conversation_ids))
    AND (user_id IS NULL OR t.conversation_id IN (SELECT id FROM conversations WHERE user_id = search_conversation_turns.user_id))
    AND (role IS NULL OR t.role = role)
    AND (date_from IS NULL OR t.created_at >= date_from)
    AND (date_to IS NULL OR t.created_at <= date_to)
  ORDER BY
    CASE WHEN order_by = 'relevance' THEN ts_rank(t.search_vector, to_tsquery('english', search_query)) END DESC,
    CASE WHEN order_by = 'created_at' THEN t.created_at END DESC
  LIMIT limit_val
  OFFSET offset_val;
END;
$$ LANGUAGE plpgsql;