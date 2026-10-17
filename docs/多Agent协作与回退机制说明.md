# 多 Agent 协作与回退机制说明（面试要点）

> 用途：面试时快速对照「我做的每个设计决策 → 对应哪个 Multi-Agent 知识点」。
> 配套代码见 `src/`，真实运行日志见 `run_log.txt`，检查点见 `.checkpoints/main/`。

---

## 0. 一页速览：设计决策 → Multi-Agent 知识点

| # | 设计决策 | 落地代码 | 对应 Multi-Agent 知识点 |
|---|---|---|---|
| 1 | 层级流程，Manager 统一调度四个专员 | `crew.py` 的 `process=Process.hierarchical` | **Hierarchical Process / Manager Orchestration** |
| 2 | 每个专员 `allow_delegation=True` | `agents.py` 四个 Agent | **Task Delegation（Delegate Work Tool）** |
| 3 | 筛选专员对来源/时间存疑时主动问采集专员 | `tasks.py` filter_task 描述 | **Ask Question Tool / Inter-Agent Communication** |
| 4 | 摘要/归档任务挂 `guardrail` + `guardrail_max_retries` | `tasks.py` + `guardrails.py` | **Guardrails / Validation & Retry** |
| 5 | 下游发现上游不合格 → 回退给上游 | Manager 指令 + 护栏反馈（组合） | **Cross-Agent Fallback / Rework Loop** |
| 6 | Manager 按结果数量决定是否扩采集范围 | `agents.py` manager backstory | **Dynamic Task Planning** |
| 7 | `Crew(checkpoint=True)` 写状态快照 | `crew.py` | **Checkpointing / State Persistence** |

---

## 1. Hierarchical Process（Manager 动态调度）

**实现**：`Crew(process=Process.hierarchical, manager_agent=manager_agent)`。

- 与 `Process.sequential`（固定顺序执行）不同，层级流程下 Manager 会**根据任务类型和 Agent 能力动态分配任务**，并在每一步后校验结果。
- 我用**自定义 Manager**（`manager_agent`），把调度策略写进 backstory：按任务分派、检查产出、不合格退回、结果 < 3 条时扩范围。

**真实运行验证**：Manager 通过 `delegate_work_to_coworker` 工具依次把「采集 / 筛选 / 摘要 / 归档」委派给四个专员，每次拿到产出后再决策下一步。

**关键约束（源码级）**：自定义 `manager_agent` **不能挂自定义 tools**——CrewAI 会抛 `Manager agent should not have tools`。所以 Manager 只定义 role/goal/backstory。

---

## 2. Task Delegation（Delegate Work Tool）

**实现**：`Agent(allow_delegation=True)`，CrewAI 会自动给 Agent 挂上 **Delegate Work Tool** 和 **Ask Question Tool**。

**真实运行验证**：Manager 的委派全部成功（见日志中 `delegate_work_to_coworker` 的多次调用与返回）。

**⚠️ 重要发现（见第 8 节）**：在**层级流程 + 任务显式指定 `agent=`** 的组合下，**非 Manager 专员之间无法互相委派**——专员拿到的是「仅含自己」的协作名单。跨 Agent 委派必须由 Manager 完成。这正是「原生原语 vs 组合实现」要讲清楚的坑。

---

## 3. Ask Question Tool（主动询问）

**实现**：同样由 `allow_delegation=True` 带来。

- 场景：筛选专员对某条内容的来源/发布时间存疑 → 主动向采集专员询问。
- 我在 filter_task 描述里显式写了这条指令。

**真实运行说明**：本次模拟数据的来源/时间都明确，筛选专员**没有实际触发询问**（工具已挂载但未调用）。Ask 与 Delegate 的区别——Ask 是**同步获取信息**，Delegate 是**整块任务转交**。同样受第 8 节的作用域限制约束。

---

## 4. Guardrails & Retry（任务护栏与重试）

**实现**：`Task(guardrail=fn, guardrail_max_retries=3)`。

- 护栏签名：`guardrail(task_output) -> Tuple[bool, Any]`（必须是 `typing.Tuple`，小写 `tuple` 会被校验拒绝——真实踩过的坑）。
- `(True, 结果)` 通过；`(False, 反馈)` 不通过，失败原因注入 Agent 上下文触发重试。

**真实运行验证**：日志中出现两次 `🛡️ Guardrail Check → Guardrail Passed`（摘要护栏 + 日报完整性护栏），均一次性通过，未触发重试。

**面试要点（重试参数，容易考）**：

| 参数 | 作用域 | 语义 |
|---|---|---|
| `guardrail_max_retries` | Task | **护栏验证失败**后的重试（逻辑/质量不合格） |
| `max_retries` | Task | **技术性异常**（网络/超时）后的重试 |
| `max_retry_limit` | Agent | Agent 完成任务的重试上限 |

---

## 5. Cross-Agent Fallback（跨 Agent 回退）—— 重点

> **护栏重试 = 同 Agent 重做；真正的跨 Agent 回退 = Manager 动态重新分派。二者组合实现。**

