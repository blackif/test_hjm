# PPTX 生成参考手册

## 工具函数库

在每个生成脚本顶部引入以下工具函数：

```javascript
const pptxgen = require("pptxgenjs");
// 图标支持（可选，如需使用图标则引入）
// const React = require("react");
// const ReactDOMServer = require("react-dom/server");
// const sharp = require("sharp");

// ===== 颜色与字体常量（根据主题调整） =====
const C = {
  primary:   "1E2761",   // 主色
  secondary: "CADCFC",   // 辅色
  accent:    "F5A623",   // 强调色
  white:     "FFFFFF",
  dark:      "1A1A2E",
  text:      "2D3748",
  textMuted: "718096",
  bgLight:   "F7F9FC"
};
const F = { title: "Georgia", body: "Calibri" };

// ===== Shadow 工厂（避免对象复用导致的文件损坏） =====
const makeShadow = () => ({
  type: "outer", color: "000000", blur: 8, offset: 3, angle: 135, opacity: 0.12
});

// ===== 图标工具（需要安装 react-icons + sharp） =====
/*
async function iconPng(IconComp, color = "#FFFFFF", size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComp, { color, size: String(size) })
  );
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}
*/
```

---

## 封面幻灯片模板

```javascript
async function addCoverSlide(pres, { title, subtitle, company, date }) {
  const slide = pres.addSlide();
  
  // 深色全屏背景
  slide.background = { color: C.primary };
  
  // 左侧装饰色条（accent 色竖线）
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.25, h: 5.625,
    fill: { color: C.accent }, line: { width: 0 }
  });
  
  // 右下角装饰圆（辅色，透明度）
  slide.addShape(pres.shapes.OVAL, {
    x: 7.5, y: 3.5, w: 3.5, h: 3.5,
    fill: { color: C.secondary, transparency: 80 }, line: { width: 0 }
  });
  
  // 主标题
  slide.addText(title, {
    x: 0.6, y: 1.6, w: 8.5, h: 1.6,
    fontSize: 44, fontFace: F.title, bold: true,
    color: C.white, align: "left", valign: "middle",
    margin: 0
  });
  
  // 副标题
  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.6, y: 3.3, w: 8, h: 0.7,
      fontSize: 20, fontFace: F.body, bold: false,
      color: C.secondary, align: "left"
    });
  }
  
  // 底部信息栏
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 4.9, w: 10, h: 0.725,
    fill: { color: C.dark, transparency: 40 }, line: { width: 0 }
  });
  slide.addText(`${company || ""}  |  ${date || new Date().getFullYear()}`, {
    x: 0.6, y: 4.95, w: 9, h: 0.6,
    fontSize: 13, fontFace: F.body, color: C.secondary,
    align: "left"
  });
}
```

---

## 标题+要点页模板（单栏）

```javascript
function addBulletSlide(pres, { title, points }) {
  // points: [{ icon?: "✓", heading: "标题", body: "内容说明" }, ...]
  const slide = pres.addSlide();
  slide.background = { color: C.bgLight };
  
  // 顶部标题栏
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 1.1,
    fill: { color: C.primary }, line: { width: 0 }
  });
  slide.addText(title, {
    x: 0.4, y: 0, w: 9.2, h: 1.1,
    fontSize: 28, fontFace: F.title, bold: true,
    color: C.white, valign: "middle", margin: 0
  });
  
  // 左侧 accent 装饰条
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 1.1, w: 0.12, h: 4.525,
    fill: { color: C.accent }, line: { width: 0 }
  });
  
  // 内容要点
  const startY = 1.35;
  const gap = (4.0) / points.length;
  points.forEach((pt, i) => {
    const y = startY + i * gap;
    
    // 数字圆圈
    slide.addShape(pres.shapes.OVAL, {
      x: 0.3, y: y + 0.05, w: 0.45, h: 0.45,
      fill: { color: C.primary }, line: { width: 0 }
    });
    slide.addText(String(i + 1), {
      x: 0.3, y: y + 0.05, w: 0.45, h: 0.45,
      fontSize: 14, fontFace: F.body, bold: true,
      color: C.white, align: "center", valign: "middle", margin: 0
    });
    
    // 小标题
    slide.addText(pt.heading, {
      x: 0.9, y: y, w: 8.7, h: 0.35,
      fontSize: 17, fontFace: F.body, bold: true,
      color: C.text
    });
    
    // 内容说明
    if (pt.body) {
      slide.addText(pt.body, {
        x: 0.9, y: y + 0.32, w: 8.7, h: 0.5,
        fontSize: 13, fontFace: F.body, color: C.textMuted
      });
    }
  });
}
```

---

## 两栏对比页模板

