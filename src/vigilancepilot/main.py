"""
Main CLI entry point for VigilancePilot.
"""

import typer
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel

from vigilancepilot.config import load_config
from vigilancepilot.utils.logging import setup_logging, get_logger
from vigilancepilot.detection.aggregator import ValidationAggregator
from vigilancepilot.integrations.postman_client import PostmanClient
from vigilancepilot.models import TestCase, TestPlan  # test planning models


logger = get_logger(__name__)

app = typer.Typer(help="VigilancePilot – Agentic API Quality Coach")


# ---------------------------
# Helper Functions
# ---------------------------


def build_basic_test_plan(requirement: str) -> TestPlan:
    """
    Internal helper to create a deterministic 3-case TestPlan.

    This keeps the logic in one place so both:
      - `plan`
      - `export-postman`
    can reuse it without duplicating code.
    """

    # ---------------------
    # 1) Happy path
    # ---------------------
    happy = TestCase(
        id="TC-HAPPY-001",
        category="happy",
        description=f"Happy path scenario for: {requirement}",
        steps=[
            "Prepare valid request payload and headers",
            "Send request to the correct endpoint",
            "Verify response status code indicates success (e.g., 200/201)",
            "Verify response body matches the expected schema/fields",
        ],
        expected_result="API returns a success response with correct schema and values.",
    )

    # ---------------------
    # 2) Negative path
    # ---------------------
    negative = TestCase(
        id="TC-NEG-001",
        category="negative",
        description=f"Failure scenario for: {requirement}",
        steps=[
            "Prepare invalid or missing fields in the request payload",
            "Send request to the same endpoint",
            "Verify response status code is a 4xx client error",
            "Verify error message is clear and does not leak internal details",
        ],
        expected_result="API returns a 4xx error with a clear, user-safe error message.",
    )

    # ---------------------
    # 3) Boundary case
    # ---------------------
    boundary = TestCase(
        id="TC-BND-001",
        category="boundary",
        description=f"Boundary scenario for: {requirement}",
        steps=[
            "Prepare edge-case values (e.g., min/max length, empty strings, limits)",
            "Send request with these edge-case values",
            "Verify response is either successful OR a well-defined validation error",
        ],
        expected_result="API behaves predictably when given edge-case values.",
    )

    # Assemble TestPlan
    return TestPlan(
        requirement=requirement,
        generated_cases=[happy, negative, boundary],
    )


# ---------------------------
# Data Models
# ---------------------------


class Requirement(BaseModel):
    description: str


# ---------------------------
# Test planning data models
# ---------------------------


class TestCase(BaseModel):
    """
    Represents a single API test case.

    Fields:
      - id:            Stable identifier for the test case (e.g., "TC-HAPPY-001").
      - category:      Type of test such as "happy", "negative", "boundary".
      - description:   Human-readable explanation of what this test verifies.
      - steps:         Ordered list of high-level steps the test will perform.
      - expected_result: What we expect the API to return / do.
    """
    id: str
    category: str
    description: str
    steps: List[str]
    expected_result: str


class TestPlan(BaseModel):
    """
    Groups all generated test cases for a single requirement.

    Fields:
      - requirement:      Original natural-language requirement text.
      - generated_cases:  List of concrete TestCase objects derived from it.
    """
    requirement: str
    generated_cases: List[TestCase]


@app.command()
def interpret(requirement: str):
    """
    First tiny command:
    Takes a natural-language requirement and confirms the agent received it.
    Next steps will expand this into structured test plans.
    """
    req = Requirement(description=requirement)

    typer.echo("📘 VigilancePilot Requirement Intake")
    typer.echo("----------------------------------")
    typer.echo(f"Raw requirement: {req.description}")
    typer.echo("\nStatus: Received ✓")
    typer.echo("Next: Generate test plan (coming in future bytes).")


@app.command()
def plan(requirement: str):
    """
    Generate a deterministic test plan skeleton for a requirement.

    This version is intentionally simple and does NOT call any LLM.
    It just produces 3 generic test cases:
      - happy path
      - negative path
      - boundary case
    """
    # Re-use the shared helper so logic stays in one place.
    plan_obj = build_basic_test_plan(requirement)

    typer.echo("📘 VigilancePilot Test Plan")
    typer.echo("----------------------------------")
    # Pretty-print JSON so it's easy to read or redirect to a file.
    typer.echo(plan_obj.model_dump_json(indent=2))


