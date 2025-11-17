"""
Contraindication Rule Engine
P0.1 CONTRA-CHECK: Policy engine for drug contraindications
"""

import re

# Drug aliases mapping (common medications and their variants)
DRUG_ALIASES = {
    'nsaids': ['nsaid', 'nsaids', 'ibuprofen', 'naproxen', 'diclofenac', 'indomethacin', 'ketorolac', 'advil', 'motrin', 'aleve'],
    'aspirin': ['aspirin', 'asa', 'acetylsalicylic acid'],
    'acetaminophen': ['acetaminophen', 'paracetamol', 'tylenol'],
    'warfarin': ['warfarin', 'coumadin'],
    'metformin': ['metformin', 'glucophage'],
    'ace inhibitors': ['ace inhibitor', 'lisinopril', 'enalapril', 'ramipril', 'captopril'],
    'beta blockers': ['beta blocker', 'metoprolol', 'atenolol', 'carvedilol', 'propranolol'],
    'statins': ['statin', 'atorvastatin', 'simvastatin', 'rosuvastatin', 'pravastatin'],
}

# Condition aliases mapping
CONDITION_ALIASES = {
    'heart failure': ['heart failure', 'hf', 'chf', 'congestive heart failure', 'cardiac failure'],
    'kidney disease': ['kidney disease', 'renal disease', 'ckd', 'chronic kidney disease', 'renal failure', 'kidney failure'],
    'liver disease': ['liver disease', 'hepatic disease', 'cirrhosis', 'liver failure', 'hepatic failure'],
    'peptic ulcer': ['peptic ulcer', 'gastric ulcer', 'stomach ulcer', 'duodenal ulcer', 'gi ulcer'],
    'asthma': ['asthma', 'reactive airway disease'],
    'diabetes': ['diabetes', 'dm', 'diabetes mellitus', 'diabetic'],
    'hypertension': ['hypertension', 'htn', 'high blood pressure', 'elevated blood pressure'],
}


def extract_drug_mentions(question):
    """
    Extract drug names from question text
    Returns list of lowercase drug aliases
    """
    question_lower = question.lower()
    found_drugs = []

    # Check each drug group
    for drug_group, aliases in DRUG_ALIASES.items():
        for alias in aliases:
            # Use word boundaries to avoid partial matches
            if re.search(r'\b' + re.escape(alias) + r'\b', question_lower):
                found_drugs.extend(aliases)
                break  # Found one alias, add all

    # Also extract any standalone medication-like words
    # (e.g., drug names not in our predefined list)
    med_patterns = [
        r'\b(\w+cin)\b',  # Words ending in 'cin' (e.g., penicillin)
        r'\b(\w+pril)\b',  # ACE inhibitors ending in 'pril'
        r'\b(\w+olol)\b',  # Beta blockers ending in 'olol'
        r'\b(\w+statin)\b',  # Statins
    ]

    for pattern in med_patterns:
        matches = re.findall(pattern, question_lower)
        found_drugs.extend(matches)

    return list(set(found_drugs))  # Deduplicate


def get_patient_conditions(n4j, gid):
    """
    Get patient conditions from the matched GID subgraph
    Returns list of lowercase condition aliases
    """
    disease_query = """
    MATCH (n)
    WHERE n.gid = $gid AND NOT n:Summary
    AND (n:Disease OR n:Condition OR 'Disease' IN labels(n))
    RETURN DISTINCT toLower(n.id) AS disease_name, toLower(n.name) AS alt_name
    """

    try:
        diseases = n4j.query(disease_query, {'gid': gid})
        condition_names = []

        for d in diseases:
            disease_name = d.get('alt_name') or d.get('disease_name', '')
            if disease_name:
                condition_names.append(disease_name)

                # Add aliases for this condition
                for condition_group, aliases in CONDITION_ALIASES.items():
                    if disease_name in aliases:
                        condition_names.extend(aliases)
                        break

        return list(set(condition_names))  # Deduplicate

    except Exception as e:
        print(f"[Warning] Could not retrieve patient conditions: {e}")
        return []


def check_contraindications(n4j, gid, question):
    """
    Check for contraindication rules before answer generation

    Args:
        n4j: Neo4jGraph instance
        gid: Graph ID of matched subgraph
        question: User's question

    Returns:
        dict with:
        - has_warnings: bool
        - rules: list of contraindication rules
        - drugs: list of drug names mentioned
        - conditions: list of patient conditions
    """

    print(f"\n[CONTRA-CHECK] Checking for contraindications...")

    # Extract drug mentions from question
    drug_aliases = extract_drug_mentions(question)
    print(f"[CONTRA-CHECK] Drugs mentioned: {drug_aliases[:5]}")

    # Get patient conditions from GID
    condition_aliases = get_patient_conditions(n4j, gid)
    print(f"[CONTRA-CHECK] Patient conditions: {condition_aliases[:5]}")

    # If no drugs mentioned, no need to check
    if not drug_aliases:
        print(f"[CONTRA-CHECK] No drugs mentioned in question - skipping")
        return {
            'has_warnings': False,
            'rules': [],
            'drugs': [],
            'conditions': condition_aliases
        }

    # Query contraindication rules from graph
    rule_query = """
    MATCH (d)-[r]->(c)
    WHERE (d:Drug OR d:Medication OR 'Medication' IN labels(d) OR 'Drug' IN labels(d))
      AND (c:Disease OR c:Condition OR 'Disease' IN labels(c) OR 'Condition' IN labels(c))
      AND type(r) IN ['CONTRAINDICATED_IN', 'WORSENS', 'INTERACTS_WITH']
      AND (toLower(d.id) IN $drug_aliases OR toLower(d.name) IN $drug_aliases)
      AND (toLower(c.id) IN $condition_aliases OR toLower(c.name) IN $condition_aliases)
    RETURN d.id AS drug, d.name AS drug_name,
           c.id AS condition, c.name AS condition_name,
           type(r) AS rule_type
    """

    try:
        rules = n4j.query(rule_query, {
            'drug_aliases': drug_aliases,
            'condition_aliases': condition_aliases
        })

        print(f"[CONTRA-CHECK] Found {len(rules)} contraindication rules")

        for rule in rules:
            drug = rule.get('drug_name') or rule.get('drug', 'Unknown')
            condition = rule.get('condition_name') or rule.get('condition', 'Unknown')
            rule_type = rule.get('rule_type', 'CONTRAINDICATED_IN')
            print(f"  - {drug} {rule_type} {condition}")

        return {
            'has_warnings': len(rules) > 0,
            'rules': rules,
            'drugs': drug_aliases,
            'conditions': condition_aliases
        }

    except Exception as e:
        print(f"[CONTRA-CHECK] Error querying contraindications: {e}")
        return {
            'has_warnings': False,
            'rules': [],
            'drugs': drug_aliases,
            'conditions': condition_aliases
        }


def format_contraindication_rules(rules):
    """
    Format contraindication rules for injection into context
    """
    if not rules:
        return ""

    formatted = []
    for rule in rules:
        drug = rule.get('drug_name') or rule.get('drug', 'Unknown')
        condition = rule.get('condition_name') or rule.get('condition', 'Unknown')
        rule_type = rule.get('rule_type', 'CONTRAINDICATED_IN')

        # Convert rule type to readable format
        rule_text = rule_type.replace('_', ' ').lower()

        formatted.append(f"  WARNING: {drug.upper()} is {rule_text} {condition.upper()}")

    return "\n".join(formatted)
