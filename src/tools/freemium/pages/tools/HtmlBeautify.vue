<template>
  <TransformTool
    :transform="transform"
    :options="options"
    :sample="sample"
    accept=".html,.htm,.erb,.ejs,.hbs,.vue,text/html,text/plain"
    :download="
      (o) =>
        o.lang === 'erb'
          ? 'template.html.erb'
          : o.mode === 'minify'
            ? 'index.min.html'
            : 'index.html'
    "
  />
</template>

<script setup>
import beautify from 'js-beautify'
import TransformTool from '../../components/TransformTool.vue'

const options = [
  {
    key: 'mode',
    type: 'segmented',
    label: '模式',
    default: 'beautify',
    options: [
      { value: 'beautify', label: '格式化' },
      { value: 'minify', label: '压缩' },
    ],
  },
  {
    key: 'lang',
    type: 'segmented',
    label: '语言',
    default: 'html',
    options: [
      { value: 'html', label: 'HTML' },
      { value: 'erb', label: 'ERB' },
    ],
  },
  {
    key: 'indent',
    type: 'select',
    label: '缩进',
    default: '2',
    options: [
      { value: '2', label: '2 个空格' },
      { value: '4', label: '4 个空格' },
      { value: 'tab', label: 'Tab 缩进' },
    ],
  },
  {
    key: 'wrap',
    type: 'select',
    label: '属性换行',
    default: 'auto',
    options: [
      { value: 'auto', label: '自动' },
      { value: 'force-aligned', label: '每个属性单独一行' },
      { value: 'preserve', label: '保留原样' },
    ],
  },
]

const sample =
  '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Freemium</title><style>body{font-family:system-ui;margin:0}</style></head><body><!-- main --><header class="hero"><h1>Developer Toolbox</h1><p>41 tools, <strong>zero</strong> uploads.</p></header><ul><li><a href="/json-formatter">JSON</a></li><li><a href="/base64">Base64</a></li></ul><% if user.signed_in? %><p>Hi, <%= user.name %></p><% end %><script>document.querySelector("h1").addEventListener("click",()=>alert("hi"))<\/script></body></html>'

// ERB/EJS tags are swapped for placeholders so the HTML beautifier leaves them untouched.
// Control tags (<% if %>, <% end %>) become block-level custom elements so each gets its own line;
// output tags (<%= %>) stay inline text.
function protectTemplates(src) {
  const saved = []
  const out = src.replace(/<%(=|-)?[\s\S]*?%>/g, (m, output) => {
    const i = saved.push(m) - 1
    return output ? `__ERB${i}__` : `<x-erb data-i="${i}"></x-erb>`
  })
  const restore = (s) =>
    s
      .replace(/<x-erb data-i="(\d+)"><\/x-erb>/g, (_, i) => saved[i])
      .replace(/__ERB(\d+)__/g, (_, i) => saved[i])
  return { out, restore }
}

// Collapse whitespace between tags and strip comments, but leave <pre>, <textarea>, <script> and <style> bodies intact.
function minify(src) {
  const keep = []
  const guarded = src.replace(
    /<(pre|textarea|script|style)\b[\s\S]*?<\/\1>/gi,
    (m) => `\u0000${keep.push(m) - 1}\u0000`,
  )
  const out = guarded
    .replace(/<!--(?!\[if)[\s\S]*?-->/g, '')
    .replace(/\s+/g, ' ')
    .replace(/>\s+</g, '><')
    .replace(/\s+(\/?>)/g, '$1')
    .trim()
  return out.replace(/\u0000(\d+)\u0000/g, (_, i) => keep[i])
}

function transform(input, o) {
  const { out, restore } =
    o.lang === 'erb' ? protectTemplates(input) : { out: input, restore: (s) => s }
  if (o.mode === 'minify') return restore(minify(out))
  return restore(
    beautify.html(out, {
      indent_size: o.indent === 'tab' ? 1 : Number(o.indent),
      indent_char: o.indent === 'tab' ? '\t' : ' ',
      wrap_attributes: o.wrap,
      wrap_line_length: 120,
      indent_inner_html: true,
      inline_custom_elements: o.lang !== 'erb',
      extra_liners: [],
    }),
  )
}
</script>
