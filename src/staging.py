import os
import shutil
import shutil
import logging

class StagingManager:
    def __init__(self, staging_dir, min_free_gb=10):
        self.staging_dir = os.path.abspath(staging_dir)
        self.min_free_gb = min_free_gb
        
        if not os.path.exists(self.staging_dir):
            os.makedirs(self.staging_dir)
            
    def check_disk_space(self):
        """Returns True if there is enough space in the staging directory."""
        total, used, free = shutil.disk_usage(self.staging_dir)
        free_gb = free // (2**30)
        return free_gb > self.min_free_gb

    def create_scene_staging(self, scene_name):
        """Creates a dedicated subfolder for a scene's assets."""
        path = os.path.join(self.staging_dir, scene_name)
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    def move_to_staging(self, source_path, scene_name):
        """Copies a file to the staging directory. Supports local and rclone paths."""
        if not self.check_disk_space():
            raise Exception("Insufficient disk space in staging area.")
            
        scene_path = self.create_scene_staging(scene_name)
        file_name = os.path.basename(source_path)
        dest_path = os.path.join(scene_path, file_name)
        
        import subprocess
        
        if ":" in source_path: # Looks like an rclone remote path
            print(f"Rclone downloading: {source_path} to {dest_path}")
            cmd = ["rclone", "copyto", source_path, dest_path]
            try:
                subprocess.run(cmd, check=True)
            except Exception as e:
                raise Exception(f"Rclone download failed: {e}")
        else: # Local file
            shutil.copy2(source_path, dest_path)
            
        return dest_path

    def cleanup_scene(self, scene_name):
        """Deletes the staging folder for a scene."""
        path = os.path.join(self.staging_dir, scene_name)
        if os.path.exists(path):
            shutil.rmtree(path)
            
    def atomic_move_to_s3(self, scene_staging_path, s3_dest_path):
        """
        Moves the entire scene folder to S3 using rclone for reliability.
        """
        import subprocess
        
        # Ensure destination exists (rclone handles this but let's be explicit)
        if not os.path.exists(s3_dest_path):
            os.makedirs(s3_dest_path)
            
        print(f"Rclone moving: {scene_staging_path} to {s3_dest_path}")
        
        # rclone move --progress --transfers 4
        cmd = ["rclone", "move", scene_staging_path, s3_dest_path, "--delete-empty-src-dirs"]
        
        try:
            subprocess.run(cmd, check=True)
            return True
        except Exception as e:
            logging.error(f"Rclone move failed: {e}")
            raise Exception(f"Failed to move folder to S3: {e}")

    def verify_upload(self, s3_dest_path, expected_assets):
        """
        Verifies that all expected assets exist in the destination folder.
        """
        missing = []
        for asset in expected_assets:
            if not os.path.exists(os.path.join(s3_dest_path, asset)):
                missing.append(asset)
        
        if missing:
            raise Exception(f"Verification failed! Missing files: {', '.join(missing)}")
        return True