```javascript
function addTwoColumnSlide(pres, { title, leftTitle, leftItems, rightTitle, rightItems }) {
  const slide = pres.addSlide();
  slide.background = { color: C.bgLight };
  
  // 标题栏
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 1.0,
    fill: { color: C.primary }, line: { width: 0 }
  });
  slide.addText(title, {
    x: 0.4, y: 0, w: 9.2, h: 1.0,
    fontSize: 26, fontFace: F.title, bold: true,
    color: C.white, valign: "middle", margin: 0
  });
  
  // 左栏卡片
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.3, y: 1.15, w: 4.4, h: 4.2,
    fill: { color: C.primary }, line: { width: 0 },
    shadow: makeShadow()
  });
  slide.addText(leftTitle, {
    x: 0.5, y: 1.3, w: 4.0, h: 0.5,
    fontSize: 18, fontFace: F.title, bold: true,
    color: C.accent, align: "center", margin: 0
  });
  slide.addText(leftItems.map(t => ({ text: t, options: { bullet: true, breakLine: true, color: C.secondary } })), {
    x: 0.55, y: 1.9, w: 3.9, h: 3.2,
    fontSize: 13, fontFace: F.body, color: C.secondary
  });
  
  // 右栏卡片
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 5.3, y: 1.15, w: 4.4, h: 4.2,
    fill: { color: C.white }, line: { color: C.secondary, width: 1.5 },
    shadow: makeShadow()
  });
  slide.addText(rightTitle, {
    x: 5.5, y: 1.3, w: 4.0, h: 0.5,
    fontSize: 18, fontFace: F.title, bold: true,
    color: C.primary, align: "center", margin: 0
  });
  slide.addText(rightItems.map(t => ({ text: t, options: { bullet: true, breakLine: true, color: C.text } })), {
    x: 5.55, y: 1.9, w: 3.9, h: 3.2,
    fontSize: 13, fontFace: F.body, color: C.text
  });
}
```

---

## 大数据展示页模板

```javascript
function addStatsSlide(pres, { title, stats, caption }) {
  // stats: [{ value: "95%", label: "客户满意度" }, ...]（2-4个）
  const slide = pres.addSlide();
  slide.background = { color: C.primary };
  
  // 标题
  slide.addText(title, {
    x: 0.5, y: 0.4, w: 9, h: 0.8,
    fontSize: 30, fontFace: F.title, bold: true,
    color: C.white, align: "center"
  });
  
  // 分隔线
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 3.5, y: 1.3, w: 3, h: 0.06,
    fill: { color: C.accent }, line: { width: 0 }
  });
  
  // 统计数字
  const count = stats.length;
  const colW = 9 / count;
  stats.forEach((stat, i) => {
    const cx = 0.5 + i * colW + colW / 2 - 2;
    slide.addText(stat.value, {
      x: cx, y: 1.7, w: 4, h: 1.5,
      fontSize: 68, fontFace: F.title, bold: true,
      color: C.accent, align: "center"
    });
    slide.addText(stat.label, {
      x: cx, y: 3.2, w: 4, h: 0.5,
      fontSize: 16, fontFace: F.body, color: C.secondary, align: "center"
    });
  });
  
  // 底部说明
  if (caption) {
    slide.addText(caption, {
      x: 0.5, y: 4.8, w: 9, h: 0.5,
      fontSize: 12, fontFace: F.body, color: C.secondary,
      align: "center", italic: true
    });
  }
}
```

---

## 流程/时间线页模板

```javascript
function addTimelineSlide(pres, { title, steps }) {
  // steps: [{ label: "阶段一", title: "需求分析", desc: "..." }, ...]（3-5步）
  const slide = pres.addSlide();
  slide.background = { color: C.bgLight };
  
  // 标题栏
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 1.0,
    fill: { color: C.primary }, line: { width: 0 }
  });
  slide.addText(title, {
    x: 0.4, y: 0, w: 9.2, h: 1.0,
    fontSize: 26, fontFace: F.title, bold: true,
    color: C.white, valign: "middle", margin: 0
  });
  
  // 时间线主轴
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 2.75, w: 9, h: 0.08,
    fill: { color: C.primary, transparency: 60 }, line: { width: 0 }
  });
  
  const count = steps.length;
  const stepW = 9 / count;
  steps.forEach((step, i) => {
    const cx = 0.5 + i * stepW + stepW / 2;
    
    // 节点圆圈
    slide.addShape(pres.shapes.OVAL, {
      x: cx - 0.3, y: 2.49, w: 0.6, h: 0.6,
      fill: { color: i === 0 ? C.accent : C.primary }, line: { width: 0 },
      shadow: makeShadow()
    });
    slide.addText(String(i + 1), {
      x: cx - 0.3, y: 2.49, w: 0.6, h: 0.6,
      fontSize: 14, bold: true, color: C.white,
      align: "center", valign: "middle", margin: 0
    });
    
    // 阶段标签（节点上方）
    slide.addText(step.label, {
      x: cx - stepW / 2 + 0.05, y: 1.9, w: stepW - 0.1, h: 0.4,
      fontSize: 11, fontFace: F.body, color: C.textMuted,
      align: "center", italic: true
    });
    
    // 步骤标题
    slide.addText(step.title, {
      x: cx - stepW / 2 + 0.05, y: 3.2, w: stepW - 0.1, h: 0.5,
      fontSize: 14, fontFace: F.body, bold: true,
      color: C.text, align: "center"
    });
    
    // 步骤描述
    if (step.desc) {
      slide.addText(step.desc, {
        x: cx - stepW / 2 + 0.1, y: 3.75, w: stepW - 0.2, h: 1.5,
        fontSize: 11, fontFace: F.body, color: C.textMuted,
        align: "center"
      });
    }
  });
}
```

