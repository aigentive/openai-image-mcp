"""File organization system for generated images."""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

class FileOrganizer:
    """Manages organized file storage for generated images."""
    
    def __init__(self, workspace_root: Optional[str] = None):
        """
        Initialize file organizer.
        
        Args:
            workspace_root: Root directory for the workspace. If None, auto-detect.
        """
        if workspace_root is None:
            # Auto-detect workspace root (same logic as existing code)
            script_dir = os.path.dirname(os.path.abspath(__file__))
            workspace_root = os.path.dirname(os.path.dirname(script_dir))
            
        self.workspace_root = workspace_root
        self.base_dir = os.path.join(workspace_root, "generated_images")
        self.logger = logger
        
        # Create base directory structure
        self._ensure_directory_structure()
    
    def _ensure_directory_structure(self):
        """Create the organized directory structure."""
        subdirs = [
            "general",
            "products", 
            "ui_assets",
            "ui_assets/icons",
            "ui_assets/illustrations",
            "ui_assets/backgrounds",
            "ui_assets/heroes",
            "batch_generations",
            "edited_images",
            "variations"
        ]
        
        for subdir in subdirs:
            path = os.path.join(self.base_dir, subdir)
            try:
                os.makedirs(path, exist_ok=True)
                self.logger.debug(f"Ensured directory exists: {path}")
            except OSError as e:
                self.logger.error(f"Failed to create directory {path}: {e}")
    
    def get_save_path(
        self,
        use_case: str = "general",
        filename_prefix: str = "image",
        file_format: str = "png",
        batch_id: Optional[str] = None,
        product_name: Optional[str] = None,
        asset_type: Optional[str] = None,
        custom_subdir: Optional[str] = None
    ) -> str:
        """
        Generate organized file path based on use case and parameters.
        
        Args:
            use_case: Type of image generation (general, product, ui, batch, edit)
            filename_prefix: Base name for the file
            file_format: File extension without dot
            batch_id: ID for batch operations
            product_name: Name for product images
            asset_type: Type of UI asset (icon, illustration, etc.)
            custom_subdir: Custom subdirectory name
            
        Returns:
            Full file path for saving the image
        """
        
        # Generate timestamp for uniqueness
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]  # Remove last 3 microsecond digits
        
        # Determine subdirectory based on use case
        if custom_subdir:
            subdir = custom_subdir
        elif use_case == "product":
            if product_name:
                # Sanitize product name for filesystem
                safe_product_name = self._sanitize_filename(product_name)
                subdir = f"products/{safe_product_name}_{timestamp}"
            else:
                subdir = f"products/product_{timestamp}"
        elif use_case == "ui":
            asset_subdir = asset_type if asset_type in ["icons", "illustrations", "backgrounds", "heroes"] else "misc"
            subdir = f"ui_assets/{asset_subdir}"
        elif use_case == "batch":
            batch_name = batch_id if batch_id else f"batch_{timestamp}"
            subdir = f"batch_generations/{batch_name}"
        elif use_case == "edit":
            subdir = "edited_images"
        elif use_case == "variation":
            subdir = "variations"
        else:
            subdir = "general"
            
        # Create filename
        filename = f"{filename_prefix}_{timestamp}.{file_format.lower()}"
        
        # Create full directory path
        full_dir = os.path.join(self.base_dir, subdir)
        try:
            os.makedirs(full_dir, exist_ok=True)
        except OSError as e:
            self.logger.error(f"Failed to create directory {full_dir}: {e}")
            # Fallback to base directory
            full_dir = self.base_dir
            
        return os.path.join(full_dir, filename)
    
    def save_image_metadata(
        self,
        image_path: str,
        metadata: Dict[str, Any]
    ) -> Optional[str]:
        """
        Save metadata alongside the image file.
        
        Args:
            image_path: Path to the saved image
            metadata: Image generation metadata
            
        Returns:
            Path to metadata file if successful, None if failed
        """
        
        try:
            # Create metadata file path
            base_path = os.path.splitext(image_path)[0]
            metadata_path = f"{base_path}_metadata.json"
            
            # Prepare metadata for saving
            save_metadata = {
                "timestamp": datetime.now().isoformat(),
                "image_path": image_path,
                **metadata
            }
            
            # Save as JSON
            import json
            with open(metadata_path, 'w') as f:
                json.dump(save_metadata, f, indent=2, default=str)
                
            self.logger.debug(f"Saved metadata to: {metadata_path}")
            return metadata_path
            
        except Exception as e:
            self.logger.error(f"Failed to save metadata for {image_path}: {e}")
            return None
    
    def get_recent_images(
        self,
        use_case: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get list of recently generated images with metadata.
        
        Args:
            use_case: Filter by use case (general, product, ui, etc.)
            limit: Maximum number of images to return
            
        Returns:
            List of image info dictionaries
        """
        
        images = []
        search_dirs = []
        
        if use_case:
            if use_case == "product":
                search_dirs = [os.path.join(self.base_dir, "products")]
            elif use_case == "ui":
                search_dirs = [os.path.join(self.base_dir, "ui_assets")]
            elif use_case == "batch":
                search_dirs = [os.path.join(self.base_dir, "batch_generations")]
            elif use_case == "edit":
                search_dirs = [os.path.join(self.base_dir, "edited_images")]
            else:
                search_dirs = [os.path.join(self.base_dir, use_case)]
        else:
            search_dirs = [self.base_dir]
        
        # Find image files
        for search_dir in search_dirs:
            if os.path.exists(search_dir):
                for root, dirs, files in os.walk(search_dir):
                    for file in files:
                        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                            file_path = os.path.join(root, file)
                            stat = os.stat(file_path)
                            
                            # Look for metadata file
                            metadata_path = f"{os.path.splitext(file_path)[0]}_metadata.json"
                            metadata = {}
                            if os.path.exists(metadata_path):
                                try:
                                    import json
                                    with open(metadata_path, 'r') as f:
                                        metadata = json.load(f)
                                except Exception as e:
                                    self.logger.warning(f"Failed to load metadata from {metadata_path}: {e}")
                            
                            images.append({
                                "path": file_path,
                                "filename": file,
                                "size_bytes": stat.st_size,
                                "created": datetime.fromtimestamp(stat.st_ctime),
                                "modified": datetime.fromtimestamp(stat.st_mtime),
                                "metadata": metadata
                            })
        
        # Sort by creation time (newest first) and limit
        images.sort(key=lambda x: x["created"], reverse=True)
        return images[:limit]
    
    def cleanup_old_images(
        self,
        days_old: int = 30,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Clean up old generated images.
        
        Args:
            days_old: Delete images older than this many days
            dry_run: If True, only report what would be deleted
            
        Returns:
            Summary of cleanup operation
        """
        
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        files_to_delete = []
        total_size = 0
        
        if os.path.exists(self.base_dir):
            for root, dirs, files in os.walk(self.base_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        stat = os.stat(file_path)
                        created = datetime.fromtimestamp(stat.st_ctime)
                        
                        if created < cutoff_date:
                            files_to_delete.append({
                                "path": file_path,
                                "size": stat.st_size,
                                "created": created
                            })
                            total_size += stat.st_size
                    except OSError:
                        continue
        
        if not dry_run:
            deleted_count = 0
            for file_info in files_to_delete:
                try:
                    os.remove(file_info["path"])
                    deleted_count += 1
                except OSError as e:
                    self.logger.error(f"Failed to delete {file_info['path']}: {e}")
        
        return {
            "files_found": len(files_to_delete),
            "total_size_mb": total_size / (1024 * 1024),
            "cutoff_date": cutoff_date.isoformat(),
            "deleted": 0 if dry_run else deleted_count,
            "dry_run": dry_run
        }
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize a string for use as filename."""
        # Remove or replace problematic characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Limit length and strip whitespace
        filename = filename.strip()[:50]
        
        # Ensure it's not empty
        if not filename:
            filename = "unnamed"
            
        return filename