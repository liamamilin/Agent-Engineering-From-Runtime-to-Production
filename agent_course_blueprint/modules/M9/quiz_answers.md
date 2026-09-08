# Quiz Answers — M9

1. **B**
   
   解释：Composition before multi-agent 原则是优先使用 single-agent + tools，只在必要时使用 multi-agent。Multi-agent 系统增加了复杂性、通信开销和成本，应该只在 single-agent 无法解决问题时才使用。

2. **B**
   
   解释：Agent-as-tool 模式的主要优点是 Coordinator 保持控制权，接口简单。Coordinator agent 调用 specialized agent 就像调用普通工具一样，不需要复杂的通信协议。Specialized agent 的内部状态对 coordinator 是隐藏的。

3. **B**
   
   解释：Handoff 模式适用于任务需要不同专业知识，或 agent 达到能力边界的场景。当一个 agent 发现自己无法继续处理任务时，可以将控制权转移给更适合的 agent。这不是并行处理，而是顺序处理。

4. **B**
   
   解释：Supervisor/Worker 模式中，supervisor 的主要职责是分解任务，分配给 workers，聚合结果。Supervisor 不直接执行任务，而是协调 workers 的工作。Supervisor 不应该监控 workers 的内部状态，只关注任务结果。

5. **B**
   
   解释：Multi-agent 系统的主要挑战是通信开销、协调复杂性、上下文泄漏风险、成本增加。这些挑战使得 multi-agent 系统比 single-agent 系统更复杂、更昂贵、更容易出错。因此应该谨慎使用。
