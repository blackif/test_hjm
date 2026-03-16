// ═══════════════════════════════════════════════
// PPT 工具模块 - 设计系统、文字溢出防护、安全尺寸表
// ═══════════════════════════════════════════════

// 1. 设计系统配置（颜色、字体）
// 注意：可根据不同主题修改以下配置
const C = {
  primary: "36454F",
  secondary: "F2F2F2",
  accent: "C9A84C",
  white: "FFFFFF",
  dark: "1A1A1A",
  text: "2D2D2D",
  textMuted: "666666",
  bgLight: "F8F8F8"
};

const F = {
  title: "Cambria",
  body: "Calibri"
};

// 2. 文字溢出防护函数

/**
 * 超出 maxLen 时截断并补省略号
 * @param {string} text - 原始文字
 * @param {number} maxLen - 最大字符数
 * @returns {string} - 安全文字
 */
function safe(text, maxLen) {
  if (!text) return "";
  const s = String(text);
  return s.length > maxLen ? s.slice(0, maxLen - 1) + "…" : s;
}

/**
 * 根据文字框尺寸和字号动态计算最大安全字符数
 * @param {number} boxW - 文字框宽度（英寸）
 * @param {number} boxH - 文字框高度（英寸）
 * @param {number} fontSize - 字号（pt）
 * @param {number} lines - 最大行数
 * @returns {number} - 最大字符数
 */
function maxChars(boxW, boxH, fontSize, lines = 1) {
  const perLine = Math.floor(boxW / (fontSize * 0.0108));
  const maxLines = Math.floor(boxH / (fontSize * 0.018));
  return perLine * Math.min(lines, maxLines);
}

// 3. 常用元素安全尺寸表
// 用法：safe(text, SAFE.pageTitle.max)
// 自定义尺寸：safe(text, maxChars(w, h, fs, lines))
const SAFE = {
  pageTitle:  { w: 9.2,  h: 1.1,  fs: 28, max: 22 },   // 顶部标题栏
  coverTitle: { w: 8.5,  h: 1.6,  fs: 44, max: 14 },   // 封面大标题
  coverSub:   { w: 8.0,  h: 0.6,  fs: 18, max: 28 },   // 封面副标题
  cardTitle:  { w: 2.3,  h: 0.42, fs: 15, max: 11 },   // 小卡片标题
  cardBody:   { w: 2.3,  h: 0.95, fs: 12, max: 42 },   // 小卡片正文
  wideTitle:  { w: 4.0,  h: 0.45, fs: 16, max: 16 },   // 宽卡片标题
  wideBody:   { w: 3.9,  h: 1.1,  fs: 13, max: 55 },   // 宽卡片正文
  fullBody:   { w: 8.5,  h: 0.65, fs: 13, max: 65 },   // 全宽正文
  bigStat:    { w: 2.9,  h: 1.35, fs: 60, max: 5 },    // 大统计数字
  statLabel:  { w: 2.9,  h: 0.55, fs: 14, max: 18 },   // 统计标签
  statSource: { w: 2.9,  h: 0.4,  fs: 10, max: 24 },   // 数据来源
  tlYear:     { w: 1.8,  h: 0.4,  fs: 15, max: 6 },    // 时间线年份
  tlTitle:    { w: 1.8,  h: 0.38, fs: 13, max: 8 },    // 时间线标题
  tlDesc:     { w: 1.9,  h: 0.6,  fs: 10, max: 28 },   // 时间线描述
  stepTitle:  { w: 1.95, h: 0.5,  fs: 14, max: 9 },    // 流程步骤标题
  stepDesc:   { w: 1.95, h: 1.5,  fs: 11, max: 48 },   // 流程步骤描述
  listTitle:  { w: 8.0,  h: 0.38, fs: 16, max: 20 },   // 列表行标题
  listBody:   { w: 8.0,  h: 0.6,  fs: 12, max: 55 },   // 列表行正文
  endCta:     { w: 9.0,  h: 1.1,  fs: 44, max: 16 },   // 封底 CTA
  endContact: { w: 9.0,  h: 0.9,  fs: 16, max: 40 },   // 封底联系方式
  
  // 内容页 Key Point（标准布局 2-3 个）
  singleTitle: { w: 8.5, h: 0.4,  fs: 18, max: 12 },   // 小标题
  singleBody:  { w: 8.5, h: 0.6,  fs: 14, max: 45 },   // 正文
  
  // 内容页 Key Point（压缩布局 4 个）
  singleTitleC: { w: 8.5, h: 0.35, fs: 17, max: 11 },  // 小标题
  singleBodyC:  { w: 8.5, h: 0.5,  fs: 13, max: 35 }   // 正文
};

// 4. 导出模块
module.exports = { C, F, safe, maxChars, SAFE };
