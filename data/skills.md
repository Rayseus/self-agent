# 技能清单

## AI Agent 与大语言模型 (AI Agent & LLM)

李睿阳在 AI Agent 与 LLM 领域具备深度实践经验，核心技能包括：

- **RAG（检索增强生成）**：熟练掌握从文档切分、向量化、混合检索到 Prompt 约束生成的完整链路。在 Self-Agent 项目中实现 pgvector + pg_trgm + RRF 混合检索方案；在智能餐饮推荐平台项目中主导 LLM 应用与 RAG 方向的工程实践落地。
- **Prompt Engineering**：擅长设计高约束 System Prompt 实现防幻觉、引用溯源、语言跟随等能力。在 AI-Role-Player 项目中通过提示工程实现性格化角色扮演。
- **长程记忆 Agent**：在 CLI-based Personal AI Agent 项目中设计结构化记忆存储与检索机制，使用 SQLite 持久化外部记忆并引入确定性引用验证，实现跨会话用户事实记忆与多工具调用。
- **Fine-Tuning**：具备模型微调经验。
- **KVMemNet 架构思想**：在佐治亚理工学院从零实现基于注意力机制的键值记忆网络，合成数据集与真实数据均达到 97% 准确率；在 Self-Agent 与 CLI-based AI Agent 项目中借鉴键值寻址逻辑优化检索与记忆链路。
- **强化学习**：系统实践 Value Iteration、Policy Iteration、SARSA、Q-learning 算法，具备状态空间离散化、ε-greedy 探索策略设计与超参数调优经验。
- **监督学习**：深入分析神经网络、SVM（Linear/RBF）、KNN 的泛化能力，擅长通过学习曲线、混淆矩阵进行模型诊断与调优。
- **框架与工具**：LangChain / LangGraph、PyTorch、scikit-learn、Coze、OpenAI API、Gemini API、Claude API。
- **AI 开发工具**：Claude Code、Cursor 等 AI 辅助编程工具。

## AI Infra 与模型量化压缩 (AI Infra & Model Quantization)

李睿阳具备模型推理优化与量化压缩的系统性实践经验：

- **后训练量化算法**：熟悉 GPTQ、AWQ、SmoothQuant 等主流后训练量化（PTQ）算法的原理与工程实现，覆盖权重量化、激活量化与 KV cache 处理。
- **W4A8 端到端验证链路**：在与美国某头部科技公司合作的课题研究中，搭建 GPTQ / AWQ / SmoothQuant 在 7B-13B 参数规模开源模型上的 W4A8 量化端到端验证链路，论文撰写中。
- **推理框架**：vLLM（量化后模型的吞吐与延迟基准测试）、CUDA（底层算子与显存优化的工程理解）。
- **精度与性能权衡评估**：能够系统对比不同量化算法在精度、显存占用与推理速度三个维度上的取舍，给出工程化选型建议。

## 前端与 3D 可视化 (Frontend & 3D Visualization)

李睿阳拥有 7 年以上前端开发经验，擅长复杂可视化与跨平台方案：

- **核心框架**：React（主力）、TypeScript、Next.js、Angular。
- **3D / 可视化**：Three.js (WebGL)，在大疆车载构建 4D 点云标注平台，每日处理 10,000+ 帧数据；OpenGL，在爱立信实现车联网实时大屏。
- **数据可视化**：AntV/G6、ECharts、Canvas，在华为云开发 IoT 时序分析仪表盘。
- **跨平台**：Flutter（在路特斯汽车与 Rust 结合实现车载推荐系统）、Electron（在 Shopee 开发语音通话与截图功能）。
- **微前端**：在爱立信重构 Qiankun 框架实现严格沙箱隔离，跨应用冲突减少 95%。

## 后端、云与 DevOps (Backend, Cloud & DevOps)

李睿阳具备扎实的后端工程能力与云原生实践经验：

- **后端语言与框架**：Python（FastAPI，主力后端框架）、Node.js（Express）、Golang。
- **API 设计**：RESTful APIs，在大疆车载开发高吞吐量数据管道 API，将训练数据准备流程加速 40%。
- **数据库**：PostgreSQL（+ pgvector 向量检索）、MySQL、Redis、SQLite（用于 CLI Agent 持久化记忆）。
- **云与基础设施**：AWS、Kubernetes (K8s)、Docker、Terraform、Nginx。
- **Serverless**：在股票分析系统中依托 Serverless 架构实现核心引擎的高效解耦与自动化调度。

## 边缘计算与物联网 (Edge Computing & IoT)

李睿阳在 IoT 与边缘计算领域有丰富的工程实践：

- **Rust**：在路特斯汽车采用 Flutter + Rust 方案，保持边缘硬件原生性能同时减少 70% 代码冗余。
- **WebAssembly**：具备 Wasm 开发经验。
- **通信协议**：MQTT、COAP（在路特斯车载系统中使用）、WebRTC（在 Shopee 实现语音通话）。
- **IoT 平台**：在华为云 IoT 工作 3 年，全栈开发实时与时序分析功能，推动高级订阅增长 15%。
