# SupplyLine — 3-Minute Demo Script
Semis @ GSB Hackathon | Stanford GSB | May 2026

---

## THE HOOK (20 seconds)
"Nokia just closed a $6.65B acquisition of Infinera. Right now their engineers 
are sitting down to design the next generation of optical line cards — picking 
components, choosing foundries, locking in vendors. Those decisions will govern 
their supply chain for the next 5 to 7 years. And they're making them with zero 
supply chain visibility. By the time procurement tries to source these parts, 
they'll discover 52-week lead times, single-source dependencies on InP fabs 
that three companies in the world can make. SupplyLine fixes that. At design 
time, not procurement time."

---

## STEP 1 — UPLOAD THE BOM (30 seconds)
Action: Click "Try sample BOM" → select photonics_bom.csv → click "Demo Mode"

Say: "I'm going to upload a realistic BOM for an optical line card — the kind 
Nokia or Ciena would be designing right now. 15 components: coherent transceivers, 
InP photonic ICs, merchant silicon ASICs, power and timing. Let's run it."

Wait for analysis to complete (~3 seconds in demo mode).

---

## STEP 2 — THE DASHBOARD (30 seconds)
Action: Point to the summary metrics at the top.

Say: "Out of 15 parts, 9 are flagged RED. That's not a bad BOM — that's a 
normal photonics BOM. The industry runs on single-sourced InP chips, 
Taiwan-fab ASICs, and coherent transceivers where Coherent is allocating 
60% of capacity to hyperscalers. The engineer who designed this had no idea. 
Now they do, before tape-out."

---

## STEP 3 — DRILL INTO THE WORST PART (45 seconds)
Action: Click on "OP-27635" (the Coherent InP PIC — worst risk score).

Say: "This is the InP photonic integrated circuit — the modulator at the heart 
of the coherent transceiver. Let's look at what we're dealing with."

Point to the data fields:
- "Stock: 8 units. Lead time: 60 weeks. Single source — only Coherent makes 
  this exact part globally."
- "Geo risk: HIGH — InP wafer fabrication has only 3 fabs in the world."
- "And the price has spiked 15% above baseline."

Action: Scroll to Substitution Options.

Say: "SupplyLine doesn't just tell you there's a problem — it tells you what 
to do. Here are three alternatives: EFFECT Photonics as a drop-in InP PIC, 
Lumentum's coherent receiver as a minor rework, and a silicon photonics 
migration path if the team wants to redesign for long-term resilience. It 
tells you compatibility grade, qualification timeline, and why each one 
addresses this specific risk."

---

## STEP 4 — SHOW THE FILTER (15 seconds)
Action: Use the "Filter by risk level" dropdown → select RED.

Say: "A procurement manager can immediately filter to just the critical parts. 
No spreadsheet. No manually calling Avnet. No 2-week wait for a sourcing 
recommendation."

---

## STEP 5 — DOWNLOAD (15 seconds)
Action: Click "Annotated BOM (Excel)" download.

Say: "The engineer gets their original BOM back, color-coded, with risk flags 
and substitute recommendations built in. They send this to procurement. 
Procurement sends it to leadership. The whole organization has the same picture 
in minutes."

---

## THE CLOSE (25 seconds)
"Avnet and Arrow earn 11 to 13 percent gross margin on a $100 billion 
distribution market. About 5 points of that is pure information rent — 
the fee for knowing what's in stock and what's available. AI destroys that 
information asymmetry. Arrow's revenue fell 20% in 2024 — the disruption 
has already started. SupplyLine captures 2 points on transactions that 
currently cost OEMs 11. Nokia wins. Coherent wins. We win. And Avnet's 
margins compress — the same way department store margins compressed when 
Zara owned the intelligence loop."

---

## BACKUP ANSWERS FOR JUDGES

Q: How is this different from SiliconExpert?
A: "SiliconExpert is owned by Arrow — fundamental conflict of interest. 
It's also a 2005 tool with no AI, no AVL awareness, and no design-time 
integration. It tells you a part is EOL after you've already taped out."

Q: Why photonics specifically?
A: "Photonics is the highest-risk segment in semiconductor supply chains. 
InP fab concentration is extreme — three fabs globally. Coherent transceivers 
are being preferentially allocated to hyperscalers. The lead times are the 
longest in the industry. If SupplyLine works here, it works everywhere."

Q: What's the business model?
A: "Phase 1: $50–200K/year SaaS per OEM for the design co-pilot. 
Phase 2: 1.5–2.5% commission on procurement routed directly OEM-to-manufacturer. 
The photonics transceiver market alone is $10–15B/year. 2% of that is 
$200–300M revenue — no inventory, pure orchestration."

Q: Who's the first customer?
A: "Nokia/Infinera. They just closed a $6.65B merger and are merging two 
completely different BOMs and AVLs right now. Maximum supply chain chaos, 
maximum willingness to pay."
