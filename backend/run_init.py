import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import init_sys
import asyncio

asyncio.run(init_sys.init())
