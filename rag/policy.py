"""Conservative query routing for retrieval. Not a complete chatbot safety layer."""

import re

try:
    from rag.lexical import contains, fold
except ModuleNotFoundError:
    from lexical import contains, fold


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
    if any(contains(value, term) for term in config['unsupported_terms']):
        return 'insufficient_evidence', 'corpus_coverage_gap'
    if not any(contains(value, term) for term in config['supported_terms']):
        return 'out_of_scope', 'outside_bone_tumor_corpus'
    return None, None
