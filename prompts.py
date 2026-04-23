PAGE_EXTRACTION_PROMPT = """You are an expert document reader. Extract ALL text content from this health insurance policy document page.

Instructions:
- Extract every piece of text visible on the page, preserving the structure
- Include headings, subheadings, bullet points, table data, footnotes, and fine print
- For tables, preserve the row/column structure using markdown table format
- Do not summarize or paraphrase — extract the text exactly as it appears
- If the page is blank or contains only images/logos with no meaningful text, respond with "NO_TEXT_CONTENT"
- Maintain the logical reading order of the document"""

STRUCTURED_EXTRACTION_PROMPT = """You are a health insurance policy analyst. Extract the following metrics from this health insurance policy document.

For each metric, provide:
- "value": the actual value/detail from the policy
- "benchmark": one of "good", "moderate", or "bad" based on the benchmark criteria below

Return a JSON object with these exact keys. If a metric is not found in the document, set it to null.

Metrics and benchmarks:

1. "claim_settlement_ratio" — CSR percentage. Good: >95%, Moderate: 90-95%, Bad: <90%
2. "incurred_claim_ratio" — ICR percentage. Good: 70-90%, Moderate: 60-70%, Bad: <60%
3. "cashless_hospital_network" — Number of network hospitals. Good: 10,000+, Moderate: 5,000-10,000, Bad: <5,000
4. "sum_insured" — Coverage amount. Good: high coverage, Moderate: moderate, Bad: low coverage
5. "restoration_benefit" — Restoration policy. Good: Unlimited, Moderate: Once a year, Bad: No restoration
6. "cumulative_bonus" — No Claim Bonus per year. Good: 50-100%/yr, Moderate: 20-50%/yr, Bad: <20%/yr
7. "max_ncb_limit" — Maximum NCB cap. Good: 300-500%, Moderate: 200%, Bad: <=100%
8. "room_rent_limit" — Room rent restrictions. Good: No cap, Moderate: 2% of SI, Bad: 1% of SI or fixed
9. "co_payment" — Co-payment percentage. Good: 0%, Moderate: 0-20%, Bad: >20%
10. "disease_sub_limits" — Sub-limit caps. Good: No cap/only ambulance/dental, Moderate: 2-4 caps, Bad: >4 caps
11. "pre_existing_disease_waiting" — Waiting period. Good: <=2 years, Moderate: 2-3 years, Bad: 3+ years
12. "specific_disease_waiting" — Waiting period. Good: <=2 years, Moderate: 2-3 years, Bad: 3+ years
13. "pre_hospitalisation" — Coverage period before. Good: 60-90 days, Moderate: 30 days, Bad: <30 days
14. "post_hospitalisation" — Coverage period after. Good: 90-180 days, Moderate: 60-90 days, Bad: <60 days
15. "day_care_procedures" — Number covered. Good: 500+, Moderate: 200-500, Bad: <200
16. "modern_treatments" — Coverage level. Good: Fully covered, Moderate: Capped, Bad: Not covered
17. "consumables_coverage" — Whether consumables are covered. Provide value as description.
18. "organ_donor_cover" — Whether organ donor expenses are covered. Provide value as description.
19. "ambulance_cover" — Ambulance coverage details. Provide value as description.
20. "ayush_treatment" — AYUSH treatment coverage. Provide value as description.
21. "opd_benefits" — OPD coverage details. Provide value as description.
22. "preventive_health_checkups" — Preventive checkup benefits. Provide value as description.
23. "teleconsultation" — Teleconsultation benefits. Provide value as description.
24. "wellness_rewards" — Wellness/reward programs. Provide value as description.
25. "maternity_benefits" — Maternity coverage details. Provide value as description.
26. "home_healthcare" — Home healthcare coverage. Provide value as description.

Document content:
{document_content}"""

