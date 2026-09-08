# Quiz — M0

1. 以下哪个最准确地描述了 Agent 的定义？
   - A) 一个能够自主思考和行动的 AI 系统
   - B) 一个使用 LangChain Agent 类的程序
   - C) 一个有状态的运行时控制器，通过观察、决策、动作和终止来追求任务
   - D) 一个能够调用工具的 LLM

2. 在 Agent 运行时方程中，`Context` 是什么？
   - A) 完整的 State
   - B) 聊天历史
   - C) 为一次模型调用从 State、TaskSpec、Observation 等构建的选择性视图
   - D) System prompt

3. 以下哪个等式正确描述了状态转移？
   - A) `State = Model(Context)`
   - B) `State_(t+1) = Transition(State_t, Observation_t, Decision_t, ActionResult_t)`
   - C) `State = ChatHistory`
   - D) `State = Prompt + Response`

4. 一个 Agent 在运行时反复调用同一个工具，每次参数都相同，陷入无限循环。这属于哪个层级的故障？
   - A) Policy 失败
   - B) Action 失败
   - C) Control 失败
   - D) Observation 失败

5. 以下哪个陈述是正确的？
   - A) RAG = Agent
   - B) Tool calling = Agent
   - C) Multi-agent = 自动更好的 Agent
   - D) LLM != Agent
