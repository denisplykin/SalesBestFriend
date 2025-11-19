"""
Client Card Configuration

Defines the structured fields for tracking client information during the call.
These fields are:
1. Displayed in the Client Card UI
2. Auto-filled by LLM analysis of the conversation
3. Editable by the sales manager

Designed for trial class sales calls (Indonesian context).
"""

from typing import List, Dict, TypedDict, Optional


class ClientCardField(TypedDict):
    """Definition of a single field in the client card"""
    id: str
    label: str
    hint: str  # Helper text for what to capture
    multiline: bool  # True for text area, False for single line
    category: str  # For grouping: "child_info" | "parent_info" | "needs" | "concerns"


# Default client card structure for trial class sales
DEFAULT_CLIENT_CARD_FIELDS: List[ClientCardField] = [
    # Child Information
    {
        "id": "child_name",
        "label": "Child's Name",
        "hint": "Name and age of the child",
        "multiline": False,
        "category": "child_info"
    },
    {
        "id": "child_interests",
        "label": "Child's Interests",
        "hint": "Games, activities, subjects they enjoy",
        "multiline": True,
        "category": "child_info"
    },
    {
        "id": "child_experience",
        "label": "Prior Experience",
        "hint": "Any coding or tech experience",
        "multiline": True,
        "category": "child_info"
    },
    
    # Parent Information & Goals
    {
        "id": "parent_goal",
        "label": "Parent's Goal",
        "hint": "What parent wants child to achieve",
        "multiline": True,
        "category": "parent_info"
    },
    {
        "id": "learning_motivation",
        "label": "Why Learning Now",
        "hint": "Motivation or trigger for enrolling",
        "multiline": True,
        "category": "parent_info"
    },
    
    # Needs & Pain Points
    {
        "id": "main_pain_point",
        "label": "Main Pain Point",
        "hint": "Primary challenge or concern",
        "multiline": True,
        "category": "needs"
    },
    {
        "id": "desired_outcome",
        "label": "Desired Outcome",
        "hint": "What success looks like for them",
        "multiline": True,
        "category": "needs"
    },
    
    # Concerns & Objections
    {
        "id": "objections",
        "label": "Objections Raised",
        "hint": "Price, time, quality, or other concerns",
        "multiline": True,
        "category": "concerns"
    },
    {
        "id": "budget_constraint",
        "label": "Budget Situation",
        "hint": "Any budget constraints mentioned",
        "multiline": False,
        "category": "concerns"
    },
    {
        "id": "schedule_constraint",
        "label": "Schedule Constraints",
        "hint": "Available times, schedule flexibility",
        "multiline": False,
        "category": "concerns"
    },
    
    # Additional Notes
    {
        "id": "additional_notes",
        "label": "Additional Notes",
        "hint": "Any other important details",
        "multiline": True,
        "category": "notes"
    }
]


def get_default_client_card_fields() -> List[ClientCardField]:
    """Get the default client card field configuration"""
    return DEFAULT_CLIENT_CARD_FIELDS


def get_fields_by_category(category: str) -> List[ClientCardField]:
    """
    Get all fields in a specific category
    
    Args:
        category: One of "child_info", "parent_info", "needs", "concerns", "notes"
        
    Returns:
        List of fields in that category
    """
    return [field for field in DEFAULT_CLIENT_CARD_FIELDS if field['category'] == category]


def get_field_by_id(field_id: str) -> Optional[ClientCardField]:
    """
    Get a specific field by its ID
    
    Args:
        field_id: The field identifier
        
    Returns:
        Field definition or None if not found
    """
    return next((field for field in DEFAULT_CLIENT_CARD_FIELDS if field['id'] == field_id), None)


def validate_client_card_config(fields: List[Dict]) -> bool:
    """
    Validate a client card configuration
    
    Args:
        fields: List of field dictionaries
        
    Returns:
        True if valid, raises ValueError if invalid
    """
    required_fields = ['id', 'label', 'hint', 'multiline', 'category']
    valid_categories = ['child_info', 'parent_info', 'needs', 'concerns', 'notes']
    
    if not isinstance(fields, list) or len(fields) == 0:
        raise ValueError("Fields must be a non-empty list")
    
    field_ids = set()
    
    for field in fields:
        # Check required fields
        for req_field in required_fields:
            if req_field not in field:
                raise ValueError(f"Field missing required property: {req_field}")
        
        # Check unique ID
        if field['id'] in field_ids:
            raise ValueError(f"Duplicate field ID: {field['id']}")
        field_ids.add(field['id'])
        
        # Validate category
        if field['category'] not in valid_categories:
            raise ValueError(f"Invalid category: {field['category']}. Must be one of {valid_categories}")
        
        # Validate multiline type
        if not isinstance(field['multiline'], bool):
            raise ValueError(f"Field multiline must be boolean")
    
    return True


# LLM extraction hints for each field
# Used to guide LLM when extracting info from conversation
LLM_EXTRACTION_HINTS = {
    "child_name": "Extract child's name and age if mentioned (e.g. 'Budi, 10 years old')",
    "child_interests": "Extract what the child likes: games (Minecraft, Roblox), activities, favorite subjects",
    "child_experience": "Note if child has tried coding, used computers, or has tech experience",
    "parent_goal": "What does the parent want for their child? Skills, career prep, creativity, logical thinking?",
    "learning_motivation": "Why are they seeking lessons now? School requirement, child's request, parent's initiative?",
    "main_pain_point": "The biggest challenge or concern. E.g., 'child struggles with logic', 'bored with traditional learning'",
    "desired_outcome": "What would success look like? Better grades, career readiness, confidence, creativity?",
    "objections": "Any concerns raised: too expensive, no time, doubt about results, child's motivation",
    "budget_constraint": "Budget mentioned? Payment concerns? Looking for discounts or installments?",
    "schedule_constraint": "When can they attend? Weekends only? After school? Specific time preferences?",
    "additional_notes": "Anything else important that doesn't fit other categories"
}


def get_extraction_hint(field_id: str) -> str:
    """
    Get the LLM extraction hint for a specific field
    
    Args:
        field_id: The field identifier
        
    Returns:
        Hint string for LLM extraction
    """
    return LLM_EXTRACTION_HINTS.get(field_id, "Extract relevant information from the conversation")