POLICY_SCORE_PROMPT = """You are a health insurance policy grading expert. Based on the structured metrics extracted from the user's policy, provide a comprehensive policy score and grade.

Each metric has a "value" (the actual policy detail) and a "benchmark" rating of "good", "moderate", or "bad".

Scoring rules:
- good = 3 points, moderate = 2 points, bad = 1 point
- Only count metrics that have a benchmark rating (skip nulls and metrics without benchmarks)
- Overall score = (total points / max possible points) * 100
- Grade: A (>=85), B (>=70), C (>=55), D (>=40), F (<40)

Your response MUST include:
1. **Overall Score**: X/100 with letter grade
2. **Strengths**: List the "good" rated metrics with their values
3. **Areas of Concern**: List the "bad" rated metrics with their values and why they matter
4. **Improvements**: List the "moderate" rated metrics that could be better
5. **Summary**: A 2-3 sentence overall assessment of the policy quality

Be specific — reference actual values from the metrics, not generic advice.

Structured metrics:
{structured_content}"""

GENERAL_INSURANCE_FAQ = {
    "claim_rejected": {
        "keywords": ["claim rejected", "claim denial", "claim refused", "why was my claim rejected"],
        "answer": "Claim rejections usually come down to a handful of reasons — the treatment might fall under a waiting period that hasn't completed yet, it could be listed as an exclusion in your policy, or there may be a documentation gap. Sometimes it's simply a mismatch between what was billed and what was pre-authorised. The rejection letter itself usually mentions a reason code — that's your best starting point to understand exactly what happened.",
    },
    "cashless_denied": {
        "keywords": ["cashless denied", "cashless request denied", "cashless rejected", "cashless request was denied"],
        "answer": "First, don't panic — a cashless denial doesn't mean your claim is rejected entirely. Ask the hospital's insurance desk for the denial reason in writing. Go ahead and pay the bills, collect every document (discharge summary, all bills, investigation reports, prescriptions), and file for reimbursement once you're discharged. Cashless denials often happen due to documentation delays or pre-authorisation issues, and the same claim gets settled smoothly through reimbursement.",
    },
    "claim_partially_paid": {
        "keywords": ["partially paid", "claim deducted", "why did they deduct", "claim only partially"],
        "answer": "Partial claim settlements happen when the insurer applies policy sub-limits, room rent capping, co-payment clauses, or excludes certain items (like non-medical consumables). If your room category exceeded the policy limit, proportionate deductions are applied across the entire bill — not just the room rent. Check your settlement letter for the breakup of what was deducted and why.",
    },
    "reimbursement_claim": {
        "keywords": ["reimbursement claim", "file a reimbursement", "documents do I need", "how do I file"],
        "answer": "The general process is: notify your insurer within 24–48 hours of hospitalisation (or as soon as possible), collect all original documents at discharge — discharge summary, hospital bills, pharmacy receipts, investigation reports, and doctor's prescriptions — and submit the claim form along with these within the deadline mentioned in your policy (usually 15–30 days post discharge). Keep photocopies of everything you submit.",
    },
    "claim_settlement_time": {
        "keywords": ["settle my claim", "how long", "claim settlement time", "insurer delay", "if they delay"],
        "answer": "IRDAI regulations require insurers to settle claims within 30 days of receiving all documents. If they need an investigation, it can extend to 45 days, but they must inform you. If your claim goes beyond this without a resolution or communication, you can formally escalate through the insurer's grievance team, and if unresolved within 30 days, approach the Insurance Ombudsman.",
    },
    "appeal_rejected_claim": {
        "keywords": ["appeal a rejected claim", "appeal rejected", "challenge claim rejection"],
        "answer": "Yes, you absolutely can. Start by raising a formal grievance with your insurer's grievance redressal team — they're required to respond within 15 days. If you're not satisfied, you can approach the Insurance Ombudsman (free of charge, covers disputes up to ₹50 lakhs). As a last resort, consumer forums and civil courts are also options available to you.",
    },
    "pre_existing_condition": {
        "keywords": ["pre-existing condition", "pre existing", "diabetes", "hypertension", "thyroid", "pre-existing disease"],
        "answer": "Most health insurance policies do cover pre-existing conditions, but only after a waiting period — typically 2 to 4 years depending on the insurer and plan. Once that waiting period is served, your pre-existing condition is covered just like any other illness. The key is that the condition must have been declared at the time of buying the policy. If it was declared and accepted, you're on track — just check when your waiting period ends.",
    },
    "exclusions": {
        "keywords": ["not covered", "exclusions", "common exclusions", "what is excluded"],
        "answer": "While specific exclusions vary by policy, most health insurance plans commonly exclude: cosmetic or aesthetic treatments, self-inflicted injuries, war or nuclear-related conditions, experimental treatments, dental and vision care (unless caused by an accident), and illnesses arising from substance abuse. There's also typically an initial 30-day waiting period where no claims are payable except for accidents.",
    },
    "network_hospitals": {
        "keywords": ["any hospital", "network hospital", "only network"],
        "answer": "Most health insurance policies work in two ways — cashless treatment at network hospitals, where the insurer settles directly with the hospital, and reimbursement at non-network hospitals, where you pay first and claim later. So you're not strictly limited to network hospitals, but cashless is more convenient and requires less paperwork on your end.",
    },
    "mental_health": {
        "keywords": ["mental health", "psychiatric treatment", "psychiatric", "depression", "anxiety"],
        "answer": "Yes — as per the Mental Healthcare Act 2017, all health insurers in India are required to cover mental health conditions on par with physical illnesses. So conditions like depression, anxiety disorders, and psychiatric hospitalisation should be covered under your policy. The extent of coverage and any applicable waiting periods may vary, so it's worth checking the specific benefit in your schedule.",
    },
    "waiting_period_portability": {
        "keywords": ["switch insurers", "lose the waiting period", "portability", "waiting period carry"],
        "answer": "No, you don't lose it. IRDAI's portability guidelines protect your continuity benefits when you switch insurers. The waiting period credit you've built up — for pre-existing conditions and time-bound exclusions — carries over to your new policy. The key is to apply for portability before your renewal date and not let the policy lapse.",
    },
    "how_much_cover": {
        "keywords": ["how much health cover", "how much cover do I need", "adequate cover"],
        "answer": "A general rule of thumb is to have coverage of at least ₹5–10 lakhs as a baseline, with a super top-up on top if budget is a concern. Factors like your city (metro healthcare costs are higher), age, family size, and any existing conditions all play a role. If you have an employer cover, factor that in too — but don't rely on it entirely since it doesn't stay with you if you change jobs.",
    },
    "cover_enough_metro": {
        "keywords": ["5L", "10L", "cover enough", "family of 3", "metro"],
        "answer": "For a metro city, ₹5 lakhs can feel tight for a family — a single hospitalisation at a private hospital can run ₹2–4 lakhs easily. ₹10 lakhs is more comfortable but still vulnerable to a serious illness or surgery. A practical approach many people take is a base plan of ₹5–10 lakhs combined with a super top-up for higher coverage at a lower premium.",
    },
    "ncb": {
        "keywords": ["no claim bonus", "NCB", "lose it if I make a claim"],
        "answer": "NCB is a reward for not making claims — each claim-free year typically increases your sum insured by 10–50% (or reduces your premium, depending on the plan). If you make a claim, the accumulated bonus may reduce or reset, depending on your insurer's policy. Some plans now offer NCB protection as an add-on, which lets you make one claim without losing the bonus.",
    },
    "premium_increase": {
        "keywords": ["premium increase", "premium increased", "premium so much", "renewal premium"],
        "answer": "Premium increases at renewal are common and usually driven by a combination of factors — your age moving into a higher bracket, general medical inflation, your claims history, and sometimes industry-wide rate revisions approved by IRDAI. It's not always personal; a lot of it is actuarial. Comparing with other insurers at renewal is a good idea — portability means you can switch without losing your benefits.",
    },
    "co_payment": {
        "keywords": ["co-payment", "copayment", "co payment", "pay out of pocket"],
        "answer": "Co-payment means you share a fixed percentage of every claim with the insurer — for example, a 10% co-pay on a ₹1 lakh claim means you pay ₹10,000 and the insurer pays ₹90,000. Not all policies have co-pay — many premium plans don't. Policies for senior citizens or those bought at older ages more commonly carry a co-pay clause. It's worth checking your policy schedule to know if this applies to you.",
    },
    "super_top_up": {
        "keywords": ["super top-up", "super topup", "top up", "upgrading my base plan"],
        "answer": "A super top-up kicks in after your total claims in a year cross a threshold (called the deductible) — it's designed to cover large, less frequent expenses at a much lower premium than upgrading your base plan. Upgrading your base plan raises your coverage from the first rupee but costs significantly more. Super top-ups work best when you already have a base plan and want higher coverage without a big premium jump.",
    },
    "employer_insurance": {
        "keywords": ["employer health insurance", "employer insurance enough", "personal policy", "employer cover"],
        "answer": "Employer insurance is a great starting benefit but has real gaps — it typically ends when you leave the job, may not cover your full family, and the sum insured is often on the lower side. Having a personal policy running alongside it gives you continuity (waiting periods keep building), flexibility, and a safety net if you're between jobs. It's generally a good idea to have at least a basic personal policy running independently.",
    },
    "senior_citizen_parents": {
        "keywords": ["senior citizens", "parents", "family floater", "separate policy for parents"],
        "answer": "Most family floaters allow parents to be included, but it often makes more sense to get them a separate senior citizen policy. When parents are on a floater, their higher health risk drives up the premium for everyone, and if they make a claim, it affects the shared pool. A dedicated senior citizen plan is usually better structured for their needs and keeps your family floater premium more manageable.",
    },
    "maternity": {
        "keywords": ["maternity", "having a baby", "newborn care", "pregnancy"],
        "answer": "Maternity coverage is available in many comprehensive health plans, but it almost always comes with a waiting period of 2–4 years before you can claim it. If your policy includes maternity benefits, it typically covers delivery expenses (normal and caesarean) and newborn care up to a specified limit for the first 90 days. Check your schedule of benefits for the specific waiting period and coverage limits applicable to your plan.",
    },
    "policy_lapsed": {
        "keywords": ["policy lapsed", "lapsed policy", "waiting periods and NCB", "policy lapse"],
        "answer": "If your policy lapses — meaning the renewal wasn't done before the grace period (usually 30 days) — you typically lose all continuity benefits. That means your waiting periods restart from scratch and your NCB resets to zero on the new policy. Most insurers give a 30-day grace period after the due date; if you renew within that window, your benefits are preserved. Beyond that, it's treated as a fresh policy.",
    },
    "legal_rights": {
        "keywords": ["legal rights", "wrongly rejecting", "insurer wrongly", "claim dispute"],
        "answer": "You have clear recourse. First, submit a formal written grievance to your insurer — they're required to respond within 15 days. If unresolved within 30 days, you can approach the Insurance Ombudsman in your region, which is a free and relatively fast process covering disputes up to ₹50 lakhs. You can also file a complaint with IRDAI's consumer portal (Bima Bharosa) or approach a consumer forum for compensation beyond just the claim amount.",
    },
    "mis_sold": {
        "keywords": ["mis-sold", "missold", "mis sold", "wrong policy sold"],
        "answer": "A few signs to watch for: you were promised coverage that isn't in your policy document, the agent glossed over waiting periods or exclusions, the premium doesn't match what you were quoted, or you were sold a plan that clearly doesn't fit your needs. IRDAI has a free look period of 15–30 days from policy receipt — within that window, you can return the policy for a full refund if you feel it wasn't what you agreed to.",
    },
    "buying_channel": {
        "keywords": ["buy from a bank", "agent", "aggregator", "directly from the insurer", "affect my claim"],
        "answer": "The channel you buy from doesn't affect your claim — once the policy is issued, it's between you and the insurer regardless of who sold it. Where the channel matters is in the buying experience: aggregators let you compare across insurers easily, agents can help with paperwork and claims support, and buying directly can sometimes offer slightly better pricing. The more important factor is choosing the right insurer and plan, not the channel.",
    },
}

