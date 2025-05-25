"""Session management for conversational image generation."""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import threading

logger = logging.getLogger(__name__)


@dataclass
class ImageGenerationCall:
    """Represents a single image generation within conversation."""
    id: str  # OpenAI generation call ID
    prompt: str
    revised_prompt: str
    image_path: str
    generation_params: Dict[str, Any]
    created_at: datetime
    image_data: Optional[str] = None  # Base64 image data if available


@dataclass
class ImageSession:
    """Complete session state for conversational image generation."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    model: str = "gpt-4o"
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    session_name: Optional[str] = None
    description: str = ""
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    generated_images: List[ImageGenerationCall] = field(default_factory=list)
    active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "model": self.model,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "session_name": self.session_name,
            "description": self.description,
            "total_generations": len(self.generated_images),
            "active": self.active
        }


class SessionManager:
    """Manages all active image generation sessions."""
    
    def __init__(self, max_sessions: int = 100, session_timeout_hours: int = 1):
        """Initialize session manager.
        
        Args:
            max_sessions: Maximum number of concurrent sessions
            session_timeout_hours: Hours before inactive sessions expire
        """
        self._sessions: Dict[str, ImageSession] = {}
        self._max_sessions = max_sessions
        self._session_timeout = timedelta(hours=session_timeout_hours)
        self._lock = threading.RLock()  # Thread-safe operations
        
        logger.info(f"SessionManager initialized with max_sessions={max_sessions}, timeout={session_timeout_hours}h")
    
    def create_session(
        self, 
        description: str, 
        model: str = "gpt-4o", 
        session_name: Optional[str] = None
    ) -> ImageSession:
        """Create new session with initial context.
        
        Args:
            description: Initial description/context for the session
            model: OpenAI model to use (gpt-4o, gpt-4.1, gpt-4o-mini)
            session_name: Optional human-readable name
            
        Returns:
            New ImageSession instance
            
        Raises:
            ValueError: If max sessions reached or invalid model
        """
        with self._lock:
            # Clean up expired sessions first
            self._cleanup_expired_sessions()
            
            # Check session limit
            if len(self._sessions) >= self._max_sessions:
                raise ValueError(f"Maximum sessions ({self._max_sessions}) reached. Close existing sessions first.")
            
            # Validate model
            supported_models = ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini", "o3"]
            if model not in supported_models:
                raise ValueError(f"Unsupported model '{model}'. Supported: {supported_models}")
            
            # Create session
            session = ImageSession(
                model=model,
                session_name=session_name,
                description=description
            )
            
            self._sessions[session.session_id] = session
            
            # Add initial system context to conversation
            self.add_conversation_turn(
                session.session_id,
                "system",
                [{"type": "input_text", "text": f"Session Context: {description}"}]
            )
            
            logger.info(f"Created session {session.session_id} with model {model}")
            return session
    
    def get_session(self, session_id: str) -> Optional[ImageSession]:
        """Retrieve session by ID.
        
        Args:
            session_id: UUID of the session
            
        Returns:
            ImageSession if found, None otherwise
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session and session.active:
                return session
            return None
    
    def update_activity(self, session_id: str) -> None:
        """Update last activity timestamp.
        
        Args:
            session_id: UUID of the session
        """
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id].last_activity = datetime.now()
                logger.debug(f"Updated activity for session {session_id}")
    
    def add_conversation_turn(
        self, 
        session_id: str, 
        role: str, 
        content: List[Dict[str, Any]]
    ) -> None:
        """Add conversation turn to session history.
        
        Args:
            session_id: UUID of the session
            role: Role of the speaker (user, assistant, system)
            content: Content items for this turn
        """
        with self._lock:
            if session_id in self._sessions:
                session = self._sessions[session_id]
                
                turn = {
                    "role": role,
                    "content": content,
                    "timestamp": datetime.now().isoformat()
                }
                
                session.conversation_history.append(turn)
                session.last_activity = datetime.now()
                
                # Trim old history if too long
                max_history = 50
                if len(session.conversation_history) > max_history:
                    # Keep system message and recent history
                    system_turns = [t for t in session.conversation_history if t["role"] == "system"]
                    recent_turns = session.conversation_history[-(max_history-len(system_turns)):]
                    session.conversation_history = system_turns + recent_turns
                    logger.debug(f"Trimmed conversation history for session {session_id}")
                
                logger.debug(f"Added {role} turn to session {session_id}")
    
    def add_generated_image(
        self, 
        session_id: str, 
        generation_call: ImageGenerationCall
    ) -> None:
        """Record new image generation in session.
        
        Args:
            session_id: UUID of the session
            generation_call: Image generation result
        """
        with self._lock:
            if session_id in self._sessions:
                session = self._sessions[session_id]
                session.generated_images.append(generation_call)
                session.last_activity = datetime.now()
                
                logger.info(f"Added image generation {generation_call.id} to session {session_id}")
    
    def close_session(self, session_id: str) -> bool:
        """Close and cleanup session.
        
        Args:
            session_id: UUID of the session
            
        Returns:
            True if session was closed, False if not found
        """
        with self._lock:
            if session_id in self._sessions:
                session = self._sessions[session_id]
                session.active = False
                del self._sessions[session_id]
                
                logger.info(f"Closed session {session_id} with {len(session.generated_images)} images")
                return True
            return False
    
    def list_active_sessions(self) -> List[ImageSession]:
        """Get all active sessions.
        
        Returns:
            List of active ImageSession objects
        """
        with self._lock:
            # Clean up expired sessions first
            self._cleanup_expired_sessions()
            
            return list(self._sessions.values())
    
    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session status summary.
        
        Args:
            session_id: UUID of the session
            
        Returns:
            Session summary dictionary or None if not found
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        # Get recent image paths
        recent_images = [img.image_path for img in session.generated_images[-5:]]
        
        # Create conversation summary
        total_turns = len(session.conversation_history)
        user_turns = len([t for t in session.conversation_history if t["role"] == "user"])
        
        conversation_summary = f"{user_turns} user interactions, {len(session.generated_images)} images generated"
        
        return {
            "session_id": session.session_id,
            "active": session.active,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "model": session.model,
            "session_name": session.session_name,
            "total_generations": len(session.generated_images),
            "recent_images": recent_images,
            "conversation_summary": conversation_summary,
            "total_conversation_turns": total_turns
        }
    
    def _cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session in self._sessions.items():
            if current_time - session.last_activity > self._session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.close_session(session_id)
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        
        return len(expired_sessions)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics.
        
        Returns:
            Statistics dictionary
        """
        with self._lock:
            sessions = list(self._sessions.values())
            total_images = sum(len(s.generated_images) for s in sessions)
            
            return {
                "active_sessions": len(sessions),
                "max_sessions": self._max_sessions,
                "total_images_generated": total_images,
                "session_timeout_hours": self._session_timeout.total_seconds() / 3600,
                "models_in_use": list(set(s.model for s in sessions))
            }