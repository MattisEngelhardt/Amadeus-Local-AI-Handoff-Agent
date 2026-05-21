import os
import logging
import yaml
from jinja2 import Environment, FileSystemLoader
from anthropic import Anthropic
from dotenv import load_dotenv
from speech_to_code.models.requirements import RequirementsModel
from speech_to_code.models.project import ProjectFileModel

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class ProjectGenerator:
    def __init__(self, api_key=None, model="claude-3-5-sonnet-20241022", llm_provider="claude"):
        """
        Initialize the Project Generator.
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
                logger.warning("Anthropic API key not found. Generation will fail unless key is passed later or set in environment.")
            else:
                self.client = Anthropic(api_key=self.api_key)

        # Setup Jinja2 environment
        template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates"))
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))

    def _get_project_type_details(self, project_type):
        """Loads run/test commands for the given project type from project_types.yaml."""
        types_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates", "project_types.yaml"))
        default_details = {
            "run_command": "python main.py",
            "test_command": "pytest",
            "lint_command": "",
            "has_env": False
        }
        
        if not os.path.exists(types_path):
            logger.warning(f"project_types.yaml not found at {types_path}. Using hardcoded defaults.")
            return default_details

        try:
            with open(types_path, "r", encoding="utf-8") as f:
                types_data = yaml.safe_load(f)
                
            # Try to match the project type, case-insensitive
            for key, val in types_data.items():
                if key.lower() == project_type.lower():
                    return val
            
            return types_data.get("default", default_details)
        except Exception as e:
            logger.error(f"Error loading project types yaml: {e}")
            return default_details

    def generate_file_content(self, requirements: RequirementsModel, target_file_path, file_purpose):
        """
        Calls Claude to generate the code/text content of a specific file in the project.
        :param requirements: The full validated RequirementsModel.
        :param target_file_path: The relative path of the file to generate.
        :param file_purpose: The purpose/description of the file.
        :return: Syntactically correct file content as a string.
        """
        logger.info(f"Generating content for file: {target_file_path}...")

        # Prepare full architectural context so LLM knows the overall design
        files_roadmap = "\n".join([f"- `{f.file_path}`: {f.purpose}" for f in requirements.files_to_create])
        specifications_list = "\n".join([f"- {spec}" for spec in requirements.specifications])
        quality_criteria_list = "\n".join([f"- {qc}" for qc in requirements.quality_criteria])
        tech_stack_list = ", ".join(requirements.tech_stack)
        dependencies_list = ", ".join(requirements.dependencies)

        system_prompt = f"""You are an Expert Lead Software Engineer. Your task is to write the complete, high-quality, production-ready file contents for a specific file in a new project.

PROJECT DETAILS:
- Name: {requirements.display_name}
- Short Description: {requirements.short_description}
- Project Type: {requirements.project_type}
- Tech Stack: {tech_stack_list}
- Required Dependencies: {dependencies_list}

PROJECT ROADMAP / DIRECTORY STRUCTURE:
{files_roadmap}

FUNCTIONAL SPECIFICATIONS:
{specifications_list}

CODE QUALITY GUIDELINES:
{quality_criteria_list}

YOUR TASK:
Generate the contents for the file: `{target_file_path}`
File Purpose: {file_purpose}

