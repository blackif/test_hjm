---
name: auto-ppt
description: >
  根据一句话提示词自动生成完整、专业、视觉精美的 PowerPoint 演示文稿。
  当用户输入任何类似"帮我做一个关于X的PPT"、"生成X主题的演示"、"制作X的幻灯片"、
  "做一个X的演讲稿/presentation/deck/slides"等请求时，立即触发此技能。
  无论主题是销售演示、产品介绍、项目汇报、培训材料还是任何其他演讲场景，
  只要涉及生成PPT文件，都必须使用此技能，不要跳过任何步骤。
---

# Auto-PPT 生成技能

## 工作流程概览

接收到 PPT 生成请求后，**严格按照以下5个阶段顺序执行**，不可跳步：

```
阶段1 → 主题分析与结构规划
阶段2 → 生成页面大纲（含每页详细内容）
阶段3 → 确定视觉设计方案
阶段4 → 用 PptxGenJS 生成 PPTX 文件
阶段5 → QA 验证与交付
```

---

## 阶段1：主题分析与结构规划

分析用户输入的主题，确定以下要素并**向用户展示确认**：

| 要素 | 说明 |
|------|------|
| 演示目的 | 销售/汇报/培训/介绍/融资等 |
| 目标受众 | 客户/管理层/团队/投资人等 |
| 演讲时长 | 预估（影响页数） |
| 核心信息 | 这份PPT最想传达什么 |
| 建议页数 | 通常 10-16 页最佳 |

**标准结构模板（根据目的选择）：**

- **销售演示**：封面 → 问题/痛点 → 市场机会 → 解决方案 → 产品特性 → 差异化优势 → 客户案例 → 实施路线 → 定价方案 → 下一步行动 → 封底
- **项目汇报**：封面 → 执行摘要 → 背景/目标 → 现状分析 → 方案详情 → 资源计划 → 风险管理 → 里程碑 → 总结 → 封底
- **产品介绍**：封面 → 市场背景 → 产品概述 → 核心功能 → 技术架构 → 使用场景 → 竞品对比 → 路线图 → 联系方式 → 封底
- **融资路演**：封面 → 电梯演讲 → 市场规模 → 痛点/机会 → 解决方案 → 商业模式 → 牵引力数据 → 竞争格局 → 团队介绍 → 融资用途 → 封底

---

## 阶段2：生成页面大纲


### 字数硬限制（超出时主动缩写，不得超过）

| 元素 | 最大字数 | 超出时处理方式 |
|------|----------|----------------|
| 页面主标题 | 22 字 | 提炼关键词，删除修饰语 |
| Key Point 小标题 | 12 字 | 只保留动宾短语核心 |
| Key Point 正文说明（标准布局） | 45 字 | 删除举例，保留核心结论 |
| Key Point 正文说明（压缩布局） | 35 字 | 删除举例，保留核心结论 |
| 封面大标题 | 14 字 | 只保留品牌名 + 核心价值 |
| 大数字统计值 | 5 字 | 如 $47B、40%、10x |
| 时间线/流程描述 | 28 字 | 仅保留关键事件名称 |
| 两栏 bullet 每条 | 20 字 | 一条一个观点 |
为**每一页**输出以下结构（在对话中展示给用户）：

```
第 N 页：[页面标题]
├── 布局类型：[封面/标题+内容/两栏/全图/数据图表/时间线]
├── Key Points（2-4个）：
│   ├── KP1：[主要观点标题]（内容：[1-2句具体说明]）
│   ├── KP2：[主要观点标题]（内容：[1-2句具体说明]）
│   └── KP3：[主要观点标题]（内容：[1-2句具体说明]）
├── 视觉元素：[图表类型/图标/数据展示方式]
└── 演讲要点：[发言人需要口头补充的核心内容]
```


### Key Point 数量规则

| Key Point 数量 | 布局方式 | 每点最大字数 | 优先级 |
|---------------|---------|-------------|--------|
| 2-3 个 | 标准单列 | 45 字 | 高（优先选择） |
| 4 个 | 压缩单列 | 35 字 | 低（内容需要时才用） |

