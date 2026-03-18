// ═══════════════════════════════════════════════
// Auto-PPT 生成脚本 - 死亡的意义
// ═══════════════════════════════════════════════

const pptxgen = require("pptxgenjs");
const { C, F, safe, maxChars, SAFE } = require("./ppt-utils");

const SHAPE = { rect: "rect", ellipse: "ellipse", chevron: "chevron", line: "line" };

// ═══════════════════════════════════════════════
// 幻灯片生成函数
// ═══════════════════════════════════════════════

function addTitleSlide(pres, title, subtitle, footer) {
  const slide = pres.addSlide();
  slide.background = { color: C.primary };
  slide.addText(safe(title, SAFE.coverTitle.max), {
    x: 0.5, y: 2.5, w: SAFE.coverTitle.w, h: SAFE.coverTitle.h,
    fontSize: SAFE.coverTitle.fs, color: C.white, fontFace: F.title, bold: true, align: "center"
  });
  slide.addText(safe(subtitle, SAFE.coverSub.max), {
    x: 0.5, y: 4.0, w: SAFE.coverSub.w, h: SAFE.coverSub.h,
    fontSize: SAFE.coverSub.fs, color: C.secondary, fontFace: F.body, align: "center"
  });
  slide.addText(safe(footer, 30), {
    x: 0.5, y: 6.8, w: 9, h: 0.4,
    fontSize: 12, color: C.white, fontFace: F.body, align: "center", transparency: 40
  });
  return slide;
}

function addTitleBar(slide, title) {
  slide.addShape(SHAPE.rect, { x: 0, y: 0, w: "100%", h: 1.1, fill: { color: C.primary } });
  slide.addText(safe(title, SAFE.pageTitle.max), {
    x: 0.5, y: 0.3, w: SAFE.pageTitle.w, h: SAFE.pageTitle.h,
    fontSize: SAFE.pageTitle.fs, color: C.white, fontFace: F.title, bold: true
  });
  return slide;
}

function addContentSlide(pres, title, points) {
  const slide = pres.addSlide();
  addTitleBar(slide, title);
  
  const numPoints = points.length;
  const isCompact = numPoints >= 4;
  
  let y = 1.5;
  points.forEach(point => {
    slide.addShape(SHAPE.ellipse, { x: 0.5, y: y, w: 0.4, h: 0.4, fill: { color: C.accent } });
    
    slide.addText(safe(point.title, isCompact ? SAFE.singleTitleC.max : SAFE.singleTitle.max), {
      x: 1.0, y: y, w: 8.5, h: isCompact ? SAFE.singleTitleC.h : SAFE.singleTitle.h,
      fontSize: isCompact ? SAFE.singleTitleC.fs : SAFE.singleTitle.fs,
      color: C.primary, fontFace: F.title, bold: true
    });
    
    slide.addText(safe(point.content, isCompact ? SAFE.singleBodyC.max : SAFE.singleBody.max), {
      x: 1.0, y: y + 0.3, w: 8.5, h: isCompact ? SAFE.singleBodyC.h : SAFE.singleBody.h,
      fontSize: isCompact ? SAFE.singleBodyC.fs : SAFE.singleBody.fs,
      color: C.text, fontFace: F.body
    });
    
    y += isCompact ? 1.0 : 1.2;
  });
  
  return slide;
}

function addTwoColumnSlide(pres, title, leftTitle, leftPoints, rightTitle, rightPoints) {
  const slide = pres.addSlide();
  addTitleBar(slide, title);
  slide.addShape(SHAPE.rect, { x: 0.3, y: 1.3, w: 4.5, h: 5.0, fill: { color: C.secondary, transparency: 80 } });
  slide.addShape(SHAPE.rect, { x: 5.2, y: 1.3, w: 4.5, h: 5.0, fill: { color: C.white } });
  slide.addText(safe(leftTitle, 20), { x: 0.5, y: 1.5, w: 4.0, h: 0.4, fontSize: 18, color: C.primary, fontFace: F.title, bold: true });
  let y = 2.0;
  leftPoints.forEach(point => { slide.addText("* " + safe(point, 20), { x: 0.5, y: y, w: 4.0, h: 0.4, fontSize: 14, color: C.text, fontFace: F.body }); y += 0.5; });
  slide.addText(safe(rightTitle, 20), { x: 5.4, y: 1.5, w: 4.0, h: 0.4, fontSize: 18, color: C.primary, fontFace: F.title, bold: true });
  y = 2.0;
  rightPoints.forEach(point => { slide.addText("* " + safe(point, 20), { x: 5.4, y: y, w: 4.0, h: 0.4, fontSize: 14, color: C.text, fontFace: F.body }); y += 0.5; });
  return slide;
}

