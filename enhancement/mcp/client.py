"""
MCP Client Boundary for CAPABL Recruitment Intelligence Agent.

Milestone 9: External Tool Integration, MCP Boundary & Advanced Agent Capabilities.
Provides:
1. CAPABLMCPClient: Client interface for discovering and executing MCP tools.
2. get_mcp_langchain_tools: Exposes approved MCP tools as first-class LangChain BaseTools.
3. Strict timeout enforcement (MCP_TIMEOUT_SECONDS) and failure classification.
4. Preserves backward compatibility with prior MCPClientBridge references.
"""

import json
import time
import logging
from typing import Optional, List, Dict, Any, Union
from langchain_core.tools import tool, BaseTool

from capabl_core.evidence.service import EvidenceService
from capabl_core.calendar.service import MockCalendarService, DEFAULT_CALENDAR_SERVICE
from enhancement.mcp.schemas import (
    CandidateEvidenceInput,
    JobEvidenceInput,
    PolicyEvidenceInput,
    InterviewSearchInput,
    BookingInput,
    MCPToolResponse,
)
from enhancement.mcp.registry import (
    MCP_TOOL_REGISTRY,
    is_tool_approved,
    get_tool_definition,
)
from enhancement.mcp.tools import MCPToolAdapters
from enhancement.mcp.transport import MCPTransportConfig, DEFAULT_TRANSPORT_CONFIG
from enhancement.security.audit_logger import DEFAULT_AUDIT_LOGGER

logger = logging.getLogger(__name__)


