// Static mock roster for the manual-routing dropdowns on the AI-vs-manual
// page. Deliberately NOT the real `employee` table — that page never touches
// the database, this is just enough of a roster to make "assigned to" /
// "reports to" feel real.

export type RosterEntry = {
  name: string;
  role: string;
  team: string;
  reportsTo: string;
};

export const ROSTER: RosterEntry[] = [
  { name: "Priya Nair", role: "Specialist", team: "Billing Team", reportsTo: "Dana Fischer" },
  { name: "Sam Okafor", role: "Senior Specialist", team: "Billing Team", reportsTo: "Dana Fischer" },
  { name: "Marcus Lee", role: "Specialist", team: "Developer Support (Tier 2)", reportsTo: "Elena Petrova" },
  { name: "Elena Petrova", role: "Senior Specialist", team: "Developer Support (Tier 2)", reportsTo: "Dana Fischer" },
  { name: "Jordan Kim", role: "Specialist", team: "Account & Security Team", reportsTo: "Aisha Rahman" },
  { name: "Aisha Rahman", role: "Senior Specialist", team: "Account & Security Team", reportsTo: "Dana Fischer" },
  { name: "Tom Becker", role: "Engineer", team: "Engineering - Product Team", reportsTo: "Nina Volkov" },
  { name: "Nina Volkov", role: "Engineering Manager", team: "Engineering - Product Team", reportsTo: "Dana Fischer" },
  { name: "Carlos Mendez", role: "On-Call Engineer", team: "Engineering - On-Call/SRE", reportsTo: "Nina Volkov" },
  { name: "Liam O'Brien", role: "Product Manager", team: "Product Team", reportsTo: "Dana Fischer" },
  { name: "Grace Chen", role: "Associate", team: "Tier 1 Support", reportsTo: "Sam Okafor" },
  { name: "Yusuf Demir", role: "Specialist", team: "Trust & Safety", reportsTo: "Aisha Rahman" },
];

export const MANAGER_NAMES = Array.from(new Set(ROSTER.map((r) => r.reportsTo))).sort();

export function reportsToFor(name: string): string {
  return ROSTER.find((r) => r.name === name)?.reportsTo ?? "";
}
