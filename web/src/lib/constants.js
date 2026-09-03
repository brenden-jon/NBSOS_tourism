export const ACTIONS = {
  PROTECT: { key: 'PROTECT', label: 'Protect / Restore', color: '#2E7D5B',
    blurb: 'High nature and biodiversity value with a protection gap — conserve or restore first.' },
  INVEST:  { key: 'INVEST',  label: 'Invest / Develop',  color: '#3E7CAB',
    blurb: 'Real attraction and workable access, but little tourism supply yet.' },
  ADAPT:   { key: 'ADAPT',   label: 'Adapt / Strengthen', color: '#D99A2B',
    blurb: 'Established destination whose natural base needs shoring up.' },
  MANAGE:  { key: 'MANAGE',  label: 'Manage / Avoid',    color: '#9B4B54',
    blurb: 'Sensitive places where tourism pressure should be limited or carefully managed.' },
}

export const FAMILIES = [
  { key: 'NAV',  label: 'Nature attraction',   desc: 'Ecosystems, terrain and named natural features that a visitor would travel for.' },
  { key: 'TDL',  label: 'Tourism development', desc: 'Accommodation, food service, attractions, trails and marine operators already present.' },
  { key: 'ACC',  label: 'Accessibility',       desc: 'Modelled travel time to tourism gateways and to Panama City over a road and sea friction surface.' },
  { key: 'BCV',  label: 'Biodiversity value',  desc: 'Recorded species richness, forest, mangrove and shelf habitat, ecoregion rarity and protection.' },
  { key: 'RES',  label: 'Resilience function', desc: 'Screening-level contribution of nature to coastal and watershed protection. Not a hazard model.' },
  { key: 'JOBS', label: 'Local opportunity',   desc: 'Local labour pool, community-tourism context and contribution to decentralisation.' },
]

export const GOV_RELATION = {
  reinforces: { label: 'Reinforces a government priority', color: '#7FA23A' },
  refines:    { label: 'Refines a government priority',    color: '#D99A2B' },
  partial:    { label: 'Partly overlaps a priority',       color: '#8EA0AF' },
  new:        { label: 'Outside government priorities',    color: '#3E7CAB' },
}

export const BASE = import.meta.env.BASE_URL
// eslint-disable-next-line no-undef
const BUILD = typeof __BUILD_ID__ !== 'undefined' ? __BUILD_ID__ : 'dev'
export const dataUrl = (f) => `${BASE}data/${f}?v=${BUILD}`
