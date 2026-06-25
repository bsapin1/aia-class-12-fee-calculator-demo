from __future__ import annotations

import json
from typing import Any

from calculators.config_loader import load_market_rates
from services.claude_client import call_claude_json, call_claude_text


PROJECT_ANALYSIS_SYSTEM = (
    "You are an architectural fee consultant for U.S. projects. "
    "Return valid JSON only with no markdown fences."
)

PROPOSAL_SYSTEM = (
    "You are an architectural practice consultant writing clear, professional "
    "fee proposal language. Use plain English. Do not invent specific contract terms."
)


def analyze_project_description(description: str) -> dict[str, Any]:
    benchmarks = load_market_rates()
    prompt = f"""Analyze this architectural project description and suggest calculator inputs.

Project description:
{description}

Available project types: {list(benchmarks['project_types'].keys())}
Available regions: {list(benchmarks['regions'].keys())}

Return JSON with this schema:
{{
  "project_type": "one of the project type keys",
  "region": "one of the region keys",
  "construction_budget": number,
  "fee_percentage": number,
  "total_weeks": number,
  "include_ca": boolean,
  "include_bidding": boolean,
  "complexity": "simple|standard|complex",
  "estimated_arch_sheets": number,
  "rationale": "2-3 sentences explaining your suggestions",
  "risks": ["risk1", "risk2"]
}}

Base suggestions on typical U.S. market practice. Stay within reasonable ranges from the benchmarks.
Benchmarks reference:
{json.dumps(benchmarks['project_types'], indent=2)}
"""
    return call_claude_json(PROJECT_ANALYSIS_SYSTEM, prompt)


def advise_on_fee(
    project_summary: dict[str, Any],
    fee_result: dict[str, Any],
    comparison: dict[str, Any],
) -> str:
    prompt = f"""Review this architectural fee estimate and provide brief advisory commentary.

Project:
{json.dumps(project_summary, indent=2, default=str)}

Fee result:
{json.dumps(fee_result, indent=2, default=str)}

Market comparison:
{json.dumps(comparison, indent=2, default=str)}

In 3-5 short paragraphs, cover:
1. Whether the fee appears reasonable for the project type and region
2. Phase allocation observations
3. Any risks or assumptions to flag for the client
4. One practical recommendation

Do not recalculate fees. Reference the numbers provided.
"""
    return call_claude_text(PROPOSAL_SYSTEM, prompt)


def generate_proposal_narrative(
    project_summary: dict[str, Any],
    fee_result: dict[str, Any],
) -> str:
    prompt = f"""Write a client-facing fee proposal narrative (250-400 words) for an architectural services engagement.

Project:
{json.dumps(project_summary, indent=2, default=str)}

Fee summary:
{json.dumps(fee_result, indent=2, default=str)}

Include: scope overview, total fee, phase breakdown summary, schedule overview, and assumptions.
Tone: professional, clear, not overly legalistic.
"""
    return call_claude_text(PROPOSAL_SYSTEM, prompt)
