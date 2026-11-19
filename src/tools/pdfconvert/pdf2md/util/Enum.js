// Small local replacement for the enumify API used by the MIT pdf2md pipeline.
export class Enum {
  static initEnum(values) {
    for (const [name, value] of Object.entries(values)) {
      this[name] = Object.freeze({ ...value, name })
    }
  }

  static enumValueOf(name) {
    if (!Object.hasOwn(this, name)) throw new Error(`Unknown enum value: ${name}`)
    return this[name]
  }
}
