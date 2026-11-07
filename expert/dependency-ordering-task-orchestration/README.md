# Dependency Management & Task Orchestration

Code for the **[Dependency Management & Task Orchestration](https://www.nautomationprime.io/foundation/tutorials/expert/dependency-ordering-task-orchestration/)** lesson on Nautomation Prime.

> Coordinate complex multi-device workflows. Task DAGs, dependency ordering, and safe parallel execution. Orchestrate enterprise automation at scale.

Work through the lesson first: it explains every file here. Use this folder to
check your own code, or to skip the typing when you just want to run it.

## Files

| File | From the lesson section |
|---|---|
| `src/conditional_execution.py` | Pattern 3: Conditional Task Execution |
| `src/nornir_orchestration.py` | Pattern 2: Nornir-Based Orchestration |
| `src/orchestrator_example.py` | Pattern 1: Task DAG (Directed Acyclic Graph) → Usage Example |
| `src/parallel_subtasks.py` | Pattern 4: Parallelizable Subtasks |
| `src/task_orchestrator.py` | Pattern 1: Task DAG (Directed Acyclic Graph) → The Implementation |
| `src/visualize_plan.py` | Advanced: Visualizing Execution Plans |

## Run it

```bash
python -m venv .venv
source .venv/bin/activate      # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

This lesson's modules import each other by name (`from conditional_execution import ...`
and so on), so run the examples from inside `src/`:

```bash
cd src
python <example>.py
```

Anything that connects to a device needs a lab. Edit the inventory, testbed or
device details to point at your own lab equipment first, and never run a
tutorial against production.

---

[← Back to the lesson](https://www.nautomationprime.io/foundation/tutorials/expert/dependency-ordering-task-orchestration/) · [All lessons](../../README.md)
