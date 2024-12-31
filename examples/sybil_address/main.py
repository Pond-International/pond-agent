from pond_agent import setup_logging
from pond_agent import CompetitionAgent

# For development - more verbose console output
setup_logging(console_level="INFO", file_level="DEBUG")

# Initialize the agent
agent = CompetitionAgent(
    working_dir=".",
    competition_url="https://cryptopond.xyz/modelFactory/detail/2",
    llm_provider="openai",
    model_name="gpt-4o"
)

# Run the agent and watch it to complete the whole model development pipeline
agent.run()