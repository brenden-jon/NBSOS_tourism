// Labels name the action explicitly. "Invest / Develop" was ambiguous - readers could not
// tell whether it meant building infrastructure or building up ecosystems.
export const ACTIONS = {
  PROTECT: { key: 'PROTECT', label: 'Protect ecosystems', color: '#2E7D5B',
    blurb: 'High nature and biodiversity value with a protection gap. Conservation leads; visitor access stays low-impact.' },
  INVEST:  { key: 'INVEST',  label: 'Build tourism infrastructure', color: '#3E7CAB',
    blurb: 'Real attraction and workable access with little existing supply. New visitor infrastructure is the binding constraint.' },
  ADAPT:   { key: 'ADAPT',   label: 'Upgrade destination', color: '#D99A2B',
    blurb: 'An established destination. Upgrade what exists and shore up the ecosystems it depends on.' },
  MANAGE:  { key: 'MANAGE',  label: 'Limit development',  color: '#9B4B54',
    blurb: 'Sensitive and reachable. Steer new construction elsewhere and invest in management capacity.' },
  NONE:    { key: 'NONE',    label: 'No strong basis',   color: '#D3DAE0',
    blurb: 'Nothing here meets the evidence threshold for a screening-level recommendation.' },
}

export const FAMILIES = [
  { key: 'NAV',  label: 'Nature attraction',   desc: 'Ecosystems, terrain and named natural features that a visitor would travel for.' },
  { key: 'TDL',  label: 'Tourism development', desc: 'Accommodation, food service, attractions, trails and marine operators already present.' },
  { key: 'ACC',  label: 'Accessibility',       desc: 'Modelled travel time to tourism gateways and to Panama City over a road and sea friction surface.' },
  { key: 'BCV',  label: 'Biodiversity value',  desc: 'Threatened (IUCN CR/EN/VU) species richness, total recorded richness, forest, mangrove and shelf habitat, ecoregion rarity and protection.' },
  { key: 'RES',  label: 'Resilience function', desc: 'Nature’s protective role against modelled flood hazard: the share of wave energy mangrove and reef remove from what reaches people in the 1-in-100 year coastal flood zone, plus catchment forest above river-flood-exposed population.' },
  { key: 'JOBS', label: 'Local opportunity',   desc: 'Local labour pool, community-tourism context and contribution to decentralisation.' },
]

// A single, plain distinction. The earlier four-way taxonomy made readers learn a
// vocabulary before they could read a result.
export const GOV_PLAN = {
  1: { label: 'In a government priority destination', color: '#7FA23A' },
  0: { label: 'Outside the government plan', color: '#8EA0AF' },
}

// The two independent recommendations. Blue is the built side, green the ecosystem side,
// used consistently on cards, dossiers and the map.
export const INFRA_LEVELS = {
  develop: { label: 'Develop new capacity', color: '#1F4E6E', short: 'Develop' },
  upgrade: { label: 'Upgrade and diversify', color: '#4E8FBF', short: 'Upgrade' },
  light:   { label: 'Low-impact access only', color: '#9CC3DC', short: 'Low-impact' },
  none:    { label: 'No new development', color: '#C7D2DA', short: 'None' },
}

export const NATURE_LEVELS = {
  protect_restore: { label: 'Protect and restore', color: '#14513C', short: 'Protect + restore' },
  protect:         { label: 'Protect', color: '#3E9B7E', short: 'Protect' },
  restore:         { label: 'Restore', color: '#8FBF6A', short: 'Restore' },
  maintain:        { label: 'Maintain', color: '#CFD9CE', short: 'Maintain' },
}

export const BASE = import.meta.env.BASE_URL
// eslint-disable-next-line no-undef
const BUILD = typeof __BUILD_ID__ !== 'undefined' ? __BUILD_ID__ : 'dev'
export const dataUrl = (f) => `${BASE}data/${f}?v=${BUILD}`
