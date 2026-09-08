from agent_course.core import TaskSpec, Observation, AgentState, Decision, Transition, TerminationPolicy, TerminationReason


def simulate_run():
    """Simulate a 3-step agent run and return the trace."""
    task = TaskSpec(
        goal="Find information about Python and summarize it",
        success_criteria=["Summary provided"],
        max_steps=10,
    )
    state = AgentState(task=task)
    trace = []

    # Step 1: User input -> decide to call search tool
    obs1 = Observation.from_user("Find information about Python programming language")
    state.add_observation(obs1)
    decision1 = Decision.call_tool("search", {"query": "Python programming language"})
    result1 = {"results": ["Python is a high-level programming language", "Python supports multiple paradigms"]}
    state = Transition.apply(state, obs1, decision1, result1)
    trace.append({"step": 1, "observation": obs1, "decision": decision1, "result": result1})

    # Step 2: Tool result -> decide to call another tool
    obs2 = Observation.from_tool("search", result1)
    state.add_observation(obs2)
    decision2 = Decision.call_tool("get_details", {"topic": "Python features"})
    result2 = {"details": "Python features: dynamic typing, garbage collection, extensive standard library"}
    state = Transition.apply(state, obs2, decision2, result2)
    trace.append({"step": 2, "observation": obs2, "decision": decision2, "result": result2})

    # Step 3: Final decision
    obs3 = Observation.from_tool("get_details", result2)
    state.add_observation(obs3)
    decision3 = Decision.final_answer("Python is a high-level, dynamically typed programming language with extensive standard library.")
    state = Transition.apply(state, obs3, decision3)
    trace.append({"step": 3, "observation": obs3, "decision": decision3, "result": None})

    # Check termination
    policy = TerminationPolicy()
    should_stop, reason = policy.should_stop(task, state)

    return {
        "task": task,
        "state": state,
        "trace": trace,
        "should_stop": should_stop,
        "termination_reason": reason,
    }
