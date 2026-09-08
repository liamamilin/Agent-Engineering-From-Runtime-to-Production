# Quiz — M5

1. Context 和 State 的区别是什么？
   - A) 没有区别
   - B) Context 是 State 的子集，是为模型调用构建的视图
   - C) State 是 Context 的子集
   - D) Context 包含所有信息，State 只包含当前信息

2. 为什么需要 token budget？
   - A) 为了节省成本
   - B) 因为模型有上下文长度限制
   - C) 为了加快响应速度
   - D) 所有以上

3. CRITICAL 优先级的项应该如何处理？
   - A) 可以丢弃如果超过预算
   - B) 总是包含，即使超过预算
   - C) 截断后包含
   - D) 只在有空间时包含

4. 哪种压缩策略适合保留最近信息？
   - A) Truncation
   - B) Summarization
   - C) Sliding Window
   - D) Random Selection

5. Prompt injection 的风险是什么？
   - A) 模型响应变慢
   - B) 不可信内容可能覆盖系统指令
   - C) Token 使用增加
   - D) 输出格式错误