强制规则：
- 严禁单页超过 4 个 Key Point
- 超过 4 个要点时必须拆分到多页
- 优先选择 2-3 个 Key Point 的标准布局
所有页面大纲确认完毕后，再进入阶段3。

---

## 阶段3：确定视觉设计方案

根据主题和受众选择设计方案，**向用户展示选择**：

### 配色选择逻辑

| 主题类型 | 推荐配色 | Primary | Secondary | Accent |
|---------|---------|---------|-----------|--------|
| 企业B2B/金融 | Midnight Executive | `1E2761` | `CADCFC` | `F5A623` |
| 科技/SaaS | Ocean Gradient | `065A82` | `1C7293` | `02C39A` |
| 医疗/健康 | Sage Calm | `84B59F` | `69A297` | `2C5F2D` |
| 创新/消费品 | Coral Energy | `F96167` | `F9E795` | `2F3C7E` |
| 高端/奢华 | Charcoal Minimal | `36454F` | `F2F2F2` | `C9A84C` |
| 环保/可持续 | Forest & Moss | `2C5F2D` | `97BC62` | `F5F5F5` |
| 品牌/营销 | Cherry Bold | `990011` | `FCF6F5` | `2F3C7E` |

### 字体配对

| 标题字体 | 正文字体 | 适用场景 |
|---------|---------|---------|
| Georgia | Calibri | 专业、权威 |
| Arial Black | Arial | 现代、有力 |
| Cambria | Calibri | 传统、正式 |
| Trebuchet MS | Calibri | 科技、清新 |

### 尺寸规范
- 幻灯片标题：40-44pt bold
- 节标题：22-28pt bold  
- 正文：14-16pt
- 数据大字：60-72pt bold
- 说明文字：11-12pt

---


---

## 阶段 3.5：用户确认与调整（交互环节）

**重要：必须等待用户明确确认后才能进入阶段 4**

### 输出确认清单

在阶段 3 完成后，向用户输出以下确认清单：

```
=== PPT 方案确认清单 ===

【阶段 1：主题分析】
- 演示目的：[XXX]
- 目标受众：[XXX]
- 建议页数：[XX] 页

【阶段 2：页面大纲】
- 第 1 页：[页面标题]
- 第 2 页：[页面标题]
- ...
- 第 N 页：[页面标题]

【阶段 3：视觉设计】
- 配色方案：[XXX]（主色：#XXXXXX）
- 字体配对：[标题字体] + [正文字体]

========================

请确认以上方案是否满意？
- 输入"OK"、"确认"、"继续"等 → 进入阶段 4 生成 PPT
- 输入"调整 XX"或具体修改意见 → 重新执行阶段 1-3
- 例如："调整配色为科技蓝"、"增加 2 页案例"、"修改目标受众为技术团队"
```

### 用户反馈处理逻辑

**情况 A：用户确认（进入阶段 4）**
- 用户输入包含："OK"、"确认"、"继续"、"没问题"、"可以"等肯定词
- 动作：进入阶段 4，开始生成 PPTX 文件

**情况 B：用户要求调整（返回阶段 1-3）**
- 用户输入包含："调整"、"修改"、"变更"、"改成"、"增加"、"减少"、"删除"等调整词
- 动作：
  1. 分析用户具体调整需求
  2. 根据调整内容，重新执行阶段 1-3 中受影响的部分
  3. 输出更新后的确认清单
  4. 再次等待用户确认

**情况 C：用户有疑问（解答后继续等待确认）**
- 用户输入包含："为什么"、"如何"、"能否"等疑问词
- 动作：
  1. 解答用户疑问
  2. 询问是否需要调整
  3. 继续等待用户确认

### 调整类型与对应处理