IMPORTANT INSTRUCTIONS:
1. Provide the complete code or text for the file. Do not use placeholders, comments like "// todo implement", or truncate the output.
2. The code must compile and run cleanly, matching the project guidelines and interacting correctly with other files in the roadmap.
3. OUTPUT ONLY the direct file contents. Do NOT wrap the file contents in markdown code block ticks (like ```python or ```) under any circumstances. Start directly with imports or code. Do not include any conversational preamble or postscript.
"""

        if self.llm_provider == "gemini":
            try:
                import google.generativeai as genai
                self.gemini_key = self.gemini_key or os.getenv("GEMINI_API_KEY")
                if not self.gemini_key:
                    logger.error("Cannot generate code: GEMINI_API_KEY is missing.")
                    return ""
                genai.configure(api_key=self.gemini_key)

                logger.info(f"Generating content via Gemini for file: {target_file_path}...")
                model_inst = genai.GenerativeModel(self.model)
                prompt = f"{system_prompt}\n\nPlease generate the complete, ready-to-use contents for `{target_file_path}`."
                
                response = model_inst.generate_content(prompt)
                content = response.text.strip()
                
                # Clean up code blocks if present
                if content.startswith("```"):
                    lines = content.splitlines()
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].startswith("```"):
                        lines = lines[:-1]
                    content = "\n".join(lines).strip()
                    
                return content
            except Exception as e:
                logger.error(f"Error generating content via Gemini for {target_file_path}: {e}")
                return ""

        if not self.client:
            self.api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
            if not self.api_key:
                logger.error("Cannot generate code: Anthropic API key is missing.")
                return ""
            self.client = Anthropic(api_key=self.api_key)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"Please generate the complete, ready-to-use contents for `{target_file_path}`."}
                ]
            )

            content = response.content[0].text.strip()
            
            # Clean up markdown code block wrapping if Claude ignored the prompt constraints
            if content.startswith("```"):
                lines = content.splitlines()
                # Remove the starting ```... line
                if lines[0].startswith("```"):
                    lines = lines[1:]
                # Remove the trailing ``` line
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                content = "\n".join(lines).strip()

            return content
        except Exception as e:
            logger.error(f"Error generating content for {target_file_path}: {e}")
            return ""

    def generate_all_files(self, requirements: RequirementsModel):
        """
        Generates the list of ProjectFileModel objects for all requirements files, plus CLAUDE.md and README.md.
        :param requirements: Validated RequirementsModel.
        :return: List of ProjectFileModel objects ready to be scaffolded.
        """
        generated_files = []

        # 1. Generate code content for each requirements-defined file
        for file_placeholder in requirements.files_to_create:
            content = self.generate_file_content(
                requirements=requirements,
                target_file_path=file_placeholder.file_path,
                file_purpose=file_placeholder.purpose
            )
            if content:
                generated_files.append(ProjectFileModel(
                    file_path=file_placeholder.file_path,
                    content=content,
                    purpose=file_placeholder.purpose
                ))

        # Get defaults based on project type
        type_details = self._get_project_type_details(requirements.project_type)

        # Jinja template rendering context
        template_ctx = {
            "display_name": requirements.display_name,
            "project_name": requirements.project_name,
            "short_description": requirements.short_description,
            "tech_stack": requirements.tech_stack,
            "files_to_create": requirements.files_to_create,
            "quality_criteria": requirements.quality_criteria,
            "run_command": type_details.get("run_command", "python main.py"),
            "test_command": type_details.get("test_command", "pytest"),
            "lint_command": type_details.get("lint_command", ""),
            "has_env": type_details.get("has_env", False)
        }

        # 2. Render CLAUDE.md using Jinja2
        try:
            claude_md_template = self.jinja_env.get_template("claude_md.j2")
            claude_md_content = claude_md_template.render(template_ctx)
            generated_files.append(ProjectFileModel(
                file_path="CLAUDE.md",
                content=claude_md_content,
                purpose="Developer guidelines and build/run commands"
            ))
        except Exception as e:
            logger.error(f"Failed to render CLAUDE.md: {e}")

        # 3. Render README.md using Jinja2
        try:
            readme_template = self.jinja_env.get_template("readme.j2")
            readme_content = readme_template.render(template_ctx)
            generated_files.append(ProjectFileModel(
                file_path="README.md",
                content=readme_content,
                purpose="Public-facing project overview and setup instructions"
            ))
        except Exception as e:
            logger.error(f"Failed to render README.md: {e}")

        # 4. Generate requirements.txt
        dependencies_txt = "\n".join(requirements.dependencies) + "\n"
        generated_files.append(ProjectFileModel(
            file_path="requirements.txt",
            content=dependencies_txt,
            purpose="Python library dependencies"
        ))

        # 5. Generate .env.example if necessary
        if type_details.get("has_env", False):
            # Propose a simple template for API key / env config
            env_example_content = "# Environment configuration template\n# Copy this file to .env and fill in variables\n"
            # Attempt to extract env vars from description or guess based on stack
            stack_lower = [t.lower() for t in requirements.tech_stack]
            if "openai" in stack_lower or "whisper" in stack_lower:
                env_example_content += "OPENAI_API_KEY=your_openai_api_key_here\n"
            if "anthropic" in stack_lower or "claude" in stack_lower:
                env_example_content += "ANTHROPIC_API_KEY=your_anthropic_api_key_here\n"
            
            env_example_content += "PORT=8000\nDATABASE_URL=sqlite:///./sql_app.db\n"
            
            generated_files.append(ProjectFileModel(
                file_path=".env.example",
                content=env_example_content,
                purpose="Environment variables template"
            ))

        return generated_files
