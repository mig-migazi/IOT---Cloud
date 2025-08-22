#!/usr/bin/env python3
"""
FDI Blob Storage Service
Handles storage and retrieval of FDI packages in blob storage
"""

import os
import json
import hashlib
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional, BinaryIO
from pathlib import Path
import structlog

logger = structlog.get_logger()

class FDIPackageBlobStorage:
    """Blob storage for FDI packages"""
    
    def __init__(self, storage_path: str = "/app/fdi-packages"):
        self.storage_path = Path(storage_path)
        self.manifest_path = self.storage_path / "manifest.json"
        self.packages_path = self.storage_path / "packages"
        
        # Ensure storage directories exist
        self._ensure_storage_dirs()
        
        # Load or create manifest
        self.manifest = self._load_manifest()
    
    def _ensure_storage_dirs(self):
        """Ensure storage directories exist"""
        try:
            self.storage_path.mkdir(parents=True, exist_ok=True)
            self.packages_path.mkdir(parents=True, exist_ok=True)
            logger.info("FDI storage directories created", storage_path=str(self.storage_path))
        except Exception as e:
            logger.error("Failed to create storage directories", error=str(e))
            raise
    
    def _load_manifest(self) -> Dict[str, Any]:
        """Load or create manifest file"""
        try:
            if self.manifest_path.exists():
                with open(self.manifest_path, 'r') as f:
                    manifest = json.load(f)
                logger.info("FDI manifest loaded", packages_count=len(manifest.get('packages', {})))
                return manifest
            else:
                # Create new manifest
                manifest = {
                    "version": "1.0.0",
                    "created_at": datetime.utcnow().isoformat() + "Z",
                    "last_updated": datetime.utcnow().isoformat() + "Z",
                    "packages": {},
                    "metadata": {
                        "description": "FDI Package Manifest",
                        "total_packages": 0
                    }
                }
                self._save_manifest(manifest)
                logger.info("New FDI manifest created")
                return manifest
        except Exception as e:
            logger.error("Failed to load manifest", error=str(e))
            # Return empty manifest on error
            return {
                "version": "1.0.0",
                "created_at": datetime.utcnow().isoformat() + "Z",
                "last_updated": datetime.utcnow().isoformat() + "Z",
                "packages": {},
                "metadata": {
                    "description": "FDI Package Manifest",
                    "total_packages": 0
                }
            }
    
    def _save_manifest(self, manifest: Dict[str, Any]):
        """Save manifest to file"""
        try:
            manifest["last_updated"] = datetime.utcnow().isoformat() + "Z"
            manifest["metadata"]["total_packages"] = len(manifest["packages"])
            
            with open(self.manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2, default=str)
                
            logger.debug("Manifest saved successfully")
        except Exception as e:
            logger.error("Failed to save manifest", error=str(e))
            raise
    
    def store_package(self, package_data: Dict[str, Any], package_id: str) -> bool:
        """Store FDI package in blob storage"""
        try:
            # Create package directory
            package_dir = self.packages_path / package_id
            package_dir.mkdir(exist_ok=True)
            
            # Store package definition
            package_file = package_dir / "package.json"
            with open(package_file, 'w') as f:
                json.dump(package_data, f, indent=2, default=str)
            
            # Calculate checksum
            checksum = self._calculate_checksum(package_data)
            
            # Update manifest
            self.manifest["packages"][package_id] = {
                "package_id": package_id,
                "device_type": package_data.get("device_type", {}).get("device_type", "unknown"),
                "manufacturer": package_data.get("device_type", {}).get("manufacturer", "unknown"),
                "model": package_data.get("device_type", {}).get("model", "unknown"),
                "version": package_data.get("version", "1.0.0"),
                "created_at": package_data.get("created_at", datetime.utcnow().isoformat() + "Z"),
                "stored_at": datetime.utcnow().isoformat() + "Z",
                "checksum": checksum,
                "file_path": str(package_file),
                "size_bytes": os.path.getsize(package_file),
                "metadata": package_data.get("metadata", {})
            }
            
            self._save_manifest(self.manifest)
            
            logger.info("FDI package stored successfully", 
                       package_id=package_id,
                       device_type=package_data.get("device_type", {}).get("device_type", "unknown"))
            return True
            
        except Exception as e:
            logger.error("Failed to store FDI package", package_id=package_id, error=str(e))
            return False
    
    def retrieve_package(self, package_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve FDI package from blob storage"""
        try:
            if package_id not in self.manifest["packages"]:
                logger.warning("Package not found in manifest", package_id=package_id)
                return None
            
            package_info = self.manifest["packages"][package_id]
            package_file = Path(package_info["file_path"])
            
            if not package_file.exists():
                logger.error("Package file not found", package_id=package_id, file_path=str(package_file))
                return None
            
            # Load package data
            with open(package_file, 'r') as f:
                package_data = json.load(f)
            
            # Verify checksum
            current_checksum = self._calculate_checksum(package_data)
            if current_checksum != package_info["checksum"]:
                logger.warning("Package checksum mismatch", package_id=package_id)
            
            logger.info("FDI package retrieved successfully", package_id=package_id)
            return package_data
            
        except Exception as e:
            logger.error("Failed to retrieve FDI package", package_id=package_id, error=str(e))
            return None
    
    def list_packages(self, device_type: Optional[str] = None, manufacturer: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available packages with optional filtering"""
        try:
            packages = []
            
            for package_id, package_info in self.manifest["packages"].items():
                # Apply filters
                if device_type and package_info.get("device_type") != device_type:
                    continue
                if manufacturer and package_info.get("manufacturer") != manufacturer:
                    continue
                
                packages.append({
                    "package_id": package_id,
                    "device_type": package_info.get("device_type"),
                    "manufacturer": package_info.get("manufacturer"),
                    "model": package_info.get("model"),
                    "version": package_info.get("version"),
                    "created_at": package_info.get("created_at"),
                    "stored_at": package_info.get("stored_at"),
                    "metadata": package_info.get("metadata", {})
                })
            
            logger.info("Packages listed successfully", 
                       total_packages=len(packages),
                       filters={"device_type": device_type, "manufacturer": manufacturer})
            return packages
            
        except Exception as e:
            logger.error("Failed to list packages", error=str(e))
            return []
    
    def delete_package(self, package_id: str) -> bool:
        """Delete FDI package from blob storage"""
        try:
            if package_id not in self.manifest["packages"]:
                logger.warning("Package not found in manifest", package_id=package_id)
                return False
            
            package_info = self.manifest["packages"][package_id]
            package_dir = self.packages_path / package_id
            
            # Remove package directory
            if package_dir.exists():
                shutil.rmtree(package_dir)
            
            # Remove from manifest
            del self.manifest["packages"][package_id]
            self._save_manifest(self.manifest)
            
            logger.info("FDI package deleted successfully", package_id=package_id)
            return True
            
        except Exception as e:
            logger.error("Failed to delete FDI package", package_id=package_id, error=str(e))
            return False
    
    def get_package_info(self, package_id: str) -> Optional[Dict[str, Any]]:
        """Get package information without loading full package data"""
        try:
            if package_id not in self.manifest["packages"]:
                return None
            
            return self.manifest["packages"][package_id]
            
        except Exception as e:
            logger.error("Failed to get package info", package_id=package_id, error=str(e))
            return None
    
    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate checksum for package data"""
        try:
            # Convert to sorted JSON string for consistent checksum
            json_str = json.dumps(data, sort_keys=True, default=str)
            return hashlib.sha256(json_str.encode()).hexdigest()
        except Exception as e:
            logger.error("Failed to calculate checksum", error=str(e))
            return ""
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            total_size = 0
            for package_info in self.manifest["packages"].values():
                total_size += package_info.get("size_bytes", 0)
            
            return {
                "total_packages": len(self.manifest["packages"]),
                "total_size_bytes": total_size,
                "storage_path": str(self.storage_path),
                "manifest_path": str(self.manifest_path),
                "last_updated": self.manifest.get("last_updated")
            }
        except Exception as e:
            logger.error("Failed to get storage stats", error=str(e))
            return {}
    
    def cleanup_orphaned_files(self) -> int:
        """Clean up orphaned package files not in manifest"""
        try:
            cleaned_count = 0
            
            for package_dir in self.packages_path.iterdir():
                if package_dir.is_dir():
                    package_id = package_dir.name
                    if package_id not in self.manifest["packages"]:
                        shutil.rmtree(package_dir)
                        cleaned_count += 1
                        logger.info("Cleaned up orphaned package directory", package_id=package_id)
            
            logger.info("Cleanup completed", cleaned_count=cleaned_count)
            return cleaned_count
            
        except Exception as e:
            logger.error("Failed to cleanup orphaned files", error=str(e))
            return 0
