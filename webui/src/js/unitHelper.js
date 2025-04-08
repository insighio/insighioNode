const unitMap = [
  { unit: "m/s2", label: "Acceleration" },
  { unit: "Ah", label: "Ampere Hour" },
  { unit: "A", label: "Ampere" },
  { unit: "beats", label: "Beats" },
  { unit: "Bq", label: "Becquerel" },
  { unit: "Bspl", label: "Bel" },
  { unit: "bit/s", label: "Bit per second" },
  { unit: "bit", label: "Bit" },
  { unit: "beat/min", label: "Bpm" },
  { unit: "B", label: "Byte" },
  { unit: "cd/m2", label: "Candela per square meter" },
  { unit: "cd", label: "Candela" },
  { unit: "C", label: "Coulomb" },
  { unit: "count", label: "Counter" },
  { unit: "m3/s", label: "Cubic meter per second" },
  { unit: "m3", label: "Cubic meter" },
  { unit: "dBm", label: "Decibel Milliwatt" },
  { unit: "dBW", label: "Decibel relative to 1 w" },
  { unit: "db", label: "Decibel" },
  { unit: "Cel", label: "Degrees celsius" },
  { unit: "lat", label: "Degrees latitude" },
  { unit: "lon", label: "Degrees longitude" },
  { unit: "1/min", label: "Event rate per minute" },
  { unit: "1/s", label: "Event rate per second" },
  { unit: "F", label: "Farad" },
  { unit: "g", label: "Gram" },
  { unit: "Gy", label: "Gray" },
  { unit: "hPa", label: "Hectopascal" },
  { unit: "H", label: "Henry" },
  { unit: "Hz", label: "Hertz" },
  { unit: "h", label: "Hour" },
  { unit: "J", label: "Joule" },
  { unit: "kat", label: "Katal" },
  { unit: "K", label: "Kelvin" },
  { unit: "kg", label: "Kilogram" },
  { unit: "km", label: "Kilometer" },
  { unit: "km/h", label: "Kilometer" },
  { unit: "kVA", label: "Kilovolt Ampere" },
  { unit: "kVAh", label: "Kilovolt Hour" },
  { unit: "kWh", label: "Kilowatt Hour" },
  { unit: "kW", label: "Kilowatt" },
  { unit: "l/s", label: "Liter per second" },
  { unit: "l", label: "Liter" },
  { unit: "lm", label: "Lumen" },
  { unit: "lx", label: "Lux" },
  { unit: "m", label: "Meter" },
  { unit: "mA", label: "Milliampere" },
  { unit: "mm", label: "Millimeter" },
  { unit: "ms", label: "Millisecond" },
  { unit: "mV", label: "Millivolt" },
  { unit: "min", label: "Minute" },
  { unit: "mol", label: "Mole" },
  { unit: "N", label: "Newton" },
  { unit: "Ohm", label: "Ohm" },
  { unit: "ppm", label: "Parts per million" },
  { unit: "Pa", label: "Pascal" },
  { unit: "%EL", label: "Percentage remaining battery level" },
  { unit: "pH", label: "Ph" },
  { unit: "rad", label: "Radian" },
  { unit: "//", label: "Ratio" },
  { unit: "%RH", label: "Relative humidity" },
  { unit: "s", label: "Second" },
  { unit: "EL", label: "Seconds remaining battery level" },
  { unit: "S/m", label: "Siemens per meter" },
  { unit: "S", label: "Siemens" },
  { unit: "Sv", label: "Sievert" },
  { unit: "m2", label: "Square meter" },
  { unit: "sr", label: "Steradian" },
  { unit: "T", label: "Tesla" },
  { unit: "", label: "Text" },
  { unit: "m/s", label: "Velocity" },
  { unit: "V", label: "Volt" },
  { unit: "Wh", label: "Watt Hour" },
  { unit: "W/m2", label: "Watt per square meter" },
  { unit: "W", label: "Watt" },
  { unit: "Wb", label: "Weber" }
]

export function getUnitDetails(unit) {
  if (!unit) return unitMap.get("")
  const description = unitMap.get(unit)
  if (description) return description
  else return ""
}

export function getUnitList() {
  return Array.from(unitMap.keys())
}

export function getUnitDetailList() {
  return Array.from(unitMap.values())
}

export function getMapObject() {
  return unitMap //Object.fromEntries(unitMap.entries())
}