| 调整类型 | 影响阶段 | 处理方式 |
|---------|---------|---------|
| 演示目的/受众变更 | 阶段 1 | 重新分析主题，调整结构模板 |
| 页数增减 | 阶段 1-2 | 调整建议页数，增删页面大纲 |
| 页面内容调整 | 阶段 2 | 修改对应页面大纲 |
| 配色方案调整 | 阶段 3 | 更换配色方案 |
| 字体调整 | 阶段 3 | 更换字体配对 |
| 布局风格调整 | 阶段 3 | 调整设计方案 |

### 确认状态追踪

在对话中明确告知用户当前状态：
- 【等待确认】阶段 1-3 已完成，等待用户确认
- 【调整中】根据用户反馈调整方案
- 【已确认】用户已确认，正在生成 PPT
## 阶段4：生成 PPTX 文件

> 详见 [references/pptx-generation.md](references/pptx-generation.md) 了解完整的代码规范

### 环境准备

```bash
# 安装依赖（已全局安装）
npm install -g pptxgenjs
npm install -g react-icons react react-dom sharp

# QA 工具安装
pip3 install markitdown --target /home/ubuntu/.nvm/versions/node/v24.14.0/lib/node_modules/openclaw/skills/public/auto-ppt/tools/
sudo apt-get install -y libreoffice-core poppler-utils
```

### 生成脚本结构

详见 generate_ppt.js (/home/ubuntu/.nvm/versions/node/v24.14.0/lib/node_modules/openclaw/skills/public/auto-ppt/script/generate_ppt.js) 了解完整的脚本结构。

脚本必须包含以下核心组件：

1. 模块导入
   - pptxgenjs 主库
   - ppt-utils.js 工具模块（颜色、字体、安全函数）

2. 设计系统配置（在 ppt-utils.js 中定义）
   - 颜色常量（C.primary, C.secondary, C.accent 等）
   - 字体常量（F.title, F.body）

3. 文字溢出防护（必须使用）
   - safe(text, maxLen) - 截断文字并加省略号
   - SAFE 常量表 - 18 种常用元素的安全尺寸定义
   - 所有 addText 调用必须使用 safe() 包裹

4. 幻灯片生成函数
   - 每页一个函数（如 addTitleSlide, addContentSlide）
   - 主构建函数 buildPresentation()

5. 输出路径
   - /home/ubuntu/.openclaw/workspace/auto-ppt-outputs/presentation.pptx

6. 动态布局逻辑
   - 根据 Key Point 数量自动选择布局模式
   - 2-3 个：标准单列（字体 18pt/14pt，间距 1.2）
   - 4 个：压缩单列（字体 17pt/13pt，间距 1.0）

### 关键布局模式

**封面页：**
- 全色背景（primary color）
- 大标题居中（44-48pt，white，bold）
- 副标题（20-22pt，secondary color）
- 日期/公司名（底部，14pt，white，60%透明度）

**内容页（标题+要点）：**
- 顶部色块（primary，全宽，h:1.1"）中放白色标题
- 正文区域：图标圆圈 + 粗体小标题 + 正文说明
- 右侧可配图表、图形或装饰性色块

**两栏对比页：**
- 左右各占4.5英寸
- 左栏 primary 色背景，右栏 white 背景
- 适合 Before/After、功能对比、竞品对比

**数据展示页：**
- 3个大数字居中排列（60-72pt bold，accent color）
- 每个数字下方小标签（14pt，textLight）
- 底部横线分隔后加说明文字

**时间线/流程页：**
- 水平箭头流程图（addShape RECTANGLE + 文字）
- 或纵向步骤列表（左侧彩色数字圆圈 + 右侧内容）

---

## 阶段5：QA 验证

