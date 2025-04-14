"""
UI Application Module

This module provides the Streamlit UI for the voice agent application.
"""

import os
import asyncio
import datetime
from typing import Dict, List, Optional, Any, Callable

import streamlit as st
from loguru import logger

from src.auth.models import User
from src.conversation.models import Conversation, ConversationTurn, ConversationRole
from src.admin.models import SystemPrompt, PromptCategory
from src.ui import (
    Container,
    Text,
    Button,
    IconButton,
    VoiceControls,
    ConversationView,
    ConversationList,
    SystemPromptSelector,
    VoiceSettings,
    Dialog,
    Snackbar,
    Tabs
)


# Initialize session state
def init_session_state():
    """Initialize Streamlit session state variables."""
    if "user" not in st.session_state:
        st.session_state.user = None
    
    if "current_conversation" not in st.session_state:
        st.session_state.current_conversation = None
    
    if "conversations" not in st.session_state:
        st.session_state.conversations = []
    
    if "system_prompts" not in st.session_state:
        st.session_state.system_prompts = []
    
    if "is_listening" not in st.session_state:
        st.session_state.is_listening = False
    
    if "is_processing" not in st.session_state:
        st.session_state.is_processing = False
    
    if "is_muted" not in st.session_state:
        st.session_state.is_muted = False
    
    if "error_message" not in st.session_state:
        st.session_state.error_message = None
    
    if "success_message" not in st.session_state:
        st.session_state.success_message = None
    
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = 0
    
    if "voice_enabled" not in st.session_state:
        st.session_state.voice_enabled = True
    
    if "auto_play_responses" not in st.session_state:
        st.session_state.auto_play_responses = True
    
    if "voice_volume" not in st.session_state:
        st.session_state.voice_volume = 100


