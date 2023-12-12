const unitMap = new Map([
  ["m/s2", "Acceleration"],
  ["Ah", "Ampere Hour"],
  ["A", "Ampere"],
  ["beats", "Beats"],
  ["Bq", "Becquerel"],
  ["Bspl", "Bel"],
  ["bit/s", "Bit per second"],
  ["bit", "Bit"],
  ["beat/min", "Bpm"],
  ["B", "Byte"],
  ["cd/m2", "Candela per square meter"],
  ["cd", "Candela"],
  ["C", "Coulomb"],
  ["count", "Counter"],
  ["m3/s", "Cubic meter per second"],
  ["m3", "Cubic meter"],
  ["dBm", "Decibel Milliwatt"],
  ["dBW", "Decibel relative to 1 w"],
  ["db", "Decibel"],
  ["Cel", "Degrees celsius"],
  ["lat", "Degrees latitude"],
  ["lon", "Degrees longitude"],
  ["1/min", "Event rate per minute"],
  ["1/s", "Event rate per second"],
  ["F", "Farad"],
  ["g", "Gram"],
  ["Gy", "Gray"],
  ["hPa", "Hectopascal"],
  ["H", "Henry"],
  ["Hz", "Hertz"],
  ["h", "Hour"],
  ["J", "Joule"],
  ["kat", "Katal"],
  ["K", "Kelvin"],
  ["kg", "Kilogram"],
  ["km", "Kilometer"],
  ["km/h", "Kilometer"],
  ["kVA", "Kilovolt Ampere"],
  ["kVAh", "Kilovolt Hour"],
  ["kWh", "Kilowatt Hour"],
  ["kW", "Kilowatt"],
  ["l/s", "Liter per second"],
  ["l", "Liter"],
  ["lm", "Lumen"],
  ["lx", "Lux"],
  ["m", "Meter"],
  ["mA", "Milliampere"],
  ["mm", "Millimeter"],
  ["ms", "Millisecond"],
  ["mV", "Millivolt"],
  ["min", "Minute"],
  ["mol", "Mole"],
  ["N", "Newton"],
  ["Ohm", "Ohm"],
  ["ppm", "Parts per million"],
  ["Pa", "Pascal"],
  ["%EL", "Percentage remaining battery level"],
  ["pH", "Ph"],
  ["rad", "Radian"],
  ["//", "Ratio"],
  ["%RH", "Relative humidity"],
  ["s", "Second"],
  ["EL", "Seconds remaining battery level"],
  ["S/m", "Siemens per meter"],
  ["S", "Siemens"],
  ["Sv", "Sievert"],
  ["m2", "Square meter"],
  ["sr", "Steradian"],
  ["T", "Tesla"],
  ["", "Text"],
  ["m/s", "Velocity"],
  ["V", "Volt"],
  ["Wh", "Watt Hour"],
  ["W/m2", "Watt per square meter"],
  ["W", "Watt"],
  ["Wb", "Weber"]
])

function getUnitDetails(unit) {
  if (!unit) return unitMap.get("")
  const description = unitMap.get(unit)
  if (description) return description
  else return ""
}

function getUnitList() {
  return Array.from(unitMap.keys())
}

function getUnitDetailList() {
  return Array.from(unitMap.values())
}

function getMapObject() {
  return Object.fromEntries(unitMap.entries())
}
