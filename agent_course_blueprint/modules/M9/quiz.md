# Quiz — M9

1. 什么是 "composition before multi-agent" 原则？
   - A) 总是使用 multi-agent 系统
   - B) 优先使用 single-agent + tools，只在必要时使用 multi-agent
   - C) 先创建多个 agent，再组合它们
   - D) 不使用 composition 模式

2. Agent-as-tool 模式的主要优点是什么？
   - A) 允许 agent 之间共享所有状态
   - B) Coordinator 保持控制权，接口简单
   - C) 减少通信开销
   - D) 允许并行执行

3. Handoff 模式适用于什么场景？
   - A) 需要并行处理多个任务
   - B) 任务需要不同专业知识，或 agent 达到能力边界
   - C) 需要共享内存
   - D) 需要松耦合系统

4. Supervisor/Worker 模式中，supervisor 的主要职责是什么？
   - A) 执行所有任务
   - B) 分解任务，分配给 workers，聚合结果
   - C) 与 workers 共享状态
   - D) 监控 workers 的内部状态

5. Multi-agent 系统的主要挑战是什么？
   - A) 无法并行执行
   - B) 通信开销、协调复杂性、上下文泄漏风险、成本增加
   - C) 无法使用工具
   - D) 无法处理复杂任务