function addDataSlide(pres, title, dataPoints) {
  const slide = pres.addSlide();
  addTitleBar(slide, title);
  const colWidth = 3.0;
  dataPoints.forEach((point, index) => {
    const x = 0.5 + (index * colWidth);
    slide.addText(safe(point.value, SAFE.bigStat.max), { x: x, y: 2.0, w: SAFE.bigStat.w, h: SAFE.bigStat.h, fontSize: SAFE.bigStat.fs, color: C.accent, fontFace: F.title, bold: true, align: "center" });
    slide.addText(safe(point.label, SAFE.statLabel.max), { x: x, y: 3.3, w: SAFE.statLabel.w, h: SAFE.statLabel.h, fontSize: SAFE.statLabel.fs, color: C.textMuted, fontFace: F.body, align: "center" });
  });
  slide.addShape(SHAPE.line, { x: 0.5, y: 4.0, w: 9.0, h: 0, line: { color: C.textMuted, width: 1 } });
  return slide;
}

function addTimelineSlide(pres, title, phases) {
  const slide = pres.addSlide();
  addTitleBar(slide, title);
  const phaseWidth = 1.8;
  const colors = [C.primary, C.accent, C.secondary, C.dark, C.text];
  phases.forEach((phase, index) => {
    const x = 0.5 + (index * phaseWidth);
    slide.addShape(SHAPE.chevron, { x: x, y: 2.0, w: phaseWidth - 0.1, h: 1.2, fill: { color: colors[index % colors.length] } });
    slide.addText(safe(phase.name, SAFE.tlTitle.max), { x: x, y: 2.3, w: phaseWidth - 0.1, h: 0.6, fontSize: 12, color: C.white, fontFace: F.body, bold: true, align: "center", valign: "middle" });
    slide.addText(safe(phase.desc, SAFE.tlDesc.max), { x: x, y: 3.4, w: phaseWidth - 0.1, h: 1.5, fontSize: 11, color: C.text, fontFace: F.body, align: "center" });
  });
  return slide;
}

function addSummarySlide(pres, title, points) {
  const slide = pres.addSlide();
  slide.background = { color: C.primary };
  slide.addText(safe(title, 30), { x: 0.5, y: 1.0, w: 9, h: 0.8, fontSize: 32, color: C.white, fontFace: F.title, bold: true, align: "center" });
  let y = 2.5;
  points.forEach(point => { slide.addText("V " + safe(point, 40), { x: 1.0, y: y, w: 8, h: 0.6, fontSize: 18, color: C.white, fontFace: F.body }); y += 0.7; });
  return slide;
}

function addEndSlide(pres, title, subtitle) {
  const slide = pres.addSlide();
  slide.background = { color: C.primary };
  slide.addText(safe(title, SAFE.endCta.max), { x: 0.5, y: 2.5, w: 9, h: 1.5, fontSize: 44, color: C.white, fontFace: F.title, bold: true, align: "center" });
  slide.addText(safe(subtitle, SAFE.endContact.max), { x: 0.5, y: 4.5, w: 9, h: 0.6, fontSize: 18, color: C.secondary, fontFace: F.body, align: "center" });
  return slide;
}

// ═══════════════════════════════════════════════
// 主构建函数
// ═══════════════════════════════════════════════