QA_SYSTEM_PROMPT = """You are a helpful health insurance policy assistant. Answer the user's question using the provided document content first. Only fall back to the General Insurance FAQ if the document has absolutely no relevant information.

Rules:
- ALWAYS prioritise the user's policy document content over the General Insurance FAQ
- Scan the ENTIRE document carefully — answers may appear in tables, schedules, annexures, or fine print, not just in plain paragraphs
- If the document mentions the topic AT ALL (even a single relevant keyword, table row, or value like "Waived", "Covered", "Not Applicable", a rupee amount, or a percentage), you MUST answer from the document and cite the page numbers. Do NOT fall back to the FAQ in this case
- Only use the General Insurance FAQ if, after scanning every page, the document contains absolutely NO mention of the topic
- If NEITHER the document NOR the FAQ contains the answer, say so clearly
- When answering from the document, be specific to the user's policy — reference actual values, limits, and conditions stated in the document
- When answering from the FAQ, you may adapt the language slightly but keep the substance intact
- Be concise but thorough
- If the document is still being processed, mention that partial information is available
- At the very end of your answer, on a new line, output the page numbers you referenced in this exact format: SOURCE_PAGES: [1, 3, 5]
- Only include pages that actually contributed to your answer. If you answered from the FAQ or no pages were relevant, output: SOURCE_PAGES: []

Document content:
{context}

---

General Insurance FAQ (use ONLY if the document above has no relevant information):
{faq_context}"""


