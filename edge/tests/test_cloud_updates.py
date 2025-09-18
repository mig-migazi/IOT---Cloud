#!/usr/bin/env python3
"""
Test Cloud Update Functionality for GRM Service
Demonstrates receiving and processing cloud updates
"""
import asyncio
import json
import time
import websockets
from loguru import logger
import sys
import os

# Add the parent directory to the path to access grm_service
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from grm_service.edge_core_client import EdgeCoreClient, ResourceConfig, CloudUpdateMessage
from grm_service.resource_manager_async import AsyncResourceManager
from grm_service.config import settings


class CloudUpdateTester:
    """Test class for cloud update functionality"""
    
    def __init__(self):
        self.edge_core_client: EdgeCoreClient = None
        self.resource_manager: AsyncResourceManager = None
        self.test_results = {
            "resource_updates": 0,
            "configuration_updates": 0,
            "commands": 0,
            "errors": []
        }
    
    async def setup(self) -> bool:
        """Setup test environment"""
        try:
            logger.info("Setting up cloud update test...")
            
            # Parse Edge Core connection details
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
                host = "192.168.1.198"
                port = 8081
            
            # Initialize Edge Core client
            self.edge_core_client = EdgeCoreClient(
                host=host,
                port=port,
                name="cloud-update-tester"
            )
            
            # Connect to Edge Core
            connected = await self.edge_core_client.connect()
            if not connected:
                logger.error("Failed to connect to Edge Core")
                return False
            
            # Initialize resource manager
            self.resource_manager = AsyncResourceManager(self.edge_core_client)
            
            # Set up cloud update callback
            self.edge_core_client.set_cloud_update_callback(self._test_cloud_update_callback)
            
            # Start message listening
            await self.edge_core_client.start_message_listening()
            
            logger.info("Cloud update test setup completed")
            return True
            
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return False
    
    async def _test_cloud_update_callback(self, cloud_update: CloudUpdateMessage):
        """Test callback for cloud updates"""
        try:
            logger.info(f"🔔 TEST: Received cloud update: {cloud_update.message_type}")
            
            # Handle the update
            results = await self.resource_manager.handle_cloud_update(cloud_update)
            
            # Update test statistics
            if cloud_update.is_resource_update():
                self.test_results["resource_updates"] += 1
            elif cloud_update.is_configuration_update():
                self.test_results["configuration_updates"] += 1
            elif cloud_update.is_command():
                self.test_results["commands"] += 1
            
            # Log results
            if results["processed"]:
                logger.info(f"✅ TEST: Cloud update processed successfully")
                if results["updated_resources"] > 0:
                    logger.info(f"   Updated {results['updated_resources']} resources")
                if results["errors"]:
                    for error in results["errors"]:
                        logger.warning(f"   Warning: {error}")
            else:
                logger.error(f"❌ TEST: Cloud update processing failed")
                for error in results["errors"]:
                    logger.error(f"   Error: {error}")
                    self.test_results["errors"].append(error)
                    
        except Exception as e:
            error_msg = f"Error in test callback: {e}"
            logger.error(error_msg)
            self.test_results["errors"].append(error_msg)
    
    async def send_test_cloud_update(self, update_type: str, data: dict):
        """Send a test cloud update message"""
        try:
            # Create test message
            test_message = {
                "type": update_type,
                "timestamp": time.time(),
                "device_id": "test-device-001",
                **data
            }
            
            # Send via WebSocket (this would normally come from the cloud)
            if self.edge_core_client.websocket:
                message_str = json.dumps(test_message)
                await self.edge_core_client.websocket.send(message_str)
                logger.info(f"📤 TEST: Sent {update_type} message")
                return True
            else:
                logger.error("WebSocket not connected")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send test message: {e}")
            return False
    
    async def test_resource_update(self):
        """Test resource update functionality"""
        logger.info("🧪 Testing resource update...")
        
        test_data = {
            "resource_updates": [
                {
                    "object_id": 1234,
                    "instance_id": 0,
                    "resource_id": 0,
                    "value": 85.5
                },
                {
                    "object_id": 1234,
                    "instance_id": 0,
                    "resource_id": 1,
                    "value": 65.2
                }
            ]
        }
        
        success = await self.send_test_cloud_update("resource_update", test_data)
        if success:
            logger.info("✅ Resource update test sent")
        else:
            logger.error("❌ Resource update test failed")
    
    async def test_configuration_update(self):
        """Test configuration update functionality"""
        logger.info("🧪 Testing configuration update...")
        
        test_data = {
            "metadata": {
                "configuration_changes": {
                    "add_resource": {
                        "object_id": 9999,
                        "instance_id": 0,
                        "resource_id": 0,
                        "resource_name": "new_sensor",
                        "operations": 3,
                        "resource_type": "float",
                        "value": 42.0,
                        "periodic_update": True
                    }
                }
            }
        }
        
        success = await self.send_test_cloud_update("configuration_update", test_data)
        if success:
            logger.info("✅ Configuration update test sent")
        else:
            logger.error("❌ Configuration update test failed")
    
    async def test_command(self):
        """Test command functionality"""
        logger.info("🧪 Testing command...")
        
        test_data = {
            "metadata": {
                "command": {
                    "type": "set_resource_value",
                    "parameters": {
                        "object_id": 1234,
                        "instance_id": 0,
                        "resource_id": 0,
                        "value": 100.0
                    }
                }
            }
        }
        
        success = await self.send_test_cloud_update("command", test_data)
        if success:
            logger.info("✅ Command test sent")
        else:
            logger.error("❌ Command test failed")
    
    async def run_tests(self):
        """Run all cloud update tests"""
        logger.info("🚀 Starting cloud update tests...")
        
        # Setup
        if not await self.setup():
            logger.error("Test setup failed")
            return
        
        # Wait a moment for setup to complete
        await asyncio.sleep(2)
        
        # Run tests
        await self.test_resource_update()
        await asyncio.sleep(3)  # Wait for processing
        
        await self.test_configuration_update()
        await asyncio.sleep(3)  # Wait for processing
        
        await self.test_command()
        await asyncio.sleep(3)  # Wait for processing
        
        # Print results
        logger.info("📊 Test Results:")
        logger.info(f"   Resource Updates: {self.test_results['resource_updates']}")
        logger.info(f"   Configuration Updates: {self.test_results['configuration_updates']}")
        logger.info(f"   Commands: {self.test_results['commands']}")
        logger.info(f"   Errors: {len(self.test_results['errors'])}")
        
        if self.test_results["errors"]:
            logger.warning("⚠️  Test errors:")
            for error in self.test_results["errors"]:
                logger.warning(f"   - {error}")
        
        # Get cloud update statistics
        if self.resource_manager:
            stats = self.resource_manager.get_cloud_update_stats()
            logger.info(f"📈 Cloud Update Statistics:")
            logger.info(f"   Total Updates: {stats['total_updates']}")
            logger.info(f"   Successful: {stats['successful_updates']}")
            logger.info(f"   Failed: {stats['failed_updates']}")
        
        # Cleanup
        await self.cleanup()
        
        logger.info("🏁 Cloud update tests completed")
    
    async def cleanup(self):
        """Cleanup test environment"""
        try:
            if self.edge_core_client:
                await self.edge_core_client.disconnect()
            logger.info("Test cleanup completed")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


async def main():
    """Main test function"""
    tester = CloudUpdateTester()
    await tester.run_tests()


if __name__ == "__main__":
    # Setup logging
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}"
    )
    
    asyncio.run(main())