---

## 图文混排页模板

```javascript
function addImageTextSlide(pres, { title, points, imageUrl }) {
  const slide = pres.addSlide();
  slide.background = { color: C.bgLight };
  
  // 标题栏
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 1.0,
    fill: { color: C.primary }, line: { width: 0 }
  });
  slide.addText(title, {
    x: 0.4, y: 0, w: 9.2, h: 1.0,
    fontSize: 26, fontFace: F.title, bold: true,
    color: C.white, valign: "middle", margin: 0
  });
  
  // 左侧文字区
  const startY = 1.3;
  points.forEach((pt, i) => {
    const y = startY + i * 1.1;
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0.3, y: y, w: 0.06, h: 0.7,
      fill: { color: C.accent }, line: { width: 0 }
    });
    slide.addText(pt.heading, {
      x: 0.55, y: y, w: 4.7, h: 0.38,
      fontSize: 15, fontFace: F.body, bold: true, color: C.text
    });
    slide.addText(pt.body || "", {
      x: 0.55, y: y + 0.35, w: 4.7, h: 0.5,
      fontSize: 12, fontFace: F.body, color: C.textMuted
    });
  });
  
  // 右侧图片（或占位矩形）
  if (imageUrl) {
    slide.addImage({ path: imageUrl, x: 5.5, y: 1.2, w: 4, h: 4.0, sizing: { type: 'cover', w: 4, h: 4 } });
  } else {
    // 无图片时用装饰色块代替
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 5.5, y: 1.2, w: 4.0, h: 4.0,
      fill: { color: C.primary, transparency: 85 }, line: { width: 0 }
    });
    slide.addShape(pres.shapes.OVAL, {
      x: 6.5, y: 2.2, w: 2, h: 2,
      fill: { color: C.secondary, transparency: 50 }, line: { width: 0 }
    });
  }
}
```

---

## 封底模板

```javascript
function addEndSlide(pres, { callToAction, contact, website }) {
  const slide = pres.addSlide();
  slide.background = { color: C.primary };
  
  // 大号 CTA 文字
  slide.addText(callToAction || "谢谢！", {
    x: 0.5, y: 1.5, w: 9, h: 1.2,
    fontSize: 48, fontFace: F.title, bold: true,
    color: C.white, align: "center"
  });
  
  // 分隔线
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 3.5, y: 2.9, w: 3, h: 0.06,
    fill: { color: C.accent }, line: { width: 0 }
  });
  
  // 联系方式
  if (contact || website) {
    slide.addText([
      ...(contact ? [{ text: `📧 ${contact}`, options: { breakLine: true } }] : []),
      ...(website ? [{ text: `🌐 ${website}` }] : [])
    ], {
      x: 0.5, y: 3.3, w: 9, h: 1.2,
      fontSize: 18, fontFace: F.body, color: C.secondary, align: "center"
    });
  }
  
  // 底部装饰
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 5.1, w: 10, h: 0.525,
    fill: { color: C.accent, transparency: 20 }, line: { width: 0 }
  });
}
```

---

## 常见陷阱检查清单

生成前必须检查：
- [ ] 所有颜色值不含 `#` 前缀
- [ ] shadow 对象每次都是全新的（用工厂函数 `makeShadow()`）
- [ ] 多行文本使用 `breakLine: true` 而不是 `\n`
- [ ] 列表使用 `bullet: true` 而不是 `•` unicode
- [ ] 阴影 `offset` 为正数（负数会损坏文件）
- [ ] 输出路径为 `/mnt/user-data/outputs/xxx.pptx`