CLASSIFICATION_PROMPT = """You are an insurance document classifier. Classify the following document into exactly one of these five types.

Types and distinguishing markers:

1. "retail_policy" — an individual/family health insurance POLICY SCHEDULE. Names one or more specific insured persons, lists sum insured, premium breakdown, policy number, period of insurance. Addressed to the policyholder.

2. "policy_wording" — the insurer's generic TERMS AND CONDITIONS document. Dense legal/clinical definitions, long exclusion lists, waiting period clauses, claim procedures. No personal data about any specific policyholder; describes the product in the abstract.

3. "brochure" — a marketing/sales collateral document. Pitch-shaped, uses promotional language, lists plan options/variants, eligibility bands, discounts, and optional covers. No personal data. Often has phrases like "Why choose us", "Key benefits", "Plan variants".

4. "group_policy" — a CORPORATE / EMPLOYER-SPONSORED policy document. Names an employer/company as the policyholder, defines who counts as employee / spouse / dependent children / parents, references corporate floater, termination of employment, and typically has blanket co-payment clauses.

5. "rejection_letter" — a claim denial letter addressed to a claimant. References a specific CLAIM NUMBER, states a rejection reason, cites a policy clause, often mentions the rejected amount and an appeals/grievance process.

Return JSON only with this exact shape:
{{"type": "retail_policy" | "policy_wording" | "brochure" | "group_policy" | "rejection_letter", "confidence": <number between 0.0 and 1.0>, "reasoning": "<one sentence explaining the markers you saw>"}}

Document content (first few pages):
{document_content}"""


