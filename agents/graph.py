"""
Simple Graph
"""
from typing import TypedDict, Union, List
from langgraph.graph import StateGraph, END
from agents.nodes import validate_content, generate_content

class GraphState(TypedDict):
    content: str
    standard: str
    subject: str
    chapter: str
    is_valid: bool
    success: bool
    error: str | None
    generated_content: dict | None
    validation_result: Union[dict, str] | None

def create_graph():
    """Create simple graph with proper error handling"""
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("validate_content", validate_content)
    workflow.add_node("generate_content", generate_content)
    
    # Set entry point
    workflow.set_entry_point("validate_content")
    
    # Define conditional routing
    def route_after_validation(state):
        """Route to next step based on validation result"""
        if state.get("is_valid"):
            return "generate_content"
        else:
            return END
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "validate_content",
        route_after_validation
    )
    
    # Add final edge
    workflow.add_edge("generate_content", END)
    
    return workflow.compile()

graph = create_graph() 