def normalize_mcp_response(raw_result: Any, tool_name: str = "") -> Dict[str, Any]:
    """
    Normalizes an MCP tool execution result into a stable typed/structured dictionary.
    
    The UI and consumers must receive a stable structured result regardless of whether
    the MCP tool returns:
    1. Structured dictionary / Pydantic object (e.g. MCPToolResponse, EvidenceEnvelope)
    2. MCP content wrapper (e.g. CallToolResult or dict with 'content' blocks)
    3. JSON text content (raw json string)

    Guarantees:
    - Never returns None for 'data' or 'items'.
    - Preserves candidate_id, job_id, sources, document_type, and evidence chunks.
    - Provides both 'evidence' and 'data["items"]' for evidence tools so that any
      caller convention works stably.
    """
    if raw_result is None:
        return {
            "status": "error",
            "tool": tool_name,
            "candidate_id": None,
            "job_id": None,
            "evidence": [],
            "sources": [],
            "data": {"items": []},
            "error_code": "EMPTY_RESPONSE",
            "message": "Tool returned an empty response.",
        }

    # 1. Handle Pydantic models
    if hasattr(raw_result, "model_dump") and callable(raw_result.model_dump):
        raw_result = raw_result.model_dump(mode="json")
    elif hasattr(raw_result, "dict") and callable(raw_result.dict):
        raw_result = raw_result.dict()

    # 2. Handle MCP Content Wrapper object (e.g. CallToolResult with .content)
    if hasattr(raw_result, "content") and not isinstance(raw_result, dict):
        content_items = getattr(raw_result, "content", None)
        extracted_text = None
        if isinstance(content_items, list):
            for item in content_items:
                txt = getattr(item, "text", None) or (item.get("text") if isinstance(item, dict) else None)
                if txt:
                    extracted_text = txt
                    break
        elif isinstance(content_items, str):
            extracted_text = content_items
        raw_result = extracted_text if extracted_text is not None else {}

    # 3. Handle JSON text content
    if isinstance(raw_result, str):
        cleaned = raw_result.strip()
        try:
            parsed = json.loads(cleaned)
            raw_result = parsed
        except Exception:
            raw_result = {
                "status": "success",
                "tool": tool_name,
                "message": cleaned,
                "evidence": [],
                "data": {"items": []},
            }

    # 4. Handle dict that wraps MCP content: {"content": [{"type": "text", "text": "..."}]}
    if isinstance(raw_result, dict) and "content" in raw_result and isinstance(raw_result["content"], list):
        found_parsed = None
        for item in raw_result["content"]:
            txt = item.get("text") if isinstance(item, dict) else getattr(item, "text", None)
            if txt:
                try:
                    parsed = json.loads(txt)
                    if isinstance(parsed, dict):
                        found_parsed = parsed
                        break
                except Exception:
                    pass
        if found_parsed is not None:
            raw_result = found_parsed

    # Ensure raw_result is a dictionary
    if not isinstance(raw_result, dict):
        if isinstance(raw_result, list):
            raw_result = {
                "status": "success",
                "tool": tool_name,
                "evidence": raw_result,
                "data": {"items": raw_result},
            }
        else:
            raw_result = {
                "status": "success",
                "tool": tool_name,
                "message": str(raw_result),
                "evidence": [],
                "data": {"items": []},
            }

    status = raw_result.get("status") or "success"
    tool = raw_result.get("tool") or tool_name
    error_code = raw_result.get("error_code")
    message = raw_result.get("message")
    candidate_id = raw_result.get("candidate_id")
    job_id = raw_result.get("job_id")

    # Extract evidence list
    evidence = raw_result.get("evidence")
    if evidence is None:
        raw_data = raw_result.get("data")
        if isinstance(raw_data, dict):
            evidence = raw_data.get("items") or raw_data.get("evidence")
        if evidence is None:
            if isinstance(raw_result.get("items"), list):
                evidence = raw_result.get("items")
            elif isinstance(raw_result.get("results"), list):
                evidence = raw_result.get("results")

    if evidence is not None and not isinstance(evidence, list):
        evidence = [evidence]

    # Normalize data payload (MUST NEVER BE None!)
    data = raw_result.get("data")
    if data is None or not isinstance(data, dict):
        if evidence is not None:
            data = {"items": evidence}
        else:
            data = {}
    else:
        data = dict(data)
        if evidence is not None and "items" not in data:
            data["items"] = evidence
        elif "items" in data and evidence is None:
            evidence = data["items"]

    # Extract sources
    sources = raw_result.get("sources")
    if not sources and evidence:
        sources = list({
            item.get("source") for item in evidence
            if isinstance(item, dict) and item.get("source")
        })
    elif sources is None:
        sources = []

    # Preserve candidate_id / job_id from evidence items if missing at top-level
    if not candidate_id and evidence:
        for item in evidence:
            if isinstance(item, dict) and item.get("candidate_id"):
                candidate_id = item["candidate_id"]
                break

    if not job_id and evidence:
        for item in evidence:
            if isinstance(item, dict) and item.get("job_id"):
                job_id = item["job_id"]
                break

    return {
        "status": status,
        "tool": tool,
        "candidate_id": candidate_id,
        "job_id": job_id,
        "evidence": evidence if evidence is not None else [],
        "sources": sources,
        "data": data,
        "error_code": error_code,
        "message": message,
    }


class MCPClientError(Exception):
    """Exception raised for MCP client failures."""
    def __init__(self, message: str, error_code: str = "CLIENT_ERROR", retryable: bool = False):
        super().__init__(message)
        self.error_code = error_code
        self.retryable = retryable


