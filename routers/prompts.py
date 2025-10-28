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
    architecture: str  # "universal" or "individual"


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
    
    Supports two loading strategies:
    1. Universal: shared_directives.prompt + universal.prompt (with app overlay selection)
    2. Individual: shared_directives.prompt + scholarship_api.prompt
    
    This endpoint validates the CEO directive's system prompt pack implementation.
    """
    prompt_dir = Path("docs/system-prompts")
    
    # Check shared directives (always required)
    shared_path = prompt_dir / "shared_directives.prompt"
    shared_info = get_prompt_info(str(shared_path))
    
    # Check for universal prompt (v1.0.0 architecture)
    universal_path = prompt_dir / "universal.prompt"
    universal_info = get_prompt_info(str(universal_path))
    
    # Check app-specific prompt (individual file approach)
    app_path = prompt_dir / "scholarship_api.prompt"
    app_info = get_prompt_info(str(app_path))
    
    # Determine loading strategy (prefer universal if available)
    if universal_info.exists:
        # Universal prompt architecture (v1.0.0)
        prompts = [shared_info, universal_info]
        app_specific_loaded = True  # App overlay [APP: scholarship_api] is in universal.prompt
        architecture = "universal"
    else:
        # Individual file architecture
        prompts = [shared_info, app_info]
        app_specific_loaded = app_info.exists
        architecture = "individual"
    
    total_size = sum(p.size_bytes for p in prompts if p.exists)
    
    # Create verification hash (combined prompts)
    verification_content = ""
    for prompt in prompts:
        if prompt.exists:
            path = Path(prompt.path)
            verification_content += path.read_text()
    
    verification_hash = hashlib.sha256(verification_content.encode()).hexdigest()[:16]
    
    return PromptVerification(
        app="scholarship_api",
        prompts_loaded=sum(1 for p in prompts if p.exists),
        prompts_expected=2,
        shared_directives_loaded=shared_info.exists,
        app_specific_loaded=app_specific_loaded,
        total_size_bytes=total_size,
        verification_hash=verification_hash,
        prompts=prompts,
        architecture=architecture
    )


@router.get("/list")
async def list_all_prompts():
    """
    List all system prompts in the ScholarshipAI ecosystem.
    
    Returns information about all prompts:
    - 1 shared directive (global)
    - 1 universal prompt (all 8 app overlays) OR 8 individual app prompts
    """
    prompt_dir = Path("docs/system-prompts")
    
    if not prompt_dir.exists():
        raise HTTPException(status_code=404, detail="Prompt directory not found")
    
    prompt_files = list(prompt_dir.glob("*.prompt"))
    
    prompts_info = []
    for prompt_file in sorted(prompt_files):
        info = get_prompt_info(str(prompt_file))
        prompts_info.append(info)
    
    # Determine architecture
    has_universal = any(p.name == "universal.prompt" for p in prompts_info)
    architecture = "universal" if has_universal else "individual"
    
    return {
        "total_prompts": len(prompts_info),
        "architecture": architecture,
        "prompts": prompts_info
    }


@router.get("/{prompt_name}")
async def get_prompt(prompt_name: str):
    """
    Retrieve a specific system prompt by name.
    
    Examples:
    - GET /api/prompts/shared_directives
    - GET /api/prompts/universal
    - GET /api/prompts/scholarship_api
    """
    # Remove .prompt extension if provided
    if prompt_name.endswith(".prompt"):
        prompt_name = prompt_name[:-7]
    
    prompt_path = Path(f"docs/system-prompts/{prompt_name}.prompt")
    
    if not prompt_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Prompt '{prompt_name}' not found. Available prompts: shared_directives, universal, scholarship_api, student_pilot, provider_register, scholar_auth, auto_page_maker, scholarship_agent, scholarship_sage, executive_command_center"
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
    Get the merged prompt for Scholarship API.
    
    Load order (universal architecture):
    1. shared_directives.prompt
    2. universal.prompt → select [APP: scholarship_api] overlay
    
    Load order (individual architecture):
    1. shared_directives.prompt
    2. scholarship_api.prompt
    """
    shared_path = Path("docs/system-prompts/shared_directives.prompt")
    universal_path = Path("docs/system-prompts/universal.prompt")
    app_path = Path("docs/system-prompts/scholarship_api.prompt")
    
    if not shared_path.exists():
        raise HTTPException(status_code=404, detail="shared_directives.prompt not found")
    
    shared_content = shared_path.read_text()
    
    # Prefer universal architecture
    if universal_path.exists():
        universal_content = universal_path.read_text()
        merged_content = f"{shared_content}\n\n---\n\n{universal_content}"
        load_order = ["shared_directives.prompt", "universal.prompt"]
        architecture = "universal"
        note = "App overlay [APP: scholarship_api] is selected at runtime from universal.prompt"
    elif app_path.exists():
        app_content = app_path.read_text()
        merged_content = f"{shared_content}\n\n---\n\n{app_content}"
        load_order = ["shared_directives.prompt", "scholarship_api.prompt"]
        architecture = "individual"
        note = "Individual app-specific prompt loaded"
    else:
        raise HTTPException(
            status_code=404,
            detail="Neither universal.prompt nor scholarship_api.prompt found"
        )
    
    return {
        "app": "scholarship_api",
        "architecture": architecture,
        "load_order": load_order,
        "total_size_bytes": len(merged_content),
        "hash": hashlib.sha256(merged_content.encode()).hexdigest()[:16],
        "note": note,
        "content": merged_content
    }


