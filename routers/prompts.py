"""Prompt verification endpoints for system prompt pack validation"""
import os
import hashlib
from pathlib import Path
from typing import Dict, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/prompts", tags=["System Prompts"])


class PromptInfo(BaseModel):
    """Information about a loaded system prompt"""
    name: str
    path: str
    exists: bool
    size_bytes: int
    hash: str


class PromptVerification(BaseModel):
    """Verification result for prompt loading"""
    app: str
    prompts_loaded: int
    prompts_expected: int
    shared_directives_loaded: bool
    app_specific_loaded: bool
    total_size_bytes: int
    verification_hash: str
    prompts: List[PromptInfo]


def get_prompt_info(prompt_path: str) -> PromptInfo:
    """Get metadata about a prompt file"""
    path = Path(prompt_path)
    
    if not path.exists():
        return PromptInfo(
            name=path.name,
            path=prompt_path,
            exists=False,
            size_bytes=0,
            hash=""
        )
    
    content = path.read_text()
    file_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
    
    return PromptInfo(
        name=path.name,
        path=prompt_path,
        exists=True,
        size_bytes=len(content),
        hash=file_hash
    )


@router.get("/verify", response_model=PromptVerification)
async def verify_prompts():
    """
    Verify that system prompts are properly loaded.
    
    Returns verification status for:
    - shared_directives.prompt (global foundation)
    - scholarship_api.prompt (app-specific overlay)
    
    This endpoint validates the CEO directive's system prompt pack implementation.
    """
    prompt_dir = Path("docs/system-prompts")
    
    # Check shared directives
    shared_path = prompt_dir / "shared_directives.prompt"
    shared_info = get_prompt_info(str(shared_path))
    
    # Check app-specific prompt
    app_path = prompt_dir / "scholarship_api.prompt"
    app_info = get_prompt_info(str(app_path))
    
    prompts = [shared_info, app_info]
    total_size = sum(p.size_bytes for p in prompts if p.exists)
    
    # Create verification hash (both prompts combined)
    verification_content = ""
    if shared_info.exists:
        verification_content += shared_path.read_text()
    if app_info.exists:
        verification_content += app_path.read_text()
    
    verification_hash = hashlib.sha256(verification_content.encode()).hexdigest()[:16]
    
    return PromptVerification(
        app="scholarship_api",
        prompts_loaded=sum(1 for p in prompts if p.exists),
        prompts_expected=2,
        shared_directives_loaded=shared_info.exists,
        app_specific_loaded=app_info.exists,
        total_size_bytes=total_size,
        verification_hash=verification_hash,
        prompts=prompts
    )


@router.get("/list")
async def list_all_prompts():
    """
    List all system prompts in the ScholarshipAI ecosystem.
    
    Returns information about all 9 prompts:
    - 1 shared directive (global)
    - 8 app-specific overlays
    """
    prompt_dir = Path("docs/system-prompts")
    
    if not prompt_dir.exists():
        raise HTTPException(status_code=404, detail="Prompt directory not found")
    
    prompt_files = list(prompt_dir.glob("*.prompt"))
    
    prompts_info = []
    for prompt_file in sorted(prompt_files):
        info = get_prompt_info(str(prompt_file))
        prompts_info.append(info)
    
    return {
        "total_prompts": len(prompts_info),
        "prompts": prompts_info
    }


@router.get("/{prompt_name}")
async def get_prompt(prompt_name: str):
    """
    Retrieve a specific system prompt by name.
    
    Examples:
    - GET /api/prompts/shared_directives
    - GET /api/prompts/scholarship_api
    """
    # Remove .prompt extension if provided
    if prompt_name.endswith(".prompt"):
        prompt_name = prompt_name[:-7]
    
    prompt_path = Path(f"docs/system-prompts/{prompt_name}.prompt")
    
    if not prompt_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Prompt '{prompt_name}' not found. Available prompts: shared_directives, scholarship_api, student_pilot, provider_register, scholar_auth, auto_page_maker, scholarship_agent, scholarship_sage, executive_command_center"
        )
    
    content = prompt_path.read_text()
    
    return {
        "name": prompt_name,
        "path": str(prompt_path),
        "size_bytes": len(content),
        "hash": hashlib.sha256(content.encode()).hexdigest()[:16],
        "content": content
    }


@router.get("/merge/scholarship_api")
async def get_merged_prompt():
    """
    Get the merged prompt for Scholarship API (shared + app-specific).
    
    This is the actual prompt that should be used by the application,
    following the load order: shared_directives → scholarship_api.
    """
    shared_path = Path("docs/system-prompts/shared_directives.prompt")
    app_path = Path("docs/system-prompts/scholarship_api.prompt")
    
    if not shared_path.exists():
        raise HTTPException(status_code=404, detail="shared_directives.prompt not found")
    
    if not app_path.exists():
        raise HTTPException(status_code=404, detail="scholarship_api.prompt not found")
    
    shared_content = shared_path.read_text()
    app_content = app_path.read_text()
    
    # Merge with separator
    merged_content = f"{shared_content}\n\n---\n\n{app_content}"
    
    return {
        "app": "scholarship_api",
        "load_order": ["shared_directives.prompt", "scholarship_api.prompt"],
        "total_size_bytes": len(merged_content),
        "hash": hashlib.sha256(merged_content.encode()).hexdigest()[:16],
        "content": merged_content
    }
