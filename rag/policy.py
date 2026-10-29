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
        'acupuncture', 'hyperbaric oxygen', 'herbal', 'herb', 'herbs', 'supplement',
        'homeopathy', 'essential oil', 'detox', 'cu den',
    )
    cure_verbs = (
        'chua khoi', 'ngan', 'tai phat', 'prevent', 'cure', 'cures', 'eradicate',
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


def _requests_personal_image_interpretation(question):
    """Catch case-specific image requests without carrying cues across sentences."""
    image = r'(?:x\s*ray|xray|radiograph(?:y)?|mri|ct|scan|image|picture|photo|film|anh|hinh|phim)'
    personal = (r'(?:this|these|that|my|our|her|his|their|my patient|patient of mine|patient s|'
                r'attached|uploaded|provided|above|here|nay|cua toi|cua con toi|con toi|'
                r'cua benh nhan|benh nhan nay|nguoi benh nay|benh nhan cua toi|ca benh nay|'
                r'toi gui|vua gui|dinh kem)')
    case_specific = (r'(?:my patient|our patient|patient s|patient of mine|'
                     r'patient i m seeing|patient i am seeing|patient i m treating|'
                     r'patient i am treating|patient i follow|patient i am following|'
                     r'patient i manage|patient i am managing|patient under my care|'
                     r'patient i saw|patient i reviewed|patient i examined|patient i assessed|patient i treated|'
                     r'patient i treat|patient sent me|patient has sent me|patient submitted|patient uploaded|'
                     r'i reviewed|i read|i interpreted|patient i am reviewing|'
                     r'patient i consult(?:ed)?(?: on)?|patient in my clinic|'
                     r'patient in our clinic|patient from my clinic|patient from our clinic|'
                     r'patient from my hospital|patient from our hospital|patient from our service|'
                     r'patient i care for|child i care for|child under my care|my child|child s|'
                     r'my case|case i treat|case i manage|case i am treating|case i am managing|'
                     r'case i follow|case i am following|case under my care|'
                     r'case from my clinic|case from our clinic|'
                     r'someone i care for|someone under my care|'
                     r'someone who is currently under my care|someone i am treating|'
                     r'someone i am following|person i am treating|person i am following|'
                     r'person under my care|person in my care|patient from my clinic|'
                     r'benh nhan nay|nguoi benh nay|'
                     r'one of my patients|one of our patients|'
                     r'ca benh cua toi|benh nhan gui toi|benh nhan gui minh|'
                     r'ca benh toi dang theo doi|'
                     r'ca benh toi dang dieu tri|ca benh toi dang kham|ca benh toi phu trach|'
                     r'ca toi dang theo doi|ca toi dang dieu tri|ca toi dang kham|ca toi phu trach|'
                     r'benh nhan toi gui|benh nhan ma toi dang dieu tri|benh nhan ma toi dang kham|'
                     r'benh nhan toi dang theo doi|benh nhan toi dang dieu tri|benh nhan toi dang kham|'
                     r'nguoi benh toi dang theo doi|nguoi benh toi dang dieu tri|nguoi benh toi dang kham)')
    interpretation = (r'\b(?:what|show|diagnos\w*|interpret\w*|read|review|assess|examin\w*|analy\w*|identif\w*|classif\w*|'
                      r'suggest\w*|indicat\w*|reveal\w*|finding\w*|lesion|tumou?r|cancer|benign\w*|malignan\w*|'
                      r'look\w*|appear\w*|comment\w*|opinion|concerning|normal|abnormal|abnormalit\w*|help|ung thu(?: xuong)?|ac tinh|'
                      r'dau hieu|ton thuong|tell|describe|chan doan|doc|xem|nhan xet|mo ta|goi y|u gi|benh gi|noi gi|cho thay|co gi|ket qua|'
                      r'co phai|co ve|trong nhu|lanh hay ac|dang lo|lo ngai|bat thuong|nguy hiem)\b')
    image_outcome_followup = (
        r'\b(?:what does (?:it|this|that|the (?:image|scan|mri|ct|x ray|radiograph)) show|'
        r'what is shown|what is it|show\w*|diagnos\w*|interpret\w*|read|review|assess|'
        r'abnormalit\w*|lesion|tumou?r|cancer|finding\w*|opinion|describe|'
        r'cho thay|nhan xet|doc|mo ta|ket qua|co gi|noi gi)\b')
    # Preserve sentence boundaries before folding; a case reference in one
    # sentence must not turn a separate general-education question into a
    # personal-image request. Keep semicolon-linked clauses together because
    # the second clause may ask for an opinion about the image in the first.
    segments = re.split(r'[.!?\n]+', question)
    for index, segment in enumerate(segments):
        value = fold(segment)
        if not value:
            continue
        personal_image = re.search(rf'\b{personal}\b(?:\s+\w+){{0,3}}\s+\b{image}\b', value) or \
                         re.search(rf'\b{image}\b(?:\s+\w+){{0,3}}\s+\b{personal}\b', value)
        # Explicit case ownership may be farther from the modality in the
        # same sentence ("radiograph of the lesion in a patient of mine").
        personal_case_image = re.search(
            rf'\b{case_specific}\b(?:\s+\w+){{0,8}}\s+\b{image}\b', value) or \
            re.search(rf'\b{image}\b(?:\s+\w+){{0,8}}\s+\b{case_specific}\b', value)
        published_case_reference = re.search(
            r'\b(?:published|reported)\b.{0,40}\bcase report\b|\bin (?:the )?case report\b|\bpublished article\b',
            value)
        explicit_personal_reference = re.search(
            r'\b(?:my|our|attached|uploaded|provided|this|these|that|my patient|patient i)\b', value)
        if published_case_reference and not explicit_personal_reference and re.search(r'\bpatient s\b', value):
            personal_case_image = False
            personal_image = False
        if (personal_image or personal_case_image) and re.search(interpretation, value):
            return True
        acquired_clinical_image = re.search(
            r'\b(?:this|that|the)(?:\s+(?:image|scan|picture|photo|film|x\s*ray|radiograph|mri|ct))?\b'
            r'.{0,50}\b(?:taken|obtained|acquired|captured)\b.{0,30}\b(?:from|at)\s+(?:my|our)\s+'
            r'(?:clinic|hospital|service)\b', value)
        if acquired_clinical_image and re.search(interpretation, value):
            return True
        if (index + 1 < len(segments)
                and (personal_image or personal_case_image or acquired_clinical_image)
                and re.search(interpretation, fold(segments[index + 1]))
                and not re.search(r'\b(?:in general|generally|published|review articles?)\b',
                                  fold(segments[index + 1]))):
            return True
        if (index + 1 < len(segments) and re.search(case_specific, value)
                and re.search(rf'\b{image}\b', fold(segments[index + 1]))
                and re.search(image_outcome_followup, fold(segments[index + 1]))
                and not re.search(r'\b(?:in general|generally|published|review articles?|typically|typical|common|usually)\b',
                                  fold(segments[index + 1]))):
            return True
    return False


def _requests_dataset_label_mapping(value):
    """Do not infer a dataset's operational class definition from keyword overlap."""
    dataset_reference = re.search(r'\b(?:btxrd|dataset|data set|data-set)\b', value)
    mapping_request = any(contains(value, term) for term in (
        'dong nghia', 'tuong duong', 'anh xa', 'mapping', 'equivalent', 'same as',
        'same', 'mean', 'define', 'definition', 'criteria', 'class', 'label', 'nhan',
        'tieu chi', 'dinh nghia',
    ))
    return bool(dataset_reference and mapping_request)


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
    image_interpretation = (
        'what does this x ray show', 'does this x ray show', 'interpret this x ray',
        'read this x ray', 'can you diagnose from this x ray',
        'what does this radiograph show', 'what is shown on this radiograph',
        'interpret this radiograph', 'read this radiograph',
        'can you diagnose from this radiograph', 'does this radiograph show',
        'what does this attached image show', 'what does this image show',
        'what is shown in this image', 'diagnose this image',
        'interpret this image', 'read this scan', 'does this image show',
        'phim x quang nay la u gi', 'doc phim x quang nay',
        'anh x quang nay co phai ung thu', 'chan doan tu phim x quang nay',
        'x quang nay cho thay gi', 'x quang nay la u gi',
        'x quang nay cho thay u gi', 'phim nay goi y gi',
        'phim nay goi y benh gi', 'nhan xet phim nay', 'doc phim nay',
        'anh nay la u gi', 'hinh nay la u gi', 'hinh anh nay cho thay gi',
        'doc anh nay', 'nhan xet anh nay', 'chan doan tu anh nay',
        'tu anh nay co the chan doan', 'chan doan tu hinh anh nay',
        'anh nay co phai u xuong',
    )
    if any(contains(value, phrase) for phrase in image_interpretation):
        return 'insufficient_evidence', 'image_requires_specialist_assessment'
    if _requests_personal_image_interpretation(question):
        return 'insufficient_evidence', 'image_requires_specialist_assessment'
    if _requests_dataset_label_mapping(value):
        return 'insufficient_evidence', 'unverified_dataset_label_mapping'
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
    if re.search(r'\bgct\b', value) and any(contains(value, term) for term in
                                             ('pituitary', 'pineal', 'intracranial', 'germ cell')):
        return 'out_of_scope', 'outside_bone_tumor_corpus'
    # GCT is ambiguous without a bone-imaging context, so do not add it as a
    # globally supported term. Evaluate it only after safety/scope guards.
    if re.search(r'\bgct\b', value) and any(contains(value, term) for term in
                                             ('bone', 'bone tumor', 'bone lesion', 'mri', 'ct', 'radiograph', 'x ray', 'xray')):
        return None, None
    if not any(contains(value, term) for term in config['supported_terms']):
        return 'out_of_scope', 'outside_bone_tumor_corpus'
    return None, None
