# Quiz — M1

1. ModelAdapter 的主要目的是什么？
   - A) 让 Agent 直接调用 OpenAI API
   - B) 封装 provider 差异，提供统一的模型接口
   - C) 替代 LangChain 的 LLM 类
   - D) 实现 Agent 的决策逻辑

2. 以下哪种消息角色用于传递工具执行结果？
   - A) system
   - B) user
   - C) assistant
   - D) tool

3. 为什么需要 FakeModel？
   - A) 因为它比真实模型更快
   - B) 因为它不需要 API key
   - C) 为了在没有网络或 API key 的情况下进行离线测试
   - D) 因为真实模型不支持工具调用

4. 结构化输出解析失败时，应该怎么做？
   - A) 忽略错误，使用默认值
   - B) 抛出异常，让调用者处理
   - C) 重新调用模型，直到成功
   - D) 使用正则表达式强制提取

5. 重试策略中，指数退避（exponential backoff）的目的是什么？
   - A) 加快重试速度
   - B) 减少重复请求对服务器的压力
   - C) 增加重试次数
   - D) 降低 token 消耗
