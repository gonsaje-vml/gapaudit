"""Readiness reports preserve evidence boundaries, counts and useful page/block views."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import shutil
import re

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/pdf-gap-audit/scripts/build_readiness_pdf.py'


def load_builder():
    assert SCRIPT.is_file(), 'Readiness renderer is not implemented'
    spec = importlib.util.spec_from_file_location('readiness_builder', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture(root):
    common = {'visualStatus':'Unverified', 'functionalStatus':'Partial', 'readiness':'Unverified'}
    components = []
    for cid, family, variants, usage in [('B01','hero-carousel',['hero-carousel'],{'P1':1}), ('B02','faq',['faq','faq compact'],{'P2':2})]:
        assessments = [{'variant':v, 'usage':{'P1':1} if cid=='B01' else {'P2':1}, **common, 'note':'Synthetic fixture; sampled behavior only.'} for v in variants]
        components.append({'id':cid,'family':family,'variants':variants,'usage':usage,**common,
            'expected':'Source behavior for this synthetic fixture.', 'retained':['Text is retained.'],
            'visualGaps':['Complete visual review remains open.'], 'functionalGaps':['Not every state was tested.'],
            'remainingWork':['Complete the required comparison.'], 'acceptance':['Verify the stated states and viewports.'],
            'evidence':['Synthetic fixture observation'], 'limitations':['Only a sampled state was reviewed.'],
            'variantAssessments':assessments})
    pages=[]
    for pid,name in [('P1','Home'),('P2','Product')]:
        rows=[{'family':c['family'],'variant':v['variant'],'count':v['usage'][pid],**common,'note':v['note']} for c in components for v in c['variantAssessments'] if pid in v['usage']]
        pages.append({'id':pid,'name':name,'route':'/' if pid=='P1' else '/product',
            'sourceUrl':'https://source.example/'+name.lower(),'targetUrl':'https://preview.example/'+name.lower(),
            **common,'retained':['Synthetic retained content.'],'gaps':['Synthetic untested state.'],
            'components':rows,'screenshotPairs':[],'qualityNotes':['Not a real website audit.']})
    record=root/'checks.json';record.write_text('{"synthetic":true,"outcome":"Unverified"}\n')
    return {'schemaVersion':2,'meta':{'title':'Synthetic readiness audit','date':'2026-11-05','baseline':'Production parity',
        'method':'Synthetic test fixture; no website tests.','sourceEvidenceSha256':'a'*64,
        'summary':['Synthetic report verifies the output contract.'],'limitations':['Not a real site assessment.']},
        'pages':pages,'components':components,'sharedComponents':[],
        'capabilities':[{'id':'K01','name':'Synthetic capability','pageIds':['P2'],'status':'Unverified','retained':'Text.', 'missing':'Untested control.','action':'Test it.','evidence':['Synthetic fixture']}],
        'qualityAreas':[{'name':'Accessibility','outcome':'Unverified','observations':['Not performed.'],'remainingWork':['Review it.'],'evidence':['Synthetic fixture']}],
        'workItems':[{'id':'W01','title':'Complete fixture checks','status':'Unverified','priority':'To triage','componentIds':['B01','B02'], 'pageIds':['P1','P2'],'action':'Test the open states.','doneWhen':'Evidence covers required states.','owner':'TBD','evidence':['Synthetic fixture']}],
        'records':[{'path':'checks.json','label':'Original check record'}]}


class ReadinessPDFTests(unittest.TestCase):
    def test_scope_wide_readiness_precedes_optional_comparison(self):
        from PIL import Image
        from pypdf import PdfReader
        import pdfplumber
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);data=fixture(root)
            panels={}
            for side,color in [('source','#203c58'),('target','#d7a641')]:
                path=root/(side+'.png');Image.new('RGB',(600,240),color).save(path)
                panels[side]={'path':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                    'url':'https://'+side+'.example/','viewport':'1440x900','state':'Synthetic matched state',
                    'capturedAt':'2026-11-05T12:00:00Z'}
            data['pages'][0]['screenshotPairs']=[{'title':'Fixture comparison','caption':'Synthetic matched evidence, not a real audit.',**panels}]
            data['meta'].update({'openingVisual':{'pageId':'P1','pairIndex':0,'title':'Representative comparison','takeaway':'A bounded sample; the scope-wide verdict remains separate.'},
                'reportRevisionDate':'2026-11-06','summaryChartStyle':'isometric'})
            path=root/'readiness.json';path.write_text(json.dumps(data));pdf=root/'report.pdf'
            load_builder().build(path,pdf)
            first=PdfReader(pdf).pages[0]
            self.assertEqual(len(first.images),2,'Selected comparison must be on the first physical page')
            self.assertIn('Representative comparison',first.extract_text())
            self.assertIn('2026-11-06',first.extract_text())
            with pdfplumber.open(pdf) as document:
                page=document.pages[0]
                chart_title=page.search('Component readiness')[0]
                self.assertLess(chart_title['top'],min(im['top'] for im in page.images),'Readiness must lead; a screenshot is supporting evidence')

    def test_opening_chart_and_table_share_body_family_counts(self):
        from pypdf import PdfReader
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);data=fixture(root)
            data['components'][0]['readiness']='Substantial work'
            shared=deepcopy(data['components'][0]);shared.update({'id':'S01','family':'header','variants':['header'],'usage':{'P1':1,'P2':1}})
            shared['variantAssessments']=[{'variant':'header','usage':{'P1':1,'P2':1},'visualStatus':'Unverified','functionalStatus':'Partial','readiness':'Substantial work','note':'Synthetic shared record; separate from body.'}]
            data['sharedComponents']=[shared]
            path=root/'readiness.json';path.write_text(json.dumps(data));pdf=root/'report.pdf'
            result=load_builder().build(path,pdf)
            self.assertIn('openingSummary',result,'Record the chart/table denominator and exact source counts')
            summary=result['openingSummary']
            self.assertEqual(summary['unit'],'block types')
            self.assertEqual(summary['counts'],{'Ready':0,'Minor work':0,'Substantial work':1,'Capability missing':0,'Unverified':1})
            self.assertEqual(summary['total'],2)
            self.assertTrue(summary['chartRendered'])
            text=PdfReader(pdf).pages[0].extract_text()
            for label,count in summary['counts'].items():self.assertRegex(text,re.escape(label)+r'\s+'+str(count))
            self.assertEqual(summary['style'],'flat')

    def test_unrecorded_body_inventory_is_not_an_empty_completion_chart(self):
        from pypdf import PdfReader
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);data=fixture(root);data['components']=[]
            for page in data['pages']:page['components']=[]
            for task in data['workItems']:task['componentIds']=[]
            path=root/'readiness.json';path.write_text(json.dumps(data));pdf=root/'report.pdf'
            result=load_builder().build(path,pdf)
            self.assertIn('openingSummary',result)
            self.assertEqual(result['openingSummary']['total'],0)
            self.assertFalse(result['openingSummary']['chartRendered'])
            self.assertIn('Block-type inventory unrecorded',PdfReader(pdf).pages[0].extract_text())

    def test_page_chart_counts_uses_and_preserves_page_exceptions(self):
        from pypdf import PdfReader
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);data=fixture(root)
            data['pages'][1]['components'][0]['readiness']='Capability missing'
            path=root/'readiness.json';path.write_text(json.dumps(data));pdf=root/'report.pdf'
            result=load_builder().build(path,pdf)
            self.assertIn('pageReadiness',result['openingSummary'])
            rows=result['openingSummary']['pageReadiness']
            self.assertEqual([r['total'] for r in rows],[1,2])
            self.assertEqual(rows[1]['counts']['Capability missing'],1)
            self.assertEqual(rows[1]['counts']['Unverified'],1)
            self.assertEqual(result['openingSummary']['counts']['Unverified'],2,'Two types are distinct from three uses and a page exception')
            self.assertIn('Block uses by page',PdfReader(pdf).pages[0].extract_text())

    def test_report_terms_do_not_rename_actual_block_identifiers(self):
        from pypdf import PdfReader
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);data=fixture(root);c=data['components'][0]
            c['family']='family-banner';c['variants']=['family-banner'];c['variantAssessments'][0]['variant']='family-banner'
            data['pages'][0]['components'][0].update({'family':'family-banner','variant':'family-banner'})
            data['meta']['summary']=['This family has one instance.']
            path=root/'readiness.json';path.write_text(json.dumps(data));pdf=root/'report.pdf'
            load_builder().build(path,pdf);reader=PdfReader(pdf)
            first=reader.pages[0].extract_text()
            self.assertIn('This block type has one use.',first)
            self.assertIn('Block types',first)
            self.assertNotIn('Actual body families',first)
            self.assertIn('family-banner','\n'.join(p.extract_text() or '' for p in reader.pages))

    def test_opening_comparison_reference_and_chart_style_are_validated(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);builder=load_builder();data=fixture(root)
            for ref in [
                {'pageId':'invented','pairIndex':0,'title':'Title','takeaway':'Scope'},
                {'pageId':'P1','pairIndex':0,'title':'Title','takeaway':'No capture exists'},
                {'pageId':'P1','pairIndex':-1,'title':'Title','takeaway':'Invalid index'},
                {'pageId':'P1','pairIndex':True,'title':'Title','takeaway':'Boolean is not an index'},
            ]:
                bad=deepcopy(data);bad['meta']['openingVisual']=ref
                with self.assertRaisesRegex(ValueError,'openingVisual'):builder.validate_assessment(bad,root)
            bad=deepcopy(data);bad['meta']['summaryChartStyle']='invented'
            with self.assertRaisesRegex(ValueError,'summaryChartStyle'):builder.validate_assessment(bad,root)

    def test_reconciles_page_family_variant_and_instance_counts(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); data=fixture(root); builder=load_builder()
            result=builder.validate_assessment(data,root)
            self.assertEqual(result,{'pages':2,'bodyFamilies':2,'exactVariants':3,'bodyInstances':3,'sharedFamilies':0})
            invalid=deepcopy(data);invalid['components'][1]['usage']['P2']=3
            with self.assertRaisesRegex(ValueError,'usage|count|reconcile'):
                builder.validate_assessment(invalid,root)

    def test_ready_cannot_hide_missing_states_quality_or_visual_review(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);builder=load_builder();data=fixture(root)
            data['components'][0].update({'readiness':'Ready','visualStatus':'Close','functionalStatus':'Complete',
                'requiredStates':['keyboard selection','autoplay'],'verifiedStates':['keyboard selection'],
                'requiredViewports':['desktop','mobile'],'verifiedViewports':['desktop'],'qualityComplete':False})
            with self.assertRaisesRegex(ValueError,'Ready|Complete|required'):
                builder.validate_assessment(data,root)

    def test_rejects_unknown_variants_negative_counts_and_capture_changes(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);builder=load_builder();data=fixture(root)
            bad=deepcopy(data);bad['pages'][1]['components'][0]['variant']='invented'
            with self.assertRaises(ValueError):builder.validate_assessment(bad,root)
            bad=deepcopy(data);bad['pages'][0]['components'][0]['count']=-1
            with self.assertRaises(ValueError):builder.validate_assessment(bad,root)
            Image.new('RGB',(600,400),'white').save(root/'source.png')
            panel={'path':'source.png','sha256':'wrong','url':'https://source.example/','viewport':'1440x900','state':'Synthetic fixture','capturedAt':'2026-11-05T00:00:00Z'}
            bad=deepcopy(data);bad['pages'][0]['screenshotPairs']=[{'title':'Fixture','caption':'Synthetic.', 'source':panel,'target':panel}]
            with self.assertRaisesRegex(ValueError,'hash'):builder.validate_assessment(bad,root)

    def test_ready_family_cannot_average_away_unverified_variants(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);builder=load_builder();data=fixture(root)
            data['components'][1].update({'readiness':'Ready','visualStatus':'Close','functionalStatus':'Complete',
                'requiredStates':['open','close'],'verifiedStates':['open','close'],
                'requiredViewports':['desktop','mobile'],'verifiedViewports':['desktop','mobile'],
                'qualityComplete':True,'limitations':[], 'functionalGaps':[], 'visualGaps':[], 'remainingWork':[]})
            with self.assertRaisesRegex(ValueError,'variant|Ready|Complete'):
                builder.validate_assessment(data,root)

    def test_report_is_readiness_first_contains_all_variants_and_embeds_exact_records(self):
        from pypdf import PdfReader
        import zipfile
        from io import BytesIO
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);builder=load_builder();data=fixture(root);path=root/'readiness.json';path.write_text(json.dumps(data))
            first=builder.build(path,root/'first.pdf');second=builder.build(path,root/'second.pdf')
            self.assertEqual((root/'first.pdf').read_bytes(),(root/'second.pdf').read_bytes())
            r=PdfReader(root/'first.pdf');text='\n'.join(p.extract_text() or '' for p in r.pages)
            for value in ['Page breakdown','Block usage by page','Exact authored variants','hero-carousel','faq compact','Visual','Functional','Remaining work','Final work board','Unverified']:
                self.assertIn(value,text)
            self.assertIn('Synthetic report verifies the output contract.',r.pages[0].extract_text())
            self.assertTrue(r.outline)
            with zipfile.ZipFile(BytesIO(r.attachments['audit-records.zip'][0])) as archive:
                self.assertEqual(archive.read('checks.json'),(root/'checks.json').read_bytes())
                self.assertEqual(json.loads(archive.read('readiness.json')),data)
            self.assertEqual(first['counts']['bodyInstances'],3)
            self.assertEqual(first['pdfSha256'],second['pdfSha256'])

    def test_assessment_aware_verification_rejects_stale_source_records(self):
        from pypdf import PdfReader
        spec=importlib.util.spec_from_file_location('readiness_verify',ROOT/'skills/pdf-gap-audit/scripts/verify_pdf.py')
        verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)
        self.assertTrue(hasattr(verifier,'verify_readiness'),'Assessment-aware PDF verification is not implemented')
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);data=fixture(root);path=root/'readiness.json';path.write_text(json.dumps(data));pdf=root/'report.pdf'
            load_builder().build(path,pdf)
            result=verifier.verify_readiness(PdfReader(pdf),path,pdf)
            self.assertEqual(result['bodyInstances'],3)
            (root/'checks.json').write_text('{"altered":true}')
            with self.assertRaisesRegex(ValueError,'record|hash|source'):
                verifier.verify_readiness(PdfReader(pdf),path,pdf)

    def test_relative_packet_relocation_preserves_pdf_bytes_and_source_verification(self):
        from pypdf import PdfReader
        spec=importlib.util.spec_from_file_location('relocated_verify',ROOT/'skills/pdf-gap-audit/scripts/verify_pdf.py')
        verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)
        with tempfile.TemporaryDirectory() as temp:
            first=Path(temp)/'first';second=Path(temp)/'moved';first.mkdir()
            data=fixture(first);(first/'readiness.json').write_text(json.dumps(data))
            shutil.copytree(first,second)
            builder=load_builder();builder.build(first/'readiness.json',first/'report.pdf');builder.build(second/'readiness.json',second/'report.pdf')
            self.assertEqual((first/'report.pdf').read_bytes(),(second/'report.pdf').read_bytes())
            counts=verifier.verify_readiness(PdfReader(second/'report.pdf'),second/'readiness.json',second/'report.pdf')
            self.assertEqual(counts['bodyInstances'],3)

    def test_frequency_matrices_show_readiness_and_preserve_variant_exceptions(self):
        from pypdf import PdfReader
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);data=fixture(root)
            changed={'visualStatus':'Far off','functionalStatus':'Missing','readiness':'Capability missing'}
            data['components'][1]['variantAssessments'][0].update(changed)
            data['pages'][1]['components'][0].update(changed)
            assessment=root/'readiness.json';assessment.write_text(json.dumps(data));pdf=root/'report.pdf';load_builder().build(assessment,pdf)
            family='';exact=''
            for page in PdfReader(pdf).pages:
                text=page.extract_text() or ''
                if 'FREQUENCY / ORIGINAL AUTHORED HTML' in text:
                    if 'Exact authored variants' in text:exact+=text
                    else:family+=text
            self.assertIn('Visual',family);self.assertIn('Function',family);self.assertIn('Readiness',family)
            self.assertRegex(exact,r'faq\s+-\s+1\s+1\s+Far off\s+Missing\s+Capability missing')
            self.assertRegex(family,r'faq\s+-\s+2\s+2\s+Unverified\s+Partial\s+Unverified')


if __name__=='__main__':unittest.main()
