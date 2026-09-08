# Quiz — M3

1. Agent 控制循环的正确顺序是什么？
   - A) Decide -> Observe -> Act -> Transition
   - B) Observe -> Decide -> Act -> Transition
   - C) Act -> Observe -> Decide -> Transition
   - D) Transition -> Observe -> Decide -> Act

2. State 和 Messages 的区别是什么？
   - A) State 是序列化的，Messages 是结构化的
   - B) State 是运行时信息，Messages 是模型交互的视图
   - C) 没有区别，它们是同义词
   - D) State 只包含工具结果，Messages 包含所有信息

3. 为什么终止原因（termination reason）很重要？
   - A) 用于计算成本
   - B) 用于调试和评估，区分成功、失败和预算耗尽
   - C) 用于选择下一个模型
   - D) 不重要，可以忽略

4. 如果模型返回空响应，Agent 应该怎么做？
   - A) 继续循环
   - B) 返回成功
   - C) 产生 fail 决策并终止
   - D) 重试无限次

5. 为什么用确定性控制器包裹概率性策略？
   - A) 让 Agent 更快
   - B) 让 Agent 行为可审计、可调试、可控制
   - C) 减少 token 使用
   - D) 让代码更简洁
