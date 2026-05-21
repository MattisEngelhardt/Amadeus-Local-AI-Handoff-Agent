import os
import logging
import json
import yaml
from anthropic import Anthropic
from dotenv import load_dotenv
from speech_to_code.models.requirements import RequirementsModel

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class TranscriptAnalyzer:
    def __init__(self, api_key=None, model="claude-3-5-sonnet-20241022", config_path=None, llm_provider="claude"):
        """
        Initialize the Transcript Analyzer.
        :param api_key: Optional API key.
        :param model: LLM model to use.
        :param config_path: Path to config.yaml to load default quality criteria.
        :param llm_provider: "claude" or "gemini".
        """
        load_dotenv()
        self.llm_provider = llm_provider or "claude"
        self.model = model
        self.client = None
        self.quality_criteria = []

        if self.llm_provider == "gemini":
            import google.generativeai as genai
            self.gemini_key = api_key or os.getenv("GEMINI_API_KEY")
            if not self.gemini_key:
                logger.warning("GEMINI_API_KEY not found in environment.")
            else:
                genai.configure(api_key=self.gemini_key)
        else:
            self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            if not self.api_key:
                logger.warning("Anthropic API key not found. Analysis will fail unless key is passed later or set in environment.")
            else:
                self.client = Anthropic(api_key=self.api_key)

        # Load default quality criteria from config if available
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                    self.quality_criteria = config.get("quality_criteria", [])
            except Exception as e:
                logger.error(f"Failed to load config for quality criteria: {e}")

    def analyze(self, transcript_text):
        """
        Analyzes a raw voice transcript and returns a structured RequirementsModel.
        :param transcript_text: Raw text transcribed from audio.
        :return: RequirementsModel instance, or None if analysis failed.
        """
        if not transcript_text:
            logger.error("Transcript text is empty.")
            return None

        # Prepare quality criteria context
        quality_context = ""
        if self.quality_criteria:
            quality_context = "\nEnsure the generated requirements enforce the following default quality guidelines:\n" + \
                              "\n".join([f"- {criterion}" for criterion in self.quality_criteria])

        system_prompt = f"""You are a Senior Project Architect. Your job is to analyze a raw transcript of a developer describing a project they want to build. 

You must extract and organize a structured, comprehensive project specification plan. 
To do this, analyze the user's intent, resolve ambiguities, and organize the requirements into a coherent design.
{quality_context}

IMPORTANT GUIDELINES:
1. Infer additional necessary files that the developer did not explicitly mention but are essential for a complete, production-ready, clean boilerplate structure (e.g. entrypoint scripts, CLI parser, main window code, helper classes, config loader, test cases).
2. Ensure the display name is clean and the project name is filesystem-friendly (e.g., kebab-case or snake_case).
3. Ensure all files listed in `files_to_create` are essential and have specific, clear purposes.
4. If the developer mentioned specific dependencies or frameworks, include them. Also add any standard helper dependencies (e.g. python-dotenv, PyYAML, pytest).
"""

        if self.llm_provider == "gemini":
            try:
                import google.generativeai as genai
                self.gemini_key = self.gemini_key or os.getenv("GEMINI_API_KEY")
                if not self.gemini_key:
                    logger.error("Cannot analyze: GEMINI_API_KEY is missing.")
                    return None
                genai.configure(api_key=self.gemini_key)

                logger.info("Sending transcript to Gemini for requirements extraction...")
                model_inst = genai.GenerativeModel(self.model)
                prompt = f"{system_prompt}\n\nHere is the raw audio transcript of the project description:\n\n{transcript_text}"
                
                response = model_inst.generate_content(
                    prompt,
                    generation_config={
                        "response_mime_type": "application/json",
                        "response_schema": RequirementsModel
                    }
                )
                
                data = json.loads(response.text)
                return RequirementsModel(**data)
            except Exception as e:
                logger.error(f"Error during Gemini API analysis: {e}")
                return None

        # Re-initialize client if api_key was provided later or loaded
        if not self.client:
            self.api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
            if not self.api_key:
                logger.error("Cannot analyze: Anthropic API key is missing. Please set ANTHROPIC_API_KEY.")
                return None
            self.client = Anthropic(api_key=self.api_key)

        logger.info("Sending transcript to Claude for requirements extraction...")
        try:
            # Force tool usage to get guaranteed structured JSON matching the Pydantic schema
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"Here is the raw audio transcript of the project description:\n\n{transcript_text}"}
                ],
                tools=[
                    {
                        "name": "save_requirements",
                        "description": "Saves the extracted structured project requirements.",
                        "input_schema": RequirementsModel.model_json_schema()
                    }
                ],
                tool_choice={"type": "tool", "name": "save_requirements"}
            )

            # Find the tool use block
            tool_use_block = None
            for block in response.content:
                if block.type == "tool_use" and block.name == "save_requirements":
                    tool_use_block = block
                    break

            if not tool_use_block:
                logger.error("Claude did not use the 'save_requirements' tool as requested.")
                return None

            requirements_data = tool_use_block.input
            logger.info("Successfully parsed requirements JSON from Claude response.")
            
            # Instantiate Pydantic model to validate and return
            requirements = RequirementsModel(**requirements_data)
            return requirements

        except Exception as e:
            logger.error(f"Error during Claude API analysis: {e}")
            return None

# Local manual testing
if __name__ == "__main__":
    sample_transcript = (
        "I want to make a simple stock tracking application in Python. It should use Streamlit for a simple web interface. "
        "The user should be able to type a stock ticker and see the current price and a history chart. "
        "For drawing the chart, let's use pandas and plotly. "
        "Also, we should fetch data from yfinance. "
        "Let's put the streamlit code in app.py, and the logic for fetching stock data in a module core/finance.py. "
        "Make sure to add some default stock tickers like AAPL and MSFT. "
        "I also want some basic unit tests using pytest."
    )
    
    analyzer = TranscriptAnalyzer()
    res = analyzer.analyze(sample_transcript)
    if res:
        print(json.dumps(res.model_dump(), indent=2))
