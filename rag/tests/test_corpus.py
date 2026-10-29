import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import rag.build_corpus as corpus_builder
from rag.build_corpus import (extract_blocks, extract_bioc_blocks, extract_jats_blocks,
                              extract_nci_glossary_blocks, chunks_for, validate_source)


ROOT = Path(__file__).resolve().parents[1] / 'data'


class CorpusTests(unittest.TestCase):
    def test_chunker_excludes_non_evidence_publication_disclosures(self):
        source = {'id': 'test-source', 'title': 'Test review', 'authors': 'A. Author',
                  'publisher': 'Test journal', 'url': 'https://example.org/review',
                  'license': 'CC BY 4.0', 'license_url': 'https://creativecommons.org/licenses/by/4.0/',
                  'scope': 'Test scope'}
        blocks = [
            ('h2', 'Conclusion'),
            ('p', 'The review summarizes lesion imaging and differential considerations.'),
            ('h2', 'Declaration of Generative AI and AI-assisted technologies in the writing process'),
            ('p', 'Authors used a language model for copyediting.'),
            ('h2', 'Funding statement'),
            ('p', 'This research received no external grant funding.'),
            ('h2', 'Declaration of Competing Interest'),
            ('p', 'The authors declare no competing interests.'),
        ]
        chunks = chunks_for(source, blocks, 'source-hash', '2026-01-01T00:00:00+00:00', '2025-01-01')
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]['section'], 'Conclusion')
        self.assertIn('differential considerations', chunks[0]['text'])
        self.assertNotIn('language model', chunks[0]['text'])
        self.assertNotIn('external grant funding', chunks[0]['text'])
        self.assertNotIn('competing interests', chunks[0]['text'])

    def test_nci_glossary_parser_extracts_only_the_matching_patient_definition(self):
        payload = {
            'termId': 723860, 'language': 'en', 'dictionary': 'Cancer.gov',
            'audience': 'Patient', 'termName': 'osteochondroma',
            'definition': {'html': '<p>A benign tumor with bone and cartilage.</p>',
                           'text': 'A benign tumor with bone and cartilage.'},
            'pronunciation': {'key': 'ignore pronunciation', 'audio': 'https://example.org/audio.mp3'}
        }
        blocks, term_id = extract_nci_glossary_blocks(json.dumps(payload).encode())
        self.assertEqual(term_id, 723860)
        self.assertEqual(blocks, [('h2', 'osteochondroma'),
                                  ('p', 'A benign tumor with bone and cartilage.')])

    def test_nci_glossary_parser_rejects_wrong_dictionary_audience_or_missing_definition(self):
        payload = {'termId': 723860, 'language': 'en', 'dictionary': 'Cancer.gov',
                   'audience': 'Patient', 'termName': 'osteochondroma',
                   'definition': {'text': 'A sufficiently clear dictionary definition.'}}
        with self.assertRaisesRegex(ValueError, 'metadata'):
            extract_nci_glossary_blocks(json.dumps({**payload, 'audience': 'Professional'}))
        with self.assertRaisesRegex(ValueError, 'metadata'):
            extract_nci_glossary_blocks(json.dumps({**payload, 'definition': {'text': ''}}))
        with self.assertRaisesRegex(ValueError, 'metadata'):
            extract_nci_glossary_blocks(json.dumps(payload), expected_term_id=723861)

    def test_nci_glossary_parser_rejects_malformed_json_shapes_cleanly(self):
        for invalid in ([], {'definition': None}, {'definition': []},
                        {'dictionary': None, 'definition': {'text': 'A valid-length definition.'}}):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(ValueError, 'metadata'):
                extract_nci_glossary_blocks(json.dumps(invalid))

    def test_bioc_parser_keeps_prose_and_omits_tables_figures_and_references(self):
        payload = [{"documents": [{"id": "PMC12345", "infons": {"license": "CC BY"}, "passages": [
            {"infons": {"type": "abstract", "license": "CC-BY 4.0"},
             "text": "An abstract about aneurysmal bone cyst diagnosis and imaging."},
            {"infons": {"type": "title_1"}, "text": "Diagnosis"},
            {"infons": {"type": "paragraph"}, "text": "Biopsy"},
            {"infons": {"type": "paragraph"},
             "text": "A biopsy examines tissue and should be planned by the specialist team."},
            {"infons": {"type": "fig_caption", "section_type": "FIG"}, "text": "Patient image caption."},
            {"infons": {"type": "table_title_caption", "section_type": "TABLE"}, "text": "Adapted table caption."},
            {"infons": {"type": "table", "section_type": "TABLE"}, "text": "Third-party table content."},
            {"infons": {"type": "ref", "section_type": "REF"}, "text": "Reference title."},
        ]}]}]
        blocks, pmcid = extract_bioc_blocks(json.dumps(payload).encode())
        self.assertEqual(pmcid, 'PMC12345')
        self.assertEqual(blocks[:4], [('h2', 'Abstract'),
                                      ('p', 'An abstract about aneurysmal bone cyst diagnosis and imaging.'),
                                      ('h2', 'Diagnosis'), ('h3', 'Biopsy')])
        self.assertIn(('p', 'A biopsy examines tissue and should be planned by the specialist team.'), blocks)
        self.assertNotIn(('p', 'Patient image caption.'), blocks)
        self.assertNotIn(('p', 'Adapted table caption.'), blocks)
        self.assertNotIn(('p', 'Third-party table content.'), blocks)
        self.assertNotIn(('p', 'Reference title.'), blocks)

    def test_bioc_parser_requires_explicit_cc_by_4_license_text(self):
        license_text = ('This article is licensed under a Creative Commons Attribution 4.0 '
                        'International License.')
        payload = [{'documents': [{'id': 'PMC12345', 'infons': {'license': 'CC BY'},
                                   'passages': [{'infons': {'type': 'paragraph', 'license': license_text},
                                                 'text': 'A sufficiently long article paragraph about bone sarcoma.'}]}]}]
        blocks, _ = extract_bioc_blocks(json.dumps(payload))
        self.assertIn(('p', 'A sufficiently long article paragraph about bone sarcoma.'), blocks)
        for restriction in ('NonCommercial', 'NoDerivatives', 'ShareAlike'):
            with self.subTest(restriction=restriction):
                payload[0]['documents'][0]['passages'][0]['infons']['license'] = (
                    f'Creative Commons Attribution-{restriction} 4.0 International License')
                with self.assertRaisesRegex(ValueError, 'registered CC BY license'):
                    extract_bioc_blocks(json.dumps(payload))
        payload[0]['documents'][0]['passages'][0]['infons']['license'] = 'Creative Commons Attribution'
        with self.assertRaisesRegex(ValueError, 'registered CC BY license'):
            extract_bioc_blocks(json.dumps(payload))

    def test_jats_parser_validates_identity_license_and_excludes_non_text_assets(self):
        xml = '''<article><front><article-meta>
          <article-id pub-id-type="pmcid">PMC12345</article-id>
          <article-id pub-id-type="doi">10.1000/example</article-id>
          <abstract><p>Review of knee bone tumours and MRI findings.</p></abstract>
          <permissions><license><license-p>This article is licensed under a Creative Commons Attribution 4.0 International License.</license-p></license></permissions>
        </article-meta></front><body><sec><title>Imaging</title>
          <p>MRI can describe lesion extent and anatomic location.</p>
          <fig><caption>Figure caption must not enter the text corpus.</caption></fig>
          <ref-list><ref>Reference text must not enter the text corpus.</ref></ref-list>
        </sec></body></article>'''
        blocks, pmcid, doi = extract_jats_blocks(xml)
        self.assertEqual((pmcid, doi), ('PMC12345', '10.1000/example'))
        self.assertIn(('p', 'MRI can describe lesion extent and anatomic location.'), blocks)
        self.assertNotIn(('p', 'Figure caption must not enter the text corpus.'), blocks)
        self.assertNotIn(('p', 'Reference text must not enter the text corpus.'), blocks)
        with self.assertRaisesRegex(ValueError, 'CC BY 4.0'):
            extract_jats_blocks(xml.replace('Attribution 4.0', 'Attribution'))
        for restriction in ('NonCommercial', 'NoDerivatives', 'ShareAlike'):
            with self.subTest(restriction=restriction):
                restricted_xml = xml.replace(
                    'Creative Commons Attribution 4.0 International License',
                    f'Creative Commons Attribution-{restriction} 4.0 International License')
                with self.assertRaisesRegex(ValueError, 'CC BY 4.0'):
                    extract_jats_blocks(restricted_xml)
        linked_by_license = xml.replace(
            '<license><license-p>This article is licensed under a Creative Commons Attribution 4.0 International License.</license-p></license>',
            '<license xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="https://creativecommons.org/licenses/by/4.0/">'
            '<license-p>Creative Commons Attribution License.</license-p></license>')
        self.assertEqual(extract_jats_blocks(linked_by_license)[1:], ('PMC12345', '10.1000/example'))
        restricted_linked = linked_by_license.replace(
            'Creative Commons Attribution License.',
            'Creative Commons Attribution-NonCommercial 4.0 License.')
        with self.assertRaisesRegex(ValueError, 'CC BY 4.0'):
            extract_jats_blocks(restricted_linked)
        nc_url_with_generic_text = xml.replace(
            '<license><license-p>This article is licensed under a Creative Commons Attribution 4.0 International License.</license-p></license>',
            '<license xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="https://creativecommons.org/licenses/by-nc/4.0/">'
            '<license-p>Creative Commons Attribution 4.0 International License</license-p></license>')
        with self.assertRaisesRegex(ValueError, 'CC BY 4.0'):
            extract_jats_blocks(nc_url_with_generic_text)
        url_in_license_text = xml.replace(
            'Creative Commons Attribution 4.0 International License',
            'https://creativecommons.org/licenses/by/4.0/ Creative Commons Attribution License')
        self.assertEqual(extract_jats_blocks(url_in_license_text)[1:], ('PMC12345', '10.1000/example'))

    def test_jats_parser_accepts_single_article_ncbiefetch_wrapper(self):
        article = '''<article><front><article-meta>
          <article-id pub-id-type="pmcid">PMC67890</article-id>
          <article-id pub-id-type="doi">10.1000/efetch</article-id>
          <permissions><license><license-p>Creative Commons Attribution 4.0 International License</license-p></license></permissions>
        </article-meta></front><body><sec><title>Case</title><p>Text from the article.</p></sec></body></article>'''
        blocks, pmcid, doi = extract_jats_blocks(f'<pmc-articleset>{article}</pmc-articleset>')
        self.assertEqual((pmcid, doi), ('PMC67890', '10.1000/efetch'))
        self.assertIn(('p', 'Text from the article.'), blocks)
        for wrapper in (
            '<pmc-articleset/>',
            f'<pmc-articleset>{article}{article}</pmc-articleset>',
        ):
            with self.subTest(article_count=wrapper.count('<article>')):
                with self.assertRaisesRegex(ValueError, 'exactly one JATS article'):
                    extract_jats_blocks(wrapper)

    def test_jats_source_requires_exact_europe_pmc_pmcid_endpoint(self):
        source = {'id': 'jats-test', 'title': 'Test', 'url': 'https://pmc.ncbi.nlm.nih.gov/articles/PMC12345/',
                  'download_url': 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12345/fullTextXML',
                  'format': 'jats_xml', 'pmcid': 'PMC12345', 'doi': '10.1000/example',
                  'license': 'CC BY 4.0', 'license_url': 'https://creativecommons.org/licenses/by/4.0/',
                  'scope': 'Narrow review scope'}
        validate_source(source)
        with self.assertRaisesRegex(ValueError, 'do not match'):
            validate_source({**source, 'download_url': source['download_url'].replace('PMC12345', 'PMC99999')})

    def test_short_symptom_list_items_are_preserved(self):
        source = {'id': 'test', 'title': 'Test', 'url': 'https://example.org', 'authors': 'Test'}
        blocks = extract_blocks('<main><h2>Symptoms</h2><ul><li>Pain</li><li>Swelling</li></ul></main>')
        chunks = chunks_for(source, blocks, 'hash', 'date', None)
        self.assertEqual(chunks[0]['text'], 'Pain\nSwelling')

    def test_reference_heading_h6_excluded_and_next_section_resumes(self):
        html = ('<main><h2>Diagnosis</h2><p>Biopsy checks tissue for cancer and supports diagnosis.</p>'
                '<h6>References</h6><ol><li>Author 2020. A bibliography entry should not be retrieved.</li></ol>'
                '<h2>Symptoms</h2><p>Persistent pain requires assessment by a trained clinician.</p></main>')
        source = {'id': 'test', 'title': 'Test', 'url': 'https://example.org', 'authors': 'Test'}
        chunks = chunks_for(source, extract_blocks(html), 'hash', 'date', None)
        self.assertEqual([c['section'] for c in chunks], ['Diagnosis', 'Symptoms'])
        self.assertNotIn('bibliography', ' '.join(c['text'] for c in chunks))

    def test_nested_blocks_and_table_cells_do_not_join_words(self):
        blocks = extract_blocks('<main><ul><li><p>First sentence.</p><p>Second sentence.</p></li></ul>'
                                '<table><tr><th>Test</th><td>Biopsy</td></tr></table></main>')
        self.assertEqual(blocks, [('li', 'First sentence. Second sentence.'), ('tr', 'Test Biopsy')])

    def test_metrics_section_is_not_added_to_retrieval_corpus(self):
        source = {'id': 'test', 'title': 'Article', 'url': 'https://example.org', 'authors': 'Test'}
        blocks = [('h1', 'Article'), ('h3', 'Metrics'), ('h3', 'downloads11,803'),
                  ('li', 'Last 6 Months11,803'),
                  ('h2', 'Abstract'), ('p', 'A sufficiently long abstract sentence about bone cyst research.')]
        chunks = chunks_for(source, blocks, 'hash', 'date', None)
        self.assertEqual([row['section'] for row in chunks], ['Abstract'])

    def test_data_availability_statement_is_not_added_to_retrieval_corpus(self):
        source = {'id': 'test', 'title': 'Article', 'url': 'https://example.org', 'authors': 'Test'}
        blocks = [('h2', 'Conclusion'),
                  ('p', 'Clinical review content should remain available to retrieval.'),
                  ('h2', 'Data Availability Statement'),
                  ('p', 'No datasets were generated or analysed during the current study.')]
        chunks = chunks_for(source, blocks, 'hash', 'date', None)
        self.assertEqual([row['section'] for row in chunks], ['Conclusion'])

    def test_parser_keeps_sections_and_discards_scripts(self):
        html = '<main><h1>Bone cancer</h1><p>Primary bone cancer begins in bone tissue.</p>' \
               '<script>alert("ignore")</script><h2>Diagnosis</h2>' \
               '<p>Biopsy examines a tissue sample.</p></main>'
        blocks = extract_blocks(html)
        self.assertEqual(blocks, [('h1', 'Bone cancer'),
                                  ('p', 'Primary bone cancer begins in bone tissue.'),
                                  ('h2', 'Diagnosis'), ('p', 'Biopsy examines a tissue sample.')])

    def test_corpus_provenance_and_evaluation_links(self):
        sources = json.loads((ROOT / 'sources.json').read_text(encoding='utf-8'))
        lock = json.loads((ROOT / 'source_lock.json').read_text(encoding='utf-8'))
        rows = [json.loads(line) for line in (ROOT / 'corpus.jsonl').read_text(encoding='utf-8').splitlines()]
        questions = json.loads((ROOT / 'evaluation_questions.json').read_text(encoding='utf-8'))
        self.assertGreaterEqual(len(sources), 10)
        self.assertEqual({s['id'] for s in sources}, {s['id'] for s in lock})
        self.assertEqual({s['id'] for s in sources}, {r['source_id'] for r in rows})
        self.assertEqual(len(rows), len({r['chunk_id'] for r in rows}))
        source_by_id = {source['id']: source for source in lock}
        for row in rows:
            self.assertEqual(row['text_sha256'], hashlib.sha256(row['text'].encode('utf-8')).hexdigest())
            self.assertTrue(row['section'])
            self.assertTrue(row['authors'])
            self.assertIn('source_date', row)
            self.assertEqual(row['license'], source_by_id[row['source_id']]['license'])
            self.assertEqual(row['license_url'], source_by_id[row['source_id']]['license_url'])
            self.assertEqual(row['scope'], source_by_id[row['source_id']].get('scope', ''))
        locations = {(row['source_id'], row['section']) for row in rows}
        for question in questions:
            if question['source_id']:
                self.assertIn((question['source_id'], question['section']), locations)
            else:
                self.assertIn(question['expected_behavior'], {'insufficient_evidence', 'out_of_scope'})

    def test_expanded_evaluation_has_real_evidence_and_disjoint_splits(self):
        dataset = json.loads((ROOT / 'evaluation_v2.json').read_text(encoding='utf-8'))
        self.assertEqual(dataset['corpus_sha256'], hashlib.sha256((ROOT / 'corpus.jsonl').read_bytes()).hexdigest())
        corpus = {row['text_sha256']: row for row in
                  (json.loads(line) for line in (ROOT / 'corpus.jsonl').read_text(encoding='utf-8').splitlines())}
        questions = dataset['questions']
        self.assertEqual(len(questions), len({q['id'] for q in questions}))
        self.assertEqual(len(questions), len({q['question_vi'] for q in questions}))
        self.assertEqual({q['split'] for q in questions}, {'dev', 'test'})
        for question in questions:
            for evidence in question['evidence']:
                row = corpus[evidence['text_sha256']]
                self.assertEqual(row['source_id'], evidence['source_id'])
                self.assertEqual(row['section'], evidence['section'])
                self.assertIn(question['evidence_quote'], row['text'])

    def test_external_sources_require_an_explicit_reuse_license(self):
        source = {'id': 'test', 'url': 'https://openorthopaedicsjournal.com/article',
                  'license': 'CC BY 4.0',
                  'license_url': 'https://creativecommons.org/licenses/by/4.0/', 'scope': 'Test scope'}
        with self.assertRaisesRegex(ValueError, 'explicitly declare CC BY 4.0'):
            validate_source({**source, 'license': 'CC BY-NC-ND 4.0'})
        source.update(url='https://example.com/article')
        with self.assertRaisesRegex(ValueError, 'host is not approved'):
            validate_source(source)

    def test_nci_sources_require_the_exact_explicit_reuse_declaration(self):
        source = {'id': 'nci-test', 'url': 'https://www.cancer.gov/types/bone/bone-fact-sheet',
                  'license': 'NCI text reuse policy; credit and link to source; no images',
                  'license_url': 'https://www.cancer.gov/policies/copyright-reuse'}
        validate_source(source)
        with self.assertRaisesRegex(ValueError, 'NCI reuse declaration'):
            validate_source({**source, 'license': 'Public domain'})
        with self.assertRaisesRegex(ValueError, 'NCI reuse declaration'):
            validate_source({key: value for key, value in source.items() if key != 'license'})

    def test_offline_build_still_validates_source_reuse_declaration(self):
        with tempfile.TemporaryDirectory(prefix='bonescope-offline-license-') as temp:
            root = Path(temp)
            data_dir, cache_dir = root / 'data', root / 'cache'
            data_dir.mkdir()
            cache_dir.mkdir()
            sources = []
            for index in range(10):
                source = {'id': f'nci-{index}', 'title': f'Test source {index}',
                          'url': f'https://www.cancer.gov/test/{index}',
                          'license': 'Public domain' if index == 0 else
                                     'NCI text reuse policy; credit and link to source; no images',
                          'license_url': 'https://www.cancer.gov/policies/copyright-reuse'}
                sources.append(source)
                (cache_dir / f"{source['id']}.html").write_text(
                    '<main><p>A valid cached source paragraph for this build test.</p></main>',
                    encoding='utf-8')
            (data_dir / 'sources.json').write_text(json.dumps(sources), encoding='utf-8')
            with patch.multiple(corpus_builder, DATA=data_dir, CACHE=cache_dir,
                                OUTPUT=data_dir / 'corpus.jsonl', LOCK=data_dir / 'source_lock.json'):
                with self.assertRaisesRegex(ValueError, 'NCI reuse declaration'):
                    corpus_builder.build(offline=True)

    def test_bioc_source_must_use_the_official_matching_pmcid_endpoint(self):
        source = {'id': 'bioc-test', 'title': 'Test',
                  'url': 'https://pmc.ncbi.nlm.nih.gov/articles/PMC12345/',
                  'download_url': 'https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_json/PMC12345/unicode',
                  'format': 'bioc_json', 'pmcid': 'PMC12345', 'license': 'CC BY 4.0',
                  'license_url': 'https://creativecommons.org/licenses/by/4.0/', 'scope': 'test'}
        validate_source(source)
        with self.assertRaisesRegex(ValueError, 'do not match'):
            validate_source({**source, 'download_url': source['download_url'].replace('PMC12345', 'PMC99999')})


if __name__ == '__main__':
    unittest.main()
