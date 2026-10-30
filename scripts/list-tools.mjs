import { build } from 'esbuild'
const result = await build({
  entryPoints: ['src/tools/catalog.ts'],
  bundle: true,
  format: 'esm',
  write: false,
})
const { toolCatalog } = await import(
  `data:text/javascript;base64,${Buffer.from(result.outputFiles[0].text).toString('base64')}`
)
console.log(JSON.stringify(Object.entries(toolCatalog).map(([id, tool]) => ({ id, ...tool }))))
