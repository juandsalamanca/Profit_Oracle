from src.agents import *
from langgraph.graph import StateGraph, START, END


def build_graph():

    business_consulting_team_builder = StateGraph(State)

    business_consulting_team_builder.add_node("manager", manager_command)
    business_consulting_team_builder.add_node("research_agent", research)
    business_consulting_team_builder.add_node("analytics_agent", analytics)
    business_consulting_team_builder.add_node("synthesizer", synthesizer)

    business_consulting_team_builder.add_edge(START, "manager")
    business_consulting_team_builder.add_edge("manager", "research_agent")
    business_consulting_team_builder.add_edge("manager", "analytics_agent")
    business_consulting_team_builder.add_edge("research_agent", "synthesizer")
    business_consulting_team_builder.add_edge("analytics_agent", "synthesizer")
    business_consulting_team_builder.add_edge("synthesizer", END)

    business_consulting_team = business_consulting_team_builder.compile()

    return business_consulting_team

def run_graph(graph_input):

    business_consulting_team = build_graph()
    state = business_consulting_team.invoke(graph_input)
    report = state["final_report"]
    image_path = state["graph_file_path"]
    impact_value = state["impact_value"]
    return report, image_path, impact_value
