# Quiz Answers — M5

1. **B**
   
   解释：Context 是 State 的子集，是为模型调用构建的视图。State 包含所有运行时信息，Context 是为特定调用选择的。A 错误：它们有明确区别。C 错误：说反了。D 错误：也说反了。

2. **D**
   
   解释：Token budget 是必要的，因为模型有上下文长度限制（B），同时也为了节省成本（A）和控制响应时间（C）。所有选项都是正确的原因。

3. **B**
   
   解释：CRITICAL 优先级的项（如 system prompt、task）应该总是包含，即使超过预算。这些是 Agent 正常运行的基础。A 错误：CRITICAL 项不应该被丢弃。C 错误：截断可能破坏关键信息。D 错误：CRITICAL 项必须包含。

4. **C**
   
   解释：Sliding Window 策略保留最近的 N 项，适合需要保留最近信息的场景。A 错误：Truncation 是截断单个项。B 错误：Summarization 是总结内容。D 错误：Random Selection 不保留最近信息。

5. **B**
   
   解释：Prompt injection 的风险是不可信内容可能覆盖系统指令，让 Agent 执行恶意操作。A 错误：响应速度不是主要风险。C 错误：Token 使用不是安全风险。D 错误：输出格式不是核心问题。
