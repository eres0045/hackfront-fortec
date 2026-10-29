// WhyCode pitch deck — DESIGNED template built with PptxGenJS 4.x.
//
// Design system ("WHYCODE" master), applied to every slide:
//   • 16:9, dark forest background, green accent bar on the left edge
//   • Footer on every slide: "WhyCode · FORTEC · hackFront India 2026" + slide number
//   • Kicker (small green caps) + bold white title + green rule on content slides
//   • Terminal-styled dark panels with green/white mono text for the demo slides
//   • Stat chips for the engineering numbers
// Content: the 9 verified WhyCode slides — no invented facts.
const PptxGenJS = require('pptxgenjs');
const pptx = new PptxGenJS();

const BG = '0B1F1A';
const PANEL = '06140F';
const CHIP = '123527';
const CHIP_LINE = '1F4D33';
const GREEN = '4ADE80';
const GREEN_SOFT = '86EFAC';
const WHITE = 'FFFFFF';
const GREY = 'D1D5DB';
const MUTED = '9CA3AF';
const RED = 'F87171';
const SANS = 'Calibri';
const MONO = 'Consolas';
const ROUND = (pptx.ShapeType && pptx.ShapeType.roundRect) || 'roundRect';

pptx.defineLayout({ name: 'WIDE', width: 13.333, height: 7.5 });
pptx.layout = 'WIDE';
pptx.title = 'WhyCode — FORTEC';
pptx.author = 'FORTEC';

pptx.defineSlideMaster({
  title: 'WHYCODE',
  background: { color: BG },
  objects: [
    { rect: { x: 0, y: 0, w: 0.14, h: 7.5, fill: { color: GREEN } } },
    {
      text: {
        text: 'WhyCode  ·  FORTEC  ·  hackFront India 2026',
        options: { x: 0.6, y: 7.02, w: 11.0, h: 0.3, fontSize: 10, color: MUTED, fontFace: SANS },
      },
    },
  ],
});

let n = 0;
function slide() {
  n += 1;
  const s = pptx.addSlide({ masterName: 'WHYCODE' });
  s.addText(String(n), { x: 12.35, y: 7.02, w: 0.5, h: 0.3, fontSize: 10, color: MUTED, fontFace: SANS, align: 'right' });
  return s;
}

function titleBlock(s, kicker, title) {
  s.addText(kicker, { x: 0.6, y: 0.45, w: 12.1, h: 0.35, fontSize: 12, bold: true, color: GREEN, fontFace: SANS, charSpacing: 2 });
  s.addText(title, { x: 0.6, y: 0.85, w: 12.1, h: 0.7, fontSize: 30, bold: true, color: WHITE, fontFace: SANS });
  s.addShape(ROUND, { x: 0.6, y: 1.62, w: 0.9, h: 0.06, fill: { color: GREEN } });
}

function bullets(s, items, y0) {
  let y = y0;
  for (const item of items) {
    s.addText(
      [
        { text: '▸  ', options: { color: GREEN, bold: true } },
        { text: item, options: { color: GREY } },
      ],
      { x: 0.6, y, w: 12.1, h: 0.6, fontSize: 18, fontFace: SANS, valign: 'top' }
    );
    y += item.length > 95 ? 0.95 : 0.62;
  }
  return y;
}

// Terminal panel: dark rounded panel + mono runs. Each line: [{text, color, bold?}]
function terminal(s, lines, y, h) {
  s.addShape(ROUND, { x: 0.6, y, w: 12.13, h, fill: { color: PANEL }, line: { color: CHIP_LINE, width: 1 } });
  const runs = [];
  lines.forEach((line, i) => {
    line.forEach((run) => runs.push({ text: run.t, options: { color: run.c, bold: !!run.b, fontFace: MONO, fontSize: 13.5, breakLine: false } }));
    if (i < lines.length - 1) runs.push({ text: '', options: { breakLine: true } });
  });
  s.addText(runs, { x: 0.9, y: y + 0.3, w: 11.6, h: h - 0.6, valign: 'top', lineSpacingMultiple: 1.35 });
}

