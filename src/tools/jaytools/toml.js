// Adapted from jaywcjlove/tools packages/toml-to-json (MIT).
import TOML from 'toml'
export const transform = (input) => JSON.stringify(TOML.parse(input), null, 2)
