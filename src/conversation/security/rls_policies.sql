-- Row-Level Security Policies for Conversations and Turns
-- This file contains SQL statements to set up RLS policies for the conversations, 
-- conversation_turns, and system_prompts tables in Supabase.

-- Enable Row Level Security on tables
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_turns ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_prompts ENABLE ROW LEVEL SECURITY;

-- Create a function to check if a user has access to a conversation
CREATE OR REPLACE FUNCTION public.user_has_conversation_access(conversation_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
  conversation_user_id UUID;
  is_admin BOOLEAN;
BEGIN
  -- Get the user_id for the conversation
  SELECT user_id INTO conversation_user_id
  FROM conversations
  WHERE id = conversation_id;
  
  -- Check if the current user is an admin
  SELECT EXISTS (
    SELECT 1 FROM user_roles
    WHERE user_id = auth.uid() AND role = 'admin'
  ) INTO is_admin;
  
  -- Return true if the user is the owner or an admin
  RETURN (conversation_user_id = auth.uid() OR is_admin);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create a function to check if a user has access to a system prompt
CREATE OR REPLACE FUNCTION public.user_has_system_prompt_access(prompt_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
  prompt_user_id UUID;
  is_public BOOLEAN;
  is_admin BOOLEAN;
BEGIN
  -- Get the user_id and is_public flag for the system prompt
  SELECT user_id, is_public INTO prompt_user_id, is_public
  FROM system_prompts
  WHERE id = prompt_id;
  
  -- Check if the current user is an admin
  SELECT EXISTS (
    SELECT 1 FROM user_roles
    WHERE user_id = auth.uid() AND role = 'admin'
  ) INTO is_admin;
  
  -- Return true if the prompt is public, the user is the owner, or an admin
  RETURN (is_public OR prompt_user_id = auth.uid() OR is_admin);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Conversations Policies
-- 1. Users can view their own conversations
CREATE POLICY "Users can view their own conversations"
  ON conversations
  FOR SELECT
  USING (user_id = auth.uid());

-- 2. Admins can view all conversations
CREATE POLICY "Admins can view all conversations"
  ON conversations
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM user_roles
      WHERE user_id = auth.uid() AND role = 'admin'
    )
  );

-- 3. Users can insert their own conversations
CREATE POLICY "Users can insert their own conversations"
  ON conversations
  FOR INSERT
  WITH CHECK (user_id = auth.uid());

-- 4. Users can update their own conversations
CREATE POLICY "Users can update their own conversations"
  ON conversations
  FOR UPDATE
  USING (user_id = auth.uid());

-- 5. Users can delete their own conversations
CREATE POLICY "Users can delete their own conversations"
  ON conversations
  FOR DELETE
  USING (user_id = auth.uid());

-- 6. Admins can update all conversations
CREATE POLICY "Admins can update all conversations"
  ON conversations
  FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM user_roles
      WHERE user_id = auth.uid() AND role = 'admin'
    )
  );

-- 7. Admins can delete all conversations
CREATE POLICY "Admins can delete all conversations"
  ON conversations
  FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM user_roles
      WHERE user_id = auth.uid() AND role = 'admin'
    )
  );

-- Conversation Turns Policies
-- 1. Users can view turns for their own conversations
CREATE POLICY "Users can view turns for their own conversations"
  ON conversation_turns
  FOR SELECT
  USING (user_has_conversation_access(conversation_id));

-- 2. Users can insert turns for their own conversations
CREATE POLICY "Users can insert turns for their own conversations"
  ON conversation_turns
  FOR INSERT
  WITH CHECK (user_has_conversation_access(conversation_id));

-- 3. Users can update turns for their own conversations
CREATE POLICY "Users can update turns for their own conversations"
  ON conversation_turns
  FOR UPDATE
  USING (user_has_conversation_access(conversation_id));

-- 4. Users can delete turns for their own conversations
CREATE POLICY "Users can delete turns for their own conversations"
  ON conversation_turns
  FOR DELETE
  USING (user_has_conversation_access(conversation_id));

-- System Prompts Policies
-- 1. Users can view public system prompts and their own prompts
CREATE POLICY "Users can view public system prompts and their own prompts"
  ON system_prompts
  FOR SELECT
  USING (is_public OR user_id = auth.uid());

-- 2. Admins can view all system prompts
CREATE POLICY "Admins can view all system prompts"
  ON system_prompts
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM user_roles
      WHERE user_id = auth.uid() AND role = 'admin'
    )
  );

-- 3. Users can insert their own system prompts
CREATE POLICY "Users can insert their own system prompts"
  ON system_prompts
  FOR INSERT
  WITH CHECK (user_id = auth.uid());

-- 4. Users can update their own system prompts
CREATE POLICY "Users can update their own system prompts"
  ON system_prompts
  FOR UPDATE
  USING (user_id = auth.uid());

-- 5. Users can delete their own system prompts
CREATE POLICY "Users can delete their own system prompts"
  ON system_prompts
  FOR DELETE
  USING (user_id = auth.uid());

-- 6. Admins can update all system prompts
CREATE POLICY "Admins can update all system prompts"
  ON system_prompts
  FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM user_roles
      WHERE user_id = auth.uid() AND role = 'admin'
    )
  );

-- 7. Admins can delete all system prompts
CREATE POLICY "Admins can delete all system prompts"
  ON system_prompts
  FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM user_roles
      WHERE user_id = auth.uid() AND role = 'admin'
    )
  );

-- Create indexes to improve performance of RLS policies
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversation_turns_conversation_id ON conversation_turns(conversation_id);
CREATE INDEX IF NOT EXISTS idx_system_prompts_user_id ON system_prompts(user_id);
CREATE INDEX IF NOT EXISTS idx_system_prompts_is_public ON system_prompts(is_public);
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id_role ON user_roles(user_id, role);