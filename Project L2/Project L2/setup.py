import argparse
import logging
import os

from agent_implementations import AgentOrchestrator, LLMUtils
from data_utils import DataManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def setup_environment():
    """Set up the environment for the agent orchestrator"""
    # Create necessary directories
    os.makedirs("data", exist_ok=True)
    os.makedirs("chroma_db", exist_ok=True)

    # Initialize data manager
    data_manager = DataManager()

    # Load knowledge base
    logger.info("Loading knowledge base...")
    knowledge_base = data_manager.load_knowledge_base()

    # Prepare vector database
    logger.info("Preparing vector database...")
    vector_db = data_manager.prepare_vector_db(knowledge_base)

    # Initialize LLM utils
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model_name = os.getenv("MODEL_NAME", "llama3:8b")
    llm_utils = LLMUtils(ollama_base_url, model_name)

    # Initialize agent orchestrator
    logger.info("Initializing agent orchestrator...")
    agent_orchestrator = AgentOrchestrator(llm_utils, knowledge_base, vector_db)

    logger.info("Environment setup complete")
    return agent_orchestrator


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Set up the TechSolutions Agent Orchestrator environment"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset the environment (delete existing data)",
    )

    args = parser.parse_args()

    if args.reset:
        logger.info("Resetting environment...")
        import shutil

        if os.path.exists("chroma_db"):
            shutil.rmtree("chroma_db")

    setup_environment()