export const ACTIONS = {
  PROTECT: { key: 'PROTECT', label: 'Protect / Restore', color: '#2E7D5B',
    blurb: 'High nature and biodiversity value with a protection gap — conserve or restore first.' },
  INVEST:  { key: 'INVEST',  label: 'Invest / Develop',  color: '#3E7CAB',
    blurb: 'Real attraction and workable access, but little tourism supply yet.' },
  ADAPT:   { key: 'ADAPT',   label: 'Adapt / Strengthen', color: '#D99A2B',
    blurb: 'Established destination whose natural base needs shoring up.' },
  MANAGE:  { key: 'MANAGE',  label: 'Manage / Avoid',    color: '#9B4B54',
    blurb: 'Sensitive places where tourism pressure should be limited or carefully managed.' },
  NONE:    { key: 'NONE',    label: 'No strong basis',   color: '#D3DAE0',
    blurb: 'Nothing here meets the evidence threshold for a screening-level recommendation.' },
}

export const FAMILIES = [
  { key: 'NAV',  label: 'Nature attraction',   desc: 'Ecosystems, terrain and named natural features that a visitor would travel for.' },
  { key: 'TDL',  label: 'Tourism development', desc: 'Accommodation, food service, attractions, trails and marine operators already present.' },
  { key: 'ACC',  label: 'Accessibility',       desc: 'Modelled travel time to tourism gateways and to Panama City over a road and sea friction surface.' },
  { key: 'BCV',  label: 'Biodiversity value',  desc: 'Recorded species richness, forest, mangrove and shelf habitat, ecoregion rarity and protection.' },
  { key: 'RES',  label: 'Resilience function', desc: 'Screening-level contribution of nature to coastal and watershed protection. Not a hazard model.' },
  { key: 'JOBS', label: 'Local opportunity',   desc: 'Local labour pool, community-tourism context and contribution to decentralisation.' },
]

// A single, plain distinction. The earlier four-way taxonomy made readers learn a
// vocabulary before they could read a result.
export const GOV_PLAN = {
  1: { label: 'In a government priority destination', color: '#7FA23A' },
  0: { label: 'Outside the government plan', color: '#8EA0AF' },
}

export const BASE = import.meta.env.BASE_URL
// eslint-disable-next-line no-undef
const BUILD = typeof __BUILD_ID__ !== 'undefined' ? __BUILD_ID__ : 'dev'
export const dataUrl = (f) => `${BASE}data/${f}?v=${BUILD}`
