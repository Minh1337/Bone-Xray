"""Conservative query routing for retrieval. Not a complete chatbot safety layer."""

import re

try:
    from rag.lexical import contains, fold
except ModuleNotFoundError:
    from lexical import contains, fold


def _has_unverified_claim(value):
    """Detect questions that embed a claim the corpus cannot verify.

    Patterns include alternative-medicine cures, home-testing guarantees,
    supplement healing, pricing requests and device-replaces-doctor claims.
    Returns a reason string or None.
    """
    # Alternative medicine / supplement cure claims
    alt_treatments = (
        'nuoc ep', 'thao duoc', 'thuc pham chuc nang', 'curcumin', 'nghe',
        'acupuncture', 'hyperbaric oxygen', 'herbal', 'supplement',
        'homeopathy', 'essential oil', 'detox', 'cu den',
    )
    cure_verbs = (
        'chua khoi', 'ngan', 'tai phat', 'prevent', 'cure', 'eradicate',
        'eliminate', 'heal', 'treat', 'replace',
    )
    if any(contains(value, term) for term in alt_treatments) and any(contains(value, term) for term in cure_verbs):
        return 'unverified_alternative_medicine_claim'

    # Home testing / device guarantees
    guarantee_terms = ('bao dam', 'dam bao', 'guarantee', 'chac chan', 'chinh xac',
                       'accurately', 'reliable')
    home_device_terms = ('tai nha', 'at home', 'home dna', 'dna kit', 'thiet bi deo tay',
                         'smartphone', 'wearable', 'app')
    if any(contains(value, term) for term in home_device_terms) and any(contains(value, term) for term in guarantee_terms):
        return 'unverified_home_device_claim'
    # Home/device replacing a medical professional
    if any(contains(value, term) for term in home_device_terms) and any(contains(value, term) for term in ('phat hien som', 'early diagnosis', 'replace', 'thay the')):
        return 'unverified_home_device_claim'

    # Cost / pricing requests (not in any NCI source)
    cost_terms = ('gia bao nhieu', 'phi', 'gia tien', 'cost', 'price', 'pricing', 'fee',
                  'hom nay', 'today', 'bao nhieu tien', 'goi xet nghiem')
    location_market = ('benh vien dia phuong', 'local clinic', 'local hospital', 'nha thuoc',
                       'pharmacy', 'ban goi')
    if any(contains(value, term) for term in cost_terms) and any(contains(value, term) for term in location_market):
        return 'pricing_not_in_corpus'

    # "device/app can replace pathologist" pattern
    device_terms = ('smartphone', 'app', 'ung dung', 'thiet bi', 'may tinh', 'ai tool', 'software')
    replace_terms = ('replace', 'thay the', 'instead of', 'khong can')
    medical_role = ('pathologist', 'bac si', 'giai phau benh', 'doctor', 'specialist')
    if any(contains(value, term) for term in device_terms) and \
       any(contains(value, term) for term in replace_terms) and \
       any(contains(value, term) for term in medical_role):
        return 'unverified_device_replaces_clinician'

    return None


def assess(question, config):
    value = fold(question)
    if not value:
        return 'out_of_scope', 'empty_question'
    if len(question) > 2000:
        return 'out_of_scope', 'question_too_long'
    injections = ('ignore previous instructions', 'ignore all instructions', 'system prompt',
                  'bo qua cac huong dan', 'bo qua moi huong dan', 'bo qua huong dan', 'tiet lo prompt')
    if any(contains(value, phrase) for phrase in injections):
        return 'out_of_scope', 'instruction_override'
    if re.search(r'lieu (?:bao nhieu|luong)|\b(?:dosage|mg kg|mg m2)\b|what dose|dose (?:for|should)', value):
        return 'out_of_scope', 'individual_treatment_or_dose'
    personal = any(contains(value, phrase) for phrase in ('toi', 'benh nhan nay', 'con toi', 'for me', 'my child', 'this patient'))
    treatment = any(contains(value, phrase) for phrase in ('ke don', 'phac do', 'dung thuoc', 'chon thuoc', 'prescribe', 'chemotherapy regimen'))
    if personal and treatment:
        return 'out_of_scope', 'individual_treatment_or_dose'
    image_terms = ('softmax', 'diem mo hinh', 'model score', 'x quang', 'x ray', 'xray')
    certainty = ('ket luan', 'chan doan chac chan', 'khong can sinh thiet', 'confirm', 'definitely', 'diagnose me')
    if any(contains(value, term) for term in image_terms) and any(contains(value, term) for term in certainty):
        return 'insufficient_evidence', 'image_score_is_not_diagnostic_evidence'
    # Detect unverified claims before checking supported terms, so questions
    # that mention a supported disease but embed a baseless claim are routed
    # to insufficient_evidence instead of reaching the retriever.
    claim_reason = _has_unverified_claim(value)
    if claim_reason:
        return 'insufficient_evidence', claim_reason
    if any(contains(value, term) for term in config['unsupported_terms']):
        return 'insufficient_evidence', 'corpus_coverage_gap'
    if not any(contains(value, term) for term in config['supported_terms']):
        return 'out_of_scope', 'outside_bone_tumor_corpus'
    return None, None
