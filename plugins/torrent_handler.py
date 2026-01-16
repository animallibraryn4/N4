import asyncio
import time
import os
from typing import Optional, Dict, Callable, Any
from loguru import logger
from config import config

# Try to import libtorrent, handle gracefully if not available
try:
    import libtorrent as lt
    LIBTORRENT_AVAILABLE = True
except ImportError as e:
    logger.error(f"libtorrent import failed: {e}")
    LIBTORRENT_AVAILABLE = False
    lt = None

class TorrentHandler:
    def __init__(self):
        if not LIBTORRENT_AVAILABLE:
            raise ImportError("libtorrent is not available. Please install it first.")
        
        try:
            self.session = lt.session()
            self.session.listen_on(6881, 6891)
            self.session.start_dht()
            
            # Add public DHT routers
            dht_routers = [
                ("router.utorrent.com", 6881),
                ("router.bittorrent.com", 6881),
                ("dht.transmissionbt.com", 6881)
            ]
            
            for router in dht_routers:
                try:
                    self.session.add_dht_router(*router)
                except:
                    pass
            
            logger.info("Torrent handler initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize libtorrent session: {e}")
            raise
    
    async def download(self, magnet_link: str, update_callback=None) -> Optional[Dict]:
        """
        Download torrent from magnet link asynchronously
        
        Args:
            magnet_link: Magnet URI
            update_callback: Callback function for progress updates
            
        Returns:
            Dict containing file info or None if failed
        """
        if not LIBTORRENT_AVAILABLE:
            logger.error("libtorrent is not available")
            return None
        
        try:
            logger.info(f"Starting download: {magnet_link[:60]}...")
            
            # Create downloads directory if it doesn't exist
            os.makedirs(config.DOWNLOADS_DIR, exist_ok=True)
            
            # Add torrent to session
            params = {
                'save_path': config.DOWNLOADS_DIR,
                'storage_mode': lt.storage_mode_t.storage_mode_sparse
            }
            
            # Parse magnet link
            handle = lt.add_magnet_uri(self.session, magnet_link, params)
            
            if not handle.is_valid():
                logger.error("Invalid magnet link or handle")
                return None
            
            # Wait for metadata
            logger.info("Waiting for metadata...")
            start_time = time.time()
            metadata_timeout = 120  # 2 minutes
            
            while not handle.has_metadata():
                elapsed = time.time() - start_time
                if elapsed > metadata_timeout:
                    logger.error(f"Timeout waiting for metadata after {elapsed:.1f} seconds")
                    
                    # Try to get error info
                    try:
                        status = handle.status()
                        logger.error(f"Torrent status: {status.error}")
                    except:
                        pass
                    
                    return None
                
                # Update progress if callback provided
                if update_callback:
                    try:
                        status = handle.status()
                        progress_info = {
                            'progress': 0,
                            'state': 'downloading_metadata',
                            'name': 'Waiting for metadata...',
                            'download_rate': 0,
                            'upload_rate': 0,
                            'num_peers': 0
                        }
                        await update_callback(progress_info)
                    except:
                        pass
                
                await asyncio.sleep(1)
            
            # Get torrent info
            torrent_info = handle.get_torrent_info()
            if not torrent_info:
                logger.error("Failed to get torrent info")
                return None
            
            logger.info(f"Metadata received: {torrent_info.name()}")
            
            # Set priority to all files
            for i in range(torrent_info.num_files()):
                handle.file_priority(i, 1)
            
            # Resume download
            handle.resume()
            
            # Monitor download progress
            last_update = 0
            update_interval = 10  # seconds
            
            while not handle.is_seed():
                status = handle.status()
                
                # Calculate progress percentage
                progress = (status.total_done / max(status.total_wanted, 1)) * 100
                
                # Update progress callback periodically
                current_time = time.time()
                if update_callback and (current_time - last_update > update_interval or progress >= 99.9):
                    progress_info = {
                        'progress': progress,
                        'download_rate': status.download_rate,
                        'upload_rate': status.upload_rate,
                        'num_peers': status.num_peers,
                        'state': str(status.state),
                        'name': torrent_info.name()
                    }
                    
                    # Run callback
                    try:
                        if asyncio.iscoroutinefunction(update_callback):
                            await update_callback(progress_info)
                        elif callable(update_callback):
                            # Run synchronous callback in thread pool
                            await asyncio.get_event_loop().run_in_executor(
                                None, update_callback, progress_info
                            )
                    except Exception as e:
                        logger.error(f"Error in progress callback: {e}")
                    
                    last_update = current_time
                
                # Check if download is complete
                if progress >= 99.9:
                    logger.info("Download nearly complete, finalizing...")
                    break
                
                # Check for errors
                if status.error:
                    logger.error(f"Torrent error: {status.error}")
                    return None
                
                await asyncio.sleep(2)
            
            # Download completed
            end_time = time.time()
            elapsed = end_time - start_time
            logger.info(
                f"Download completed: {torrent_info.name()} | "
                f"Time: {int(elapsed // 60)}m {int(elapsed % 60)}s | "
                f"Size: {status.total_done / (1024*1024):.1f} MB"
            )
            
            # Find downloaded files
            downloaded_files = []
            for i in range(torrent_info.num_files()):
                file_entry = torrent_info.file_at(i)
                file_path = os.path.join(config.DOWNLOADS_DIR, file_entry.path)
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    downloaded_files.append(file_path)
            
            if not downloaded_files:
                logger.error("No valid files found after download")
                return None
            
            # Get the main video file (largest file usually)
            main_file = max(downloaded_files, key=os.path.getsize)
            file_size = os.path.getsize(main_file)
            
            logger.info(f"Main file: {main_file} ({file_size / (1024*1024):.1f} MB)")
            
            return {
                "file": main_file,
                "name": torrent_info.name(),
                "size": file_size,
                "all_files": downloaded_files
            }
            
        except Exception as e:
            logger.error(f"Torrent download error: {e}")
            return None
    
    async def cleanup(self):
        """Clean up torrent session"""
        try:
            if hasattr(self, 'session'):
                self.session.pause()
                logger.info("Torrent session cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up torrent session: {e}")
    
    @staticmethod
    def is_available() -> bool:
        """Check if libtorrent is available"""
        return LIBTORRENT_AVAILABLE
