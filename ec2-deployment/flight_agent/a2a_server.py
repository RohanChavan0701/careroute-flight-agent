"""A2A Protocol JSON-RPC 2.0 server for flight-agent.

Implements the Agent2Agent protocol for agent interoperability.
https://github.com/a2aproject/A2A
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

from .config import config
from .provider import FlightAwareProvider, ProviderError, compute_hash
from .mock_provider import MockProvider
from .schemas import FlightStatusRequest, FlightRaw
from .summarizer import GroqSummarizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


# JSON-RPC 2.0 Models
class JsonRpcRequest(BaseModel):
    """JSON-RPC 2.0 request."""
    jsonrpc: str = "2.0"
    method: str
    params: Dict[str, Any]
    id: Optional[str | int] = None


class JsonRpcError(BaseModel):
    """JSON-RPC 2.0 error."""
    code: int
    message: str
    data: Optional[Any] = None


class JsonRpcResponse(BaseModel):
    """JSON-RPC 2.0 response."""
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[JsonRpcError] = None
    id: Optional[str | int] = None


# JSON-RPC Error Codes
class ErrorCode:
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # Custom error codes
    PROVIDER_ERROR = -32000
    SUMMARIZER_ERROR = -32001


# A2A Flight Agent
class A2AFlightAgent:
    """Flight agent implementing A2A protocol."""
    
    def __init__(self):
        # Select provider based on config
        if config.PROVIDER == "mock":
            self.provider = MockProvider()
            provider_name = "Mock Provider (Demo)"
        else:
            self.provider = FlightAwareProvider()
            provider_name = "FlightAware AeroAPI v4"
        
        self.summarizer = GroqSummarizer()
        self._provider_name = provider_name
        
        # Agent Card metadata
        self.agent_card = {
            "name": "Guardian Buddy Flight Agent",
            "description": "Provides real-time flight status information with AI-powered conversational summaries using FlightAware and Groq",
            "version": "1.0.0",
            "url": f"http://localhost:{config.A2A_PORT}/a2a",
            "skills": [
                {
                    "name": "get_flight_status",
                    "description": "Get current flight status with normalized data and conversational summary",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "flight_num": {
                                "type": "string",
                                "description": "Flight designator (e.g., AA100)",
                                "pattern": "^[A-Z]{2,3}[0-9]{1,4}$"
                            },
                            "departure_date": {
                                "type": "string",
                                "description": "Departure date in YYYY-MM-DD format",
                                "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
                            },
                            "locale": {
                                "type": "string",
                                "description": "Locale for time formatting (e.g., en-US, en-GB)",
                                "default": "en-US"
                            }
                        },
                        "required": ["flight_num", "departure_date"]
                    },
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "raw": {
                                "type": "object",
                                "description": "Normalized flight data from FlightAware"
                            },
                            "script": {
                                "type": "object",
                                "description": "Conversational summary with text and SSML",
                                "properties": {
                                    "text": {"type": "string"},
                                    "ssml": {"type": "string"},
                                    "style": {"type": "string"},
                                    "locale": {"type": "string"}
                                }
                            },
                            "hash": {
                                "type": "string",
                                "description": "Hash of raw data for caching"
                            },
                            "generated_at": {
                                "type": "string",
                                "description": "ISO 8601 timestamp"
                            },
                            "schema_version": {
                                "type": "string",
                                "description": "Schema version identifier"
                            }
                        }
                    }
                }
            ],
            "metadata": {
                "provider": provider_name,
                "ai_model": "Groq llama-3.1-8b-instant",
                "capabilities": [
                    "Real-time flight tracking",
                    "AI-powered summaries",
                    "SSML for text-to-speech",
                    "Locale-aware formatting",
                    "Retry logic with exponential backoff"
                ]
            }
        }
    
    async def handle_get_flight_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_flight_status skill invocation."""
        
        try:
            # Validate params
            request = FlightStatusRequest(**params)
        except ValidationError as e:
            raise JsonRpcError(
                code=ErrorCode.INVALID_PARAMS,
                message="Invalid parameters",
                data={"validation_errors": e.errors()}
            )
        
        logger.info(f"Request: {request.flight_num} on {request.departure_date}")
        
        # Fetch from provider
        try:
            # MockProvider uses get_status, FlightAwareProvider uses fetch_status
            if hasattr(self.provider, 'fetch_status'):
                raw = await self.provider.fetch_status(
                    request.flight_num,
                    request.departure_date
                )
            else:
                raw = await self.provider.get_status(
                    request.flight_num,
                    request.departure_date
                )
        except ProviderError as e:
            logger.error(f"Provider error: {e}")
            raise JsonRpcError(
                code=ErrorCode.PROVIDER_ERROR,
                message="Flight data provider error",
                data={"details": str(e)}
            )
        except RuntimeError as e:
            logger.error(f"Provider error: {e}")
            raise JsonRpcError(
                code=ErrorCode.PROVIDER_ERROR,
                message="Flight data provider error",
                data={"details": str(e)}
            )
        
        # Generate summary
        try:
            script = await self.summarizer.summarize(raw, request.locale)
        except Exception as e:
            logger.warning(f"Summarizer error: {e}, using fallback")
            # Summarizer has built-in fallback, this shouldn't fail
            script = self.summarizer._fallback_summary(raw, request.locale)
        
        # Compute hash
        hash_value = compute_hash(raw)
        
        # Build result
        result = {
            "raw": raw.model_dump(),
            "script": script.model_dump(),
            "hash": hash_value,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "schema_version": "flight.status.v1"
        }
        
        logger.info(f"Success: {request.flight_num} status={raw.status}")
        
        return result
    
    async def handle_json_rpc(self, rpc_request: JsonRpcRequest) -> JsonRpcResponse:
        """Handle JSON-RPC 2.0 request."""
        
        try:
            # Route to appropriate skill
            if rpc_request.method == "get_flight_status":
                result = await self.handle_get_flight_status(rpc_request.params)
                return JsonRpcResponse(result=result, id=rpc_request.id)
            
            else:
                # Method not found
                return JsonRpcResponse(
                    error=JsonRpcError(
                        code=ErrorCode.METHOD_NOT_FOUND,
                        message=f"Method '{rpc_request.method}' not found",
                        data={"available_methods": ["get_flight_status"]}
                    ),
                    id=rpc_request.id
                )
        
        except JsonRpcError as e:
            return JsonRpcResponse(error=e, id=rpc_request.id)
        
        except Exception as e:
            logger.exception(f"Internal error: {e}")
            return JsonRpcResponse(
                error=JsonRpcError(
                    code=ErrorCode.INTERNAL_ERROR,
                    message="Internal server error",
                    data={"details": str(e)}
                ),
                id=rpc_request.id
            )


