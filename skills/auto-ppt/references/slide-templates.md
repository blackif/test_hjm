# 幻灯片模板参考

## 各场景大纲模板

---

### B2B 软件/SaaS 销售演示（10-12页）

```
P01 封面        — 产品名称 + 核心价值主张 + 公司名
P02 市场痛点    — 目标客户面临的3个核心挑战（图标+数据支撑）
P03 市场机会    — 市场规模(TAM/SAM/SOM) + 趋势图
P04 解决方案    — 产品定位一句话 + 核心能力全景图
P05 核心功能①  — 功能模块介绍（2-3个功能，截图或图标展示）
P06 核心功能②  — 差异化特性（与竞品对比的关键点）
P07 技术优势    — 架构图 / 安全性 / 集成能力
P08 客户成功    — 2-3个标杆客户案例（数据结果）
P09 实施路径    — 从试用到上线的时间线
P10 定价方案    — 版本对比表格（入门/专业/企业）
P11 下一步行动  — 演示预约 / 试用申请 / 联系方式
P12 封底        — 感谢 + 联系方式
```

---

### 项目立项/汇报（10页）

```
P01 封面        — 项目名称 + 汇报人 + 日期
P02 执行摘要    — 核心结论（3-4个大字统计）
P03 背景与目标  — 为什么做这个项目 + 成功标准
P04 现状分析    — 现有问题（根因分析）
P05 解决方案    — 方案设计与逻辑
P06 工作计划    — 时间线 / Gantt 图
P07 资源需求    — 人员 / 预算 / 工具
P08 风险管控    — 风险矩阵 + 应对措施
P09 预期成果    — KPI / 里程碑
P10 封底        — 结论 + 下一步行动
```

---

### 融资路演（11页）

```
P01 封面        — 公司名 + Tagline + 轮次
P02 问题        — 用户痛点（真实场景故事）
P03 解决方案    — 产品截图 + 核心价值
P04 市场规模    — TAM/SAM/SOM 数据可视化
P05 商业模式    — 收入来源 + 单位经济模型
P06 产品演示    — 关键功能/用户流程截图
P07 牵引力      — 用户/收入/增长曲线（大数字页）
P08 竞争格局    — 竞争矩阵/定位图
P09 团队介绍    — 核心团队照片 + 背景亮点
P10 融资规划    — 本轮金额 + 资金用途 + Milestone
P11 封底        — 联系方式
```

---

### 产品发布/介绍（10页）

```
P01 封面        — 产品名 + 发布日期
P02 背景        — 市场趋势 + 用户需求变化
P03 产品亮点    — 3大核心卖点（视觉化）
P04 功能详情①  — 功能A深入介绍
P05 功能详情②  — 功能B深入介绍
P06 使用场景    — 3个典型应用场景
P07 竞品对比    — 功能对比表格
P08 定价        — 价格策略
P09 上线计划    — 时间线
P10 封底        — CTA + 联系
```

---

## 配色主题速查

### 科技蓝（SaaS/企业软件推荐）
```javascript
const C = {
  primary:   "065A82",  // 深海蓝
  secondary: "1C7293",  // 中蓝
  accent:    "02C39A",  // 薄荷绿
  white:     "FFFFFF",
  text:      "1A2332",
  textMuted: "5A7A8A",
  bgLight:   "F0F7FA"
};
```

### 商务深蓝（金融/咨询推荐）
```javascript
const C = {
  primary:   "1E2761",  // 深海军蓝
  secondary: "CADCFC",  // 冰蓝
  accent:    "F5A623",  // 金色
  white:     "FFFFFF",
  text:      "2D3748",
  textMuted: "718096",
  bgLight:   "F7F9FC"
};
```

### 活力橙红（创业/消费品推荐）
```javascript
const C = {
  primary:   "C0392B",  // 深红
  secondary: "F39C12",  // 橙色
  accent:    "2C3E50",  // 深灰
  white:     "FFFFFF",
  text:      "2D3748",
  textMuted: "7F8C8D",
  bgLight:   "FFF9F0"
};
```

### 专业绿（医疗/环保/可持续推荐）
```javascript
const C = {
  primary:   "1A5276",  // 深蓝
  secondary: "27AE60",  // 翠绿
  accent:    "F39C12",  // 黄色
  white:     "FFFFFF",
  text:      "2C3E50",
  textMuted: "7F8C8D",
  bgLight:   "F0FBF5"
};
```

