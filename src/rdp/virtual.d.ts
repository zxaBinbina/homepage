declare module 'virtual:rdp-wiki' {
  type WikiBlock =
    | { type: 'html'; html: string }
    | { type: 'code'; code: string; language: string }
    | { type: 'diagram' }
  const content: {
    sections: {
      id: string
      title: string
      step?: string
      group: string
      blocks: WikiBlock[]
      search: string
    }[]
  }
  export default content
}
