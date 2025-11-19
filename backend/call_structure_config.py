"""
Call Structure Configuration for Trial Class Sales Calls

Defines the expected flow of a trial class sales call with:
- Stages (7 stages for trial class scenario)
- Timing per stage
- Checklist items per stage

This structure is used for:
1. Real-time progress tracking
2. LLM semantic matching (conversation → checklist items)
3. Time-based stage detection
4. Settings UI (editable by user)
"""

from typing import List, Dict, TypedDict, Any


class ChecklistItem(TypedDict):
    """Single checklist item within a stage"""
    id: str
    type: str  # "discuss" or "say"
    content: str  # What to ask/discuss or what to say/explain


class CallStage(TypedDict):
    """Single stage in the call structure"""
    id: str
    name: str
    startOffsetSeconds: int  # When this stage should start (from call start)
    durationSeconds: int  # How long this stage should last
    items: List[ChecklistItem]


# Default configuration for trial class sales calls (Indonesian context)
DEFAULT_CALL_STRUCTURE: List[CallStage] = [
    {
        "id": "stage_1_opening",
        "name": "Opening & Greeting",
        "startOffsetSeconds": 0,
        "durationSeconds": 120,  # 2 minutes
        "items": [
            {
                "id": "greet_client",
                "type": "say",
                "content": "Greet the client warmly and introduce yourself"
            },
            {
                "id": "confirm_time",
                "type": "discuss",
                "content": "Confirm they have time for the trial class"
            },
            {
                "id": "explain_agenda",
                "type": "say",
                "content": "Explain today's agenda and trial class structure"
            }
        ]
    },
    {
        "id": "stage_2_discovery",
        "name": "Understanding Needs",
        "startOffsetSeconds": 120,
        "durationSeconds": 300,  # 5 minutes
        "items": [
            {
                "id": "ask_child_age",
                "type": "discuss",
                "content": "Ask about the child's age and current grade"
            },
            {
                "id": "ask_interests",
                "type": "discuss",
                "content": "Discover what the child likes (games, activities, subjects)"
            },
            {
                "id": "ask_goals",
                "type": "discuss",
                "content": "Understand parent's goals for the child"
            },
            {
                "id": "ask_experience",
                "type": "discuss",
                "content": "Check if child has any coding/tech experience"
            },
            {
                "id": "identify_pain_points",
                "type": "discuss",
                "content": "Identify challenges or concerns parent has"
            }
        ]
    },
    {
        "id": "stage_3_trial_intro",
        "name": "Trial Class Introduction",
        "startOffsetSeconds": 420,
        "durationSeconds": 180,  # 3 minutes
        "items": [
            {
                "id": "explain_platform",
                "type": "say",
                "content": "Explain how the learning platform works"
            },
            {
                "id": "show_curriculum",
                "type": "say",
                "content": "Show the curriculum tailored to their child's level"
            },
            {
                "id": "set_expectations",
                "type": "say",
                "content": "Set expectations for the trial class"
            }
        ]
    },
    {
        "id": "stage_4_trial_class",
        "name": "Conducting Trial Class",
        "startOffsetSeconds": 600,
        "durationSeconds": 1200,  # 20 minutes
        "items": [
            {
                "id": "engage_child",
                "type": "discuss",
                "content": "Actively engage with the child during lesson"
            },
            {
                "id": "demonstrate_method",
                "type": "say",
                "content": "Demonstrate teaching methodology and approach"
            },
            {
                "id": "check_understanding",
                "type": "discuss",
                "content": "Check child's understanding throughout"
            },
            {
                "id": "encourage_participation",
                "type": "say",
                "content": "Encourage active participation and questions"
            },
            {
                "id": "show_progress",
                "type": "say",
                "content": "Show visible progress during the trial"
            }
        ]
    },
    {
        "id": "stage_5_feedback",
        "name": "Trial Feedback & Discussion",
        "startOffsetSeconds": 1800,
        "durationSeconds": 300,  # 5 minutes
        "items": [
            {
                "id": "ask_child_feedback",
                "type": "discuss",
                "content": "Ask the child how they felt about the lesson"
            },
            {
                "id": "ask_parent_feedback",
                "type": "discuss",
                "content": "Get parent's immediate feedback and observations"
            },
            {
                "id": "highlight_strengths",
                "type": "say",
                "content": "Highlight what the child did well"
            },
            {
                "id": "suggest_next_steps",
                "type": "say",
                "content": "Suggest learning path and next topics"
            }
        ]
    },
    {
        "id": "stage_6_objections",
        "name": "Address Concerns",
        "startOffsetSeconds": 2100,
        "durationSeconds": 300,  # 5 minutes
        "items": [
            {
                "id": "address_price",
                "type": "discuss",
                "content": "Address pricing concerns if raised"
            },
            {
                "id": "address_schedule",
                "type": "discuss",
                "content": "Discuss schedule flexibility and options"
            },
            {
                "id": "address_doubts",
                "type": "discuss",
                "content": "Address any doubts about effectiveness"
            },
            {
                "id": "show_proof",
                "type": "say",
                "content": "Share success stories and testimonials"
            }
        ]
    },
    {
        "id": "stage_7_closing",
        "name": "Closing & Next Steps",
        "startOffsetSeconds": 2400,
        "durationSeconds": 300,  # 5 minutes
        "items": [
            {
                "id": "summarize_value",
                "type": "say",
                "content": "Summarize the value and benefits discussed"
            },
            {
                "id": "present_packages",
                "type": "say",
                "content": "Present available packages and pricing"
            },
            {
                "id": "ask_commitment",
                "type": "discuss",
                "content": "Ask if they're ready to enroll"
            },
            {
                "id": "schedule_followup",
                "type": "discuss",
                "content": "Schedule follow-up or next class"
            },
            {
                "id": "thank_participant",
                "type": "say",
                "content": "Thank them for their time and participation"
            }
        ]
    }
]


