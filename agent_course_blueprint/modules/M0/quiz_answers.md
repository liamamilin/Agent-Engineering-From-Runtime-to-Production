# Quiz Answers — M0

1. **C**
   
   解释：Agent 是一个有状态的运行时控制器，它通过反复观察环境、构建决策上下文、通过策略选择动作、更新状态，并根据明确的条件终止来追求任务。A 过于拟人化，B 将 Agent 等同于特定框架，D 只描述了工具调用能力。

2. **C**
   
   解释：Context 是为一次模型调用从 State、TaskSpec、Observation 等构建的选择性视图。它不是完整的 State（A），不是聊天历史（B），也不仅仅是 system prompt（D）。Context 是构建的，不是直接传递的。

3. **B**
   
   解释：状态转移是确定性的更新：`State_(t+1) = Transition(State_t, Observation_t, Decision_t, ActionResult_t)`。A 将 State 等同于 Model 输出，C 将 State 等同于 ChatHistory，D 将 State 等同于 Prompt + Response，都是错误的简化。

4. **C**
   
   解释：这是 Control 层级的故障——编排失败，循环重复。Policy 可能正确地决定了调用工具，但 Control 层没有检测到重复并中断循环。这不是 Action 失败（工具执行成功），也不是 Observation 失败（观察正确）。

5. **D**
   
   解释：LLM != Agent。LLM 是组件，Agent 是系统。A 错误：RAG 是信息获取模式，Agent 是运行时控制器。B 错误：Tool calling 是动作，Agent 是决策循环。C 错误：Multi-agent 不自动意味着更好，它引入了额外的复杂性。
