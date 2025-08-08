import json
import logging
import os
from typing import Any, Dict, List, Optional

import uvicorn
from chromadb import PersistentClient
from chromadb.config import Settings
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agent_implementations import LLMUtils
from agent_implementations import AgentOrchestrator
from data_utils import DataManager  # Add this import

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="TechSolutions Support Agent Orchestrator")

# Initialize Data Manager
try:
    data_manager = DataManager(
        data_dir=os.getenv("DATA_DIR", "data"),
        db_dir=os.getenv("DB_DIR", "chroma_db")
    )
    logger.info("DataManager initialized successfully")
    
    # Load knowledge base and prepare vector DB
    knowledge_base = data_manager.load_knowledge_base()
    vector_db = data_manager.prepare_vector_db(knowledge_base)
    logger.info("Vector databases initialized with collections")
    
except Exception as e:
    logger.error(f"Data initialization failed: {e}")
    knowledge_base = None
    vector_db = None



OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "gemma3:1b")


# Initialize LLM utils
try:
    llm = LLMUtils(
        base_url=OLLAMA_BASE_URL,
        model_name=MODEL_NAME,
    )
    logger.info("LLM initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize LLM: {e}")
    llm = None

# Initialize Agent Orchestrator
if llm and knowledge_base and vector_db:
    agent_orchestrator = AgentOrchestrator(
        llm_utils=llm,
        knowledge_base=knowledge_base,
        vector_db=vector_db
    )
    logger.info("Agent Orchestrator initialized successfully")
else:
    agent_orchestrator = None
    logger.error("Failed to initialize Agent Orchestrator due to missing components")


# Define API models
class CustomerQuery(BaseModel):
    query: str
    conversation_id: Optional[str] = None


class AgentResponse(BaseModel):
    response: str
    agent: str
    conversation_id: str


@app.get("/")
async def root():
    return {"message": "Backend is running"}

@app.post("/api/query", response_model=AgentResponse)
async def process_customer_query(query: CustomerQuery):
    """Process a customer support query"""
    try:
        if not agent_orchestrator:
            raise HTTPException(status_code=500, detail="System not initialized properly")
            
        result = await agent_orchestrator.process_query(query.query, query.conversation_id)
        return result
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Mock API endpoints for testing
@app.get("/api/orders/{order_id}")
async def get_order(order_id: str):
    """Mock Order API endpoint"""
    # Mock order data
    orders = {
        "ORD-12345": {
            "order_id": "ORD-12345",
            "status": "shipped",
            "items": [{"product_id": "cm-pro", "quantity": 1, "price": 149.99}],
            "total": 149.99,
            "order_date": "2023-09-10",
            "shipping_date": "2023-09-12",
            "delivery_date": "2023-09-15",
        },
        "ORD-56789": {
            "order_id": "ORD-56789",
            "status": "processing",
            "items": [
                {"product_id": "cm-enterprise", "quantity": 1, "price": 499.99},
                {"product_id": "addon-premium-support", "quantity": 1, "price": 299.99},
            ],
            "total": 799.98,
            "order_date": "2023-09-22",
            "shipping_date": None,
            "delivery_date": None,
        },
    }

    if order_id in orders:
        return orders[order_id]
    else:
        raise HTTPException(status_code=404, detail="Order not found")


@app.get("/api/accounts/{account_id}")
async def get_account(account_id: str):
    """Mock Account API endpoint"""
    # Mock account data
    accounts = {
        "ACC-1111": {
            "account_id": "ACC-1111",
            "name": "Acme Corp",
            "subscription": {
                "plan": "cm-pro",
                "status": "active",
                "start_date": "2023-01-15",
                "renewal_date": "2024-01-15",
                "payment_method": "credit_card",
                "auto_renew": True,
            },
            "users": [
                {"email": "admin@acme.example.com", "role": "admin"},
                {"email": "user1@acme.example.com", "role": "viewer"},
                {"email": "user2@acme.example.com", "role": "operator"},
            ],
        },
        "ACC-2222": {
            "account_id": "ACC-2222",
            "name": "Globex Inc",
            "subscription": {
                "plan": "cm-enterprise",
                "status": "active",
                "start_date": "2023-03-10",
                "renewal_date": "2024-03-10",
                "payment_method": "invoice",
                "auto_renew": False,
            },
            "users": [
                {"email": "admin@globex.example.com", "role": "admin"},
                {"email": "finance@globex.example.com", "role": "billing"},
                {"email": "security@globex.example.com", "role": "security_admin"},
                {"email": "devops@globex.example.com", "role": "operator"},
            ],
        },
    }

    if account_id in accounts:
        return accounts[account_id]
    else:
        raise HTTPException(status_code=404, detail="Account not found")


@app.post("/api/diagnose")
async def diagnose_issue(request: Request):
    """Mock troubleshooting API endpoint"""
    try:
        data = await request.json()
        logger.info(f"Received diagnose request data: {data}")
        logger.info("********************************************")
        issue_description = data.get("description", "")

        # Simple keyword matching for demo purposes
        if "error e1234" in issue_description.lower():
            return {
                "issue_id": "E1234",
                "name": "API Connection Failure",
                "solutions": [
                    "Verify API credentials in Settings > Connections",
                    "Check if your firewall allows outbound connections to cloud provider APIs",
                    "Ensure cloud provider services are operational",
                ],
                "documentation_link": "docs.techsolutions.example.com/errors/e1234",
            }
        elif "error e5678" in issue_description.lower():
            return {
                "issue_id": "E5678",
                "name": "Container Image Verification Failed",
                "solutions": [
                    "Check image integrity and re-pull from registry",
                    "Verify signature configuration in Security > Image Signing",
                    "Review scan results in Security > Vulnerability Reports",
                ],
                "documentation_link": "docs.techsolutions.example.com/errors/e5678",
            }
        else:
            return {
                "issue_id": "unknown",
                "name": "Unrecognized Issue",
                "solutions": [
                    "Check application logs for specific error messages",
                    "Verify your configuration settings",
                    "Contact support with error details for assistance",
                ],
                "documentation_link": "docs.techsolutions.example.com/troubleshooting",
            }
    except Exception as e:
        logger.error(f"Error in diagnose endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Custom exception handler
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )


# Application startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up Support Agent Orchestrator")
    # Add any additional startup tasks here


# Application shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Support Agent Orchestrator")
    # Add any cleanup tasks here


# Add a simple health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
