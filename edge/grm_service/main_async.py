"""
Async Main GRM Service using Edge Core WebSocket Client
"""
import asyncio
import signal
import sys
import time
from typing import Optional
from loguru import logger
from .config import settings
from .edge_core_client import EdgeCoreClient, ResourceConfig
from .resource_manager_async import AsyncResourceManager


def setup_logging():
    """Setup logging configuration"""
    # Remove default logger
    logger.remove()
    
    # Add console logger
    logger.add(
        "logs/grm_service.log",
        rotation="10 MB",
        retention="7 days",
        level=settings.LOG_LEVEL,
        format=settings.LOG_FORMAT,
        backtrace=True,
        diagnose=True
    )
    
    # Add console output
    logger.add(
        lambda msg: print(msg, end=""),
        level=settings.LOG_LEVEL,
        format=settings.LOG_FORMAT
    )
    
    logger.info("Logging setup completed")


class AsyncGRMService:
    """Async GRM Service using Edge Core WebSocket client"""
    
    def __init__(self):
        self.edge_core_client: Optional[EdgeCoreClient] = None
        self.resource_manager: Optional[AsyncResourceManager] = None
        self.running = False
        self.health_check_task: Optional[asyncio.Task] = None
        self.resource_update_task: Optional[asyncio.Task] = None
        
        # Setup logging
        setup_logging()
        
        logger.info("Async GRM Service initializing...")
    
    async def initialize(self) -> bool:
        """
        Initialize the service
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Validate configuration
            if not settings.IZUMA_DEVICE_ID:
                logger.error("IZUMA_DEVICE_ID not configured")
                return False
            
            # Parse Edge Core connection details from base URL
            base_url = settings.IZUMA_API_BASE_URL
            if base_url.startswith("ws://"):
                host_port = base_url.replace("ws://", "")
                if ":" in host_port:
                    host, port_str = host_port.split(":", 1)
                    port = int(port_str)
                else:
                    host = host_port
                    port = 8081
            else:
                # Default to Edge Core defaults
                host = "192.168.1.198"
                port = 8081
            
            # Initialize Edge Core client
            self.edge_core_client = EdgeCoreClient(
                host=host,
                port=port,
                name=settings.SERVICE_NAME
            )
            
            # Connect to Edge Core
            connected = await self.edge_core_client.connect()
            if not connected:
                logger.error("Failed to connect to Edge Core")
                return False
            
            # Initialize async resource manager
            self.resource_manager = AsyncResourceManager(self.edge_core_client)
            
            logger.info("Async GRM Service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Async GRM Service: {e}")
            return False
    
    async def register_grm(self) -> bool:
        """
        Register as GRM with Edge Core
        
        Returns:
            True if registration successful, False otherwise
        """
        try:
            result = await self.edge_core_client.register_grm()
            if result:
                logger.info("GRM registration successful")
                return True
            else:
                logger.error("GRM registration failed")
                return False
            
        except Exception as e:
            logger.error(f"GRM registration failed: {e}")
            return False
    
    async def sync_resources(self) -> bool:
        """
        Synchronize resources with Edge Core
        
        Returns:
            True if sync successful, False otherwise
        """
        try:
            results = await self.resource_manager.sync_resources()
            
            if results["failed"] > 0:
                logger.warning(f"Resource sync completed with {results['failed']} failures")
                for error in results["errors"]:
                    logger.error(f"Sync error: {error}")
            
            logger.info(f"Resource sync completed: {results['registered']} registered, "
                       f"{results['updated']} updated, {results['failed']} failed")
            
            return results["failed"] == 0
            
        except Exception as e:
            logger.error(f"Resource sync failed: {e}")
            return False
    
    async def health_check_loop(self):
        """Health check loop"""
        while self.running:
            try:
                # For now, just check if we're still connected
                if not self.edge_core_client.connected:
                    logger.warning("Edge Core connection lost, attempting to reconnect...")
                    await self.edge_core_client.connect()
                
                logger.debug("Health check successful")
                
            except Exception as e:
                logger.warning(f"Health check failed: {e}")
            
            await asyncio.sleep(settings.HEALTH_CHECK_INTERVAL)
    
    async def resource_update_loop(self):
        """Resource update loop"""
        while self.running:
            try:
                # Update all resources with simulated values
                results = await self.resource_manager.update_all_resources()
                
                if results["failed"] > 0:
                    logger.warning(f"Resource update completed with {results['failed']} failures")
                    for error in results["errors"]:
                        logger.error(f"Update error: {error}")
                else:
                    logger.info(f"Resource update completed: {results['updated']} resources updated")
                
            except Exception as e:
                logger.error(f"Resource update loop failed: {e}")
            
            await asyncio.sleep(settings.RESOURCE_UPDATE_INTERVAL)
    
    async def start_health_check(self):
        """Start health check task"""
        self.health_check_task = asyncio.create_task(self.health_check_loop())
        logger.info("Health check task started")
    
    async def stop_health_check(self):
        """Stop health check task"""
        if self.health_check_task and not self.health_check_task.done():
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
            logger.info("Health check task stopped")
    
    async def start_resource_update(self):
        """Start resource update task"""
        self.resource_update_task = asyncio.create_task(self.resource_update_loop())
        logger.info(f"Resource update task started (interval: {settings.RESOURCE_UPDATE_INTERVAL}s)")
    
    async def stop_resource_update(self):
        """Stop resource update task"""
        if self.resource_update_task and not self.resource_update_task.done():
            self.resource_update_task.cancel()
            try:
                await self.resource_update_task
            except asyncio.CancelledError:
                pass
            logger.info("Resource update task stopped")
    
    async def startup_sequence(self) -> bool:
        """
        Execute startup sequence
        
        Returns:
            True if startup successful, False otherwise
        """
        logger.info("Starting Async GRM Service startup sequence...")
        
        # Step 1: Initialize service
        if not await self.initialize():
            logger.error("Service initialization failed")
            return False
        
        # Step 2: Register as GRM
        if not await self.register_grm():
            logger.error("GRM registration failed")
            return False
        
        # Step 3: Sync resources
        if not await self.sync_resources():
            logger.warning("Resource sync completed with errors")
            # Don't fail startup for resource sync issues
        
        # Step 4: Start health monitoring
        await self.start_health_check()
        
        # Step 5: Start resource updates
        await self.start_resource_update()
        
        logger.info("Async GRM Service startup sequence completed successfully")
        return True
    
    async def shutdown_sequence(self):
        """Execute shutdown sequence"""
        logger.info("Starting Async GRM Service shutdown sequence...")
        
        self.running = False
        
        # Stop health check
        await self.stop_health_check()
        
        # Stop resource updates
        await self.stop_resource_update()
        
        # Disconnect from Edge Core
        try:
            if self.edge_core_client:
                await self.edge_core_client.disconnect()
                logger.info("Edge Core disconnection successful")
        except Exception as e:
            logger.error(f"Edge Core disconnection failed: {e}")
        
        logger.info("Async GRM Service shutdown sequence completed")
    
    async def run(self):
        """Run the service"""
        logger.info("Starting Async GRM Service...")
        
        if not await self.startup_sequence():
            logger.error("Startup sequence failed, exiting")
            sys.exit(1)
        
        self.running = True
        
        # Setup signal handlers
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            asyncio.create_task(self.shutdown_sequence())
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info("Async GRM Service is running. Press Ctrl+C to stop.")
        
        # Keep the main task alive
        try:
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
            await self.shutdown_sequence()


async def main():
    """Main entry point"""
    service = AsyncGRMService()
    await service.run()


if __name__ == "__main__":
    asyncio.run(main())
