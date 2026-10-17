declare module 'virtual:gaze-content' {
  type GazeBlock =
    | { type: 'html'; html: string }
    | { type: 'code'; code: string; language: string; label?: string }
    | { type: 'code-group'; items: { label: string; code: string; language: string }[] }
    | { type: 'admonition'; kind: string; title: string; blocks: GazeBlock[] }
    | { type: 'details'; title: string; blocks: GazeBlock[] }
    | { type: 'heading'; depth: number; id: string; html: string; text: string }
  const content: {
    guides: Record<
      string,
      {
        id: string
        title: string
        intro: GazeBlock[]
        sections: { id: string; title: string; htmlTitle: string; blocks: GazeBlock[] }[]
        outline: { id: string; depth: number; title: string }[]
        search: string
      }
    >
  }
  export default content
}
