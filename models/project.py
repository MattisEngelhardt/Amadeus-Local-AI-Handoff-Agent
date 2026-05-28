from pydantic import BaseModel, Field


class ProjectFileModel(BaseModel):
    """Represents a generated project file with its path, content, and purpose."""

    file_path: str = Field(
        description=(
            "The relative path where the file should be created within the project directory."
        )
    )
    content: str = Field(
        description=(
            "The complete, syntactically correct code or text content of the file. "
            "Do not include markdown code block formatting inside the string."
        )
    )
    purpose: str = Field(description="A brief description of what this file does.")
