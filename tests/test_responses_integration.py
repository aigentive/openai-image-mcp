"""Integration tests for the new Responses API implementation."""

import pytest
import os
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.openai_image_mcp.session_manager import SessionManager, ImageSession, ImageGenerationCall
from src.openai_image_mcp.responses_client import ResponsesAPIClient
from src.openai_image_mcp.conversation_builder import ConversationBuilder
from src.openai_image_mcp.image_processor import ImageProcessor
from src.openai_image_mcp.file_organizer import FileOrganizer


class TestResponsesIntegration:
    """Integration tests for the complete Responses API implementation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock components
        self.mock_responses_client = Mock(spec=ResponsesAPIClient)
        self.mock_file_organizer = Mock(spec=FileOrganizer)
        
        # Real components for testing
        self.session_manager = SessionManager(max_sessions=10, session_timeout_hours=1)
        self.conversation_builder = ConversationBuilder()
        
        # Set up mock returns
        self.mock_file_organizer.get_save_path.return_value = os.path.join(self.temp_dir, "test_image.png")
        self.mock_file_organizer.save_image_metadata.return_value = os.path.join(self.temp_dir, "test_image_metadata.json")
        
        # Mock successful API response
        mock_generation_call = ImageGenerationCall(
            id="ig_test_123",
            prompt="test prompt",
            revised_prompt="enhanced test prompt",
            image_path=os.path.join(self.temp_dir, "test_image.png"),
            generation_params={"quality": "high", "size": "1024x1024"},
            created_at=datetime.now(),
            image_data="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGJ"
        )
        
        self.mock_responses_client.generate_with_conversation.return_value = {
            "success": True,
            "generation_calls": [mock_generation_call],
            "conversation_length": 2
        }
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_session_creation_and_management(self):
        """Test session creation and basic management."""
        # Create session
        session = self.session_manager.create_session(
            description="Test session for image generation",
            model="gpt-4o",
            session_name="Test Session"
        )
        
        assert session is not None
        assert session.model == "gpt-4o"
        assert session.session_name == "Test Session"
        assert session.description == "Test session for image generation"
        assert len(session.conversation_history) == 1  # Initial system message
        
        # Test session retrieval
        retrieved_session = self.session_manager.get_session(session.session_id)
        assert retrieved_session is not None
        assert retrieved_session.session_id == session.session_id
        
        # Test session listing
        sessions = self.session_manager.list_active_sessions()
        assert len(sessions) == 1
        assert sessions[0].session_id == session.session_id
        
        # Test session summary
        summary = self.session_manager.get_session_summary(session.session_id)
        assert summary is not None
        assert summary["session_id"] == session.session_id
        assert summary["active"] == True
        
        # Test session closure
        success = self.session_manager.close_session(session.session_id)
        assert success == True
        
        # Verify session is closed
        closed_session = self.session_manager.get_session(session.session_id)
        assert closed_session is None
    
    def test_conversation_building(self):
        """Test conversation context building."""
        # Test user input building
        user_input = self.conversation_builder.build_user_input_from_params(
            prompt="Generate a cat image",
            reference_image_path=None,
            mask_image_path=None
        )
        
        assert len(user_input) == 1
        assert user_input[0]["type"] == "input_text"
        assert user_input[0]["text"] == "Generate a cat image"
        
        # Test tools specification building
        tools = self.conversation_builder.build_tools_specification(
            quality="high",
            size="1024x1024",
            background="transparent"
        )
        
        assert len(tools) == 1
        assert tools[0]["type"] == "image_generation"
        assert tools[0]["quality"] == "high"
        assert tools[0]["size"] == "1024x1024"
        assert tools[0]["background"] == "transparent"
        
        # Test assistant response formatting
        mock_generation = Mock()
        mock_generation.id = "ig_123"
        mock_generation.image_path = "/test/path.png"
        mock_generation.revised_prompt = "A beautiful cat"
        
        assistant_content = self.conversation_builder.format_assistant_response([mock_generation])
        
        assert len(assistant_content) == 1
        assert assistant_content[0]["type"] == "image_generation_call"
        assert assistant_content[0]["id"] == "ig_123"
        assert assistant_content[0]["status"] == "completed"
    
    def test_image_processor_integration(self):
        """Test image processor with file organizer integration."""
        image_processor = ImageProcessor(
            file_organizer=self.mock_file_organizer,
            responses_client=self.mock_responses_client
        )
        
        # Create test session
        session = self.session_manager.create_session(
            description="Test session",
            model="gpt-4o"
        )
        
        # Create test generation call
        generation_call = ImageGenerationCall(
            id="ig_test_456",
            prompt="test prompt",
            revised_prompt="enhanced test prompt",
            image_path="",  # Will be set by processor
            generation_params={"quality": "high"},
            created_at=datetime.now(),
            image_data="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGJ"
        )
        
        # Process generation result
        processed_call = image_processor.process_generation_result(
            generation_call, session, use_case="general"
        )
        
        assert processed_call.image_path == os.path.join(self.temp_dir, "test_image.png")
        
        # Verify file organizer was called correctly
        self.mock_file_organizer.get_save_path.assert_called_once()
        self.mock_file_organizer.save_image_metadata.assert_called_once()
        
        # Check metadata call arguments
        metadata_call_args = self.mock_file_organizer.save_image_metadata.call_args[0]
        assert metadata_call_args[0] == processed_call.image_path  # Image path
        
        metadata = self.mock_file_organizer.save_image_metadata.call_args[0][1]
        assert metadata["session_id"] == session.session_id
        assert metadata["generation_call_id"] == "ig_test_456"
        assert metadata["original_prompt"] == "test prompt"
        assert metadata["revised_prompt"] == "enhanced test prompt"
    
    def test_full_generation_workflow(self):
        """Test complete generation workflow with all components."""
        # Create session
        session = self.session_manager.create_session(
            description="Full workflow test",
            model="gpt-4o"
        )
        
        # Build user input
        user_input = self.conversation_builder.build_user_input_from_params(
            prompt="Generate a beautiful landscape"
        )
        
        # Add conversation turn
        self.session_manager.add_conversation_turn(session.session_id, "user", user_input)
        
        # Verify conversation was added
        updated_session = self.session_manager.get_session(session.session_id)
        assert len(updated_session.conversation_history) == 2  # System + user
        
        # Mock API call
        with patch.object(self.mock_responses_client, 'generate_with_conversation') as mock_api:
            mock_generation = ImageGenerationCall(
                id="ig_workflow_789",
                prompt="Generate a beautiful landscape",
                revised_prompt="A stunning natural landscape with mountains and rivers",
                image_path="",
                generation_params={"quality": "auto", "size": "auto"},
                created_at=datetime.now(),
                image_data="base64imagedata"
            )
            
            mock_api.return_value = {
                "success": True,
                "generation_calls": [mock_generation],
                "conversation_length": 2
            }
            
            # Process with image processor
            image_processor = ImageProcessor(
                file_organizer=self.mock_file_organizer,
                responses_client=self.mock_responses_client
            )
            
            processed_call = image_processor.process_generation_result(
                mock_generation, updated_session, use_case="general"
            )
            
            # Add to session
            self.session_manager.add_generated_image(session.session_id, processed_call)
            
            # Add assistant response
            assistant_content = self.conversation_builder.format_assistant_response([processed_call])
            self.session_manager.add_conversation_turn(session.session_id, "assistant", assistant_content)
        
        # Verify final session state
        final_session = self.session_manager.get_session(session.session_id)
        assert len(final_session.conversation_history) == 3  # System + user + assistant
        assert len(final_session.generated_images) == 1
        assert final_session.generated_images[0].id == "ig_workflow_789"
    
    def test_conversation_context_building_with_history(self):
        """Test conversation context building with existing history."""
        # Create session with some history
        session = self.session_manager.create_session(
            description="Context building test",
            model="gpt-4o"
        )
        
        # Add multiple conversation turns
        user_input1 = [{"type": "input_text", "text": "Generate a cat"}]
        self.session_manager.add_conversation_turn(session.session_id, "user", user_input1)
        
        assistant_content1 = [{
            "type": "image_generation_call",
            "id": "ig_cat_123",
            "status": "completed",
            "image_path": "/test/cat.png"
        }]
        self.session_manager.add_conversation_turn(session.session_id, "assistant", assistant_content1)
        
        user_input2 = [{"type": "input_text", "text": "Make it orange"}]
        self.session_manager.add_conversation_turn(session.session_id, "user", user_input2)
        
        # Build conversation context
        updated_session = self.session_manager.get_session(session.session_id)
        context = self.mock_responses_client.build_conversation_context(updated_session)
        
        # Note: The actual implementation may vary, this tests the structure
        # The real implementation would be tested with the actual ResponsesAPIClient
        assert updated_session is not None
        assert len(updated_session.conversation_history) == 4  # System + user + assistant + user
    
    def test_error_handling(self):
        """Test error handling throughout the system."""
        # Test invalid session ID
        invalid_session = self.session_manager.get_session("invalid-uuid")
        assert invalid_session is None
        
        # Test session limit
        manager = SessionManager(max_sessions=1, session_timeout_hours=1)
        
        # Create first session
        session1 = manager.create_session("First session", "gpt-4o")
        assert session1 is not None
        
        # Try to create second session (should fail)
        with pytest.raises(ValueError, match="Maximum sessions"):
            manager.create_session("Second session", "gpt-4o")
        
        # Test invalid model with fresh manager
        model_manager = SessionManager(max_sessions=10, session_timeout_hours=1)
        with pytest.raises(ValueError, match="Unsupported model"):
            model_manager.create_session("Invalid model test", "invalid-model")
    
    def test_conversation_history_trimming(self):
        """Test conversation history trimming functionality."""
        session = self.session_manager.create_session(
            description="Trimming test",
            model="gpt-4o"
        )
        
        # Add many conversation turns
        for i in range(60):  # More than the limit
            user_input = [{"type": "input_text", "text": f"Message {i}"}]
            self.session_manager.add_conversation_turn(session.session_id, "user", user_input)
        
        updated_session = self.session_manager.get_session(session.session_id)
        
        # Should be trimmed to max_history (50)
        assert len(updated_session.conversation_history) <= 50
        
        # Should still have system message
        system_messages = [t for t in updated_session.conversation_history if t["role"] == "system"]
        assert len(system_messages) >= 1


class TestMCPToolsIntegration:
    """Test MCP tools with mocked dependencies."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('src.openai_image_mcp.server.get_session_manager')
    def test_create_image_session_tool(self, mock_get_manager):
        """Test create_image_session MCP tool."""
        from src.openai_image_mcp.server import create_image_session
        
        # Mock session manager
        mock_manager = Mock()
        mock_session = Mock()
        mock_session.session_id = "test-uuid-123"
        mock_session.model = "gpt-4o"
        mock_session.created_at = datetime.now()
        mock_session.session_name = "Test Session"
        
        mock_manager.create_session.return_value = mock_session
        mock_get_manager.return_value = mock_manager
        
        # Call the tool
        result = create_image_session(
            description="Test session creation",
            model="gpt-4o",
            session_name="Test Session"
        )
        
        # Verify result
        assert result["success"] == True
        assert result["session_id"] == "test-uuid-123"
        assert result["model"] == "gpt-4o"
        assert result["session_name"] == "Test Session"
        assert result["description"] == "Test session creation"
        
        # Verify manager was called correctly
        mock_manager.create_session.assert_called_once_with(
            description="Test session creation",
            model="gpt-4o",
            session_name="Test Session"
        )
    
    @patch('src.openai_image_mcp.server.get_session_manager')
    def test_list_active_sessions_tool(self, mock_get_manager):
        """Test list_active_sessions MCP tool."""
        from src.openai_image_mcp.server import list_active_sessions
        
        # Mock session manager
        mock_manager = Mock()
        mock_sessions = []
        
        for i in range(3):
            mock_session = Mock()
            mock_session.session_id = f"session-{i}"
            mock_session.session_name = f"Session {i}"
            mock_session.description = f"Description {i}"
            mock_session.model = "gpt-4o"
            mock_session.created_at = datetime.now()
            mock_session.last_activity = datetime.now()
            mock_session.generated_images = []
            mock_sessions.append(mock_session)
        
        mock_manager.list_active_sessions.return_value = mock_sessions
        mock_get_manager.return_value = mock_manager
        
        # Call the tool
        result = list_active_sessions()
        
        # Verify result
        assert result["success"] == True
        assert result["total_active"] == 3
        assert len(result["sessions"]) == 3
        
        for i, session_info in enumerate(result["sessions"]):
            assert session_info["session_id"] == f"session-{i}"
            assert session_info["session_name"] == f"Session {i}"
            assert session_info["total_generations"] == 0