POLICY_WORDING_EXTRACTION_PROMPT = """You are a health insurance policy wording analyst. Read the policy wording document below and populate the following JSON schema EXACTLY.

Rules:
- Preserve the schema's exact key structure. Do not add or rename keys. For fields not found in the document, leave the value as null.
- Every boolean in "add_ons_active" must be set to true ONLY if there is explicit evidence in the document that the add-on is included / active. Ambiguous or silent = false.
- "exclusions.claim_reducers.*" booleans must be true ONLY when the reducer is contractually enforced in this document (e.g. a room-rent proportionate deduction clause is stated). Do not infer from market convention.
- Waiting periods should be captured in MONTHS when the document expresses them in years (convert 2 years → 24).
- Return JSON only. No prose, no code fences.

Target schema:
{schema}

Document content:
{document_content}"""


BROCHURE_EXTRACTION_PROMPT = """You are a health insurance brochure analyst. Read the brochure below and populate the following JSON schema EXACTLY.

Rules:
- Preserve the schema's exact key structure. For fields not present in the brochure, leave the value as null.
- "coverage.sum_insured_options" should be a list of the sum-insured tiers offered (as stated).
- "eligibility.cover_type" captures individual / family floater / both.
- For "moneyback" and "loyalty_boost", "trigger" is the condition the brochure states unlocks the benefit, in the brochure's own words (short phrase).
- Return JSON only. No prose, no code fences.

Target schema:
{schema}

Document content:
{document_content}"""