```bash
# 1. 文字内容检查
PYTHONPATH=/home/ubuntu/.nvm/versions/node/v24.14.0/lib/node_modules/openclaw/skills/public/auto-ppt/tools/ python3 -m markitdown /home/ubuntu/.openclaw/workspace/auto-ppt-outputs/presentation.pptx

# 2. 转换为图片进行视觉检查
python3 /home/ubuntu/.nvm/versions/node/v24.14.0/lib/node_modules/openclaw/skills/public/auto-ppt/tools/office/soffice.py --headless --convert-to pdf /home/ubuntu/.openclaw/workspace/auto-ppt-outputs/presentation.pptx
rm -f /home/ubuntu/.openclaw/workspace/auto-ppt-outputs/slide-*.jpg
pdftoppm -jpeg -r 150 /home/ubuntu/.openclaw/workspace/auto-ppt-outputs/presentation.pdf /home/ubuntu/.openclaw/workspace/auto-ppt-outputs/slide
ls -1 "$PWD"/home/ubuntu/.openclaw/workspace/auto-ppt-outputs/slide-*.jpg
```

用 `view` 工具检查每张幻灯片图片，重点检查：
- 文字是否溢出边界
- 元素是否重叠
- 色彩对比是否清晰
- 布局是否美观一致
- 无文字溢出或截断

发现问题后修复脚本并重新生成，直到无明显问题。

---

## 阶段 6：GitHub 上传与交付

QA 验证通过后，自动将 PPT 文件上传到 GitHub 并清理本地文件。

### GitHub 配置

| 配置项 | 值 |
|--------|-----|
| 仓库 | `https://github.com/blackif/claw_hjm` |
| 上传目录 | `autofile/` |
| Token | `YOUR_GITHUB_TOKEN`（在 TOOLS.md 中配置） |

### 上传流程

```bash
# 1. 配置 Git 用户信息
git config --global user.name "auto-ppt-bot"
git config --global user.email "auto-ppt@local"

# 2. 生成带时间戳的文件名
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DEST_FILE="autofile/presentation_${TIMESTAMP}.pptx"

# 3. 克隆仓库（如果尚未克隆）
if [ ! -d "/home/ubuntu/.openclaw/workspace/claw_hjm" ]; then
  cd /home/ubuntu/.openclaw/workspace
  git clone https://${GITHUB_TOKEN}@github.com/blackif/claw_hjm.git
fi

# 4. 复制 PPT 文件到仓库目录
cd /home/ubuntu/.openclaw/workspace/claw_hjm
git pull origin main 2>/dev/null || true
cp /home/ubuntu/.openclaw/workspace/auto-ppt-outputs/presentation.pptx "${DEST_FILE}"

# 5. 提交并推送
git add "${DEST_FILE}"
git commit -m "📊 Auto-generated PPT: presentation_${TIMESTAMP}.pptx"
git push origin main

# 6. 清理本地文件
rm -f /home/ubuntu/.openclaw/workspace/auto-ppt-outputs/presentation.pptx
rm -f /home/ubuntu/.openclaw/workspace/auto-ppt-outputs/presentation.pdf
rm -f /home/ubuntu/.openclaw/workspace/auto-ppt-outputs/slide-*.jpg

echo "✅ PPT 已上传至 GitHub: https://github.com/blackif/claw_hjm/blob/main/${DEST_FILE}"
```

### 环境变量

在脚本中设置 `GITHUB_TOKEN`：
```javascript
const GITHUB_TOKEN = process.env.GITHUB_TOKEN; // 从环境变量读取
```

---

## 质量标准

✅ **必须达到：**
- 每页有视觉元素（图标/图形/色块/图表），无纯文字页面
- 配色统一，遵循60-30-10原则（主色-辅色-强调色）
- 标题层级清晰（大小、粗细有明显区别）
- 留白充足（最小0.5"边距，内容区域不拥挤）
- 布局多样（不同页面使用不同布局）

❌ **严禁出现：**
- 标题下方的下划线装饰线（AI生成特征，必须避免）
- 纯白背景纯黑文字的无设计感幻灯片
- 重复使用相同布局超过3页
- 文字溢出或被截断
- `#` 前缀的颜色值（会导致文件损坏）

---

## 参考资源

- [references/pptx-generation.md](references/pptx-generation.md) — 完整代码示例和工具函数
- [references/slide-templates.md](references/slide-templates.md) — 各类型幻灯片模板代码
