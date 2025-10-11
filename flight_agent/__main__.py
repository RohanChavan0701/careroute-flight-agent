"""Main entry point for flight-agent NATS service."""

import asyncio
import json
import logging
from datetime import datetime

import nats
from nats.aio.client import Client as NATS

from .config import config
from .provider import FlightAwareProvider, ProviderError, compute_hash
from .schemas import FlightStatusRequest, FlightStatusResponse, FlightStatusData
from .summarizer import GroqSummarizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


class FlightAgent:
    """NATS-based flight status agent."""
    
    def __init__(self):
        self.nc: NATS | None = None
        self.provider = FlightAwareProvider()
        self.summarizer = GroqSummarizer()
    
    async def start(self):
        """Connect to NATS and start listening."""
        logger.info(f"Connecting to NATS at {config.NATS_URL}")
        
        self.nc = await nats.connect(config.NATS_URL)
        logger.info(f"Connected to NATS")
        
        logger.info(f"Subscribing to {config.NATS_SUBJECT}")
        await self.nc.subscribe(config.NATS_SUBJECT, cb=self.handle_request)
        
        logger.info(f"Flight agent ready (provider={config.PROVIDER})")
    
    async def handle_request(self, msg):
        """Handle incoming NATS request."""
        try:
            # Parse request
            payload = json.loads(msg.data.decode())
            request = FlightStatusRequest(**payload)
            
            logger.info(f"Request: {request.flight_num} on {request.departure_date}")
            
            # Fetch from provider
            try:
                raw = await self.provider.fetch_status(
                    request.flight_num,
                    request.departure_date
                )
            except ProviderError as e:
                logger.error(f"Provider error: {e}")
                response = FlightStatusResponse(ok=False, error=str(e))
                await msg.respond(response.model_dump_json().encode())
                return
            
            # Generate summary
            script = await self.summarizer.summarize(raw, request.locale)
            
            # Compute hash
            hash_value = compute_hash(raw)
            
            # Build response
            data = FlightStatusData(
                raw=raw,
                script=script,
                hash=hash_value,
                generated_at=datetime.utcnow()
            )
            
            response = FlightStatusResponse(ok=True, data=data)
            
            logger.info(f"Success: {request.flight_num} status={raw.status}")
            
            # Reply
            await msg.respond(response.model_dump_json().encode())
            
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            response = FlightStatusResponse(ok=False, error=f"Internal error: {str(e)}")
            await msg.respond(response.model_dump_json().encode())
    
    async def stop(self):
        """Gracefully shutdown."""
        if self.nc:
            logger.info("Closing NATS connection")
            await self.nc.close()
            logger.info("Shutdown complete")


async def main():
    """Main entry point."""
    # Validate config
    try:
        config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return
    
    agent = FlightAgent()
    
    try:
        await agent.start()
        
        # Keep running until interrupted
        logger.info("Press Ctrl+C to stop")
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())

