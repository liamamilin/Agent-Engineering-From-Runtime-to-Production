# Exercises — M0

## Exercise 1: System Classification

给定以下三个系统，分类每个系统是 LLM 调用、workflow 还是 Agent，并画出运行时对象和边界。

### System A: 聊天机器人

```python
def chat(user_message: str) -> str:
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": user_message}]
    )
    return response.choices[0].message.content
```

**问题**：
1. 这是 LLM 调用、workflow 还是 Agent？
2. 系统边界在哪里？
3. 有没有 State？有没有 Termination？

---

### System B: 固定审批流程

```python
def approval_process(request: dict) -> dict:
    # Step 1: 自动检查
    if request["amount"] > 10000:
        return {"status": "rejected", "reason": "Amount too high"}
    
    # Step 2: 经理审批
    manager_approved = call_manager_api(request)
    if not manager_approved:
        return {"status": "rejected", "reason": "Manager rejected"}
    
    # Step 3: 财务审批
    finance_approved = call_finance_api(request)
    if not finance_approved:
        return {"status": "rejected", "reason": "Finance rejected"}
    
    return {"status": "approved"}
```

**问题**：
1. 这是 LLM 调用、workflow 还是 Agent？
2. 控制流是预定义的还是动态的？
3. 如果需要在 Step 2 和 Step 3 之间根据请求内容动态决定是否跳过财务审批，需要添加什么？

---

### System C: 研究助手

```python
def research_assist(question: str) -> str:
    task = TaskSpec(goal=question, success_criteria=["Answer with evidence"])
    state = AgentState(task=task)
    
    while True:
        observation = get_latest_observation(state)
        context = build_context(task, state, observation, tools)
        decision = model.decide(context)
        
        if decision.kind == "tool":
            result = execute_tool(decision.name, decision.arguments)
            state = transition(state, observation, decision, result)
        elif decision.kind == "final":
            return decision.content
        elif decision.kind == "fail":
            raise Exception(decision.reason)
        
        if should_stop(task, state):
            break
```

**问题**：
1. 这是 LLM 调用、workflow 还是 Agent？
2. 识别代码中的 TaskSpec、Observation、State、Decision、Transition、Termination
3. 系统边界在哪里？哪些部分在边界内，哪些在边界外？

---

## Exercise 2: Runtime Object Mapping

对于以下场景，识别每个运行时对象：

**场景**：一个 Agent 帮助用户查找并总结 GitHub 上关于"LLM agent"的最新论文。

1. TaskSpec 应该包含什么？
2. 第一步的 Observation 可能是什么？
3. State 在第三步可能包含什么？
4. Context 是如何从 State 构建的？
5. 一个可能的 Decision 是什么？
6. 对应的 Action 是什么？
7. Transition 如何更新 State？
8. Termination 条件可能是什么？

---

## Exercise 3: Failure Classification

对于以下故障，判断它们属于哪个层级：

1. LLM 返回了错误的工具名称
2. 工具执行超时
3. 达到最大步数但任务未完成
4. 搜索结果没有被加入到最终答案的证据中
5. Agent 重复调用同一个工具，陷入死循环
6. 成功标准定义模糊，无法判断是否完成
7. 工具参数格式错误，执行失败
8. 上下文太长，超出了模型的 token 限制

---

## Exercise 4: System Boundary Drawing

画出一个 Agent 系统的边界图，包含以下组件：

- 用户
- TaskSpec
- State
- Context Builder
- Model
- Decision Validator
- Tool Executor
- 文件系统（作为环境）
- 数据库（作为环境）
- LLM API（作为环境）

标注哪些在 Agent 边界内，哪些在边界外。
