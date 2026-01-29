from typing_extensions import TypedDict
from pydantic import BaseModel, Field

# Structures outputs
# -------------------------------

class Instructions(BaseModel):
    tasks: str = Field(description="List of tasks to be completed by the agent")
    focus: str = Field(description="Focus or lens through which the agent should get its task done")
    standards: str = Field(description="The standrads for the assigned tasks to be considered succesfully completed")

class ManagerCommand(BaseModel):
    research_instructions: Instructions = Field(description="The tasks, standards and focus for the research agent")
    analytics_instructions: Instructions = Field(description="The tasks, standards and focus for the analytics agent")

# States for the graph and nodes
# ------------------------------------------

class State(TypedDict):
    goal: str
    business_profile: str
    data_path: str
    research_instructions: Instructions
    analytics_instructions: Instructions
    qa_research_report: str
    qa_analytics_report: str
    research_report: str
    analytics_report: str
    graph_file_path: str
    impact_value: str
    final_report: str

# This subclasses are useful for testing each agent individually:

class ResearchState(TypedDict):
    research_instructions: Instructions

class AnalyticsState(TypedDict):
    analytics_instructions: Instructions
    data_path: str

class SynthersizerState(TypedDict):
    business_profile: str
    goal: str
    research_report: str
    analytics_report: str
    graph_file_path: str