async function buildPresentation() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = "Auto-PPT Generator";
  pres.company = "Philosophy Exploration";
  pres.title = "死亡的意义";

  // 第 1 页：封面
  addTitleSlide(pres, "死亡的意义", "理解死亡，珍惜生命", "哲学思考 | 2026 年");

  // 第 2 页：两种死亡观对比（2 个 Key Point - 标准布局）
  addContentSlide(pres, "两种死亡观", [
    { title: "终结论", content: "死亡是生命的终点，一切归于虚无，因此活着时要尽情体验" },
    { title: "转化论", content: "死亡是生命的转化，精神或灵魂以另一种形式继续存在" }
  ]);

  // 第 3 页：死亡的三重意义（3 个 Key Point - 标准布局）
  addContentSlide(pres, "死亡的三重意义", [
    { title: "生物学意义", content: "生命周期的自然结束，为新生命腾出空间和资源" },
    { title: "心理学意义", content: "促使人反思生命价值，产生存在性觉醒和成长" },
    { title: "社会学意义", content: "维系社会结构，传承文化价值，促进代际更替" }
  ]);

  // 第 4 页：面对死亡的四种态度（4 个 Key Point - 压缩布局）
  addContentSlide(pres, "面对死亡的四种态度", [
    { title: "恐惧逃避", content: "拒绝谈论死亡，回避相关话题，活在否认中" },
    { title: "被动接受", content: "承认死亡必然性，但消极等待，缺乏主动规划" },
    { title: "理性面对", content: "正视死亡现实，做好生前规划，安排后事" },
    { title: "积极超越", content: "将死亡视为老师，向死而生，活出深度和意义" }
  ]);

  // 第 5 页：哲学视角
  addTwoColumnSlide(pres, "哲学视角", "西方哲学",
    ["苏格拉底：哲学是练习死亡", "海德格尔：向死而生", "加缪：反抗荒谬"],
    "东方哲学",
    ["庄子：鼓盆而歌", "孔子：未知生焉知死", "禅宗：生死一如"]
  );

  // 第 6 页：宗教视角
  addContentSlide(pres, "宗教视角", [
    { title: "基督教", content: "死亡是通往永生的门，信者得救，与神同在" },
    { title: "佛教", content: "死亡是轮回的一站，解脱生死是修行目标" },
    { title: "道教", content: "生死如昼夜循环，顺应自然，返璞归真" },
    { title: "伊斯兰教", content: "死亡是回归真主，后世审判决定永恒归宿" }
  ]);

  // 第 7 页：心理学视角
  addContentSlide(pres, "心理学视角", [
    { title: "哀伤五阶段", content: "否认、愤怒、讨价还价、抑郁、接受" },
    { title: "意义治疗", content: "弗兰克尔：在苦难和死亡中发现生命意义" },
    { title: "存在心理学", content: "死亡焦虑是成长的动力，直面死亡获得自由" }
  ]);

  // 第 8 页：死亡与生命意义
  addDataSlide(pres, "核心洞见", [
    { value: "有限", label: "因死亡而珍贵" },
    { value: "选择", label: "因死亡而自由" },
    { value: "当下", label: "因死亡而真实" }
  ]);

  // 第 9 页：哀伤与告别
  addContentSlide(pres, "哀伤与告别", [
    { title: "允许悲伤", content: "哀伤是爱的延续，不是需要治愈的疾病" },
    { title: "寻找支持", content: "家人、朋友、专业咨询师都是重要资源" },
    { title: "纪念仪式", content: "葬礼、追思会、纪念物帮助完成心理告别" },
    { title: "继续生活", content: "带着逝者的爱和记忆，继续有意义的生活" }
  ]);

  // 第 10 页：遗产与传承
  addTwoColumnSlide(pres, "遗产与传承", "物质遗产",
    ["财产分配", "遗嘱规划", "物品传承", "数字遗产"],
    "精神遗产",
    ["价值观传递", "人生智慧", "家族故事", "影响力延续"]
  );

  // 第 11 页：临终智慧
  addContentSlide(pres, "临终智慧", [
    { title: "临终关怀", content: "减轻痛苦，维护尊严，陪伴走过最后旅程" },
    { title: "未完成事宜", content: "道歉、道谢、道爱、道别，完成心理 closure" },
    { title: "平静离世", content: "接纳死亡，放下执念，安详走向生命终点" }
  ]);

  // 第 12 页：向死而生
  addTimelineSlide(pres, "向死而生的实践", [
    { name: "觉察", desc: "意识到生命有限" },
    { name: "反思", desc: "审视当前生活" },
    { name: "选择", desc: "做出真实选择" },
    { name: "行动", desc: "活出想要的人生" },
    { name: "感恩", desc: "珍惜每一天" }
  ]);

  // 第 13 页：珍惜当下
  addContentSlide(pres, "珍惜当下", [
    { title: "正念生活", content: "专注此时此刻，充分体验每个瞬间的美好" },
    { title: "深度关系", content: "投入时间与所爱之人相处，建立真实连接" },
    { title: "追求热爱", content: "做真正喜欢的事，而非他人期待的事" },
    { title: "简化生活", content: "减少不必要的消耗，专注于真正重要的事" }
  ]);

  // 第 14 页：总结
  addSummarySlide(pres, "总结", [
    "死亡不是生命的对立面，而是生命的一部分",
    "理解死亡能帮助我们更好地活着",
    "向死而生，活出真实、深度、有意义的人生",
    "珍惜当下，爱护身边的人，做热爱的事"
  ]);

  // 第 15 页：封底
  addEndSlide(pres, "感谢聆听", "愿你找到生命的意义与平静");

  // 保存文件
  await pres.writeFile({ fileName: "../auto-ppt-outputs/presentation.pptx" });
  console.log("OK PPT 生成完成");
}

// ═══════════════════════════════════════════════
// 执行入口
// ═══════════════════════════════════════════════

buildPresentation().catch(err => {
  console.error("错误:", err);
  process.exit(1);
});
