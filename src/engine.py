import os
import json
from src.database import Content, Asset, db
from src.vlm import VLMClient
from src.staging import StagingManager
from src.utils import StandardNaming, RemotePaths

from src.video_utils import VideoUtils

class TaskScheduler:
    def __init__(self, config):
        self.config = config
        ssh_config = {
            "host": config.get("ssh_host"),
            "port": config.get("ssh_port", 22),
            "ssh_key": config.get("ssh_key")
        }
        self.vlm = VLMClient(config['vlm_endpoint'], model_name=config['vlm_model'], ssh_config=ssh_config)
        self.staging = StagingManager(config['staging_dir'], min_free_gb=config['min_free_space_gb'])
        
    def process_item(self, content, dry_run=False):
        """Processes a specific content item."""
        if content.status != "pending" and content.status != "processing":
            # Allow reprocessing for test
            pass
            
        print(f"--- Processing: {content.source_path} ---")
        
        # Verify if file is \"real\" (minimun 1MB)
        if content.file_size < 1024 * 1024:
            print("Skipping: File too small (likely junk).")
            content.status = "failed"
            content.error_log = "File size below 1MB threshold."
            content.save()
            return True
            
        content.status = "processing"
        content.save()
        
        # Signal heartbeat
        try:
            from src.heartbeat import update_heartbeat
            update_heartbeat()
        except:
            pass
        
        try:
            # 1. Move Master to Staging & Probe
            staging_path = self.staging.move_to_staging(content.source_path, f"scene_{content.id}")
            duration = VideoUtils.get_duration(staging_path)
            content.duration = duration
            scene_staging = os.path.dirname(staging_path)

            # --- MASTER-ASSET SYNC: Bring in pre-existing assets ---
            print("Syncing pre-existing assets (FYPs, Trailers) to staging...")
            linked_assets = Asset.select().where(Asset.content == content)
            for asset in linked_assets:
                # If it has a local path but hasn't been processed yet, move it in
                if asset.status == "pending" and asset.local_path:
                    try:
                        # Use standardized name for the asset
                        # We use parse_filename to get its original type (FYP/Trailer)
                        original_name = os.path.basename(asset.local_path)
                        from src.utils import parse_filename
                        asset_meta = parse_filename(original_name)
                        
                        ext = os.path.splitext(asset.local_path)[1]
                        std_asset_name = StandardNaming.get_file_name(content.id, str(content.content_date), content.scene_name, content_type=asset_meta["type"], ext=ext)
                        
                        asset_staging_path = self.staging.move_to_staging(asset.local_path, std_asset_name, dest_dir=scene_staging)
                        asset.local_path = asset_staging_path
                        asset.status = "staged"
                        asset.save()
                    except Exception as ae:
                        print(f"Warning: Failed to stage pre-existing asset {asset.local_path}: {ae}")

            # 2. Extract Candidate Frames for Thumbnail/Analysis
            print("Extracting candidate frames...")
            candidates = []
            for i in range(1, 6):
                ts = (duration / 6) * i
                frame_path = os.path.join(scene_staging, f"thumb_candidate_{i}.jpg")
                if VideoUtils.extract_frame(staging_path, ts, frame_path):
                    candidates.append(frame_path)
            
            # 3. VLM Analysis & Thumbnail Selection
            print("Running High-Density Action Burst VLM analysis...")
            
            # Action Burst Overhaul v3: 10 clusters (High-Res Forensic Scan)
            vlm_frames = []
            burst_points = [
                duration * 0.1, duration * 0.2, duration * 0.3, 
                duration * 0.4, duration * 0.5, duration * 0.6,
                duration * 0.7, duration * 0.8, duration * 0.9, 
                (duration * 0.5) + 2.0
            ]
            f_idx = 1
            for base_ts in burst_points:
                for offset in [0, 0.5, 1.0, 1.5]:
                    ts = min(duration - 0.05, base_ts + offset)
                    fpath = os.path.join(scene_staging, f"vlm_frame_{f_idx}.png")
                    # High-Res Forensic Scan: 1280px + Brightening
                    if VideoUtils.extract_frame(staging_path, ts, fpath, width=1280, brighten=True):
                        vlm_frames.append(fpath)
                    f_idx += 1
            
            final_meta = self.vlm.get_metadata_from_video(vlm_frames)
            
            # Cleanup VLM frames (keep only one for thumbnail)
            best_frame = vlm_frames[0] if vlm_frames else None
            if final_meta and "sensor_log_raw" in final_meta:
                content.sensor_log_raw = final_meta["sensor_log_raw"]
                content.ai_description = final_meta.get("description")
                content.ai_tags = ", ".join(final_meta.get("tags", []))
            
            # Store final thumbnail
            thumb_name = StandardNaming.get_file_name(content.id, str(content.content_date), content.scene_name, content_type="THUMB", ext=".jpg")
            thumb_path = os.path.join(scene_staging, thumb_name)
            if best_frame:
                # We'll just use the first frame as a placeholder or improve logic to pick a 'good' one
                # For now, let's just rename the first one
                os.rename(best_frame, thumb_path)
                Asset.create(content=content, asset_type="thumb", local_path=thumb_path, status="staged")
                content.thumbnail_path = thumb_path
            
            # 4. Generate clips ONLY if they don't already exist from the master-asset sync
            print("Checking/Generating supplemental clips...")
            # (continue with generating clips)
            has_trailer = any(a.asset_type.lower() == "trailer" for a in linked_assets)
            has_fyp = any(a.asset_type.lower() == "fyp" for a in linked_assets)

            if not has_trailer:
                trailer_name = StandardNaming.get_file_name(content.id, str(content.content_date), content.scene_name, content_type="TRAILER", ext=".mp4")
                trailer_path = os.path.join(scene_staging, trailer_name)
                if VideoUtils.generate_clip(staging_path, duration/2, min(60, duration/2), trailer_path):
                    Asset.create(content=content, asset_type="trailer", local_path=trailer_path, status="staged")
                
            if not has_fyp:
                fyp_name = StandardNaming.get_file_name(content.id, str(content.content_date), content.scene_name, content_type="FYP", ext=".mp4")
                fyp_path = os.path.join(scene_staging, fyp_name)
                if VideoUtils.generate_clip(staging_path, duration/2, 15, fyp_path, vertical=True):
                    Asset.create(content=content, asset_type="fyp", local_path=fyp_path, status="staged")

            # 5. Metadata JSON
            meta_name = StandardNaming.get_file_name(content.id, str(content.content_date), content.scene_name, content_type="META", ext=".json")
            meta_path = os.path.join(scene_staging, meta_name)
            with open(meta_path, 'w') as f:
                json.dump(final_meta, f, indent=4)
            Asset.create(content=content, asset_type="meta", local_path=meta_path, status="staged")
            
            # 6. Build Destination & Move
            dest_folder_name = generate_standard_name(
                content.content_type, str(content.content_date), content.scene_name, content.scene_number, ext=""
            )
            final_s3_path = os.path.join(self.config['s3_organized_path'], dest_folder_name)
            
            print(f"Moving to S3: {final_s3_path}")
            
            if dry_run:
                print(f"DRY RUN: Skipping move to {final_s3_path}")
                content.status = "dry_run_complete"
                content.save()
                return True

            self.staging.atomic_move_to_s3(scene_staging, final_s3_path)
            
            content.status = "completed"
            content.save()
            # Mark all assets as completed
            Asset.update(status="completed").where(Asset.content == content).execute()
            print(f"DONE: {dest_folder_name}")
            
        except Exception as e:
            content.status = "failed"
            content.error_log = str(e)
            content.save()
            print(f"FAILED: {e}")
            
        return True

    def process_next(self, dry_run=False):
        """Fetches and processes the next pending content."""
        content = Content.select().where(Content.status == "pending").first()
        if not content:
            return False
            
        return self.process_item(content, dry_run=dry_run)

    def run_batch(self, limit=None, dry_run=False):
        processed = 0
        while self.process_next(dry_run=dry_run):
            processed += 1
            if limit and processed >= limit:
                break
        print(f"Batch finished. Processed {processed} items.")

def process_batch(config, limit=None, dry_run=False):
    """Convenience function for GUI/Batch triggers."""
    scheduler = TaskScheduler(config)
    return scheduler.run_batch(limit=limit, dry_run=dry_run)