GROUP_POLICY_EXTRACTION_PROMPT = """You are a corporate/group health insurance policy analyst. Read the group policy document below and populate the following JSON schema EXACTLY.

Rules:
- Preserve the schema's exact key structure. For fields not found, leave the value as null.
- "family_definition.*" — capture exactly who the policy lists as eligible family members. lgbtq_members / gender_reassignment_surgery / hormonal_therapy are booleans set only if the document explicitly includes them.
- "copayment.*_pct" values are percentages as numbers (10 not "10%"). If a different copay applies to specified illnesses or modern treatments, fill those fields separately.
- "critical_flags" is the MOST IMPORTANT block. For each flag, set it to true ONLY if the document's terms match the described gotcha:
    * coverage_ends_on_termination: policy cover terminates when the employee leaves the employer
    * no_portability_to_personal_retail_on_exit: exiting employee cannot port this cover to a personal retail plan carrying their waiting-period credits
    * copay_10pct_all_claims_real_oop: a blanket co-pay of ≥10% applies to all claims (not just one sub-category)
    * modern_treatments_50pct_copay_significant_exposure: modern / advanced treatments (robotic, stem cell, oral chemo, etc.) carry a co-pay of 50% or more
    * corporate_floater_not_for_maternity: the corporate floater sum insured cannot be drawn against maternity claims
    * parents_one_set_only: only one set of parents is allowed (not both own + in-laws)
    * ayush_govt_hospital_only: AYUSH treatment is payable only in government/accredited hospitals
    * reimbursement_intimation_within_24hrs_of_admission: claim intimation required within 24 hours of admission under threat of partial/total denial
- Return JSON only. No prose, no code fences.

Target schema:
{schema}

Document content:
{document_content}"""


REJECTION_LETTER_EXTRACTION_PROMPT = """You are a claim rejection letter analyst. Read the rejection letter below and populate the following JSON schema EXACTLY.

Rules:
- Preserve the schema's exact key structure. For fields not present in the letter, leave the value as null.
- "rejection_details.clause_cited" should be the specific policy clause text or identifier the insurer points to (e.g. "Section 3(c) - Pre-existing Disease waiting period").
- "rejection_details.amount_rejected" should include the amount with currency symbol if the letter provides one (e.g. "INR 1,25,000").
- "appeal_flags":
    * is_appeal_possible: true unless the letter explicitly closes the matter with no further recourse.
    * anomaly_flag: true if the rejection cites procedural or documentary reasons that could be rectified (missing doc, intimation delay) rather than substantive policy exclusion.
    * deadline_flag: true if the letter mentions a time-bound window for appeal/grievance.
    * cross_doc_flag: true if the rejection references another document (earlier letter, policy schedule, pre-auth form) that the claimant would need to cross-reference.
    * appeal_strength: one of "strong", "moderate", "weak", "none". Use "strong" for clear procedural anomalies or obviously misapplied exclusions; "moderate" for ambiguous cases; "weak" for clean substantive denials; "none" for truly final / non-appealable matters.
- "escalation_path.*" fields — populate with whatever contact details the letter provides; leave null if not mentioned.
- Return JSON only. No prose, no code fences.

Target schema:
{schema}

Document content:
{document_content}"""
