from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.llm_config import get_llm
from tools.iac_parser import parse_terraform, summarize_terraform
from tools.security_scanner import run_checkov, format_security_findings


class ReviewState(TypedDict):
    terraform_path: str
    parsed_iac: dict
    terraform_summary: str
    security_findings: dict
    security_review: str
    cost_review: str
    best_practices_review: str
    final_report: str
    error: str


llm = get_llm(temperature=0.1)


def iac_parser_agent(state: ReviewState) -> ReviewState:
    print("🔍 IaC Parser Agent running...")
    try:
        parsed = parse_terraform(state["terraform_path"])
        summary = summarize_terraform(parsed)
        return {**state, "parsed_iac": parsed, "terraform_summary": summary, "error": ""}
    except Exception as e:
        return {**state, "error": str(e)}


def security_agent(state: ReviewState) -> ReviewState:
    print("🔐 Security Agent running...")
    findings = run_checkov(state["terraform_path"])
    checkov_report = format_security_findings(findings)

    prompt = f"""You are a Cloud Security Expert reviewing Terraform infrastructure.

## Terraform Resources:
{state["terraform_summary"]}

## Automated Security Scan (Checkov):
{checkov_report}

Provide a security review with:
1. CRITICAL issues (must fix before deployment)
2. HIGH issues (fix soon)
3. MEDIUM issues (best practice improvements)

For each issue, explain what the problem is, why it's a risk, and provide an exact fix with code example."""

    response = llm.invoke([HumanMessage(content=prompt)])
    return {**state, "security_findings": findings, "security_review": response.content}


def cost_agent(state: ReviewState) -> ReviewState:
    print("💰 Cost Agent running...")

    prompt = f"""You are a Cloud Cost Optimization Expert reviewing Terraform infrastructure.

## Terraform Resources:
{state["terraform_summary"]}

Provide:
1. Estimated monthly cost for each major resource
2. Over-provisioned resources that should be downsized
3. Cost optimization recommendations
4. Total estimated monthly cost before and after optimizations"""

    response = llm.invoke([HumanMessage(content=prompt)])
    return {**state, "cost_review": response.content}


def best_practices_agent(state: ReviewState) -> ReviewState:
    print("📋 Best Practices Agent running...")

    prompt = f"""You are an AWS Well-Architected Framework Expert reviewing Terraform infrastructure.

## Terraform Resources:
{state["terraform_summary"]}

Review against the 6 pillars:
1. Operational Excellence
2. Security
3. Reliability
4. Performance Efficiency
5. Cost Optimization
6. Sustainability

For each pillar give current state, specific recommendations, and priority (High/Medium/Low)."""

    response = llm.invoke([HumanMessage(content=prompt)])
    return {**state, "best_practices_review": response.content}


def writer_agent(state: ReviewState) -> ReviewState:
    print("✍️  Writer Agent running...")

    prompt = f"""You are a technical writer compiling an architecture review report.

## Security Review:
{state.get("security_review", "N/A")}

## Cost Review:
{state.get("cost_review", "N/A")}

## Best Practices Review:
{state.get("best_practices_review", "N/A")}

Create a final report with:
1. Executive Summary (with overall health score out of 10)
2. 🔴 Critical Issues
3. 🟡 Important Improvements
4. 🟢 Recommendations
5. 💰 Cost Summary
6. Next Steps"""

    response = llm.invoke([HumanMessage(content=prompt)])
    return {**state, "final_report": response.content}


def check_error(state: ReviewState) -> str:
    if state.get("error"):
        return "error"
    return "continue"


def build_graph():
    graph = StateGraph(ReviewState)
    graph.add_node("iac_parser", iac_parser_agent)
    graph.add_node("security_agent", security_agent)
    graph.add_node("cost_agent", cost_agent)
    graph.add_node("best_practices_agent", best_practices_agent)
    graph.add_node("writer_agent", writer_agent)
    graph.set_entry_point("iac_parser")
    graph.add_conditional_edges("iac_parser", check_error, {"error": END, "continue": "security_agent"})
    graph.add_edge("security_agent", "cost_agent")
    graph.add_edge("cost_agent", "best_practices_agent")
    graph.add_edge("best_practices_agent", "writer_agent")
    graph.add_edge("writer_agent", END)
    return graph.compile()


def run_review(terraform_path: str) -> dict:
    graph = build_graph()
    initial_state = ReviewState(
        terraform_path=terraform_path,
        parsed_iac={},
        terraform_summary="",
        security_findings={},
        security_review="",
        cost_review="",
        best_practices_review="",
        final_report="",
        error=""
    )
    print(f"\n🚀 Starting Architecture Review for: {terraform_path}\n")
    print("=" * 60)
    result = graph.invoke(initial_state)
    if result.get("error"):
        print(f" Error: {result['error']}")
    else:
        print("\n Review Complete!")
    return result


if __name__ == "__main__":
    result = run_review("./sample_terraform")
    print("\n\nFINAL REPORT")
    print("=" * 60)
    print(result.get("final_report", "No report generated"))