import json
import logging
import os
from typing import Any, Dict, List, Tuple

import markdown
from chromadb import Collection, PersistentClient
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DataManager:
    def __init__(self, data_dir: str = "data", db_dir: str = "chroma_db"):
        self.data_dir = data_dir
        self.db_dir = db_dir

        # Initialize ChromaDB
        try:
            self.chroma_client = PersistentClient(
                path=db_dir, settings=Settings(anonymized_telemetry=False)
            )
            logger.info("ChromaDB initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise

    def load_knowledge_base(self) -> Dict[str, Any]:
        """Load and prepare knowledge base for agents"""
        try:
            # Load product catalog
            with open(os.path.join(self.data_dir, "product_catalog.json"), "r") as f:
                product_catalog = json.load(f)

            # Load FAQs
            with open(os.path.join(self.data_dir, "faq.json"), "r") as f:
                faqs = json.load(f)

            # Load tech documentation
            with open(os.path.join(self.data_dir, "tech_documentation.md"), "r") as f:
                tech_docs = f.read()

            # Load customer conversations
            customer_conversations = []
            with open(
                os.path.join(self.data_dir, "customer_conversations.jsonl"), "r"
            ) as f:
                for line in f:
                    if line.strip():  # Skip empty lines
                        customer_conversations.append(json.loads(line))

            logger.info("Knowledge base loaded successfully")
            return {
                "product_catalog": product_catalog,
                "faqs": faqs,
                "tech_docs": tech_docs,
                "customer_conversations": customer_conversations,
            }
        except Exception as e:
            logger.error(f"Failed to load knowledge base: {e}")
            raise

    def prepare_vector_db(
        self, knowledge_base: Dict[str, Any]
    ) -> Dict[str, Collection]:
        """Prepare vector database collections for each type of data"""
        collections = {}

        # Create text splitter for chunking documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=[
                "\n## ",
                "\n### ",
                "\n#### ",
                "\n",
                ". ",
                "! ",
                "? ",
                ";",
                ":",
                " ",
                "",
            ],
        )

        # Prepare product information collection
        collections["products"] = self._prepare_product_collection(
            knowledge_base["product_catalog"], knowledge_base["faqs"], text_splitter
        )

        # Prepare technical documentation collection
        collections["technical"] = self._prepare_technical_collection(
            knowledge_base["tech_docs"], text_splitter
        )

        # Prepare customer conversations collection
        collections["conversations"] = self._prepare_conversations_collection(
            knowledge_base["customer_conversations"], text_splitter
        )

        return collections

    def _prepare_product_collection(
        self, product_catalog: Dict[str, Any], faqs: Dict[str, Any], text_splitter
    ) -> Collection:
        """Prepare vector collection for product information"""
        try:
            # Create or get the collection
            collection = self.chroma_client.get_or_create_collection("products")

            # Check if collection already has documents
            if collection.count() > 0:
                logger.info("Products collection already populated, skipping")
                return collection

            # Process product catalog
            product_docs = []
            product_metadatas = []
            product_ids = []

            # Process main products
            for i, product in enumerate(product_catalog.get("products", [])):
                # Main product information
                product_text = f"""
                Product: {product.get('name')}
                ID: {product.get('id')}
                Description: {product.get('description')}
                
                Price:
                Monthly: ${product.get('price', {}).get('monthly', 'N/A')}
                Annual: ${product.get('price', {}).get('annual', 'N/A')}
                
                Features:
                {self._format_features(product.get('features', []))}
                
                Limitations:
                {self._format_list(product.get('limitations', []))}
                
                Target Audience: {product.get('target_audience', 'Not specified')}
                """
                chunks = text_splitter.split_text(product_text)

                for j, chunk in enumerate(chunks):
                    product_docs.append(chunk)
                    product_metadatas.append(
                        {
                            "type": "product",
                            "product_id": product.get("id", ""),
                            "product_name": product.get("name", ""),
                            "chunk": f"{i}-{j}",
                        }
                    )
                    product_ids.append(f"product-{product.get('id', '')}-{j}")

            # Process add-ons
            for i, addon in enumerate(product_catalog.get("addons", [])):
                addon_text = f"""
                Add-on: {addon.get('name')}
                ID: {addon.get('id')}
                Description: {addon.get('description')}
                
                Price: ${addon.get('price')}
                
                Details: {addon.get('details', 'No additional details')}
                """
                chunks = text_splitter.split_text(addon_text)

                for j, chunk in enumerate(chunks):
                    product_docs.append(chunk)
                    product_metadatas.append(
                        {
                            "type": "addon",
                            "addon_id": addon.get("id", ""),
                            "addon_name": addon.get("name", ""),
                            "chunk": f"{i}-{j}",
                        }
                    )
                    product_ids.append(f"addon-{addon.get('id', '')}-{j}")

            # Process bundles
            for i, bundle in enumerate(product_catalog.get("bundles", [])):
                bundle_text = f"""
                Bundle: {bundle.get('name')}
                ID: {bundle.get('id')}
                Description: {bundle.get('description')}
                
                Included Products: {', '.join(bundle.get('included_products', []))}
                
                Price:
                Monthly: ${bundle.get('price', {}).get('monthly', 'N/A')}
                Annual: ${bundle.get('price', {}).get('annual', 'N/A')}
                Savings: {bundle.get('price', {}).get('saving_percentage', 'N/A')}%
                """
                chunks = text_splitter.split_text(bundle_text)

                for j, chunk in enumerate(chunks):
                    product_docs.append(chunk)
                    product_metadatas.append(
                        {
                            "type": "bundle",
                            "bundle_id": bundle.get("id", ""),
                            "bundle_name": bundle.get("name", ""),
                            "chunk": f"{i}-{j}",
                        }
                    )
                    product_ids.append(f"bundle-{bundle.get('id', '')}-{j}")

            # Process FAQs
            for i, category in enumerate(faqs.get("categories", [])):
                category_name = category.get("name", "")

                for j, question in enumerate(category.get("questions", [])):
                    faq_text = f"""
                    Category: {category_name}
                    Question: {question.get('question')}
                    Answer: {question.get('answer')}
                    """
                    chunks = text_splitter.split_text(faq_text)

                    for k, chunk in enumerate(chunks):
                        product_docs.append(chunk)
                        product_metadatas.append(
                            {
                                "type": "faq",
                                "category": category_name,
                                "chunk": f"{i}-{j}-{k}",
                            }
                        )
                        product_ids.append(f"faq-{i}-{j}-{k}")

            # Add documents to collection
            collection.add(
                documents=product_docs, metadatas=product_metadatas, ids=product_ids
            )

            logger.info(
                f"Added {len(product_docs)} product documents to vector database"
            )
            return collection

        except Exception as e:
            logger.error(f"Error preparing product collection: {e}")
            raise

    def _prepare_technical_collection(
        self, tech_docs: str, text_splitter
    ) -> Collection:
        """Prepare vector collection for technical documentation"""
        try:
            # Create or get the collection
            collection = self.chroma_client.get_or_create_collection("technical")

            # Check if collection already has documents
            if collection.count() > 0:
                logger.info(
                    "Technical documentation collection already populated, skipping"
                )
                return collection

            # Split documentation into chunks
            html_doc = markdown.markdown(tech_docs)
            chunks = text_splitter.split_text(tech_docs)

            tech_docs = []
            tech_metadatas = []
            tech_ids = []

            for i, chunk in enumerate(chunks):
                # Extract section title if possible (simplified approach)
                lines = chunk.split("\n")
                section_title = "Technical Documentation"
                for line in lines:
                    if line.startswith("##"):
                        section_title = line.strip("# ")
                        break
                    elif line.startswith("#"):
                        section_title = line.strip("# ")

                tech_docs.append(chunk)
                tech_metadatas.append(
                    {"type": "technical_doc", "section": section_title, "chunk": f"{i}"}
                )
                tech_ids.append(f"tech-{i}")

            # Add documents to collection
            collection.add(documents=tech_docs, metadatas=tech_metadatas, ids=tech_ids)

            logger.info(
                f"Added {len(tech_docs)} technical documents to vector database"
            )
            return collection

        except Exception as e:
            logger.error(f"Error preparing technical collection: {e}")
            raise

    def _prepare_conversations_collection(
        self, conversations: List[Dict[str, Any]], text_splitter
    ) -> Collection:
        """Prepare vector collection for customer conversations"""
        try:
            # Create or get the collection
            collection = self.chroma_client.get_or_create_collection("conversations")

            # Check if collection already has documents
            if collection.count() > 0:
                logger.info("Conversations collection already populated, skipping")
                return collection

            conv_docs = []
            conv_metadatas = []
            conv_ids = []

            for i, conversation in enumerate(conversations):
                # Format full conversation
                conv_text = f"Conversation ID: {conversation.get('conversation_id')}\n"
                conv_text += f"Customer: {conversation.get('customer_email')}\n"
                conv_text += f"Agent: {conversation.get('agent_name')}\n\n"

                for j, message in enumerate(conversation.get("messages", [])):
                    role = message.get("role", "")
                    content = message.get("content", "")
                    conv_text += f"{role.capitalize()}: {content}\n\n"

                # Split conversation into chunks
                chunks = text_splitter.split_text(conv_text)

                for j, chunk in enumerate(chunks):
                    conv_docs.append(chunk)
                    conv_metadatas.append(
                        {
                            "type": "conversation",
                            "conversation_id": conversation.get("conversation_id", ""),
                            "customer_email": conversation.get("customer_email", ""),
                            "agent_name": conversation.get("agent_name", ""),
                            "chunk": f"{i}-{j}",
                        }
                    )
                    conv_ids.append(
                        f"conv-{conversation.get('conversation_id', '')}-{j}"
                    )

            # Add documents to collection
            collection.add(documents=conv_docs, metadatas=conv_metadatas, ids=conv_ids)

            logger.info(
                f"Added {len(conv_docs)} conversation documents to vector database"
            )
            return collection

        except Exception as e:
            logger.error(f"Error preparing conversations collection: {e}")
            raise

    def _format_features(self, features: List[Dict[str, str]]) -> str:
        """Format product features into a readable string"""
        if not features:
            return "No features specified"

        result = ""
        for feature in features:
            name = feature.get("name", "Unnamed Feature")
            description = feature.get("description", "No description available")
            result += f"- {name}: {description}\n"

        return result

    def _format_list(self, items: List[str]) -> str:
        """Format a list of strings into a bullet-point string"""
        if not items:
            return "None specified"

        return "\n".join([f"- {item}" for item in items])
