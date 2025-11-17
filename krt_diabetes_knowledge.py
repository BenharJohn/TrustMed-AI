"""
Curated top 10 questions/answers on type 2 diabetes.

The ``krt_focus`` notes the Key Risk Topic (KRT) emphasis the professor mentioned—
framing each Q/A around risk-informed reasoning (prevalence, pathophysiology,
prevention, management, complications, etc.).
"""

from __future__ import annotations

from typing import List, Dict


TOP_TYPE2_QA: List[Dict[str, str]] = [
    {
        "id": "1",
        "question": "How common is type 2 diabetes in the United States today?",
        "answer": (
            "More than 38 million Americans—about 1 in 10 people—live with diabetes, and roughly "
            "90% to 95% of them have type 2 diabetes. Most diagnoses still occur after age 45, yet the CDC "
            "notes that cases among children, teens, and young adults continue to rise. "
            "Source: CDC Type 2 Diabetes overview (updated May 15, 2024)."
        ),
        "krt_focus": "Epidemiology & national burden; frames urgency for any intervention.",
    },
    {
        "id": "2",
        "question": "What makes type 2 diabetes different from type 1 diabetes?",
        "answer": (
            "Type 2 diabetes develops when the body does not make enough insulin or cannot use insulin effectively, "
            "so glucose builds up in the bloodstream instead of entering cells for energy. Unlike type 1 diabetes—"
            "which is driven by autoimmune destruction of insulin-producing beta cells—type 2 diabetes usually begins "
            "with insulin resistance that worsens over time. Source: CDC Type 2 Diabetes overview & NIDDK Type 2 "
            "Diabetes fact sheet."
        ),
        "krt_focus": "Pathophysiology contrast; clarifies mechanism and treatment rationale.",
    },
    {
        "id": "3",
        "question": "What are the most common early symptoms people should watch for?",
        "answer": (
            "Early signs often include excessive thirst and urination, increased hunger, fatigue, blurred vision, "
            "slow-healing sores, unexplained weight loss, and tingling or numbness in the hands or feet. Symptoms can "
            "develop slowly over years and may be so mild that many people are asymptomatic until complications appear. "
            "Source: NIDDK Type 2 Diabetes fact sheet."
        ),
        "krt_focus": "Clinical recognition; equips screening and triage decisions.",
    },
    {
        "id": "4",
        "question": "Who is at higher risk of developing type 2 diabetes?",
        "answer": (
            "Risk climbs if you have prediabetes, live with overweight or obesity, are physically inactive, or are 45 "
            "or older. Having a parent or sibling with type 2 diabetes, a history of gestational diabetes or delivering "
            "a baby over 9 pounds, nonalcoholic fatty liver disease, or belonging to African American, Hispanic or Latino, "
            "American Indian, Alaska Native, some Pacific Islander, or some Asian American groups also raises risk. "
            "Source: CDC Type 2 Diabetes overview."
        ),
        "krt_focus": "Risk-stratification; highlights populations for screening (KRT).",
    },
    {
        "id": "5",
        "question": "How does insulin resistance lead to high blood sugar?",
        "answer": (
            "When cells stop responding to insulin, the pancreas releases extra insulin to compensate, but eventually it "
            "can no longer keep up. As a result, glucose remains in the bloodstream, progressing first to prediabetes and "
            "then to persistent hyperglycemia that defines type 2 diabetes. Source: CDC Type 2 Diabetes overview."
        ),
        "krt_focus": "Mechanistic risk transition—from resistance to frank T2D.",
    },
    {
        "id": "6",
        "question": "What lifestyle changes can prevent or delay type 2 diabetes?",
        "answer": (
            "Proven strategies include losing 5% to 7% of your starting weight if you have overweight, choosing smaller "
            "portions and fewer high-fat foods, staying hydrated with water instead of sugary drinks, and building up to "
            "at least 30 minutes of moderate physical activity (like brisk walking) on five days each week. Consistency "
            "with these changes produced long-term risk reduction in the NIH-sponsored Diabetes Prevention Program. "
            "Source: NIDDK Type 2 Diabetes fact sheet."
        ),
        "krt_focus": "Prevention & lifestyle (core KRT intervention lever).",
    },
    {
        "id": "7",
        "question": "How is type 2 diabetes diagnosed?",
        "answer": (
            "A health care professional confirms the diagnosis through blood tests such as fasting plasma glucose, A1C, "
            "or an oral glucose tolerance test, and repeat testing is used to verify abnormal results. Screening done at "
            "fairs or pharmacies should always be followed up at a clinic to ensure accuracy and linkage to care. "
            "Source: CDC Type 2 Diabetes overview & NIDDK Type 2 Diabetes fact sheet."
        ),
        "krt_focus": "Detection & laboratory criteria; ensures consistent case identification.",
    },
    {
        "id": "8",
        "question": "Once diagnosed, what daily habits help manage type 2 diabetes?",
        "answer": (
            "Management centers on tracking blood glucose as directed, following an individualized meal plan, maintaining "
            "regular physical activity, getting adequate sleep, and addressing stress with relaxation techniques or counseling. "
            "Keeping glucose, blood pressure, and cholesterol near target ranges—and avoiding tobacco—greatly lowers the risk "
            "of future complications. Source: CDC Type 2 Diabetes overview & NIDDK Type 2 Diabetes fact sheet."
        ),
        "krt_focus": "Self-management behaviors linking risk factors to outcomes.",
    },
    {
        "id": "9",
        "question": "What role do medicines play in type 2 diabetes care?",
        "answer": (
            "Many people start with lifestyle changes alone, but oral agents, GLP-1 receptor agonists, SGLT2 inhibitors, or "
            "other injectables are often added over time to keep glucose in range. Even people not using insulin may need "
            "temporary insulin during illnesses, hospital stays, or pregnancy, and additional prescriptions may target high "
            "blood pressure or cholesterol. Source: NIDDK Type 2 Diabetes fact sheet."
        ),
        "krt_focus": "Therapeutic intensification; ties risk control to pharmacology.",
    },
    {
        "id": "10",
        "question": "What complications can arise if type 2 diabetes is poorly controlled?",
        "answer": (
            "Persistently high glucose can injure blood vessels and nerves, which increases the risk for heart disease, "
            "stroke, chronic kidney disease, neuropathy, foot ulcers, eye disease, gum disease, bladder or sexual dysfunction, "
            "and even dementia or certain cancers. Many people with type 2 diabetes also develop nonalcoholic fatty liver "
            "disease, which improves when excess weight is lost. Source: NIDDK Type 2 Diabetes fact sheet."
        ),
        "krt_focus": "Complications & adverse outcomes—the ultimate KRT endpoints.",
    },
]


def format_top_qa_text() -> str:
    """Return the curated list as a text block ready for indexing."""
    return "\n\n".join(
        f"Q: {item['question']}\nA: {item['answer']}" for item in TOP_TYPE2_QA
    )


__all__ = ["TOP_TYPE2_QA", "format_top_qa_text"]
