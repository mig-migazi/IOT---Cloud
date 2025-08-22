#!/usr/bin/env python3
"""
FDI Package Manager Main Entry Point
Starts both the web UI and FDI server
"""

import os
import sys
import asyncio
import threading
import time
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import our FDI components
from fdi_package import create_smart_breaker_fdi_package
from fdi_blob_storage import FDIPackageBlobStorage
from fdi_server import FDIServer

# Import Flask app but don't run it yet
from web_ui import app, init_fdi_components, start_fdi_server

import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Use web_ui's functions instead of local ones

def main():
    """Main entry point"""
    try:
        # Write to file to confirm main() is called
        with open('/app/main_called.txt', 'w') as f:
            f.write('main() function was called successfully\n')
        
        print("🚀 MAIN.PY: Starting FDI Package Manager...")
        logger.info("🚀 Starting FDI Package Manager...")
        
        # FDI components are now auto-initialized in web_ui.py
        print("📦 MAIN.PY: FDI components auto-initialized in web_ui.py")
        logger.info("📦 FDI components auto-initialized in web_ui.py")
        
        # Start web UI (FDI server starts automatically)
        print("🌐 MAIN.PY: Starting web UI on port 5000...")
        logger.info("🌐 Starting web UI on port 5000...")
        app.run(host='0.0.0.0', port=5000, debug=False)
        
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    except Exception as e:
        logger.error("❌ FDI Package Manager error", error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