# Authentication UI
def render_auth_ui(auth_service):
    """Render the authentication UI."""
    st.title("Voice Conversation Agent")
    
    # Login/Register tabs
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                with st.spinner("Logging in..."):
                    result = asyncio.run(auth_service.login(email, password))
                    
                    if result.success:
                        st.session_state.user = result.user
                        st.session_state.success_message = "Login successful!"
                        st.rerun()
                    else:
                        st.error(f"Login failed: {result.error}")
    
    with tab2:
        with st.form("register_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            full_name = st.text_input("Full Name")
            submit = st.form_submit_button("Register")
            
            if submit:
                if password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    with st.spinner("Registering..."):
                        result = asyncio.run(auth_service.register(email, password, full_name))
                        
                        if result.success:
                            st.session_state.user = result.user
                            st.session_state.success_message = "Registration successful!"
                            st.rerun()
                        else:
                            st.error(f"Registration failed: {result.error}")


# Main UI
def render_main_ui(
    auth_service,
    conversation_service,
    admin_service,
    storage_service,
    create_voice_service
):
    """Render the main application UI."""
    # Sidebar
    with st.sidebar:
        st.title("Voice Agent")
        
        # User info
        user = st.session_state.user
        st.write(f"Welcome, {user.full_name}")
        
        # Navigation
        st.subheader("Navigation")
        tabs = ["Conversations", "Settings"]
        
        if user.role == "admin":
            tabs.append("Admin")
        
        for i, tab in enumerate(tabs):
            if st.button(tab, key=f"tab_{i}"):
                st.session_state.active_tab = i
                st.rerun()
        
        # Logout button
        if st.button("Logout"):
            asyncio.run(auth_service.logout())
            st.session_state.user = None
            st.rerun()
    
    # Main content
    if st.session_state.active_tab == 0:
        render_conversations_tab(conversation_service, create_voice_service)
    elif st.session_state.active_tab == 1:
        render_settings_tab()
    elif st.session_state.active_tab == 2 and st.session_state.user.role == "admin":
        render_admin_tab(admin_service)


# Conversations tab
def render_conversations_tab(conversation_service, create_voice_service):
    """Render the conversations tab."""
    st.title("Conversations")
    
    # Load conversations if not loaded
    if not st.session_state.conversations:
        with st.spinner("Loading conversations..."):
            result = asyncio.run(conversation_service.list_conversations(
                user_id=st.session_state.user.id
            ))
            st.session_state.conversations = result.items
    
    # Create two columns: conversation list and conversation view
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("Your Conversations")
        
        # New conversation button
        if st.button("New Conversation"):
            with st.spinner("Creating new conversation..."):
                new_conversation = asyncio.run(conversation_service.create_conversation(
                    user_id=st.session_state.user.id,
                    title=f"Conversation {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
                ))
                
                if new_conversation:
                    st.session_state.current_conversation = new_conversation
                    st.session_state.conversations.insert(0, new_conversation)
                    
                    # Create voice service for this conversation
                    create_voice_service(
                        room_name=new_conversation.id,
                        participant_name=st.session_state.user.id
                    )
                    
                    st.rerun()
                else:
                    st.error("Failed to create new conversation")
        
        # Conversation list
        for conversation in st.session_state.conversations:
            if st.button(
                conversation.title,
                key=f"conv_{conversation.id}",
                use_container_width=True
            ):
                with st.spinner("Loading conversation..."):
                    loaded_conversation = asyncio.run(conversation_service.get_conversation(
                        conversation_id=conversation.id,
                        user_id=st.session_state.user.id
                    ))
                    
                    if loaded_conversation:
                        st.session_state.current_conversation = loaded_conversation
                        
                        # Create voice service for this conversation
                        create_voice_service(
                            room_name=loaded_conversation.id,
                            participant_name=st.session_state.user.id
                        )
                        
                        st.rerun()
                    else:
                        st.error("Failed to load conversation")
    
    with col2:
        if st.session_state.current_conversation:
            render_conversation_view(conversation_service)
        else:
            st.info("Select a conversation or create a new one to start chatting")


# Conversation view
def render_conversation_view(conversation_service):
    """Render the current conversation view."""
    conversation = st.session_state.current_conversation
    
    # Conversation header
    st.subheader(conversation.title)
    
    # Conversation turns
    for turn in conversation.turns:
        with st.chat_message("user" if turn.role == ConversationRole.USER else "assistant"):
            st.write(turn.content)
            
            if turn.audio_url:
                st.audio(turn.audio_url)
    
    # Voice controls
    voice_controls_container = st.container()
    
    with voice_controls_container:
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col2:
            # Mute button
            mute_label = "Unmute" if st.session_state.is_muted else "Mute"
            if st.button(mute_label, key="mute_button"):
                st.session_state.is_muted = not st.session_state.is_muted
                st.rerun()
            
            # Voice button
            button_label = "Stop Listening" if st.session_state.is_listening else "Start Listening"
            if st.button(button_label, key="voice_button", use_container_width=True):
                if st.session_state.is_listening:
                    # Stop listening
                    st.session_state.is_listening = False
                    st.session_state.is_processing = True
                    
                    # Process audio (in a real app, this would be handled by the voice service)
                    # For now, we'll simulate it
                    with st.spinner("Processing audio..."):
                        # Simulate processing delay
                        import time
                        time.sleep(2)
                        
                        # Add user turn
                        asyncio.run(conversation_service.add_turn(
                            conversation_id=conversation.id,
                            role=ConversationRole.USER,
                            content="This is a simulated user message from voice input."
                        ))
                        
                        # Add assistant turn
                        asyncio.run(conversation_service.add_turn(
                            conversation_id=conversation.id,
                            role=ConversationRole.ASSISTANT,
                            content="This is a simulated assistant response."
                        ))
                        
                        # Reload conversation
                        loaded_conversation = asyncio.run(conversation_service.get_conversation(
                            conversation_id=conversation.id,
                            user_id=st.session_state.user.id
                        ))
                        
                        if loaded_conversation:
                            st.session_state.current_conversation = loaded_conversation
                        
                        st.session_state.is_processing = False
                        st.rerun()
                else:
                    # Start listening
                    st.session_state.is_listening = True
                    st.rerun()
            
            # Status text
            if st.session_state.is_muted:
                st.caption("Microphone is muted")
            elif st.session_state.is_listening:
                st.caption("Listening...")
            elif st.session_state.is_processing:
                st.caption("Processing...")
            else:
                st.caption("Click to speak")
    
    # Text input as an alternative to voice
    with st.form("message_form", clear_on_submit=True):
        user_input = st.text_input("Type a message", key="user_input")
        submitted = st.form_submit_button("Send")
        
        if submitted and user_input:
            with st.spinner("Sending message..."):
                # Add user turn
                asyncio.run(conversation_service.add_turn(
                    conversation_id=conversation.id,
                    role=ConversationRole.USER,
                    content=user_input
                ))
                
                # Add assistant turn (in a real app, this would call an LLM)
                asyncio.run(conversation_service.add_turn(
                    conversation_id=conversation.id,
                    role=ConversationRole.ASSISTANT,
                    content=f"This is a simulated response to: {user_input}"
                ))
                
                # Reload conversation
                loaded_conversation = asyncio.run(conversation_service.get_conversation(
                    conversation_id=conversation.id,
                    user_id=st.session_state.user.id
                ))
                
                if loaded_conversation:
                    st.session_state.current_conversation = loaded_conversation
                    st.rerun()


# Settings tab
def render_settings_tab():
    """Render the settings tab."""
    st.title("Settings")
    
    # Voice settings
    st.subheader("Voice Settings")
    
    voice_enabled = st.toggle(
        "Enable Voice",
        value=st.session_state.voice_enabled,
        key="voice_enabled_toggle"
    )
    
    if voice_enabled != st.session_state.voice_enabled:
        st.session_state.voice_enabled = voice_enabled
    
    auto_play = st.toggle(
        "Auto-play Responses",
        value=st.session_state.auto_play_responses,
        key="auto_play_toggle"
    )
    
    if auto_play != st.session_state.auto_play_responses:
        st.session_state.auto_play_responses = auto_play
    
    voice_volume = st.slider(
        "Voice Volume",
        min_value=0,
        max_value=100,
        value=st.session_state.voice_volume,
        key="voice_volume_slider"
    )
    
    if voice_volume != st.session_state.voice_volume:
        st.session_state.voice_volume = voice_volume
    
    # Account settings
    st.subheader("Account Settings")
    
    with st.form("update_profile_form"):
        full_name = st.text_input(
            "Full Name",
            value=st.session_state.user.full_name
        )
        
        submit = st.form_submit_button("Update Profile")
        
        if submit:
            st.info("Profile update functionality would be implemented here")


# Admin tab
def render_admin_tab(admin_service):
    """Render the admin tab."""
    st.title("Admin Dashboard")
    
    # Admin tabs
    tab1, tab2 = st.tabs(["System Prompts", "User Management"])
    
    with tab1:
        render_system_prompts_tab(admin_service)
    
    with tab2:
        render_user_management_tab(admin_service)


# System prompts tab
def render_system_prompts_tab(admin_service):
    """Render the system prompts management tab."""
    st.subheader("System Prompts")
    
    # Load prompts if not loaded
    if not st.session_state.system_prompts:
        with st.spinner("Loading system prompts..."):
            result = asyncio.run(admin_service.list_system_prompts())
            st.session_state.system_prompts = result.items
    
    # Create new prompt
    with st.expander("Create New Prompt"):
        with st.form("create_prompt_form"):
            name = st.text_input("Name")
            content = st.text_area("Content")
            
            category_options = [c.value for c in PromptCategory]
            category = st.selectbox("Category", category_options)
            
            is_default = st.checkbox("Set as Default for Category")
            
            submit = st.form_submit_button("Create Prompt")
            
            if submit:
                with st.spinner("Creating prompt..."):
                    new_prompt = asyncio.run(admin_service.create_system_prompt(
                        admin_id=st.session_state.user.id,
                        name=name,
                        content=content,
                        category=PromptCategory(category),
                        is_default=is_default
                    ))
                    
                    if new_prompt:
                        st.session_state.system_prompts.append(new_prompt)
                        st.success("Prompt created successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to create prompt")
    
    # List prompts
    for prompt in st.session_state.system_prompts:
        with st.expander(f"{prompt.name} ({prompt.category.value})"):
            st.write(prompt.content)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if not prompt.is_default and st.button(
                    "Set as Default",
                    key=f"default_{prompt.id}"
                ):
                    with st.spinner("Setting as default..."):
                        success = asyncio.run(admin_service.set_default_prompt(prompt.id))
                        
                        if success:
                            # Update prompts
                            for p in st.session_state.system_prompts:
                                if p.category == prompt.category:
                                    p.is_default = (p.id == prompt.id)
                            
                            st.success("Prompt set as default")
                            st.rerun()
                        else:
                            st.error("Failed to set prompt as default")
            
            with col2:
                if st.button("Delete", key=f"delete_{prompt.id}"):
                    with st.spinner("Deleting prompt..."):
                        success = asyncio.run(admin_service.delete_system_prompt(prompt.id))
                        
                        if success:
                            st.session_state.system_prompts = [
                                p for p in st.session_state.system_prompts if p.id != prompt.id
                            ]
                            st.success("Prompt deleted successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to delete prompt")


# User management tab
def render_user_management_tab(admin_service):
    """Render the user management tab."""
    st.subheader("User Management")
    
    # List users
    with st.spinner("Loading users..."):
        result = asyncio.run(admin_service.list_users())
        users = result.items
    
    for user in users:
        with st.expander(f"{user.full_name} ({user.email})"):
            st.write(f"Role: {user.role}")
            st.write(f"Status: {user.status.value}")
            st.write(f"Conversations: {user.conversation_count}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if user.role != "admin" and st.button(
                    "Make Admin",
                    key=f"admin_{user.id}"
                ):
                    with st.spinner("Updating role..."):
                        success = asyncio.run(admin_service.update_user_role(
                            user_id=user.id,
                            role="admin"
                        ))
                        
                        if success:
                            st.success("User role updated")
                            st.rerun()
                        else:
                            st.error("Failed to update user role")
            
            with col2:
                if user.status.value == "active":
                    if st.button("Disable", key=f"disable_{user.id}"):
                        with st.spinner("Disabling user..."):
                            from src.admin.models import UserStatus
                            success = asyncio.run(admin_service.update_user_status(
                                user_id=user.id,
                                status=UserStatus.DISABLED
                            ))
                            
                            if success:
                                st.success("User disabled")
                                st.rerun()
                            else:
                                st.error("Failed to disable user")
                else:
                    if st.button("Enable", key=f"enable_{user.id}"):
                        with st.spinner("Enabling user..."):
                            from src.admin.models import UserStatus
                            success = asyncio.run(admin_service.update_user_status(
                                user_id=user.id,
                                status=UserStatus.ACTIVE
                            ))
                            
                            if success:
                                st.success("User enabled")
                                st.rerun()
                            else:
                                st.error("Failed to enable user")


# Main UI function
def run_ui(
    auth_service,
    conversation_service,
    admin_service,
    storage_service,
    create_voice_service
):
    """
    Run the Streamlit UI.
    
    Args:
        auth_service: Authentication service
        conversation_service: Conversation service
        admin_service: Admin service
        storage_service: Storage service
        create_voice_service: Function to create a voice service
    """
    # Initialize session state
    init_session_state()
    
    # Display success/error messages
    if st.session_state.success_message:
        st.success(st.session_state.success_message)
        st.session_state.success_message = None
    
    if st.session_state.error_message:
        st.error(st.session_state.error_message)
        st.session_state.error_message = None
    
    # Render appropriate UI based on authentication state
    if st.session_state.user:
        render_main_ui(
            auth_service,
            conversation_service,
            admin_service,
            storage_service,
            create_voice_service
        )
    else:
        render_auth_ui(auth_service)