import os
import logging
import json
from anthropic import Anthropic
from dotenv import load_dotenv
from speech_to_code.models.requirements import RequirementsModel

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class RequirementsValidator:
    def __init__(self, api_key=None, model="claude-3-5-sonnet-20241022", llm_provider="claude"):
        """
        Initialize the Requirements Validator.
        :param api_key: Optional API key.
        :param model: LLM model to use.
        :param llm_provider: "claude" or "gemini".
        """
        load_dotenv()
        self.llm_provider = llm_provider or "claude"
        self.model = model
        self.client = None

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
                logger.warning("Anthropic API key not found. Validation will fail unless key is passed later or set in environment.")
            else:
                self.client = Anthropic(api_key=self.api_key)

    def validate(self, original_transcript, requirements: RequirementsModel, max_iterations=2):
        """
        Validates requirements against the original transcript, correcting any issues found.
        :param original_transcript: The raw voice transcription.
        :param requirements: The current RequirementsModel to validate.
        :param max_iterations: Maximum correction loops.
        :return: A validated/corrected RequirementsModel.
        """
        current_requirements = requirements
        
        system_prompt = """You are a Quality Assurance Agent and Auditor. Your job is to verify that a structured project plan (RequirementsModel) accurately and completely represents the original developer's intent as expressed in a raw audio transcript.

You must double-check:
1. Complete Coverage: Were all specific feature requests, databases, libraries, or integration requests from the transcript captured?
2. Technical Accuracy: Did the analyzer misinterpret any libraries, languages, or structures?
3. Avoid Over-scaffolding: Did the analyzer add files or features that contradict the user's intent? (Adding logical helper files like a README, config, or tests is encouraged, but adding completely unrelated functionality is not allowed).

If you find missing features, errors, or gaps, you MUST generate an updated, corrected requirements model.
If the current requirements model is 100% complete and accurate, return the existing data without changing it.
"""

        if self.llm_provider == "gemini":
            for iteration in range(1, max_iterations + 1):
                logger.info(f"Starting Gemini validation loop iteration {iteration}/{max_iterations}...")
                try:
                    import google.generativeai as genai
                    self.gemini_key = self.gemini_key or os.getenv("GEMINI_API_KEY")
                    if not self.gemini_key:
                        logger.error("Cannot validate: GEMINI_API_KEY is missing.")
                        return current_requirements
                    genai.configure(api_key=self.gemini_key)

                    model_inst = genai.GenerativeModel(self.model)
                    prompt = f"""{system_prompt}

Please compare the proposed requirements model with the original transcript.

--- ORIGINAL TRANSCRIPT ---
{original_transcript}

--- CURRENT PROPOSED REQUIREMENTS (JSON) ---
{json.dumps(current_requirements.model_dump(), indent=2)}

Audit the requirements, correct any gaps or errors, and return the finalized requirements JSON matching the RequirementsModel schema.
"""
                    response = model_inst.generate_content(
                        prompt,
                        generation_config={
                            "response_mime_type": "application/json",
                            "response_schema": RequirementsModel
                        }
                    )
                    
                    data = json.loads(response.text)
                    current_requirements = RequirementsModel(**data)
                except Exception as e:
                    logger.error(f"Error during Gemini API validation: {e}")
                    break
            return current_requirements

        # Re-initialize client if api_key was provided later or loaded
        if not self.client:
            self.api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
            if not self.api_key:
                logger.error("Cannot validate: Anthropic API key is missing. Please set ANTHROPIC_API_KEY.")
                return requirements
            self.client = Anthropic(api_key=self.api_key)

        for iteration in range(1, max_iterations + 1):
            logger.info(f"Starting validation loop iteration {iteration}/{max_iterations}...")
            
            system_prompt = """You are a Quality Assurance Agent and Auditor. Your job is to verify that a structured project plan (RequirementsModel) accurately and completely represents the original developer's intent as expressed in a raw audio transcript.

You must double-check:
1. Complete Coverage: Were all specific feature requests, databases, libraries, or integration requests from the transcript captured?
2. Technical Accuracy: Did the analyzer misinterpret any libraries, languages, or structures?
3. Avoid Over-scaffolding: Did the analyzer add files or features that contradict the user's intent? (Adding logical helper files like a README, config, or tests is encouraged, but adding completely unrelated functionality is not allowed).

If you find missing features, errors, or gaps, you MUST generate an updated, corrected requirements model by invoking the `save_requirements` tool with the corrected information.
If the current requirements model is 100% complete and accurate, invoke the `save_requirements` tool with the existing data without changing it.
"""

            user_message = f"""Please compare the proposed requirements model with the original transcript.

--- ORIGINAL TRANSCRIPT ---
{original_transcript}

--- CURRENT PROPOSED REQUIREMENTS (JSON) ---
{json.dumps(current_requirements.model_dump(), indent=2)}

Audit the requirements, correct any gaps or errors, and invoke `save_requirements` with the finalized data.
"""

            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4000,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_message}
                    ],
                    tools=[
                        {
                            "name": "save_requirements",
                            "description": "Saves the validated and corrected requirements.",
                            "input_schema": RequirementsModel.model_json_schema()
                        }
                    ],
                    tool_choice={"type": "tool", "name": "save_requirements"}
                )

                tool_use_block = None
                for block in response.content:
                    if block.type == "tool_use" and block.name == "save_requirements":
                        tool_use_block = block
                        break

                if not tool_use_block:
                    logger.error("Claude did not use the 'save_requirements' tool during validation.")
                    break

                validated_data = tool_use_block.input
                new_requirements = RequirementsModel(**validated_data)

                # Check if anything changed between iterations
                if new_requirements.model_dump() == current_requirements.model_dump():
                    logger.info("Validation complete: No changes required.")
                    break
                else:
                    logger.info(f"Validation loop {iteration}: Discrepancies found and requirements updated.")
                    current_requirements = new_requirements

            except Exception as e:
                logger.error(f"Error during validation loop: {e}")
                break

        return current_requirements
