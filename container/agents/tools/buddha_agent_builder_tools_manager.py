import json
from typing import List, Dict, Any, Optional, Generator
from langchain_core.tools import tool, BaseTool
from langchain_core.prompts import ChatPromptTemplate
from libs.weaviate_lib import client, insert_to_collection, COLLECTION_AGENTS, COLLECTION_DOCUMENTS, get_object_by_id
from datetime import datetime
import uuid
from weaviate.collections.classes.filters import Filter
from data_classes.common_classes import ApprovalRequest, MessageType, Language, AppMessageResponse, AgentRole
from agents.extract_message import extract_message_content
from agents.tools.buddha_agent_builder_tools import create_buddhist_agent, update_buddhist_agent, delete_buddhist_agent, list_buddhist_agents, get_buddhist_teachings, search_buddhist_agents, test_buddhist_agent, add_buddhist_knowledge_to_context, search_buddhist_knowledge, add_buddhist_teaching_example, add_user_insight_to_knowledge_base, get_buddhist_agent_by_id
class ApprovalManager:
    """Manages pending approvals and execution state"""
    
    def __init__(self):
        self.pending_approvals: Dict[str, ApprovalRequest] = {}
        self.execution_state: Dict[str, Any] = {}
    
    def create_approval_request(self, tool_name: str, tool_description: str, 
                              arguments: Dict[str, Any], reasoning: str = "") -> ApprovalRequest:
        """Create a new approval request"""
        approval_id = str(uuid.uuid4())
        request = ApprovalRequest(
            id=approval_id,
            tool_name=tool_name,
            tool_description=tool_description,
            arguments=arguments,
            reasoning=reasoning,
            timestamp=str(datetime.now())
        )
        self.pending_approvals[approval_id] = request
        return request
    
    def get_pending_approval(self, approval_id: str) -> Optional[ApprovalRequest]:
        """Get pending approval by ID"""
        return self.pending_approvals.get(approval_id)
    
    def remove_pending_approval(self, approval_id: str):
        """Remove pending approval after resolution"""
        self.pending_approvals.pop(approval_id, None)

# Global approval manager instance
approval_manager = ApprovalManager()

class FrontendFriendlyApprovalTool(BaseTool):
    """Tool wrapper that sends structured approval requests to frontend"""
    
    def __init__(self, original_tool, approval_required: bool = True):
        # Extract tool information from the original tool
        self._original_tool = original_tool
        self._approval_required = approval_required
        
        # Get tool name
        tool_name = getattr(original_tool, "name", None)
        if tool_name is None and hasattr(original_tool, "func"):
            tool_name = original_tool.func.__name__
        
        # Get tool description
        tool_description = getattr(original_tool, "description", "")
        if not tool_description and hasattr(original_tool, "func"):
            tool_description = original_tool.func.__doc__ or ""
        
        # Get args schema
        args_schema = getattr(original_tool, "args_schema", None)
        
        # Initialize the BaseTool properly
        super().__init__(
            name=tool_name,
            description=tool_description,
            args_schema=args_schema
        )
    
    @property
    def original_tool(self):
        return self._original_tool
    
    @property
    def approval_required(self):
        return self._approval_required
    
    def _run(self, *args, **kwargs) -> Any:
        # Check if approval is required by looking at the tool name
        # This is more reliable than depending on instance attributes
        tool_name = getattr(self, "name", "")
        APPROVAL_REQUIRED = {
            'create_buddhist_agent',
            'update_buddhist_agent', 
            'delete_buddhist_agent',
            'add_user_insight_to_knowledge_base'
        }
        
        requires_approval = tool_name in APPROVAL_REQUIRED
        
        if not requires_approval:
            # Get the original tool safely
            original_tool = getattr(self, "_original_tool", None)
            if original_tool:
                # Extract config from kwargs if present
                config = kwargs.pop('config', None)
                return original_tool._run(*args, **kwargs, config=config)
            else:
                # Fallback: try to find the tool by name
                for tool in buddha_agent_tools:
                    if getattr(tool, "name", "") == tool_name:
                        # Extract config from kwargs if present
                        config = kwargs.pop('config', None)
                        return tool._run(*args, **kwargs, config=config)
                raise ValueError(f"Could not find original tool for {tool_name}")
        
        # Create approval request
        approval_request = approval_manager.create_approval_request(
            tool_name=self.name,
            tool_description=self.description,
            arguments=kwargs if kwargs else {"args": args},
            reasoning=f"Agent wants to execute {self.name}"
        )
        
        # Store the tool execution context in the approval manager for later retrieval
        approval_manager.execution_state[approval_request.id] = {
            "tool_name": tool_name,
            "args": args,
            "kwargs": kwargs
        }
        
        # Return special approval marker that the streaming function will catch
        return {
            "type": "approval_required",
            "approval_request": approval_request.to_dict(),
            "approval_id": approval_request.id
        }
    
    async def _arun(self, *args, **kwargs) -> Any:
        # Same logic for async
        return self._run(*args, **kwargs)