1. **护栏层（同 Agent 重做）**：摘要/归档任务护栏发现质量问题 → 触发该任务重试。
2. **Manager 层（跨 Agent 回退）**：Manager backstory 明确写了一条准则——「发现下游判定上游不合格时，把任务回退给对应上游 Agent」。护栏失败信息进入 Manager 上下文，Manager 用 Delegate 工具把活退回**正确的上游 Agent**。

**真实运行验证**：归档环节发现第 5 条链接缺失时，**没有编造链接**，而是如实标注「(链接缺失，待补全)」并记录该待办——体现了「下游发现上游产出不完整 → 反馈而非硬编」的回退纪律。同时暴露了第 8 节的委派作用域限制。

---

## 6. Dynamic Task Planning（动态扩范围）

**实现**：写在 Manager backstory——「筛选后的相关条目 < 3 条时，要求采集专员扩大采集范围」。

**真实运行验证**：本次筛选出 8 条（≥ 3），Manager 在最终把关说明中明确写「数量门槛（通过）：保留 8 条 ≥ 3 条，无需退回采集专员扩大范围」——证明这条动态决策规则被 Manager 理解并执行了判断。

---

## 7. Checkpointing（状态快照与失败恢复）

**实现**：`Crew(checkpoint=True)`，默认在每个 `task_completed` 后写 `./.checkpoints/main/` 下的 JSON 快照。

**真实运行验证**：生成 4 个 JSON 快照（每个任务完成后一个，文件名带 `_p-` 父链引用，构成可回溯的检查点链）。

- 恢复：`crew.kickoff(from_checkpoint=CheckpointConfig(restore_from="./.checkpoints/main/<file>.json"))`，已完成任务被跳过。
- 还支持 `Crew.fork(config)` 从某检查点分叉实验分支。

**⚠️ 已知限制（运行时 UserWarning）**：`guardrail` 是普通 Python 函数，**无法 JSON 序列化**，因此**从检查点恢复后不会再跑护栏**。面试时可以主动提这个权衡。

---

## 8. 源码级发现：层级流程下的委派作用域（加分项）

真实运行中，摘要专员尝试 `delegate_work_to_coworker(coworker='采集专员')` 重取链接时失败，报：

```
Error executing tool. coworker mentioned not found, it must be one of the following options:
- ai内容摘要专家
```

追到 CrewAI 源码 `crew.py` 的 `_prepare_tools` / `_update_manager_tools`：

```python
# 层级流程下，只走 _update_manager_tools（不走给普通专员的 _add_delegation_tools）
if self.process == Process.hierarchical:
    if self.manager_agent:
        tools = self._update_manager_tools(task, tools)   # crew.py:1666
...

# _update_manager_tools 的关键分支：
if task.agent:
    tools = self._inject_delegation_tools(tools, task.agent, [task.agent])  # ← 只注入「自己」！
else:
    tools = self._inject_delegation_tools(tools, self.manager_agent, self.agents)  # ← 全量名单
```

**结论**：层级流程下，如果任务**显式指定了 `agent=`**，该专员拿到的 Delegate/Ask 工具的协作名单只有**它自己**（`[task.agent]`），等于禁用了专员之间的互相委派；只有**未指定 agent（由 Manager 动态分配）**时，Manager 才会拿到全量 `self.agents` 名单。

**面试怎么讲**：
- 一句话：「在层级流程里，跨 Agent 协调是**收口在 Manager** 的，专员之间的 Delegate/Ask 工具默认是自作用域，真正要跨 Agent 回退，得让 Manager 来重新分派。」
- 这正好印证了我第 5 节的设计：**跨 Agent 回退走 Manager，而不是让下游专员直接调上游**。

---

## 9. 运行观察（真实运行实录）

| 观察项 | 结果 |
|---|---|
| Manager 委派 | ✅ `delegate_work_to_coworker` 多次调用，成功委派 4 个专员 |
| 摘要护栏 | ✅ `Guardrail Check → Passed`（一次通过，未重试） |
| 日报护栏 | ✅ `Guardrail Check → Passed`（一次通过，未重试） |
| 检查点 | ✅ `.checkpoints/main/` 生成 4 个 JSON 快照 |
| 专员间委派 | ⚠️ 摘要专员委派「采集专员」失败（自作用域，见第 8 节） |
| 主动询问 | ⚠️ 工具已挂载但本次未触发（数据来源明确，无需询问） |
| 不编造原则 | ✅ 第 5 条链接缺失，未编造，如实标注占位 |
| API 错误 | ✅ 无（401 / 超时 / 余额不足均未出现） |
| Token 用量 | 65 次请求，总计 267,885 tokens（层级流程 Manager 协调 + verbose 循环开销较大） |

---

## 10. 关键 API 校正记录

1. 需求里的 `max_retry_limit` 易与护栏重试混淆 → 护栏重试实际是 **`guardrail_max_retries`**（默认 3）；`max_retry_limit` 是 Agent 级字段。
2. 护栏返回类型注解必须是 `typing.Tuple[bool, Any]`，小写 `tuple` 会被拒绝。
3. 自定义 `manager_agent` 不能挂 tools。
4. DeepSeek：`LLM(model="deepseek/deepseek-chat", base_url="https://api.deepseek.com/v1")`，Key 走 `DEEPSEEK_API_KEY`。
