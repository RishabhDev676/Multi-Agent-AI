# agents.py
from openrouter import call_model
import json

def agent_planner(user_input: str) -> str:
    prompt = [
        {"role": "system", "content": "You are AGENT PLANNER. Produce a clear, numbered step plan."},
        {"role": "user", "content": user_input}
    ]
    return call_model("mistralai/devstral-2512:free", prompt)

def agent_analyzer(plan: str) -> str:
    prompt = [
        {"role": "system", "content": "You are AGENT ANALYZER. Critique, correct errors, and improve the plan."},
        {"role": "user", "content": plan}
    ]
    return call_model("amazon/nova-2-lite-v1:free", prompt)

def agent_executor(analysis: str) -> str:
    prompt = [
        {"role": "system", "content": "You are AGENT EXECUTOR. Produce concrete deliverables or outputs implementing the plan."},
        {"role": "user", "content": analysis}
    ]
    return call_model("tngtech/tng-r1t-chimera:free", prompt)

def agent_referee(logs: dict) -> str:
    prompt = [
        {"role": "system", "content": "You are AGENT REFEREE. Check other agents for mistakes, contradictions, or hallucinations. Provide final verdict and improvements."},
        {"role": "user", "content": json.dumps(logs, indent=2)}
    ]
    return call_model("tngtech/deepseek-r1t2-chimera:free", prompt)