class CAPABLMCPClient:
    """
    Authoritative MCP Client managing discovery, invocation, timeouts,
    and failure classification across the MCP external tool boundary.
    """

    normalize_response = staticmethod(normalize_mcp_response)

    def __init__(
        self,
        transport_config: Optional[MCPTransportConfig] = None,
        evidence_service: Optional[EvidenceService] = None,
        calendar_service: Optional[MockCalendarService] = None,
    ):
        self.config = transport_config or DEFAULT_TRANSPORT_CONFIG
        self.adapters = MCPToolAdapters(
            evidence_service=evidence_service,
            calendar_service=calendar_service,
        )

    def list_tools(self) -> List[Dict[str, Any]]:
        """Discover all approved tools exposed by the MCP server."""
        tools_list = []
        for name, defn in MCP_TOOL_REGISTRY.items():
            tools_list.append({
                "name": defn.name,
                "description": defn.description,
                "input_schema": defn.input_schema.model_json_schema(),
                "sensitivity": defn.sensitivity,
                "authorization_requirement": defn.authorization_requirement,
                "is_consequential": defn.is_consequential,
                "allows_state_mutation": defn.allows_state_mutation,
                "timeout_seconds": defn.timeout_seconds,
            })
        return tools_list

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an approved MCP tool with timeout bounding and error classification.
        """
        start_time = time.time()

        # 1. Check approval in registry
        if not is_tool_approved(tool_name):
            msg = f"Tool '{tool_name}' is not in approved MCP registry. Execution rejected."
            DEFAULT_AUDIT_LOGGER.log_event(
                event="mcp_tool_blocked",
                status="blocked",
                payload={"reason": "UNAPPROVED_TOOL", "requested_tool": tool_name},
            )
            blocked_resp = MCPToolResponse.blocked(
                tool=tool_name,
                message=msg,
                error_code="UNAPPROVED_TOOL",
            ).model_dump(mode="json")
            return normalize_mcp_response(blocked_resp, tool_name=tool_name)

        tool_def = get_tool_definition(tool_name)
        timeout = tool_def.timeout_seconds if tool_def else self.config.timeout_seconds

        # 2. Dispatch to adapter with bounded execution
        try:
            if tool_name == "get_candidate_evidence":
                result = self.adapters.get_candidate_evidence(
                    candidate_id=arguments.get("candidate_id", ""),
                    query=arguments.get("query", ""),
                    top_k=arguments.get("top_k", 4),
                )
            elif tool_name == "get_job_evidence":
                result = self.adapters.get_job_evidence(
                    job_id=arguments.get("job_id", ""),
                    query=arguments.get("query", ""),
                    top_k=arguments.get("top_k", 4),
                )
            elif tool_name == "get_policy_evidence":
                result = self.adapters.get_policy_evidence(
                    query=arguments.get("query", ""),
                    category=arguments.get("category"),
                    top_k=arguments.get("top_k", 4),
                )
            elif tool_name == "search_interview_slots":
                result = self.adapters.search_interview_slots(
                    candidate_id=arguments.get("candidate_id"),
                    job_id=arguments.get("job_id"),
                    date=arguments.get("date"),
                    start_date=arguments.get("start_date"),
                    end_date=arguments.get("end_date"),
                    duration_minutes=arguments.get("duration_minutes"),
                    timezone=arguments.get("timezone", "Asia/Kolkata"),
                )
            elif tool_name == "book_interview":
                result = self.adapters.book_interview(
                    slot_id=arguments.get("slot_id", ""),
                    candidate_id=arguments.get("candidate_id", ""),
                    job_id=arguments.get("job_id", ""),
                    confirmed=arguments.get("confirmed", False),
                    notes=arguments.get("notes"),
                )
            else:
                dispatch_err = MCPToolResponse.blocked(
                    tool=tool_name,
                    message=f"No dispatcher configured for '{tool_name}'.",
                    error_code="DISPATCH_ERROR",
                ).model_dump(mode="json")
                return normalize_mcp_response(dispatch_err, tool_name=tool_name)

            # Check if duration exceeded timeout
            duration = time.time() - start_time
            if duration > timeout:
                logger.warning("Tool %s completed in %.2fs, exceeding timeout %.2fs", tool_name, duration, timeout)

            return normalize_mcp_response(result, tool_name=tool_name)

        except Exception as e:
            duration = time.time() - start_time
            logger.error("Client error executing MCP tool %s: %s", tool_name, e)
            err_resp = MCPToolResponse.error(
                tool=tool_name,
                message=f"Client encountered an error executing '{tool_name}': {str(e)}",
                error_code="EXECUTION_ERROR",
            ).model_dump(mode="json")
            return normalize_mcp_response(err_resp, tool_name=tool_name)

    def get_langchain_tools(self) -> List[BaseTool]:
        """
        Creates LangChain BaseTool wrappers for all approved MCP tools.
        Enables agent integration while preserving native CAPABL tools.
        """
        tools: List[BaseTool] = []

        # 1. Candidate Evidence MCP Tool
        @tool("mcp_candidate_evidence", args_schema=CandidateEvidenceInput)
        def mcp_candidate_evidence(candidate_id: str, query: str, top_k: int = 4) -> Dict[str, Any]:
            """
            [MCP Tool] Retrieve factual candidate qualifications from resume via external MCP boundary.
            Strictly scoped to candidate_id. Read-only.
            """
            return self.call_tool("get_candidate_evidence", {
                "candidate_id": candidate_id,
                "query": query,
                "top_k": top_k,
            })
        tools.append(mcp_candidate_evidence)

        # 2. Job Evidence MCP Tool
        @tool("mcp_job_evidence", args_schema=JobEvidenceInput)
        def mcp_job_evidence(job_id: str, query: str, top_k: int = 4) -> Dict[str, Any]:
            """
            [MCP Tool] Retrieve job description requirements via external MCP boundary.
            Strictly scoped to job_id. Read-only.
            """
            return self.call_tool("get_job_evidence", {
                "job_id": job_id,
                "query": query,
                "top_k": top_k,
            })
        tools.append(mcp_job_evidence)

        # 3. Policy Evidence MCP Tool
        @tool("mcp_policy_evidence", args_schema=PolicyEvidenceInput)
        def mcp_policy_evidence(query: str, category: Optional[str] = None, top_k: int = 4) -> Dict[str, Any]:
            """
            [MCP Tool] Retrieve authoritative company HR policy facts via external MCP boundary.
            Isolated from candidate and JD data. Read-only.
            """
            return self.call_tool("get_policy_evidence", {
                "query": query,
                "category": category,
                "top_k": top_k,
            })
        tools.append(mcp_policy_evidence)

        # 4. Search Interview Slots MCP Tool
        @tool("mcp_search_slots", args_schema=InterviewSearchInput)
        def mcp_search_slots(
            candidate_id: Optional[str] = None,
            job_id: Optional[str] = None,
            date: Optional[str] = None,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            duration_minutes: Optional[int] = None,
            timezone: Optional[str] = "Asia/Kolkata",
        ) -> Dict[str, Any]:
            """
            [MCP Tool] Search available interview slots in the calendar via external MCP boundary.
            Non-consequential read-only query.
            """
            return self.call_tool("search_interview_slots", {
                "candidate_id": candidate_id,
                "job_id": job_id,
                "date": date,
                "start_date": start_date,
                "end_date": end_date,
                "duration_minutes": duration_minutes,
                "timezone": timezone,
            })
        tools.append(mcp_search_slots)

        # 5. Book Interview MCP Tool
        @tool("mcp_book_interview", args_schema=BookingInput)
        def mcp_book_interview(
            slot_id: str,
            candidate_id: str,
            job_id: str,
            confirmed: bool = False,
            notes: Optional[str] = None,
        ) -> Dict[str, Any]:
            """
            [MCP Tool] Book an interview slot via external MCP boundary.
            Consequential state-changing operation: REQUIRES explicit confirmed=True.
            """
            return self.call_tool("book_interview", {
                "slot_id": slot_id,
                "candidate_id": candidate_id,
                "job_id": job_id,
                "confirmed": confirmed,
                "notes": notes,
            })
        tools.append(mcp_book_interview)

        return tools


# Backward compatibility bridge
class MCPClientBridge(CAPABLMCPClient):
    """Maintains backward compatibility with earlier milestone references."""
    def __init__(self, mcp_server_url: Optional[str] = None):
        cfg = MCPTransportConfig(server_url=mcp_server_url) if mcp_server_url else DEFAULT_TRANSPORT_CONFIG
        super().__init__(transport_config=cfg)
