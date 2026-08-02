/** Seeded operator playbooks (lab scenarios / common IIQ checks). */
window.TELLER_PLAYBOOKS = [
  {
    id: "sod-triage",
    label: "SoD triage",
    group: "Governance",
    prompt:
      "How many open SoD policy violations are there right now? Summarize the top conflicts with identity display names and the conflicting entitlements.",
  },
  {
    id: "joiner-check",
    label: "Joiner check (Nina)",
    group: "JML",
    prompt:
      "Look up identity Nina Joiner (or nina.joiner / MNB00120). Summarize her cube status, manager, job title, and whether she has birthright / baseline access accounts.",
  },
  {
    id: "mover-check",
    label: "Mover check (Priya)",
    group: "JML",
    prompt:
      "Find Priya (priya.wire / MNB00090). What is her current department/manager versus a commercial banking move, and which apps/entitlements look like leftover wire access?",
  },
  {
    id: "leaver-check",
    label: "Leaver check (Jordan)",
    group: "JML",
    prompt:
      "Find Jordan Reed (jordan.reed / MNB00092). Is the identity disabled/terminated, and does any application account still look active?",
  },
  {
    id: "loa-check",
    label: "LOA check (Sofia)",
    group: "JML",
    prompt:
      "Find Sofia Torres / Sofia Murphy related to leave of absence (MNB00095 or sofia). Summarize active status, LOA signals, and whether access still looks appropriate.",
  },
  {
    id: "rehire-check",
    label: "Rehire check (Samir)",
    group: "JML",
    prompt:
      "Look up Samir Hassan (samir.hassan / MNB00094). Summarize lifecycle state (terminated vs active), manager, and whether rehire access looks restored.",
  },
  {
    id: "contractor-end",
    label: "Contractor end (Raj)",
    group: "JML",
    prompt:
      "Find Raj External (raj.external / MNB00093). Summarize contractor status, end-date signals, manager Christopher Hayes, and high-risk access such as AWS.",
  },
  {
    id: "hayes-org",
    label: "Hayes org chart",
    group: "Identities",
    prompt:
      "Who reports under Christopher Hayes (MNB00002)? List people by display name with their keys.",
  },
  {
    id: "anita-lookup",
    label: "Anita Rao lookup",
    group: "Identities",
    prompt: "Who is Anita Rao? Summarize her identity, manager, title, location, and IIQ lock/active status.",
  },
  {
    id: "agg-health",
    label: "Aggregation health",
    group: "Ops",
    prompt:
      "Check recent aggregation / task health for Meridian apps. List any failed or stuck tasks and what to do next.",
  },
  {
    id: "paris-people",
    label: "People in Paris",
    group: "Identities",
    prompt: "Find employees whose workplace or location is Paris. List display names and identity keys.",
  },
  {
    id: "cert-open",
    label: "Open certifications",
    group: "Governance",
    prompt:
      "Are there open certifications or certification campaigns? Summarize owners and how many items remain.",
  },
];
