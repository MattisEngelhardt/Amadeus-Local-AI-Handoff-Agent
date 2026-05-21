from typing import List
from pydantic import BaseModel, Field

class FilePlaceholder(BaseModel):
    """Placeholder representing a file that needs to be generated."""
    file_path: str = Field(
        description="The relative path where this file should be created within the project directory (e.g., 'main.py' or 'utils/helpers.py')."
    )
    purpose: str = Field(
        description="Detailed description of what this file should contain and its role in the application."
    )

class RequirementsModel(BaseModel):
    """Structured project requirements extracted from a voice transcript."""
    project_name: str = Field(
        description="A clean, kebab-case or snake_case name for the project folder (e.g., 'stock-tracker' or 'my_utility')."
    )
    display_name: str = Field(
        description="A user-friendly readable name for the project (e.g., 'Stock Tracker' or 'My Utility')."
    )
    short_description: str = Field(
        description="A concise 1-2 sentence description of the project and its core value proposition."
    )
    project_type: str = Field(
        description="The type of project, e.g., 'FastAPI Web API', 'Streamlit App', 'Python CLI Tool', 'Tkinter Desktop App', 'NodeJS CLI', etc."
    )
    tech_stack: List[str] = Field(
        description="List of core languages, frameworks, and technologies used (e.g., ['Python', 'FastAPI', 'SQLite'])."
    )
    dependencies: List[str] = Field(
        description="List of external packages or libraries to install (e.g., ['fastapi>=0.100.0', 'uvicorn', 'sqlalchemy'])."
    )
    specifications: List[str] = Field(
        description="List of detailed functional specifications and user requirements extracted from the transcript."
    )
    quality_criteria: List[str] = Field(
        description="List of quality/style guidelines the project code must adhere to."
    )
    files_to_create: List[FilePlaceholder] = Field(
        description="A complete list of files that must be scaffolded to make this a fully operational project."
    )