def create_frontend_friendly_tools(original_tools: List) -> List:
    """Create frontend-friendly tools with approval system"""
    
    # Tools that require approval
    APPROVAL_REQUIRED = {
        'create_buddhist_agent',
        'update_buddhist_agent', 
        'delete_buddhist_agent',
        'add_user_insight_to_knowledge_base'
    }
    
    wrapped_tools = []
    for tool in original_tools:
        # Get name from tool - handle both StructuredTool and regular Tool cases
        tool_name = getattr(tool, "name", None)
        if tool_name is None and hasattr(tool, "func"):
            # For StructuredTool, name comes from the function name
            tool_name = tool.func.__name__
        requires_approval = tool_name in APPROVAL_REQUIRED
        wrapped_tool = FrontendFriendlyApprovalTool(tool, requires_approval)
        wrapped_tools.append(wrapped_tool)
    
    return wrapped_tools


def process_tool_result_for_frontend(tool_result) -> Optional[AppMessageResponse]:
    """Process tool results for frontend"""
    try:
        # Check if this is an approval request from our wrapped tool
        if isinstance(tool_result, dict) and tool_result.get("type") == "approval_required":
            approval_request = tool_result["approval_request"]
            return AppMessageResponse(
                type=MessageType.APPROVAL_REQUEST,
                content=format_approval_message(approval_request),
                role=AgentRole.SYSTEM,
                approval_id=approval_request["id"],
                tool_name=approval_request["tool_name"],
                tool_description=approval_request["tool_description"],
                arguments=approval_request["arguments"],
                reasoning=approval_request["reasoning"],
                requires_user_action=True
            )
        
        # Handle regular tool results
        content = extract_message_content(tool_result)
        
        # If extract_message_content already processed it as an approval request, return it
        if isinstance(content, AppMessageResponse) and content.type == MessageType.APPROVAL_REQUEST:
            return content
        
        # Check if this is an approval request from the old format
        if isinstance(content, AppMessageResponse) and content.type == MessageType.APPROVAL_REQUEST:
            approval_request = content["approval_request"]
            return AppMessageResponse(
                type=MessageType.APPROVAL_REQUEST,
                content=format_approval_message(approval_request),
                role=AgentRole.SYSTEM,
                approval_id=approval_request["id"],
                tool_name=approval_request["tool_name"],
                tool_description=approval_request["tool_description"],
                arguments=approval_request["arguments"],
                reasoning=approval_request["reasoning"],
                requires_user_action=True
            )
        
        # Regular tool result
        return AppMessageResponse(
            type=MessageType.TOOL_EXECUTION,
            content=content.get("content", str(content)) if isinstance(content, dict) else str(content),
            role=AgentRole.ASSISTANT
        )
    
    except Exception as e:
        return AppMessageResponse(
            type=MessageType.ERROR,
            content=f"Error processing tool result: {str(e)}",
            role=AgentRole.SYSTEM
        )

def format_approval_message(approval_request: Dict[str, Any]) -> str:
    """Format approval request for display"""
    return f"""🔔 **Approval Required**

**Action:** {approval_request['tool_name']}
**Description:** {approval_request['tool_description']}

**Parameters:**
```json
{json.dumps(approval_request['arguments'], indent=2)}
```

The agent wants to perform this action. Do you approve?"""