# Create FastAPI app
app = FastAPI(
    title="Guardian Buddy Flight Agent (A2A)",
    description="A2A-compliant flight status agent with FlightAware and Groq",
    version="1.0.0"
)

agent = A2AFlightAgent()


@app.get("/")
async def root():
    """Root endpoint with agent info."""
    return {
        "agent": "Guardian Buddy Flight Agent",
        "protocol": "A2A (Agent2Agent)",
        "version": "1.0.0",
        "endpoints": {
            "agent_card": "/agent.json",
            "rpc": "/a2a"
        }
    }


@app.get("/agent.json")
async def get_agent_card():
    """Return Agent Card for A2A discovery."""
    return JSONResponse(content=agent.agent_card)


@app.post("/a2a")
async def a2a_endpoint(request: Request):
    """A2A JSON-RPC 2.0 endpoint."""
    
    try:
        # Parse request body
        body = await request.body()
        data = json.loads(body)
        
        # Validate JSON-RPC request
        try:
            rpc_request = JsonRpcRequest(**data)
        except ValidationError as e:
            return JSONResponse(
                content=JsonRpcResponse(
                    error=JsonRpcError(
                        code=ErrorCode.INVALID_REQUEST,
                        message="Invalid JSON-RPC request",
                        data={"validation_errors": e.errors()}
                    ),
                    id=data.get("id")
                ).model_dump(),
                status_code=200
            )
        
        # Handle request
        response = await agent.handle_json_rpc(rpc_request)
        
        return JSONResponse(content=response.model_dump())
    
    except json.JSONDecodeError as e:
        return JSONResponse(
            content=JsonRpcResponse(
                error=JsonRpcError(
                    code=ErrorCode.PARSE_ERROR,
                    message="Parse error",
                    data={"details": str(e)}
                ),
                id=None
            ).model_dump(),
            status_code=200
        )
    
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return JSONResponse(
            content=JsonRpcResponse(
                error=JsonRpcError(
                    code=ErrorCode.INTERNAL_ERROR,
                    message="Internal server error",
                    data={"details": str(e)}
                ),
                id=None
            ).model_dump(),
            status_code=200
        )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "provider": config.PROVIDER,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting A2A Flight Agent on port {config.A2A_PORT}")
    logger.info(f"Provider: {config.PROVIDER}")
    logger.info(f"Agent Card: http://localhost:{config.A2A_PORT}/agent.json")
    logger.info(f"JSON-RPC Endpoint: http://localhost:{config.A2A_PORT}/a2a")
    
    uvicorn.run(app, host="0.0.0.0", port=config.A2A_PORT)

