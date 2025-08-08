# Enterprise Customer Support Agent Orchestrator

## Challenge Overview

Zangoh is building a multi-agent AI system for a B2B SaaS company called TechSolutions that sells cloud infrastructure management software. Your task is to build an agent orchestration system that can efficiently handle diverse customer inquiries.

**Time Allotted:** 3 hours

### Resources and Starter Code

All required files are available in this Google Drive folder: [PASTE GOOGLE DRIVE LINK HERE]

The folder contains:
- Knowledge base files (product catalog, documentation, FAQs, etc.)
- Starter code framework
- Docker configuration
- Testing scenarios
- Setup instructions

## Core Requirements

Design and implement a proof-of-concept multi-agent system that can:
- Classify and route customer inquiries to specialized agents
- Extract relevant information from multiple knowledge sources
- Coordinate between agents to provide comprehensive responses
- Call external tools/APIs when necessary
- Handle the mid-session requirement addition (see below)

### Detailed Architecture Requirements

1. **Router Agent**
   - Classify incoming customer inquiries by type
   - Route inquiries to appropriate specialized agents
   - Handle multi-part queries by breaking them down

2. **Product Specialist Agent**
   - Implement RAG to answer questions about products
   - Extract relevant product specifications from the catalog
   - Provide accurate comparisons between products when asked

3. **Technical Support Agent**
   - Diagnose common technical issues based on symptom descriptions
   - Suggest troubleshooting steps using the knowledge base
   - Escalate complex issues with appropriate contextual information

4. **Order/Billing Agent**
   - Query order status through the provided API
   - Answer billing-related questions
   - Format financial information appropriately

5. **Orchestration Layer**
   - Coordinate communication between agents
   - Synthesize responses from multiple agents when needed
   - Maintain conversation context across multiple turns


### Candidate Implementation Tasks

In the provided starter code, we have built the complete architecture with fully functional mock responses. Your task is to replace these mocks with actual implementations for the following components:

#### 1. Agent Implementations

- **Router Agent:**
  - Replace the mock classification logic with a robust natural language processing module that accurately categorizes incoming customer inquiries.
  - Ensure that multi-part queries are effectively segmented and routed to the appropriate agents.
  - **Note:** Rework the current demo logic to implement real routing and query segmentation functionalities.

- **Product Specialist Agent:**
  - Implement Retrieval-Augmented Generation (RAG) methods for answering product-related questions.
  - Replace the mock responses with logic that extracts and compares product specifications from the provided product catalog.
  - **Note:** Rewrite the current demo implementation to fetch and process actual product data.

- **Technical Support Agent:**
  - Implement logic to diagnose technical issues based on customer symptom descriptions.
  - Integrate troubleshooting steps from the knowledge base to provide actionable solutions.
  - Include an escalation mechanism that flags complex issues and provides relevant context.
  - **Note:** Update the current demo code to incorporate real diagnostic and troubleshooting procedures.

- **Order/Billing Agent:**
  - Replace mock order status and billing responses with actual API queries to fetch order statuses and billing information.
  - Format financial details as required and integrate with external systems via the provided API interfaces.
  - **Note:** Reconstruct the demo responses with production-level integration to handle live API data.

#### 2. Vector Store Setup

- **Vector Store Initialization:**
  - Run the provided `setup.py` script to initialize and configure the vector store.
  - Ensure that the ingestion process accurately indexes data from the knowledge base files (product catalog, technical documentation, FAQs, etc.) before any queries are processed.

#### 3. Orchestration & Server

- **Orchestration Layer Enhancements:**
  - Connect all agent implementations within the orchestration layer.
  - Ensure that each specialized agent collaborates effectively, sharing context and synthesizing responses where needed.
  - Update the orchestration logic to leverage actual data and external tool integrations instead of static mock responses.

- **Running the Server:**
  - Use the provided `main.py` to start the server.
  - Verify that the integrated agents can handle customer inquiries end-to-end, from classification to final response generation, while properly executing all underlying tool calls and external integrations.

#### 4. LLM Integration

- **Current Setup:**
  - The current setup uses the Ollama local model for inference.
  
- **Custom Inference Options:**
  - If you prefer to use another inference server or endpoint, feel free to modify the code in `agent_implementations.py` accordingly.
  - Ensure that any changes to the LLM integration maintain compatibility with the overall agent orchestration and communication flow.


#### 5. Folder and Code Overview

Below is the folder structure (excluding `chroma_db` and `venv` directories):
```
.
├── Dockerfile
├── agent_implementations.py        # Contains the structure for all agent logic (currently with mock responses)
├── chroma_db                     # Chromadb directory which is generated after the ingestion process
├── data
│   ├── customer_conversations.jsonl
│   ├── faq.json
│   ├── product_catalog.json
│   └── tech_documentation.md
├── data_utils.py                  # Utilities for data processing
├── main.py                        # Main server that coordinates all agents
├── readme.md
├── requirements.txt
├── setup.py                       # Script to setup and ingest data into the vector store
└── tests
    ├── automated_tester.py        # Automated test scripts to validate implementation
    └── test_scenarios.md          # Scenarios for testing your implementation

```

## Submission Requirements

1. Upload your complete solution to your Google Drive and provide the link below
2. Your submission should include:
   - All code files
   - A README with setup and running instructions
   - A brief explanation of your architecture (diagram encouraged)
   - A 5-minute video demonstration of your solution

3. **Important**: Please indicate in your submission at what time you opened the mid-session requirement.

## Evaluation Criteria

Your solution will be evaluated on:
- System Architecture (agent design, orchestration mechanism, extensibility)
- Technical Implementation (RAG implementation, API integration, data processing, code quality)
- Functionality (query handling accuracy, multi-agent coordination, mid-session requirement implementation)
- User Experience & Presentation (interface design, documentation quality)