class TestPromoteImageToSession:
    """Test cases for promoting one-shot images to sessions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        import tempfile
        
        # Create test directory
        self.test_dir = tempfile.mkdtemp()
        
        # Create mock image and metadata files
        self.image_path = os.path.join(self.test_dir, "test_image.png")
        self.metadata_path = os.path.join(self.test_dir, "test_image_metadata.json")
        
        # Create mock image file
        with open(self.image_path, 'w') as f:
            f.write("mock image data")
        
        # Create mock metadata
        self.mock_metadata = {
            "original_prompt": "modern office space with plants",
            "revised_prompt": "A modern office space featuring lush green plants",
            "model": "gpt-4o",
            "generation_params": {
                "quality": "high",
                "size": "1024x1024"
            },
            "created_at": "2025-05-25T10:00:00"
        }
        
        with open(self.metadata_path, 'w') as f:
            json.dump(self.mock_metadata, f)
    
    def teardown_method(self):
        """Clean up test files."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    @patch('src.openai_image_mcp.server.get_session_manager')
    @patch('src.openai_image_mcp.server.get_conversation_builder')
    @patch('src.openai_image_mcp.server.get_file_organizer')
    def test_promote_image_success(self, mock_get_organizer, mock_get_builder, mock_get_manager):
        """Test successful image promotion to session."""
        from src.openai_image_mcp.server import promote_image_to_session
        from src.openai_image_mcp.session_manager import ImageSession
        
        # Mock session manager
        mock_manager = Mock()
        mock_session = ImageSession(
            session_id="test-session-123",
            description="Test promotion session",
            session_name="Test Session"
        )
        mock_manager.create_session.return_value = mock_session
        mock_get_manager.return_value = mock_manager
        
        # Mock conversation builder
        mock_builder = Mock()
        mock_builder.build_user_input_from_params.return_value = "mock user input"
        mock_builder.format_assistant_response.return_value = "mock assistant response"
        mock_get_builder.return_value = mock_builder
        
        # Mock file organizer
        mock_organizer = Mock()
        mock_get_organizer.return_value = mock_organizer
        
        # Test promotion
        result = promote_image_to_session(
            image_path=self.image_path,
            session_description="Refining office space design",
            session_name="Office Design Session"
        )
        
        # Verify success
        assert result["success"] is True
        assert result["session_id"] == "test-session-123"
        assert result["session_name"] == "Test Session"
        assert result["ready_for_refinement"] is True
        
        # Verify original context preserved
        assert result["original_context"]["prompt"] == "modern office space with plants"
        assert result["original_context"]["model"] == "gpt-4o"
        
        # Verify session was created with correct parameters
        mock_manager.create_session.assert_called_once_with(
            description="Refining office space design",
            model="gpt-4o",
            session_name="Office Design Session"
        )
        
        # Verify conversation history was added
        mock_manager.add_conversation_turn.assert_called()
        mock_manager.add_generated_image.assert_called_once()
    
    def test_promote_image_not_found(self):
        """Test promotion with non-existent image."""
        from src.openai_image_mcp.server import promote_image_to_session
        
        result = promote_image_to_session(
            image_path="/nonexistent/image.png",
            session_description="Test session"
        )
        
        assert result["success"] is False
        assert result["error_type"] == "image_not_found"
        assert "Image not found" in result["error"]
    
    def test_promote_image_no_metadata(self):
        """Test promotion with missing metadata."""
        from src.openai_image_mcp.server import promote_image_to_session
        
        # Remove metadata file
        os.remove(self.metadata_path)
        
        result = promote_image_to_session(
            image_path=self.image_path,
            session_description="Test session"
        )
        
        assert result["success"] is False
        assert result["error_type"] == "metadata_not_found"
        assert "metadata not found" in result["error"]
        assert "Only images generated by this server" in result["help"]
    
    def test_promote_image_invalid_metadata(self):
        """Test promotion with corrupted metadata."""
        from src.openai_image_mcp.server import promote_image_to_session
        
        # Write invalid JSON to metadata file
        with open(self.metadata_path, 'w') as f:
            f.write("invalid json content")
        
        result = promote_image_to_session(
            image_path=self.image_path,
            session_description="Test session"
        )
        
        assert result["success"] is False
        assert result["error_type"] == "metadata_read_error"
    
    def test_promote_image_incomplete_metadata(self):
        """Test promotion with metadata missing original prompt."""
        from src.openai_image_mcp.server import promote_image_to_session
        
        # Create metadata without prompt
        incomplete_metadata = {
            "model": "gpt-4o",
            "created_at": "2025-05-25T10:00:00"
        }
        
        with open(self.metadata_path, 'w') as f:
            json.dump(incomplete_metadata, f)
        
        result = promote_image_to_session(
            image_path=self.image_path,
            session_description="Test session"
        )
        
        assert result["success"] is False
        assert result["error_type"] == "incomplete_metadata"
        assert "No original prompt found" in result["error"]