@router.get("/overlay/{app_key}")
async def get_app_overlay(app_key: str):
    """
    Extract the app overlay from universal.prompt.
    
    Supports both v1.0 ([APP: {app_key}]) and v1.1 (### Overlay: {app_key}) formats.
    
    This endpoint is useful for verifying app-specific requirements
    when using the universal prompt architecture.
    """
    universal_path = Path("docs/system-prompts/universal.prompt")
    
    if not universal_path.exists():
        raise HTTPException(
            status_code=404,
            detail="universal.prompt not found. This endpoint only works with universal architecture."
        )
    
    content = universal_path.read_text()
    
    # Try v1.1 format first (### Overlay: {app_key})
    start_marker_v11 = f"### Overlay: {app_key}"
    end_marker_v11 = "### Overlay:"
    
    if start_marker_v11 in content:
        # v1.1 format
        start_idx = content.find(start_marker_v11)
        remaining = content[start_idx:]
        
        # Find next overlay section
        next_section_idx = remaining.find(end_marker_v11, len(start_marker_v11))
        
        if next_section_idx == -1:
            # Last overlay, find Section G or end
            next_section_idx = remaining.find("## Section G")
        
        if next_section_idx == -1:
            overlay_content = remaining
        else:
            overlay_content = remaining[:next_section_idx]
        
        overlay_content = overlay_content.strip()
        
        return {
            "app": app_key,
            "architecture": "universal",
            "version": "1.1",
            "overlay_size_bytes": len(overlay_content),
            "hash": hashlib.sha256(overlay_content.encode()).hexdigest()[:16],
            "content": overlay_content
        }
    
    # Try v1.0 format ([APP: {app_key}])
    start_marker_v10 = f"[APP: {app_key}]"
    end_marker_v10 = "[APP:"
    
    if start_marker_v10 in content:
        # v1.0 format
        start_idx = content.find(start_marker_v10)
        remaining = content[start_idx + len(start_marker_v10):]
        end_idx = remaining.find(end_marker_v10)
        
        if end_idx == -1:
            # Last app in the file, find operations section
            end_idx = remaining.find("[OPERATIONS:")
        
        if end_idx == -1:
            overlay_content = remaining
        else:
            overlay_content = remaining[:end_idx]
        
        overlay_content = overlay_content.strip()
        
        return {
            "app": app_key,
            "architecture": "universal",
            "version": "1.0",
            "overlay_size_bytes": len(overlay_content),
            "hash": hashlib.sha256(overlay_content.encode()).hexdigest()[:16],
            "content": overlay_content
        }
    
    # Not found
    raise HTTPException(
        status_code=404,
        detail=f"Overlay for '{app_key}' not found in universal.prompt. Available: executive_command_center, auto_page_maker, student_pilot, provider_register, scholarship_api, scholarship_agent, scholar_auth, scholarship_sage"
    )
