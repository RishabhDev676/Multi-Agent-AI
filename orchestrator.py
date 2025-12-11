# orchestrator.py
from agents import agent_planner, agent_analyzer, agent_executor, agent_referee
import time

def run_agents(user_input: str, debug: bool = True) -> dict:
    """
    Sequential pipeline:
       planner -> analyzer -> executor -> referee
    Returns logs with timestamps.
    """
    logs = {"input": user_input, "timeline": []}
    start = time.time()

    if debug: print("==> Starting planner")
    planner_out = agent_planner(user_input)
    logs["planner"] = planner_out
    logs["timeline"].append({"agent": "planner", "output": planner_out, "time": time.time() - start})
    if debug: print("Planner output:\n", planner_out)

    if debug: print("==> Starting analyzer")
    analyzer_out = agent_analyzer(planner_out)
    logs["analyzer"] = analyzer_out
    logs["timeline"].append({"agent": "analyzer", "output": analyzer_out, "time": time.time() - start})
    if debug: print("Analyzer output:\n", analyzer_out)

    if debug: print("==> Starting executor")
    executor_out = agent_executor(analyzer_out)
    logs["executor"] = executor_out
    logs["timeline"].append({"agent": "executor", "output": executor_out, "time": time.time() - start})
    if debug: print("Executor output:\n", executor_out)

    if debug: print("==> Starting referee")
    referee_out = agent_referee({
        "planner": planner_out,
        "analyzer": analyzer_out,
        "executor": executor_out
    })
    logs["referee"] = referee_out
    logs["timeline"].append({"agent": "referee", "output": referee_out, "time": time.time() - start})
    if debug: print("Referee output:\n", referee_out)

    logs["duration_seconds"] = time.time() - start
    return logs