def handle_approval_response(approval_response: Dict[str, Any], language: Language) -> Generator[AppMessageResponse, None, None]:
    """Handle approval response from frontend"""
    try:
        approval_id = approval_response.get("approval_id")
        approved = approval_response.get("approved", False)
        
        if not approval_id:
            yield AppMessageResponse(
                type=MessageType.ERROR,
                content="Invalid approval response: missing approval_id",
                role=AgentRole.SYSTEM
            )
            return
        
        # Get pending approval
        pending_approval = approval_manager.get_pending_approval(approval_id)
        if not pending_approval:
            yield AppMessageResponse(
                type=MessageType.ERROR,
                content="Approval request not found or already processed",
                role=AgentRole.SYSTEM
            )
            return
        
        if approved:
            # Execute the approved action
            try:
                # Get the tool execution context from the approval manager
                execution_context = approval_manager.execution_state.get(approval_id)
                
                if execution_context:
                    tool_name = execution_context["tool_name"]
                    args = execution_context["args"]
                    kwargs = execution_context["kwargs"]
                    
                    # Find the original tool by name
                    original_tool = None
                    for tool in buddha_agent_tools:
                        if getattr(tool, "name", "") == tool_name:
                            original_tool = tool
                            break
                    
                    if original_tool:
                        # Execute the original tool
                        # Extract config from kwargs if present
                        kwargs_copy = kwargs.copy()
                        config = kwargs_copy.pop('config', None)
                        result = original_tool._run(*args, **kwargs_copy, config=config)
                        agent_id = result.get("agent_id")
                        yield AppMessageResponse(
                            type=MessageType.TOOL_EXECUTION,
                            content=f"✅ Successfully executed: {pending_approval.tool_name}\n\nResult: {str(result)} \n\n[[{agent_id}]]",
                            role=AgentRole.ASSISTANT,
                            tool_name=pending_approval.tool_name,
                            tool_description=pending_approval.tool_description,
                            arguments=pending_approval.arguments,
                            reasoning=pending_approval.reasoning,
                            requires_user_action=False
                        )
                    else:
                        yield AppMessageResponse(
                            type=MessageType.ERROR,
                            content=f"Could not find original tool for {tool_name}",
                            role=AgentRole.SYSTEM
                        )
                    
                    # Clean up execution state
                    approval_manager.execution_state.pop(approval_id, None)
                else:
                    yield AppMessageResponse(
                        type=MessageType.ERROR,
                        content=f"Could not find execution context for {pending_approval.tool_name}",
                        role=AgentRole.SYSTEM
                    )
                
                # Remove from pending
                approval_manager.remove_pending_approval(approval_id)
                
            except Exception as e:
                yield AppMessageResponse(
                    type=MessageType.ERROR,
                    content=f"Error executing approved action: {str(e)}",
                    role=AgentRole.SYSTEM
                )
        else:
            # Action was declined
            decline_msg = (
                "❌ Hành động đã bị hủy bởi người dùng." if language == Language.VI.value 
                else "❌ Action cancelled by user."
            )
            yield AppMessageResponse(
                type=MessageType.AGENT_MESSAGE,
                content=decline_msg,
                role=AgentRole.ASSISTANT
            )
            
            # Clean up execution state and remove from pending
            approval_manager.execution_state.pop(approval_id, None)
            approval_manager.remove_pending_approval(approval_id)
    
    except Exception as e:
        yield AppMessageResponse(
            type=MessageType.ERROR,
            content=f"Error handling approval response: {str(e)}",
            role=AgentRole.SYSTEM
        )

buddha_agent_tools = [
    add_buddhist_knowledge_to_context,
    search_buddhist_knowledge,
    add_buddhist_teaching_example,
    add_user_insight_to_knowledge_base,
    
    create_buddhist_agent,
    update_buddhist_agent,
    delete_buddhist_agent,

    list_buddhist_agents,
    get_buddhist_agent_by_id,
    get_buddhist_teachings,
    
    # create_meditation_guide,
    # generate_mindfulness_exercise,
    # create_compassion_practice,
    
    search_buddhist_agents,
    test_buddhist_agent,
    # create_life_guidance_response,
    # create_study_review_material,
    # create_knowledge_test,
    # create_buddhist_poetry
]