def get_default_call_structure() -> List[CallStage]:
    """Get the default call structure configuration"""
    return DEFAULT_CALL_STRUCTURE


def get_stage_by_time(elapsed_seconds: int) -> str:
    """
    Determine current stage based on elapsed time
    
    Args:
        elapsed_seconds: Seconds since call start
        
    Returns:
        Stage ID that should be active at this time
    """
    structure = get_default_call_structure()
    
    for stage in reversed(structure):  # Check from end to start
        if elapsed_seconds >= stage['startOffsetSeconds']:
            return stage['id']
    
    return structure[0]['id']  # Default to first stage


def get_stage_timing_status(stage_id: str, elapsed_seconds: int) -> Dict[str, Any]:
    """
    Check if a stage is on time, late, or not started
    
    Args:
        stage_id: The stage to check
        elapsed_seconds: Current call time
        
    Returns:
        Dict with status: 'not_started' | 'on_time' | 'slightly_late' | 'very_late'
    """
    structure = get_default_call_structure()
    stage = next((s for s in structure if s['id'] == stage_id), None)
    
    if not stage:
        return {'status': 'unknown', 'message': 'Stage not found'}
    
    stage_start = stage['startOffsetSeconds']
    stage_end = stage_start + stage['durationSeconds']
    
    if elapsed_seconds < stage_start:
        return {
            'status': 'not_started',
            'message': f"Starts in {(stage_start - elapsed_seconds) // 60} min"
        }
    elif elapsed_seconds <= stage_end:
        return {
            'status': 'on_time',
            'message': 'On track'
        }
    elif elapsed_seconds <= stage_end + 120:  # 2 min grace period
        return {
            'status': 'slightly_late',
            'message': 'Slightly behind'
        }
    else:
        minutes_late = (elapsed_seconds - stage_end) // 60
        return {
            'status': 'very_late',
            'message': f"{minutes_late} min behind"
        }


def validate_call_structure(structure: List[Dict]) -> bool:
    """
    Validate a call structure configuration
    
    Args:
        structure: List of stage dictionaries
        
    Returns:
        True if valid, raises ValueError if invalid
    """
    required_stage_fields = ['id', 'name', 'startOffsetSeconds', 'durationSeconds', 'items']
    required_item_fields = ['id', 'type', 'content']
    
    if not isinstance(structure, list) or len(structure) == 0:
        raise ValueError("Structure must be a non-empty list")
    
    stage_ids = set()
    item_ids = set()
    
    for stage in structure:
        # Check required fields
        for field in required_stage_fields:
            if field not in stage:
                raise ValueError(f"Stage missing required field: {field}")
        
        # Check unique stage ID
        if stage['id'] in stage_ids:
            raise ValueError(f"Duplicate stage ID: {stage['id']}")
        stage_ids.add(stage['id'])
        
        # Validate items
        if not isinstance(stage['items'], list):
            raise ValueError(f"Stage {stage['id']} items must be a list")
        
        for item in stage['items']:
            for field in required_item_fields:
                if field not in item:
                    raise ValueError(f"Item missing required field: {field}")
            
            # Check unique item ID (globally)
            if item['id'] in item_ids:
                raise ValueError(f"Duplicate item ID: {item['id']}")
            item_ids.add(item['id'])
            
            # Validate item type
            if item['type'] not in ['discuss', 'say']:
                raise ValueError(f"Item type must be 'discuss' or 'say', got: {item['type']}")
    
    return True