function chip(s, x, y, value, label) {
  s.addShape(ROUND, { x, y, w: 3.85, h: 1.35, fill: { color: CHIP }, line: { color: CHIP_LINE, width: 1 } });
  s.addText(value, { x, y: y + 0.18, w: 3.85, h: 0.55, fontSize: 26, bold: true, color: GREEN, fontFace: SANS, align: 'center' });
  s.addText(label, { x, y: y + 0.8, w: 3.85, h: 0.35, fontSize: 12, color: GREY, fontFace: SANS, align: 'center' });
}

const G = (t, b) => ({ t, c: GREEN, b });
const W = (t, b) => ({ t, c: WHITE, b });
const GR = (t, b) => ({ t, c: GREY, b });
const GS = (t, b) => ({ t, c: GREEN_SOFT, b });
const R = (t, b) => ({ t, c: RED, b });

// ---------- 1 · Cover ----------
{
  const s = slide();
  s.addText('WhyCode', { x: 0.9, y: 1.9, w: 11.5, h: 1.4, fontSize: 66, bold: true, color: WHITE, fontFace: SANS });
  s.addText('Why is this code like this? Ask its own history.', { x: 0.9, y: 3.35, w: 11.5, h: 0.6, fontSize: 24, color: GREEN, fontFace: SANS });
  s.addShape(ROUND, { x: 0.9, y: 4.25, w: 1.6, h: 0.07, fill: { color: GREEN } });
  s.addText('Team FORTEC  ·  hackFront India 2026  ·  AI and Developer Tools (T-1)', { x: 0.9, y: 4.6, w: 11.5, h: 0.45, fontSize: 16, bold: true, color: WHITE, fontFace: SANS });
  s.addText('Ronit Shrimankar (lead)  ·  Anshul Kamthe  ·  Udita Singh', { x: 0.9, y: 5.15, w: 11.5, h: 0.4, fontSize: 15, color: GREY, fontFace: SANS });
  s.addText('Built on django/django', { x: 0.9, y: 5.6, w: 11.5, h: 0.4, fontSize: 15, color: MUTED, fontFace: SANS });
}

// ---------- 2 · Problem ----------
{
  const s = slide();
  titleBlock(s, '01 · THE PROBLEM', 'Nobody can explain the code anymore');
  bullets(s, [
    'Codebases accumulate decisions nobody can explain any more.',
    'A new developer reads an odd function and guesses why it exists.',
    'A wrong guess breaks something the original author fixed on purpose.',
    'The reasons live scattered across commits, pull requests and tickets — never in one place, never linked to the code they explain.',
  ], 2.0);
}

// ---------- 3 · Solution ----------
{
  const s = slide();
  titleBlock(s, '02 · THE SOLUTION', 'WhyCode: ask the history, get the evidence');
  bullets(s, [
    'Ingest a public repo’s history — commits, PRs and tickets — into a graph.',
    'Ask plain-language “why” questions about the code.',
    'Get a cited evidence chain plus a confidence score.',
    'When the graph holds no evidence, it refuses. No invented answers, ever.',
  ], 2.0);
}

// ---------- 4 · How it works ----------
{
  const s = slide();
  titleBlock(s, '03 · HOW IT WORKS', 'From repo history to cited answers');
  const steps = [
    ['1 · Ingest', 'GitHub API via gh (commits, PRs) plus Trac ticket pages — Django tracks decisions in Trac, not GitHub Issues.'],
    ['2 · Graph', 'Entities: commit, PR, ticket, file, person. Edges: authored, fixes, references, touches, supersedes.'],
    ['3 · Ask', 'Match the question, walk the evidence chain 2 hops, flag decisions superseded by newer ones — and refuse when evidence is absent.'],
    ['4 · Runs anywhere', 'The bundled SQLite database needs no credentials and no paid APIs.'],
  ];
  let y = 2.0;
  for (const [head, body] of steps) {
    s.addText(head, { x: 0.6, y, w: 2.6, h: 0.4, fontSize: 18, bold: true, color: GREEN, fontFace: SANS });
    s.addText(body, { x: 3.3, y, w: 9.4, h: 0.9, fontSize: 17, color: GREY, fontFace: SANS, valign: 'top' });
    y += body.length > 110 ? 1.15 : 0.9;
  }
}

