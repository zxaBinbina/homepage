// Chance in the upstream browser bundle assigns to an existing global in workers.
// Declare that property before the bundled module is evaluated in strict mode.
self.chance = undefined
