const unitMap = [
  { label: "Acceleration", unit: "m/s2" },
  { label: "Ampere", unit: "A" },
  { label: "Ampere hour", unit: "Ah" },
  { label: "Bar", unit: "bar" },
  { label: "Beats", unit: "beats" },
  { label: "Becquerel", unit: "Bq" },
  { label: "Bel", unit: "Bspl" },
  { label: "Bit", unit: "bit" },
  { label: "Bit per second", unit: "bit/s" },
  { label: "Bpm", unit: "beat/min" },
  { label: "Byte", unit: "B" },
  { label: "Candela", unit: "cd" },
  { label: "Candela per square meter", unit: "cd/m2" },
  { label: "Centimetre per hour", unit: "cm/h" },
  { label: "Coulomb", unit: "C" },
  { label: "Counter", unit: "count" },
  { label: "Cubic meter", unit: "m3" },
  { label: "Cubic meter per second", unit: "m3/s" },
  { label: "Decibel", unit: "db" },
  { label: "Decibel milliwatt", unit: "dBm" },
  { label: "Decibel relative to 1 w", unit: "dBW" },
  { label: "Degrees angle", unit: "deg" },
  { label: "Degrees celsius", unit: "Cel" },
  { label: "Degrees latitude", unit: "lat" },
  { label: "Degrees longitude", unit: "lon" },
  { label: "Event rate per minute", unit: "1/min" },
  { label: "Event rate per second", unit: "1/s" },
  { label: "Fahrenheit", unit: "f" },
  { label: "Farad", unit: "F" },
  { label: "Gram", unit: "g" },
  { label: "Gray", unit: "Gy" },
  { label: "Hectopascal", unit: "hPa" },
  { label: "Henry", unit: "H" },
  { label: "Hertz", unit: "Hz" },
  { label: "Hour", unit: "h" },
  { label: "Joule", unit: "J" },
  { label: "Katal", unit: "kat" },
  { label: "Kelvin", unit: "K" },
  { label: "Kilogram", unit: "kg" },
  { label: "Kilometer", unit: "km" },
  { label: "Kilometer per hour", unit: "km/h" },
  { label: "Kilovolt ampere", unit: "kVA" },
  { label: "Kilovolt hour", unit: "kVAh" },
  { label: "Kilowatt", unit: "kW" },
  { label: "Kilowatt hour", unit: "kWh" },
  { label: "Liter", unit: "l" },
  { label: "Liter per hour", unit: "l/h" },
  { label: "Liter per second", unit: "l/s" },
  { label: "Lumen", unit: "lm" },
  { label: "Lux", unit: "lx" },
  { label: "Meter", unit: "m" },
  { label: "Milliampere", unit: "mA" },
  { label: "Millimeter", unit: "mm" },
  { label: "Millisecond", unit: "ms" },
  { label: "Millivolt", unit: "mV" },
  { label: "Minute", unit: "min" },
  { label: "Mole", unit: "mol" },
  { label: "Newton", unit: "N" },
  { label: "Ohm", unit: "Ohm" },
  { label: "Parts per million", unit: "ppm" },
  { label: "Pascal", unit: "Pa" },
  { label: "Percent", unit: "/100" },
  { label: "Percentage remaining battery level", unit: "%EL" },
  { label: "Ph", unit: "pH" },
  { label: "Radian", unit: "rad" },
  { label: "Ratio", unit: "//" },
  { label: "Relative humidity", unit: "%RH" },
  { label: "Second", unit: "s" },
  { label: "Seconds remaining battery level", unit: "EL" },
  { label: "Siemens", unit: "S" },
  { label: "Siemens per meter", unit: "S/m" },
  { label: "Sievert", unit: "Sv" },
  { label: "Square meter", unit: "m2" },
  { label: "Steradian", unit: "sr" },
  { label: "Tesla", unit: "T" },
  { label: "Velocity", unit: "m/s" },
  { label: "Volt", unit: "V" },
  { label: "Watt", unit: "W" },
  { label: "Watt hour", unit: "Wh" },
  { label: "Watt per square meter", unit: "W/m2" },
  { label: "Weber", unit: "Wb" }
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
