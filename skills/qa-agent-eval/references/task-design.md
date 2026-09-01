# 自包含评测任务目录规范（qa-agent-eval）

## 三步走协议
env.reset() → harness.run(agent, task) → env.grade(run)

1. reset：加载任务可见描述与初始上下文（不含隐藏 rubric）。
2. run：Agent 在 harness 内执行，产生 trace、tool_calls、output。
3. grade：用隐藏 rubric 打分，产出 success(bool) 与 dims(五维度)。

## 目录结构（gen_task.py 生成）
```
<task_id>/
  task.md             # 可见任务（给 Agent）
  rubric_hidden.json  # 隐藏评分标准（不参与给 Agent）
  harness_stub.py     # 接入桩，实现 run_once()
  runs.jsonl          # 运行记录（run_once 写入）
```

## 隐藏 rubric 设计原则
- 评分细节（期望子串、禁止子串、工具序列、阈值）**绝不能出现在 task.md**。
- 通过 key 隔离：task.md 只描述目标与约束；rubric_hidden.json 持有判分逻辑。
- 防止「Reward Hacking」：用多信号（输出内容 + 工具序列 + 副作用校验），避免单点被钻空子。

## 多轮 / 工具环境
- 长程任务用多轮对话 + 工具调用；trace 记录每轮输入 / 输出 / 工具调用。
- 工具环境应是确定性沙箱（同输入同输出），保证评测可复现。

## 示例 runs.jsonl 单行
```json
{"task_id":"agent_task_001","success":true,"output":"...","tool_calls":[{"name":"search","correct":true}],"dims":{"task_completion":1.0,"tool_use":1.0,"planning":0.8,"memory":0.7,"reliability":0.9},"trace":"..."}
```