---

## 快速生成示例：B2B 软件销售演示完整脚本

```javascript
const pptxgen = require("pptxgenjs");

// 设计变量
const C = {
  primary: "065A82", secondary: "1C7293", accent: "02C39A",
  white: "FFFFFF", dark: "0A2540", text: "1E3A5F",
  textMuted: "5A7A8A", bgLight: "F0F7FA"
};
const F = { title: "Trebuchet MS", body: "Calibri" };
const makeShadow = () => ({ type: "outer", color: "000000", blur: 8, offset: 3, angle: 135, opacity: 0.12 });

async function createB2BSalesDeck() {
  const pres = new pptxgen();
  pres.layout = 'LAYOUT_16x9';

  // === P01: 封面 ===
  {
    const s = pres.addSlide();
    s.background = { color: C.primary };
    s.addShape(pres.shapes.RECTANGLE, { x:0, y:0, w:0.3, h:5.625, fill:{color:C.accent}, line:{width:0} });
    s.addShape(pres.shapes.OVAL, { x:7, y:3, w:4, h:4, fill:{color:C.secondary, transparency:80}, line:{width:0} });
    s.addText("智能销售管理平台", { x:0.6, y:1.4, w:8.5, h:1.4, fontSize:40, fontFace:F.title, bold:true, color:C.white, align:"left", margin:0 });
    s.addText("让每一位销售代表都能超额完成目标", { x:0.6, y:3.0, w:8, h:0.6, fontSize:18, fontFace:F.body, color:C.accent, align:"left" });
    s.addShape(pres.shapes.RECTANGLE, { x:0, y:4.9, w:10, h:0.725, fill:{color:C.dark, transparency:30}, line:{width:0} });
    s.addText("TechCorp Solutions  |  企业销售演示  |  2024", { x:0.6, y:4.95, w:9, h:0.6, fontSize:12, fontFace:F.body, color:C.secondary, align:"left" });
  }

  // === P02: 痛点页 ===
  {
    const s = pres.addSlide();
    s.background = { color: C.bgLight };
    s.addShape(pres.shapes.RECTANGLE, { x:0, y:0, w:10, h:1.1, fill:{color:C.primary}, line:{width:0} });
    s.addText("您的销售团队是否面临这些挑战？", { x:0.4, y:0, w:9.2, h:1.1, fontSize:26, fontFace:F.title, bold:true, color:C.white, valign:"middle", margin:0 });
    
    const pains = [
      { num:"01", title:"数据分散，决策滞后", body:"销售数据分散在Excel、邮件、CRM中，管理层无法实时掌握业绩进展，关键商机白白流失" },
      { num:"02", title:"过程不透明，辅导困难", body:"销售过程黑盒，销售总监无从判断哪些代表需要支持，哪些环节存在瓶颈" },
      { num:"03", title:"预测不准确，资源浪费", body:"销售预测误差超过30%，导致备货、人员、市场预算严重错配" }
    ];
    pains.forEach((p, i) => {
      const y = 1.3 + i * 1.35;
      s.addShape(pres.shapes.RECTANGLE, { x:0.3, y:y, w:9.4, h:1.15, fill:{color:C.white}, line:{color:C.secondary, width:1}, shadow:makeShadow() });
      s.addShape(pres.shapes.RECTANGLE, { x:0.3, y:y, w:0.7, h:1.15, fill:{color:C.primary}, line:{width:0} });
      s.addText(p.num, { x:0.3, y:y, w:0.7, h:1.15, fontSize:22, fontFace:F.title, bold:true, color:C.accent, align:"center", valign:"middle", margin:0 });
      s.addText(p.title, { x:1.2, y:y+0.1, w:8.3, h:0.4, fontSize:16, fontFace:F.body, bold:true, color:C.text });
      s.addText(p.body, { x:1.2, y:y+0.55, w:8.3, h:0.55, fontSize:12, fontFace:F.body, color:C.textMuted });
    });
  }

  // === P03: 市场机会（大数字页） ===
  {
    const s = pres.addSlide();
    s.background = { color: C.primary };
    s.addText("巨大的市场机会", { x:0.5, y:0.4, w:9, h:0.8, fontSize:32, fontFace:F.title, bold:true, color:C.white, align:"center" });
    s.addShape(pres.shapes.RECTANGLE, { x:3.5, y:1.35, w:3, h:0.06, fill:{color:C.accent}, line:{width:0} });
    const stats = [
      { v:"$48B", l:"全球销售工具市场规模", sub:"2027年预测" },
      { v:"23%", l:"年复合增长率", sub:"过去5年" },
      { v:"67%", l:"企业计划增加投入", sub:"2024年调研" }
    ];
    stats.forEach((st, i) => {
      const x = 0.3 + i * 3.2;
      s.addText(st.v, { x:x, y:1.7, w:3.0, h:1.3, fontSize:60, fontFace:F.title, bold:true, color:C.accent, align:"center" });
      s.addText(st.l, { x:x, y:3.1, w:3.0, h:0.5, fontSize:14, fontFace:F.body, bold:true, color:C.white, align:"center" });
      s.addText(st.sub, { x:x, y:3.65, w:3.0, h:0.4, fontSize:11, fontFace:F.body, color:C.secondary, align:"center", italic:true });
    });
  }

  // === P04: 解决方案概览 ===
  {
    const s = pres.addSlide();
    s.background = { color: C.bgLight };
    s.addShape(pres.shapes.RECTANGLE, { x:0, y:0, w:10, h:1.1, fill:{color:C.primary}, line:{width:0} });
    s.addText("一体化智能销售管理平台", { x:0.4, y:0, w:9.2, h:1.1, fontSize:26, fontFace:F.title, bold:true, color:C.white, valign:"middle", margin:0 });
    
    const modules = [
      { title:"智能 CRM", icon:"📊", desc:"全渠道客户数据统一管理" },
      { title:"销售预测", icon:"📈", desc:"AI驱动精准预测，误差<5%" },
      { title:"过程管理", icon:"🎯", desc:"可视化销售漏斗与活动追踪" },
      { title:"团队辅导", icon:"💡", desc:"基于数据的个性化培训建议" }
    ];
    modules.forEach((m, i) => {
      const x = 0.3 + i * 2.35;
      s.addShape(pres.shapes.RECTANGLE, { x:x, y:1.25, w:2.15, h:3.8, fill:{color:C.white}, line:{color:C.secondary, width:1}, shadow:makeShadow() });
      s.addShape(pres.shapes.OVAL, { x:x+0.575, y:1.45, w:1.0, h:1.0, fill:{color:i===0?C.accent:C.primary}, line:{width:0} });
      s.addText(m.icon, { x:x+0.575, y:1.45, w:1.0, h:1.0, fontSize:28, align:"center", valign:"middle", margin:0 });
      s.addText(m.title, { x:x+0.1, y:2.65, w:1.95, h:0.5, fontSize:14, fontFace:F.body, bold:true, color:C.text, align:"center" });
      s.addText(m.desc, { x:x+0.1, y:3.25, w:1.95, h:1.5, fontSize:11, fontFace:F.body, color:C.textMuted, align:"center" });
    });
  }

  // === P05: 封底 ===
  {
    const s = pres.addSlide();
    s.background = { color: C.primary };
    s.addShape(pres.shapes.RECTANGLE, { x:0, y:0, w:0.3, h:5.625, fill:{color:C.accent}, line:{width:0} });
    s.addText("立即预约产品演示", { x:0.5, y:1.6, w:9, h:1.1, fontSize:44, fontFace:F.title, bold:true, color:C.white, align:"center" });
    s.addShape(pres.shapes.RECTANGLE, { x:3.5, y:2.9, w:3, h:0.07, fill:{color:C.accent}, line:{width:0} });
    s.addText("30分钟了解如何提升您的销售团队效率 30%+", { x:0.5, y:3.2, w:9, h:0.6, fontSize:18, fontFace:F.body, color:C.secondary, align:"center", italic:true });
    s.addText([
      { text:"📧 sales@techcorp.com", options:{breakLine:true} },
      { text:"🌐 www.techcorp.com/demo" }
    ], { x:0.5, y:4.0, w:9, h:0.9, fontSize:16, fontFace:F.body, color:C.accent, align:"center" });
    s.addShape(pres.shapes.RECTANGLE, { x:0, y:5.1, w:10, h:0.525, fill:{color:C.accent, transparency:80}, line:{width:0} });
  }

  await pres.writeFile({ fileName: "/mnt/user-data/outputs/B2B销售演示.pptx" });
  console.log("✅ B2B 销售演示生成完成！");
}

createB2BSalesDeck().catch(console.error);
```
