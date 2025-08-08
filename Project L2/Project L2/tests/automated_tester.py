import argparse
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Tuple

import matplotlib.pyplot as plt
import pandas as pd
import requests
from tabulate import tabulate

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AgentTester:
    def __init__(
        self, api_url: str, ollama_url: str, model_name: str, verbose: bool = False
    ):
        self.api_url = api_url
        self.ollama_url = ollama_url
        self.model_name = model_name
        self.verbose = verbose
        self.session = requests.Session()

        # Test cases organized by agent type and scenario
        self.test_cases = self._load_test_cases()

        # Track conversation IDs for multi-turn conversations
        self.conversations = {}

        # Results tracking
        self.results = []

    def _load_test_cases(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load test cases from JSON file"""
        with open("test_cases.json", "r") as f:
            return json.load(f)

    def _evaluate_response(
        self,
        query: str,
        actual_response: str,
        expected_output: str,
        criteria: Dict[str, Any],
        agent_type: str,
    ) -> Dict[str, Any]:
        """Use the LLM to evaluate a response against expected criteria"""
        prompt = f"""
        You are evaluating an AI agent's response to a customer support query.

        QUERY:
        {query}

        ACTUAL RESPONSE:
        {actual_response}

        EXPECTED PATTERNS:
        {expected_output}

        Please evaluate the response based on the following criteria:
        1. Accuracy (0-10): Does the response contain correct information?
        2. Completeness (0-10): Does the response address all aspects of the query?
        3. Relevance (0-10): Is the response focused on answering the specific question?
        4. Clarity (0-10): Is the response clear and easy to understand?
        5. Agent appropriateness (0-10): Was this handled by the appropriate agent type? The system identified it as "{agent_type}".

        Respond with a JSON object containing:
        {{
            "accuracy": score,
            "completeness": score,
            "relevance": score,
            "clarity": score,
            "agent_appropriateness": score,
            "total_score": sum_of_scores,
            "percentage": percentage_of_max_possible,
            "strengths": ["list", "of", "strengths"],
            "weaknesses": ["list", "of", "weaknesses"],
            "passed": true/false
        }}
        
        Only respond with the JSON, nothing else.
        """

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.model_name, "prompt": prompt},
            )
            response.raise_for_status()

            # Extract the generated text
            llm_response = response.json().get("response", "")

            # Parse the JSON response
            try:
                # Find the JSON object in the response
                json_str = llm_response.strip()
                if not json_str.startswith("{"):
                    # Try to find JSON in the response
                    start_idx = llm_response.find("{")
                    end_idx = llm_response.rfind("}") + 1
                    if start_idx >= 0 and end_idx > start_idx:
                        json_str = llm_response[start_idx:end_idx]

                evaluation = json.loads(json_str)
                return evaluation
            except json.JSONDecodeError as e:
                logger.error(
                    f"Failed to parse evaluation response: {e}\nResponse: {llm_response}"
                )
                return {
                    "accuracy": 0,
                    "completeness": 0,
                    "relevance": 0,
                    "clarity": 0,
                    "agent_appropriateness": 0,
                    "total_score": 0,
                    "percentage": 0,
                    "strengths": [],
                    "weaknesses": ["Failed to evaluate response"],
                    "passed": False,
                }
        except Exception as e:
            logger.error(f"Error evaluating response: {e}")
            return {
                "accuracy": 0,
                "completeness": 0,
                "relevance": 0,
                "clarity": 0,
                "agent_appropriateness": 0,
                "total_score": 0,
                "percentage": 0,
                "strengths": [],
                "weaknesses": [f"Evaluation error: {str(e)}"],
                "passed": False,
            }

    def run_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single test case and evaluate the response"""
        query = test_case["query"]
        expected_output = test_case["expected_output"]
        category = test_case["category"]
        test_id = test_case["id"]
        criteria = test_case.get("criteria", {})

        # Generate a conversation ID for this test if not already present
        if test_id not in self.conversations:
            self.conversations[test_id] = f"test-{test_id}-{int(time.time())}"

        # Send the query to the API
        try:
            response = self.session.post(
                f"{self.api_url}/api/query",
                json={"query": query, "conversation_id": self.conversations[test_id]},
            )
            response.raise_for_status()

            # Parse the response
            api_response = response.json()
            actual_response = api_response.get("response", "")
            agent_type = api_response.get("agent", "unknown")

            # Log the test if verbose mode is enabled
            if self.verbose:
                logger.info(f"Test ID: {test_id}")
                logger.info(f"Query: {query}")
                logger.info(f"Response (from {agent_type}):\n{actual_response}")

            # Evaluate the response
            evaluation = self._evaluate_response(
                query, actual_response, expected_output, criteria, agent_type
            )

            # Create the result entry
            result = {
                "id": test_id,
                "category": category,
                "query": query,
                "expected_output": expected_output,
                "actual_response": actual_response,
                "agent_type": agent_type,
                "evaluation": evaluation,
            }

            return result
        except Exception as e:
            logger.error(f"Error running test {test_id}: {e}")
            return {
                "id": test_id,
                "category": category,
                "query": query,
                "expected_output": expected_output,
                "actual_response": f"Error: {str(e)}",
                "agent_type": "error",
                "evaluation": {
                    "accuracy": 0,
                    "completeness": 0,
                    "relevance": 0,
                    "clarity": 0,
                    "agent_appropriateness": 0,
                    "total_score": 0,
                    "percentage": 0,
                    "strengths": [],
                    "weaknesses": [f"Test execution error: {str(e)}"],
                    "passed": False,
                },
            }

    def run_tests(self, categories: List[str] = None, concurrent: bool = False):
        """Run all test cases, optionally filtering by category"""
        all_tests = []

        # Flatten the test cases and filter by category if specified
        for category, tests in self.test_cases.items():
            if categories is None or category in categories:
                for test in tests:
                    test["category"] = category
                    all_tests.append(test)

        logger.info(f"Running {len(all_tests)} tests...")

        # Run tests concurrently or sequentially
        if concurrent:
            with ThreadPoolExecutor(max_workers=5) as executor:
                self.results = list(executor.map(self.run_test, all_tests))
        else:
            self.results = [self.run_test(test) for test in all_tests]

        logger.info("Testing completed")

    def generate_report(self, output_path: str = "test_results"):
        """Generate a comprehensive test report"""
        if not self.results:
            logger.error("No test results available. Run tests first.")
            return

        # Create output directory if it doesn't exist
        os.makedirs(output_path, exist_ok=True)

        # Generate summary statistics
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["evaluation"]["passed"])
        pass_rate = passed_tests / total_tests * 100 if total_tests > 0 else 0

        avg_scores = {
            "accuracy": sum(r["evaluation"]["accuracy"] for r in self.results)
            / total_tests,
            "completeness": sum(r["evaluation"]["completeness"] for r in self.results)
            / total_tests,
            "relevance": sum(r["evaluation"]["relevance"] for r in self.results)
            / total_tests,
            "clarity": sum(r["evaluation"]["clarity"] for r in self.results)
            / total_tests,
            "agent_appropriateness": sum(
                r["evaluation"]["agent_appropriateness"] for r in self.results
            )
            / total_tests,
            "overall": sum(r["evaluation"]["percentage"] for r in self.results)
            / total_tests,
        }

        # Results by category
        category_results = {}
        for result in self.results:
            category = result["category"]
            if category not in category_results:
                category_results[category] = {"total": 0, "passed": 0, "score": 0}

            category_results[category]["total"] += 1
            if result["evaluation"]["passed"]:
                category_results[category]["passed"] += 1
            category_results[category]["score"] += result["evaluation"]["percentage"]

        # Calculate averages
        for category in category_results:
            total = category_results[category]["total"]
            if total > 0:
                category_results[category]["pass_rate"] = (
                    category_results[category]["passed"] / total * 100
                )
                category_results[category]["avg_score"] = (
                    category_results[category]["score"] / total
                )
            else:
                category_results[category]["pass_rate"] = 0
                category_results[category]["avg_score"] = 0

        # Create detailed report
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "pass_rate": pass_rate,
                "average_scores": avg_scores,
            },
            "category_results": category_results,
            "test_results": self.results,
        }

        # Write JSON report
        with open(os.path.join(output_path, "test_results.json"), "w") as f:
            json.dump(report, f, indent=2)

        # Generate human-readable summary
        with open(os.path.join(output_path, "summary_report.md"), "w") as f:
            f.write("# Automated Test Results Summary\n\n")

            f.write("## Overall Summary\n\n")
            f.write(f"- Total Tests: {total_tests}\n")
            f.write(f"- Passed Tests: {passed_tests}\n")
            f.write(f"- Pass Rate: {pass_rate:.2f}%\n\n")

            f.write("## Average Scores\n\n")
            f.write(f"- Accuracy: {avg_scores['accuracy']:.2f}/10\n")
            f.write(f"- Completeness: {avg_scores['completeness']:.2f}/10\n")
            f.write(f"- Relevance: {avg_scores['relevance']:.2f}/10\n")
            f.write(f"- Clarity: {avg_scores['clarity']:.2f}/10\n")
            f.write(
                f"- Agent Appropriateness: {avg_scores['agent_appropriateness']:.2f}/10\n"
            )
            f.write(f"- Overall Score: {avg_scores['overall']:.2f}%\n\n")

            f.write("## Results by Category\n\n")

            categories_table = []
            for category, results in category_results.items():
                categories_table.append(
                    [
                        category,
                        f"{results['passed']}/{results['total']}",
                        f"{results['pass_rate']:.2f}%",
                        f"{results['avg_score']:.2f}%",
                    ]
                )

            f.write(
                tabulate(
                    categories_table,
                    headers=["Category", "Passed/Total", "Pass Rate", "Avg Score"],
                    tablefmt="pipe",
                )
            )
            f.write("\n\n")

            f.write("## Failed Tests\n\n")
            failed_tests = [r for r in self.results if not r["evaluation"]["passed"]]

            if failed_tests:
                for i, test in enumerate(failed_tests, 1):
                    f.write(f"### {i}. Test ID: {test['id']} ({test['category']})\n\n")
                    f.write(f"**Query:** {test['query']}\n\n")
                    f.write(f"**Agent:** {test['agent_type']}\n\n")
                    f.write("**Weaknesses:**\n")
                    for weakness in test["evaluation"]["weaknesses"]:
                        f.write(f"- {weakness}\n")
                    f.write("\n")
                    f.write(f"**Score:** {test['evaluation']['percentage']:.2f}%\n\n")
                    f.write("---\n\n")
            else:
                f.write("No failed tests! 🎉\n\n")

        # Generate visual report
        self._generate_visual_report(output_path, report)

        logger.info(f"Report generated in {output_path}")

        return report["summary"]["average_scores"]["overall"]

    def _generate_visual_report(self, output_path: str, report: Dict[str, Any]):
        """Generate visual representations of test results"""
        try:
            # Create category results chart
            categories = list(report["category_results"].keys())
            pass_rates = [
                report["category_results"][c]["pass_rate"] for c in categories
            ]
            avg_scores = [
                report["category_results"][c]["avg_score"] for c in categories
            ]

            plt.figure(figsize=(10, 6))
            x = range(len(categories))
            width = 0.35

            plt.bar(
                [i - width / 2 for i in x], pass_rates, width, label="Pass Rate (%)"
            )
            plt.bar(
                [i + width / 2 for i in x], avg_scores, width, label="Avg Score (%)"
            )

            plt.xlabel("Category")
            plt.ylabel("Percentage")
            plt.title("Test Results by Category")
            plt.xticks(x, categories, rotation=45)
            plt.legend()
            plt.tight_layout()

            plt.savefig(os.path.join(output_path, "category_results.png"))

            # Create radar chart for average scores
            score_categories = [
                "Accuracy",
                "Completeness",
                "Relevance",
                "Clarity",
                "Agent Appropriateness",
            ]
            score_values = [
                report["summary"]["average_scores"]["accuracy"] / 10 * 100,
                report["summary"]["average_scores"]["completeness"] / 10 * 100,
                report["summary"]["average_scores"]["relevance"] / 10 * 100,
                report["summary"]["average_scores"]["clarity"] / 10 * 100,
                report["summary"]["average_scores"]["agent_appropriateness"] / 10 * 100,
            ]

            # Create radar chart
            angles = np.linspace(
                0, 2 * np.pi, len(score_categories), endpoint=False
            ).tolist()
            angles += angles[:1]  # Close the loop

            score_values += score_values[:1]  # Close the loop

            fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
            ax.plot(angles, score_values, "o-", linewidth=2)
            ax.fill(angles, score_values, alpha=0.25)
            ax.set_thetagrids(np.degrees(angles[:-1]), score_categories)
            ax.set_ylim(0, 100)
            ax.grid(True)
            ax.set_title("Evaluation Criteria Scores", size=20, y=1.05)

            plt.tight_layout()
            plt.savefig(os.path.join(output_path, "evaluation_radar.png"))

        except Exception as e:
            logger.error(f"Error generating visual report: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Automated testing for TechSolutions Support Agent Orchestrator"
    )
    parser.add_argument(
        "--api-url", default="http://localhost:8000", help="URL of the agent API"
    )
    parser.add_argument(
        "--ollama-url", default="http://localhost:11434", help="URL of the Ollama API"
    )
    parser.add_argument(
        "--model", default="llama3:8b", help="LLM model to use for evaluation"
    )
    parser.add_argument("--categories", nargs="+", help="Categories of tests to run")
    parser.add_argument(
        "--output", default="test_results", help="Output directory for test results"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument(
        "--concurrent", action="store_true", help="Run tests concurrently"
    )

    args = parser.parse_args()

    # Create and run the tester
    tester = AgentTester(args.api_url, args.ollama_url, args.model, args.verbose)
    tester.run_tests(args.categories, args.concurrent)
    overall_score = tester.generate_report(args.output)

    print(f"\nTesting completed. Overall score: {overall_score:.2f}%")
    print(f"Detailed results available in: {args.output}")


if __name__ == "__main__":
    main()
