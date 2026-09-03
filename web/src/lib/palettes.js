export const ECO_CLASSES = [
  ['Dense forest',                '#1B5E3F'],
  ['Forest mosaic',               '#66A177'],
  ['Mangrove',                    '#0F766E'],
  ['Wetland',                     '#86B8A9'],
  ['Shallow shelf / reef habitat','#3FA9C4'],
  ['Coastal water',               '#A8D5E2'],
  ['Open water',                  '#CDE4EC'],
  ['Cropland',                    '#D9C577'],
  ['Grassland & pasture',         '#C3CE9A'],
  ['Built-up',                    '#A2726F'],
  ['Mixed / other',               '#C9CFD4'],
]

export const TOURISM_CLASSES = [
  ['Established hub',   '#1F4E6E'],
  ['Developing',        '#3E7CAB'],
  ['Emerging',          '#71AAD7'],
  ['Marginal',          '#B9D2E6'],
  ['No mapped supply',  '#EDF1F4'],
]

export const matchExpr = (field, pairs, fallback) =>
  ['match', ['get', field], ...pairs.flatMap(([k, v]) => [k, v]), fallback]
