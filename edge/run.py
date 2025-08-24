#!/usr/bin/env python3
"""
Entry point for GRM Service (Async Edge Core Implementation)
"""
import asyncio
from grm_service.main_async import main

if __name__ == "__main__":
    asyncio.run(main())