// ---------- 5 · Demo Q1 ----------
{
  const s = slide();
  titleBlock(s, '04 · DEMO — REAL DJANGO HISTORY', 'A real answer, with cited evidence');
  terminal(s, [
    [G('$ '), W('python -m whycode.cli --question "Why does ignore_warnings match substrings by default?"')],
    [GR('refused: '), W('false', true), GR('    confidence: '), W('0.99', true)],
    [W('Best match: ', true), W('Fixed #37089 — Made ignore_warnings() match substrings by default. (commit)')],
    [GS('Evidence:')],
    [GS('→ fixes      '), W('Trac ticket #37089')],
    [GS('→ authored by '), W('HelmiDev03')],
  ], 2.0, 3.6);
}

// ---------- 6 · Demo Q2 ----------
{
  const s = slide();
  titleBlock(s, '04 · DEMO — REAL DJANGO HISTORY', 'Same for the template-tags option');
  terminal(s, [
    [G('$ '), W('python -m whycode.cli --question "Why is there a transitional option to disable multiline template tags?"')],
    [GR('refused: '), W('false', true), GR('    confidence: '), W('0.86', true)],
    [W('Best match: ', true), W('Refs #35899 — Added allow_multiline_tags transitional template option. (commit)')],
    [GS('Evidence:')],
    [GS('→ references '), W('Trac ticket #35899')],
    [GS('→ authored by '), W('boxed')],
  ], 2.0, 3.6);
}

// ---------- 7 · Refusal ----------
{
  const s = slide();
  titleBlock(s, '05 · THE REFUSAL', 'No evidence? It refuses instead of inventing');
  terminal(s, [
    [G('$ '), W('python -m whycode.cli --question "Why does Django use a microservices architecture?"')],
    [GR('refused: '), R('true', true), GR('    confidence: '), R('0.0', true)],
    [R('No evidence in the graph answers this. Refusing to invent an answer.', true)],
  ], 2.0, 2.6);
  s.addText('An earlier version answered this from an unrelated docs commit — the absent-term rule + regression test fixed it for good.',
    { x: 0.6, y: 5.0, w: 12.1, h: 0.8, fontSize: 16, color: MUTED, fontFace: SANS, valign: 'top' });
}

// ---------- 8 · Engineering ----------
{
  const s = slide();
  titleBlock(s, '06 · ENGINEERING', 'Runnable, tested, no magic');
  chip(s, 0.6, 2.0, '200', 'commits');
  chip(s, 4.75, 2.0, '100', 'pull requests');
  chip(s, 8.9, 2.0, '100', 'Trac tickets');
  chip(s, 0.6, 3.6, '161', 'files');
  chip(s, 4.75, 3.6, '90', 'people');
  chip(s, 8.9, 3.6, '630', 'edges');
  bullets(s, [
    'Python standard library only · SQLite graph · gh CLI.',
    '10/10 automated tests, including refusal and supersession cases.',
    'Bundled database runs the whole demo with zero credentials.',
  ], 5.25);
}

// ---------- 9 · Closing ----------
{
  const s = slide();
  s.addText('WhyCode — by FORTEC', { x: 0.6, y: 1.1, w: 12.1, h: 0.8, fontSize: 36, bold: true, color: WHITE, fontFace: SANS, align: 'center' });
  s.addText('github.com/eres0045/hackfront-fortec', { x: 0.6, y: 2.0, w: 12.1, h: 0.5, fontSize: 20, bold: true, color: GREEN, fontFace: SANS, align: 'center' });
  terminal(s, [
    [G('$ '), W('python -m whycode.cli --db data/whycode.db --question "Why ...?"')],
  ], 2.9, 1.4);
  s.addText('Questions welcome.', { x: 0.6, y: 4.9, w: 12.1, h: 0.6, fontSize: 24, bold: true, color: WHITE, fontFace: SANS, align: 'center' });
  s.addText('Built during the hackFront league timeline, from Django’s real, public history.',
    { x: 0.6, y: 5.6, w: 12.1, h: 0.4, fontSize: 14, color: MUTED, fontFace: SANS, align: 'center' });
}

pptx.writeFile({ fileName: 'whycode-pptxgenjs.pptx' })
  .then(() => console.log('WROTE whycode-pptxgenjs.pptx'))
  .catch((e) => { console.error('WRITE FAILED:', e); process.exit(1); });
