"""Tests for FileOrganizer functionality."""

import pytest
import os
import tempfile
import json
from datetime import datetime
from src.openai_image_mcp.file_organizer import FileOrganizer

class TestFileOrganizer:
    """Test cases for the FileOrganizer class."""
    
    def setup_method(self):
        """Set up test fixtures with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.organizer = FileOrganizer(workspace_root=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init(self):
        """Test FileOrganizer initialization."""
        assert self.organizer is not None
        assert self.organizer.workspace_root == self.temp_dir
        assert self.organizer.base_dir == os.path.join(self.temp_dir, "generated_images")
    
    def test_directory_structure_creation(self):
        """Test that required directory structure is created."""
        base_dir = self.organizer.base_dir
        
        # Check main directories exist
        assert os.path.exists(os.path.join(base_dir, "general"))
        assert os.path.exists(os.path.join(base_dir, "products"))
        assert os.path.exists(os.path.join(base_dir, "ui_assets"))
        assert os.path.exists(os.path.join(base_dir, "ui_assets", "icons"))
        assert os.path.exists(os.path.join(base_dir, "ui_assets", "illustrations"))
        assert os.path.exists(os.path.join(base_dir, "batch_generations"))
        assert os.path.exists(os.path.join(base_dir, "edited_images"))
        assert os.path.exists(os.path.join(base_dir, "variations"))
    
    def test_get_save_path_general(self):
        """Test save path generation for general use case."""
        path = self.organizer.get_save_path(
            use_case="general",
            filename_prefix="test_image",
            file_format="png"
        )
        
        assert path.startswith(os.path.join(self.organizer.base_dir, "general"))
        assert path.endswith(".png")
        assert "test_image" in path
    
    def test_get_save_path_product(self):
        """Test save path generation for product use case."""
        path = self.organizer.get_save_path(
            use_case="product",
            filename_prefix="product",
            file_format="png",
            product_name="headphones"
        )
        
        assert "products" in path
        assert "headphones" in path
        assert path.endswith(".png")
    
    def test_get_save_path_ui_asset(self):
        """Test save path generation for UI assets."""
        path = self.organizer.get_save_path(
            use_case="ui",
            filename_prefix="icon",
            file_format="png",
            asset_type="icons"
        )
        
        assert "ui_assets" in path
        assert "icons" in path
        assert path.endswith(".png")
    
    def test_get_save_path_batch(self):
        """Test save path generation for batch processing."""
        path = self.organizer.get_save_path(
            use_case="batch",
            filename_prefix="batch_item",
            file_format="png",
            batch_id="test_batch_123"
        )
        
        assert "batch_generations" in path
        assert "test_batch_123" in path
        assert path.endswith(".png")
    
    def test_get_save_path_custom_subdir(self):
        """Test save path generation with custom subdirectory."""
        path = self.organizer.get_save_path(
            use_case="general",
            filename_prefix="custom",
            file_format="jpg",
            custom_subdir="my_custom_folder"
        )
        
        assert "my_custom_folder" in path
        assert path.endswith(".jpg")
    
    def test_filename_sanitization(self):
        """Test filename sanitization."""
        # Test with problematic characters
        sanitized = self.organizer._sanitize_filename("test<>:\"/\\|?*file")
        assert "<" not in sanitized
        assert ">" not in sanitized
        assert ":" not in sanitized
        assert "\"" not in sanitized
        assert "/" not in sanitized
        assert "\\" not in sanitized
        assert "|" not in sanitized
        assert "?" not in sanitized
        assert "*" not in sanitized
        
        # Test length limiting
        long_name = "a" * 100
        sanitized = self.organizer._sanitize_filename(long_name)
        assert len(sanitized) <= 50
        
        # Test empty string handling
        sanitized = self.organizer._sanitize_filename("")
        assert sanitized == "unnamed"
    
    def test_save_image_metadata(self):
        """Test metadata saving functionality."""
        # Create a test image file
        test_image_path = os.path.join(self.temp_dir, "test_image.png")
        with open(test_image_path, "wb") as f:
            f.write(b"fake image data")
        
        metadata = {
            "prompt": "test prompt",
            "model": "gpt-image-1",
            "quality": "high"
        }
        
        metadata_path = self.organizer.save_image_metadata(test_image_path, metadata)
        
        assert metadata_path is not None
        assert os.path.exists(metadata_path)
        assert metadata_path.endswith("_metadata.json")
        
        # Verify metadata content
        with open(metadata_path, 'r') as f:
            saved_metadata = json.load(f)
            
        assert saved_metadata["prompt"] == "test prompt"
        assert saved_metadata["model"] == "gpt-image-1"
        assert saved_metadata["quality"] == "high"
        assert "timestamp" in saved_metadata
        assert "image_path" in saved_metadata
    
    def test_get_recent_images_empty(self):
        """Test getting recent images when none exist."""
        images = self.organizer.get_recent_images()
        assert images == []
    
    def test_get_recent_images_with_files(self):
        """Test getting recent images with actual files."""
        # Create test images
        general_dir = os.path.join(self.organizer.base_dir, "general")
        os.makedirs(general_dir, exist_ok=True)
        
        test_files = ["image1.png", "image2.jpg", "image3.png"]
        for filename in test_files:
            filepath = os.path.join(general_dir, filename)
            with open(filepath, "wb") as f:
                f.write(b"fake image data")
        
        images = self.organizer.get_recent_images(limit=5)
        
        assert len(images) == 3
        assert all("path" in img for img in images)
        assert all("filename" in img for img in images)
        assert all("size_bytes" in img for img in images)
        assert all("created" in img for img in images)
    
    def test_get_recent_images_with_metadata(self):
        """Test getting recent images that have associated metadata."""
        # Create test image and metadata
        general_dir = os.path.join(self.organizer.base_dir, "general")
        os.makedirs(general_dir, exist_ok=True)
        
        image_path = os.path.join(general_dir, "test_with_metadata.png")
        with open(image_path, "wb") as f:
            f.write(b"fake image data")
        
        # Create metadata file
        metadata_path = image_path.replace(".png", "_metadata.json")
        metadata = {"prompt": "test prompt", "model": "gpt-image-1"}
        with open(metadata_path, "w") as f:
            json.dump(metadata, f)
        
        images = self.organizer.get_recent_images()
        
        assert len(images) == 1
        assert images[0]["metadata"]["prompt"] == "test prompt"
        assert images[0]["metadata"]["model"] == "gpt-image-1"
    
    def test_get_recent_images_filtered_by_use_case(self):
        """Test filtering recent images by use case."""
        # Create images in different directories
        product_dir = os.path.join(self.organizer.base_dir, "products")
        ui_dir = os.path.join(self.organizer.base_dir, "ui_assets")
        os.makedirs(product_dir, exist_ok=True)
        os.makedirs(ui_dir, exist_ok=True)
        
        # Create product images
        for i in range(2):
            with open(os.path.join(product_dir, f"product{i}.png"), "wb") as f:
                f.write(b"fake image data")
        
        # Create UI images
        for i in range(3):
            with open(os.path.join(ui_dir, f"ui{i}.png"), "wb") as f:
                f.write(b"fake image data")
        
        # Test filtering
        product_images = self.organizer.get_recent_images(use_case="product")
        ui_images = self.organizer.get_recent_images(use_case="ui")
        
        assert len(product_images) == 2
        assert len(ui_images) == 3
        
        # Verify paths
        for img in product_images:
            assert "products" in img["path"]
        for img in ui_images:
            assert "ui_assets" in img["path"]
    
    def test_cleanup_old_images_dry_run(self):
        """Test cleanup functionality in dry run mode."""
        # Create some test files with different ages
        general_dir = os.path.join(self.organizer.base_dir, "general")
        os.makedirs(general_dir, exist_ok=True)
        
        # Create a few test files
        for i in range(3):
            filepath = os.path.join(general_dir, f"old_image{i}.png")
            with open(filepath, "wb") as f:
                f.write(b"fake image data" * 100)  # Make files larger for size testing
        
        # Run cleanup in dry run mode
        result = self.organizer.cleanup_old_images(days_old=0, dry_run=True)
        
        assert result["dry_run"] == True
        assert result["files_found"] >= 0
        assert result["total_size_mb"] >= 0
        assert result["deleted"] == 0
        assert "cutoff_date" in result
    
    def test_unique_timestamps(self):
        """Test that generated paths have unique timestamps."""
        import time
        
        path1 = self.organizer.get_save_path(use_case="general")
        time.sleep(0.001)  # Ensure different timestamp
        path2 = self.organizer.get_save_path(use_case="general")
        
        # Paths should be different due to timestamp
        assert path1 != path2
    
    def test_asset_type_subdirectories(self):
        """Test UI asset type subdirectory creation."""
        asset_types = ["icons", "illustrations", "backgrounds", "heroes"]
        
        for asset_type in asset_types:
            path = self.organizer.get_save_path(
                use_case="ui",
                asset_type=asset_type
            )
            assert asset_type in path
            # Directory should be created
            assert os.path.exists(os.path.dirname(path))