@app.command("export-postman")
def export_postman(
    requirement: str,
    output_dir: str = "generated/postman",
):
    """
    Generate a basic TestPlan from a requirement and export it
    as a Postman v2.1 collection JSON file.

    Usage example:
        python -m vigilancepilot.main export-postman "User must be able to login"

    The generated file will be written under:
        <project_root>/<output_dir>/vigilancepilot_<timestamp>.postman_collection.json
    """
    from vigilancepilot.postman_gen import export_postman_collection

    # 1) Build the deterministic test plan (same as `plan` command)
    test_plan = build_basic_test_plan(requirement)

    # 2) Resolve the output directory relative to the project root.
    #    Here we treat `output_dir` as relative to where you run the command.
    output_path = export_postman_collection(
        test_plan=test_plan,
        output_dir=Path(output_dir),
    )

    # 3) Print a friendly summary to the CLI.
    typer.echo("📦 VigilancePilot – Postman Collection Export")
    typer.echo("----------------------------------------")
    typer.echo(f"Requirement: {requirement}")
    typer.echo(f"Output file: {output_path}")
    typer.echo("")
    typer.echo("Next steps in Postman:")
    typer.echo("  1. Open Postman Desktop.")
    typer.echo("  2. Click 'Import'.")
    typer.echo("  3. Select the generated .postman_collection.json file.")
    typer.echo("  4. Edit HTTP method, URL path, and request body per endpoint.")


@app.command()
def validate(
    collection: str = typer.Option(..., "--collection", "-c", help="Postman collection ID"),
    config: Optional[str] = typer.Option(None, "--config", "-cfg", help="Config file path"),
    threshold: float = typer.Option(0.75, "--threshold", "-t", help="Confidence threshold"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging")
):
    """Validate a Postman collection."""
    setup_logging(debug=debug)
    logger.info("Starting validation", collection_id=collection, threshold=threshold)
    
    try:
        # Load configuration
        cfg = load_config(config)
        
        # Initialize clients
        postman = PostmanClient(api_key=cfg.postman_api_key)
        aggregator = ValidationAggregator(config=cfg)
        
        # Fetch collection
        collection_data = postman.get_collection(collection)
        logger.info("Fetched collection", name=collection_data.get("name"))
        
        # Run validation
        results = aggregator.validate_collection(collection_data, threshold=threshold)
        
        # Display results
        typer.echo(f"\n{'='*60}")
        typer.echo(f"Validation Results for: {collection_data.get('name')}")
        typer.echo(f"{'='*60}\n")
        
        for result in results:
            status = "✓" if result.passed else "✗"
            typer.echo(f"{status} {result.name} (confidence: {result.confidence:.2f})")
            if not result.passed:
                typer.echo(f"  Issue: {result.issue_description}")
        
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        typer.echo(f"\n{passed}/{total} checks passed")
        
        if passed < total:
            raise typer.Exit(1)
            
    except Exception as e:
        logger.error("Validation failed", error=str(e))
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def eval(
    scenario: str = typer.Option(..., "--scenario", "-s", help="Evaluation scenario name"),
    config: Optional[str] = typer.Option(None, "--config", "-cfg", help="Config file path"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging")
):
    """Run evaluation scenarios."""
    setup_logging(debug=debug)
    logger.info("Starting evaluation", scenario=scenario)
    
    try:
        from vigilancepilot.evals.scenarios import run_scenario
        
        cfg = load_config(config)
        results = run_scenario(scenario, cfg)
        
        typer.echo(f"\n{'='*60}")
        typer.echo(f"Evaluation: {scenario}")
        typer.echo(f"{'='*60}\n")
        typer.echo(f"Results: {results}")
        
    except Exception as e:
        logger.error("Evaluation failed", error=str(e))
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def init(output: str = typer.Option("config.yaml", "--output", "-o", help="Output file path")):
    """Initialize a new configuration file."""
    import yaml
    
    config_template = {
        "llm": {
            "provider": "openai",
            "model": "gpt-4-turbo-preview"
        },
        "thresholds": {
            "confidence": 0.75,
            "severity": "medium"
        },
        "rules": {
            "check_auth": True,
            "check_rate_limits": True,
            "check_error_handling": True
        }
    }
    
    output_path = Path(output)
    with open(output_path, "w") as f:
        yaml.dump(config_template, f, default_flow_style=False)
    
    typer.echo(f"Created config file: {output_path}")


if __name__ == "__main__":
    app()
