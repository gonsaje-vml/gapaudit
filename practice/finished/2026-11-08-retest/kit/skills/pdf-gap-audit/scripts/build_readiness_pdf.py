#!/usr/bin/env python3
"""Validate and render the page/component readiness contract; preserve original records."""
import argparse
from collections import Counter, defaultdict
from functools import partial
import hashlib
from html import escape
from io import BytesIO
import importlib.metadata
import json
import math
from pathlib import Path
import re
import sys
import zipfile

from PIL import Image as PILImage
from pypdf import PdfReader, PdfWriter
import reportlab
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image, KeepTogether, Flowable

VERSION = '1.4.0'
VISUAL = {'Close', 'Partial', 'Far off', 'Unverified'}
FUNCTIONAL = {'Complete', 'Partial', 'Missing', 'Unverified', 'Not applicable'}
READINESS = {'Ready', 'Minor work', 'Substantial work', 'Capability missing', 'Unverified'}
OUTCOMES = {'Pass', 'Fail', 'Unverified', 'Not applicable'}
W = 524
NAVY = colors.HexColor('#102a43'); INK = colors.HexColor('#263746')
TEAL = colors.HexColor('#0F766E'); GRAY = colors.HexColor('#617487')
PALE = colors.HexColor('#eef4f7'); LINE = colors.HexColor('#d9e2ea')
READINESS_ORDER = ('Ready','Minor work','Substantial work','Capability missing','Unverified')
READINESS_COLORS = dict(zip(READINESS_ORDER,map(colors.HexColor,('#237568','#77a69b','#d7a348','#c36254','#778da2'))))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def nonempty(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(field + ' must be a nonempty string')


def strings(value, field):
    if not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value):
        raise ValueError(field + ' must be a string array')


def path_at(root, value):
    path = Path(value)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def statuses(record, label):
    for field, allowed in [('visualStatus', VISUAL), ('functionalStatus', FUNCTIONAL), ('readiness', READINESS)]:
        if record.get(field) not in allowed:
            raise ValueError(label + '.' + field + ' has an unsupported value')
    if record['functionalStatus'] == 'Complete':
        required = record.get('requiredStates')
        verified = record.get('verifiedStates')
        if not isinstance(required, list) or not required or not isinstance(verified, list) or not set(required) <= set(verified):
            raise ValueError(label + ': Complete requires every stated required state to be verified')
        strings(required, label + '.requiredStates'); strings(verified, label + '.verifiedStates')
    if record['readiness'] == 'Ready':
        if record['visualStatus'] != 'Close' or record['functionalStatus'] not in ('Complete', 'Not applicable'):
            raise ValueError(label + ': Ready requires Close visuals and complete applicable behavior')
        if not set(record.get('requiredStates', [])) <= set(record.get('verifiedStates', [])):
            raise ValueError(label + ': Ready requires every stated required state verified')
        required = record.get('requiredViewports')
        verified = record.get('verifiedViewports')
        if not isinstance(required, list) or not required or not isinstance(verified, list) or not set(required) <= set(verified):
            raise ValueError(label + ': Ready requires all required viewports to be verified')
        if record.get('qualityComplete') is not True or record.get('limitations'):
            raise ValueError(label + ': Ready requires completed quality checks and no open limitations')


def validate_pair(pair, root):
    for field in ('title', 'caption'):
        nonempty(pair.get(field), 'screenshotPair.' + field)
    for side in ('source', 'target'):
        panel = pair.get(side, {})
        for field in ('path', 'sha256', 'url', 'viewport', 'state', 'capturedAt'):
            nonempty(panel.get(field), side + '.' + field)
        if not panel['url'].startswith(('https://', 'http://')):
            raise ValueError('Capture URL must be HTTP(S)')
        path = path_at(root, panel['path'])
        if not path.is_file() or sha(path) != panel['sha256']:
            raise ValueError('Screenshot hash mismatch: ' + str(path))
        with PILImage.open(path) as im:
            box = panel.get('crop', [0, 0, im.width, im.height])
            if not isinstance(box, list) or len(box) != 4 or any(type(x) is not int for x in box):
                raise ValueError('Capture crop must contain four original-pixel integer bounds')
            if not 0 <= box[0] < box[2] <= im.width or not 0 <= box[1] < box[3] <= im.height:
                raise ValueError('Capture crop exceeds original screenshot bounds')


def validate_assessment(data, root):
    root = Path(root).resolve()
    if data.get('schemaVersion') != 2:
        raise ValueError('Readiness assessment requires schemaVersion 2')
    meta = data.get('meta', {})
    for field in ('title', 'date', 'baseline', 'method', 'sourceEvidenceSha256'):
        nonempty(meta.get(field), 'meta.' + field)
    if not re.fullmatch(r'[0-9a-fA-F]{64}', meta['sourceEvidenceSha256']):
        raise ValueError('meta.sourceEvidenceSha256 must identify the frozen evidence')
    for field in ('summary', 'limitations'):
        strings(meta.get(field), 'meta.' + field)
    if 'reportRevisionDate' in meta:nonempty(meta['reportRevisionDate'],'meta.reportRevisionDate')
    if meta.get('summaryChartStyle','flat') not in ('flat','isometric'):
        raise ValueError('meta.summaryChartStyle must be flat or isometric')
    for field in ('pages', 'components', 'sharedComponents', 'capabilities', 'qualityAreas', 'workItems', 'records'):
        if not isinstance(data.get(field), list):
            raise ValueError(field + ' must be an array')
    pages = data['pages']; components = data['components']; shared = data['sharedComponents']
    if not pages:
        raise ValueError('At least one scoped page is required')
    page_ids = {p.get('id') for p in pages}
    if None in page_ids or len(page_ids) != len(pages):
        raise ValueError('Page IDs must be nonempty and unique')
    families = {c.get('family') for c in components}
    if None in families or len(families) != len(components):
        raise ValueError('Body families must be unique actual names')
    all_ids = {c.get('id') for c in components + shared}
    if None in all_ids or len(all_ids) != len(components + shared):
        raise ValueError('Component IDs must be unique')
    from_pages = Counter(); variants_from_pages = Counter()
    for p in pages:
        for field in ('id', 'name', 'route', 'sourceUrl', 'targetUrl'):
            nonempty(p.get(field), 'page.' + field)
        statuses(p, p['id'])
        for field in ('retained', 'gaps'):
            strings(p.get(field), 'page.' + field)
        if not isinstance(p.get('components'), list) or not isinstance(p.get('screenshotPairs'), list):
            raise ValueError('Pages require components and screenshotPairs arrays')
        seen = set()
        for item in p['components']:
            family, variant, count = item.get('family'), item.get('variant'), item.get('count')
            if family not in families or type(count) is not int or count < 1 or (family, variant) in seen:
                raise ValueError('Page component count/name must reconcile with the actual family inventory')
            seen.add((family, variant)); statuses(item, p['id'] + '/' + str(variant))
            from_pages[(family, p['id'])] += count
            variants_from_pages[(family, variant, p['id'])] += count
        for pair in p['screenshotPairs']:
            validate_pair(pair, root)
    if 'openingVisual' in meta:
        selection=meta['openingVisual']
        if not isinstance(selection,dict):raise ValueError('meta.openingVisual must select an existing capture pair')
        for field in ('pageId','title','takeaway'):nonempty(selection.get(field),'meta.openingVisual.'+field)
        page=next((p for p in pages if p['id']==selection['pageId']),None)
        index=selection.get('pairIndex')
        if page is None or type(index) is not int or not 0<=index<len(page['screenshotPairs']):
            raise ValueError('meta.openingVisual must reference an existing page/capture-pair index')
    instance_total = 0; variant_total = 0
    for c in components + shared:
        for field in ('id', 'family', 'expected'):
            nonempty(c.get(field), 'component.' + field)
        statuses(c, c['id'])
        for field in ('variants', 'retained', 'visualGaps', 'functionalGaps', 'remainingWork', 'acceptance', 'evidence', 'limitations'):
            strings(c.get(field), 'component.' + field)
        if not c['variants'] or len(set(c['variants'])) != len(c['variants']):
            raise ValueError('Components require distinct exact original variants')
        if not c['evidence']:
            raise ValueError('Every component assessment needs evidence or a documented unverified reason')
        usage = c.get('usage')
        if not isinstance(usage, dict) or not usage or not set(usage) <= page_ids or any(type(n) is not int or n < 1 for n in usage.values()):
            raise ValueError('Component usage requires positive counts for actual scoped page IDs')
        assessments = c.get('variantAssessments')
        if not isinstance(assessments, list) or {v.get('variant') for v in assessments} != set(c['variants']) or len(assessments) != len(c['variants']):
            raise ValueError('Every exact variant needs one assessment and per-page usage')
        summed = Counter()
        for variant in assessments:
            statuses(variant, c['id'] + '/' + variant['variant'])
            if not isinstance(variant.get('usage'), dict) or not variant['usage'] or not set(variant['usage']) <= page_ids or any(type(n) is not int or n < 1 for n in variant['usage'].values()):
                raise ValueError('Variant usage must contain positive counts for scoped pages')
            nonempty(variant.get('note'), 'variant.note')
            summed.update(variant['usage'])
            if c in components:
                for pid, count in variant['usage'].items():
                    if variants_from_pages[(c['family'], variant['variant'], pid)] != count:
                        raise ValueError('Page and exact variant usage counts do not reconcile')
        if c['readiness']=='Ready' and any(v['readiness']!='Ready' for v in assessments):
            raise ValueError(c['id'] + ': Ready cannot hide an unready exact variant')
        if c['functionalStatus']=='Complete' and any(v['functionalStatus'] not in ('Complete','Not applicable') for v in assessments):
            raise ValueError(c['id'] + ': Complete cannot hide an unverified or incomplete variant')
        if dict(summed) != usage:
            raise ValueError('Family usage counts do not reconcile with exact variants')
        if c in components:
            for pid in page_ids:
                if from_pages[(c['family'], pid)] != usage.get(pid, 0):
                    raise ValueError('Family and page usage counts do not reconcile')
            instance_total += sum(usage.values()); variant_total += len(c['variants'])
        for pair in c.get('screenshotPairs', []):
            validate_pair(pair, root)
    expected_variants = {(c['family'], v['variant'], pid) for c in components for v in c['variantAssessments'] for pid in v['usage']}
    if set(variants_from_pages) != expected_variants:
        raise ValueError('Page inventory contains an unknown or omitted exact variant')
    for page in pages:
        scoped=page['components']+[c for c in shared if page['id'] in c['usage']]
        if page['readiness']=='Ready' and any(c['readiness']!='Ready' for c in scoped):
            raise ValueError(page['id'] + ': Ready cannot hide unready body or shared components')
        if page['functionalStatus']=='Complete' and any(c['functionalStatus'] not in ('Complete','Not applicable') for c in scoped):
            raise ValueError(page['id'] + ': Complete cannot hide incomplete scoped components')
    for c in data['capabilities']:
        if c.get('status') not in OUTCOMES or not set(c.get('pageIds', [])) <= page_ids:
            raise ValueError('Capability status/page IDs are invalid')
    for area in data['qualityAreas']:
        if area.get('outcome') not in OUTCOMES:
            raise ValueError('Quality area must retain a Pass/Fail/Unverified/Not applicable outcome')
    if len({w.get('id') for w in data['workItems']}) != len(data['workItems']):
        raise ValueError('Work item IDs must be unique')
    for item in data['workItems']:
        if item.get('status') not in OUTCOMES or not set(item.get('pageIds', [])) <= page_ids or not set(item.get('componentIds', [])) <= all_ids:
            raise ValueError('Work item status or affected references are invalid')
        for field in ('id', 'title', 'priority', 'action', 'doneWhen', 'owner'):
            nonempty(item.get(field), 'workItem.' + field)
    for entry in data['records']:
        if not path_at(root, entry['path']).is_file():
            raise ValueError('Missing original record: ' + entry['path'])
    return {'pages':len(pages), 'bodyFamilies':len(components), 'exactVariants':variant_total, 'bodyInstances':instance_total, 'sharedFamilies':len(shared)}


def clean(value):
    return str(value).replace('\u2011', '-').replace('\u2013', '-').replace('\u2014', '-').replace('\u2019', "'").replace('\u2018', "'")


def esc(value):
    return escape(clean(value))


def prose(value):
    """Use reader terms in narrative; authored identifiers are rendered with esc()."""
    text=clean(value)
    for old,new in [('component families','block types'),('component family','block type'),('body families','block types'),('body family','block type'),('family/variant','block type/variant'),('families','block types'),('family','block type'),('instances','uses'),('instance','use')]:
        text=re.sub(r'(?<![\w/.-])'+re.escape(old)+r'(?![\w/-]|\.[A-Za-z0-9])',lambda m:new[0].upper()+new[1:] if m[0][0].isupper() else new,text,flags=re.I)
    return escape(text)


def link(key, label):
    return '<link href="#' + key + '" color="#0F766E">' + esc(label) + '</link>'


def styles():
    body = ParagraphStyle('body', fontName='Readiness', fontSize=10, leading=13.5, textColor=INK, spaceAfter=7)
    return {'body':body, 'title':ParagraphStyle('title', parent=body, fontName='ReadinessBold', fontSize=22, leading=26, textColor=NAVY, spaceAfter=12),
        'h':ParagraphStyle('h', parent=body, fontName='ReadinessBold', fontSize=12, leading=16, textColor=NAVY, spaceBefore=5, spaceAfter=6, keepWithNext=True),
        'small':ParagraphStyle('small', parent=body, fontSize=9, leading=12, textColor=GRAY, spaceAfter=6),
        'kicker':ParagraphStyle('kicker', parent=body, fontName='ReadinessBold', fontSize=8.5, leading=11, textColor=TEAL, spaceAfter=9),
        'cell':ParagraphStyle('cell', parent=body, fontSize=9.5, leading=12.5, spaceAfter=0)}


def measured_height(items):
    """Conservative height for this fixed frame; keep logical figures together."""
    total=0
    for item in items:
        if isinstance(item, KeepTogether):
            total+=measured_height(item._content)
        else:
            total+=item.wrap(W-12,10000)[1]+item.getSpaceBefore()+item.getSpaceAfter()
    return total


def opening_summary(data):
    counts=Counter(c['readiness'] for c in data['components'])
    pages=[]
    for page in data['pages']:
        by_status=Counter()
        for occurrence in page['components']:by_status[occurrence['readiness']]+=occurrence['count']
        pages.append({'pageId':page['id'],'name':page['name'],'unit':'block uses','total':sum(by_status.values()),'counts':{label:by_status[label] for label in READINESS_ORDER},'visualStatus':page['visualStatus']})
    return {'unit':'block types','total':len(data['components']),
        'counts':{label:counts[label] for label in READINESS_ORDER},
        'style':data['meta'].get('summaryChartStyle','flat'),
        'chartRendered':bool(data['components']),
        'comparison':data['meta'].get('openingVisual'),
        'evidenceDate':data['meta']['date'],
        'reportRevisionDate':data['meta'].get('reportRevisionDate'),'pageReadiness':pages}


class ReadinessDonut(Flowable):
    """Counted native-vector wedges; perspective changes presentation, never counts."""
    def __init__(self, summary):
        super().__init__();self.width=216;self.height=140;self.summary=summary

    def draw(self):
        c=self.canv;cx,cy=108,74
        isometric=self.summary['style']=='isometric'
        r,inner,scale=(73,44,.62) if isometric else (49,30,1)
        depth=6 if isometric else 0
        c.setFont('ReadinessBold',10);c.setFillColor(NAVY);c.drawCentredString(cx,128,'Component readiness')
        if not self.summary['total']:return
        if isometric:
            c.setFillColor(PALE);c.ellipse(cx-r-3,cy-r*scale-depth-4,cx+r+3,cy+r*scale-depth-4,stroke=0,fill=1)
        slices=[];angle=90
        for label,count in self.summary['counts'].items():
            if not count:continue
            extent=360*count/self.summary['total'];slices.append((label,angle,extent));angle-=extent
        def wedge(start,extent,offset,color,stroke):
            steps=max(2,math.ceil(extent/2));angles=[math.radians(start-extent*i/steps) for i in range(steps+1)]
            points=[(cx+r*math.cos(a),cy+r*scale*math.sin(a)+offset) for a in angles]
            points.extend((cx+inner*math.cos(a),cy+inner*scale*math.sin(a)+offset) for a in reversed(angles))
            path=c.beginPath();path.moveTo(*points[0])
            for point in points[1:]:path.lineTo(*point)
            path.close();c.setFillColor(color);c.setStrokeColor(colors.white);c.setLineWidth(.55)
            c.drawPath(path,fill=1,stroke=int(stroke))
        if depth:
            for label,start,extent in slices:
                color=READINESS_COLORS[label]
                wedge(start,extent,-depth,colors.Color(color.red*.76,color.green*.76,color.blue*.76),False)
        for label,start,extent in slices:wedge(start,extent,0,READINESS_COLORS[label],True)
        for label,start,extent in slices:
            angle=math.radians(start-extent/2);radius=(r+inner)/2
            x,y=cx+radius*math.cos(angle),cy+radius*scale*math.sin(angle)
            value=str(self.summary['counts'][label]);c.setFont('ReadinessBold',9)
            width=pdfmetrics.stringWidth(value,'ReadinessBold',9)+7
            c.setFillColor(colors.white);c.roundRect(x-width/2,y-6,width,13,3,stroke=0,fill=1)
            c.setFillColor(NAVY);c.drawCentredString(x,y-3,value)
        c.setFillColor(NAVY);c.setFont('ReadinessBold',24);c.drawCentredString(cx,72,str(self.summary['total']))
        c.setFont('Readiness',9);c.drawCentredString(cx,57,'block types')
        c.setFillColor(GRAY);c.setFont('Readiness',8.5);c.drawCentredString(cx,8,'One rating per distinct block type')


class ReadinessSwatch(Flowable):
    def __init__(self,label):super().__init__();self.width=8;self.height=12;self.label=label
    def draw(self):
        self.canv.setFillColor(READINESS_COLORS[self.label]);self.canv.circle(4,6,3.2,stroke=0,fill=1)


class PageReadinessBar(Flowable):
    def __init__(self,row):super().__init__();self.width=244;self.height=16;self.row=row
    def draw(self):
        c=self.canv
        if not self.row['total']:
            c.setFillColor(GRAY);c.setFont('Readiness',8);c.drawString(0,4,'Uses unrecorded');return
        x=0
        for label,count in self.row['counts'].items():
            if not count:continue
            width=self.width*count/self.row['total']
            c.setFillColor(READINESS_COLORS[label]);c.rect(x,1,width,14,stroke=0,fill=1)
            value=str(count);text_width=pdfmetrics.stringWidth(value,'ReadinessBold',8)
            if width>=text_width+6:
                c.setFillColor(colors.white);c.roundRect(x+(width-text_width-4)/2,2,text_width+4,12,2,stroke=0,fill=1)
                c.setFillColor(NAVY);c.setFont('ReadinessBold',8);c.drawCentredString(x+width/2,5,value)
            x+=width


class ReadinessDoc(SimpleDocTemplate):
    def afterFlowable(self, item):
        if hasattr(item, 'section_key'):
            self.canv.bookmarkPage(item.section_key)
            self.canv.addOutlineEntry(item.getPlainText(), item.section_key, level=0)
            self.destinations.append({'key':item.section_key, 'title':item.getPlainText(), 'page':self.page})


class Story:
    def __init__(self, data, root, page_map):
        self.data = data; self.root = root; self.map = page_map; self.s = styles(); self.items = []; self.sections = []
        self.pages = {p['id']:p for p in data['pages']}

    def p(self, text, style='body'):
        self.items.append(Paragraph(text, self.s[style]))

    def section(self, key, title, kicker):
        if self.items:self.items.append(PageBreak())
        self.p(esc(kicker.upper()), 'kicker')
        title_p = Paragraph(esc(title), self.s['title']); title_p.section_key = key;title_p.keepWithNext=True
        self.items.append(title_p); self.sections.append((key, title))

    def heading(self, label):self.p(esc(label), 'h')

    def bullets(self, values, style='body'):
        for value in values:self.p(prose(value), style)

    def table(self, rows, widths, size=9.5, pad=5):
        regular = ParagraphStyle('tablecell', parent=self.s['cell'], fontSize=size, leading=size*1.3)
        bold = ParagraphStyle('tablehead', parent=regular, fontName='ReadinessBold', textColor=NAVY)
        cells = [[Paragraph(value, bold if i==0 else regular) for value in row] for i,row in enumerate(rows)]
        t = Table(cells, colWidths=widths, repeatRows=1, hAlign='LEFT')
        t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),PALE),('LINEBELOW',(0,0),(-1,-1),.4,LINE),('LEFTPADDING',(0,0),(-1,-1),pad),('RIGHTPADDING',(0,0),(-1,-1),pad),('TOPPADDING',(0,0),(-1,-1),pad),('BOTTOMPADDING',(0,0),(-1,-1),pad)]))
        self.items += [t,Spacer(1,8)]
        return t

    def names(self, ids):return ', '.join(self.pages[x]['name'] for x in ids)

    def readiness_overview(self):
        summary=opening_summary(self.data)
        if not summary['total']:
            self.p('Block-type inventory unrecorded. No readiness distribution can be shown until the inventory is recorded.','small')
            return
        regular=ParagraphStyle('readinesscell',parent=self.s['cell'],fontSize=10,leading=13)
        bold=ParagraphStyle('readinesshead',parent=regular,fontName='ReadinessBold',textColor=NAVY)
        rows=[['',Paragraph('Readiness',bold),Paragraph('Block types',bold)]]
        rows.extend([ReadinessSwatch(label),Paragraph(esc(label),regular),Paragraph(str(count),regular)] for label,count in summary['counts'].items())
        table=Table(rows,colWidths=[14,198,82],hAlign='LEFT')
        table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('BACKGROUND',(0,0),(-1,0),PALE),('LINEBELOW',(0,0),(-1,-1),.4,LINE),('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
        overview=Table([[ReadinessDonut(summary),'',table]],colWidths=[216,14,294],hAlign='LEFT')
        overview.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
        self.items.extend([KeepTogether([overview]),Spacer(1,8)])

    def page_readiness_overview(self):
        rows=opening_summary(self.data)['pageReadiness']
        if not any(r['total'] for r in rows):return
        self.heading('Block uses by page')
        regular=ParagraphStyle('pagebarcell',parent=self.s['cell'],fontSize=9.5,leading=12)
        bold=ParagraphStyle('pagebarhead',parent=regular,fontName='ReadinessBold',textColor=NAVY)
        cells=[[Paragraph(t,bold) for t in ['Page','Readiness mix','Uses','Visual match']]]
        cells.extend([Paragraph(esc(r['name']),regular),PageReadinessBar(r),Paragraph(str(r['total']),regular),Paragraph(esc(r['visualStatus']),regular)] for r in rows[:5])
        table=Table(cells,colWidths=[115,256,37,116],hAlign='LEFT')
        table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('BACKGROUND',(0,0),(-1,0),PALE),('LINEBELOW',(0,0),(-1,-1),.4,LINE),('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
        self.items.extend([KeepTogether([table]),Spacer(1,5)])
        note='Same readiness colors as above. Each row counts uses on that page; repeated types can appear on several pages. Visual match is a separate assessment.'
        if len(rows)>5:note=f'First 5 of {len(rows)} scoped pages shown. '+note
        self.p(note,'small')

    def status(self, record):
        self.p('<b>Visual:</b> '+esc(record['visualStatus'])+' | <b>Functional:</b> '+esc(record['functionalStatus'])+'<br/><b>Readiness:</b> '+esc(record['readiness']))

    def pair(self, pair, maxh=150):
        columns=[]
        for side,label in [('source','PRODUCTION / SOURCE'),('target','MIGRATED / TARGET')]:
            panel=pair[side];path=path_at(self.root,panel['path'])
            with PILImage.open(path) as original:
                box=panel.get('crop',[0,0,original.width,original.height]);im=original.crop(box).convert('RGB');buffer=BytesIO();im.save(buffer,format='PNG');buffer.seek(0)
                scale=min(250/im.width,maxh/im.height)
                picture=Image(buffer,width=im.width*scale,height=im.height*scale,hAlign='LEFT')
            reference='<link href="'+escape(panel['url'],quote=True)+'" color="#0F766E">'+('Source page' if side=='source' else 'Target page')+'</link> / '+esc(panel['capturedAt'])
            reference+='<br/>Capture: '+esc(Path(panel['path']).name)
            columns.append([Paragraph(esc(label+' / '+panel['viewport']),self.s['small']),picture,Paragraph(reference,self.s['small'])])
        t=Table([[columns[0],columns[1]]],colWidths=[W/2,W/2],hAlign='LEFT');t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),7)]))
        caption=Paragraph(esc(pair['caption']),self.s['small'])
        self.items.append(KeepTogether([t,caption]))

    def matrix(self, records, exact=False):
        pages=self.data['pages'];chunks=[pages[x:x+5] for x in range(0,len(pages),5)]
        entries=[]
        for c in records:
            if exact:entries.extend((c,v['variant'],v['usage'],v) for v in c['variantAssessments'])
            else:entries.append((c,c['family'],c['usage'],c))
        for colnum,cols in enumerate(chunks):
            for start in range(0,len(entries),16):
                kind='Exact authored variants' if exact else 'Block usage by page'
                key=('variant-matrix' if exact else 'family-matrix')+f'-{colnum}-{start}'
                self.section(key,kind, 'Frequency / original authored HTML')
                self.p('Numbers count authored block uses. A dash means absent. Uses is the full-scope total. Shared header/footer uses are separate. Variants retain their exact original class names.', 'small')
                self.p('These rows summarize each block type. Page-specific and variant exceptions remain in their separate rows and detail assessments.' if not exact else 'These status columns use each exact variant assessment. Page-specific exceptions remain in the page breakdowns and notes.','small')
                self.p('; '.join(f"P{pages.index(p)+1:02d} = {esc(p['name'])}" for p in cols),'small')
                width=140/len(cols);rows=[['Exact class attribute' if exact else 'Block type',*[f"P{pages.index(p)+1:02d}" for p in cols],'Uses','Visual','Function','Readiness']]
                for c,label,usage,status in entries[start:start+16]:rows.append([link('component-'+c['id'],label),*[str(usage.get(p['id'],0)) if usage.get(p['id']) else '-' for p in cols],str(sum(usage.values())),esc(status['visualStatus']),esc(status['functionalStatus']),esc(status['readiness'])])
                grid=self.table(rows,[125]+[width]*len(cols)+[30,55,64,110],size=9.3,pad=4)
                uses=1+len(cols);visual=uses+1
                grid.setStyle(TableStyle([('LEFTPADDING',(uses,0),(uses,-1),2),('RIGHTPADDING',(uses,0),(uses,-1),2),('LEFTPADDING',(visual,0),(visual,-1),3),('RIGHTPADDING',(visual,0),(visual,-1),3)]))

    def component(self, c, shared=False, part='all', maxh=150):
        if part in ('all','core'):
            self.status(c)
            self.p('<b>Usage:</b> '+esc('; '.join(self.pages[p]['name']+' x'+str(n) for p,n in c['usage'].items()))+(' (shared header/footer; excluded from body totals)' if shared else ''),'small')
            self.p('<b>Expected:</b> '+prose(c['expected']))
            self.table([['Already retained','Visual gaps','Functional gaps'],['<br/>'.join(map(prose,c['retained'])) or 'None established','<br/>'.join(map(prose,c['visualGaps'])) or 'None recorded','<br/>'.join(map(prose,c['functionalGaps'])) or 'None recorded']],[174,175,175],size=9.5,pad=6)
            self.p('<b>Remaining work:</b> '+prose(' '.join(c['remainingWork'])))
            self.p('<b>Done when:</b> '+prose(' '.join(c['acceptance'])))
        if part in ('all','details'):
            self.table([['Exact variant / total uses','Visual / functional / readiness','Specific evidence boundary'],*[ [esc(v['variant'])+' / '+str(sum(v['usage'].values())),esc(v['visualStatus']+' / '+v['functionalStatus']+' / '+v['readiness']),prose(v['note'])] for v in c['variantAssessments']]],[150,170,204],size=9.5,pad=5)
            self.p('<b>Evidence:</b> '+esc('; '.join(c['evidence'])),'small')
            if c['limitations']:self.p('<b>Limits / open checks:</b> '+prose(' '.join(c['limitations'])),'small')
        if part in ('all','figures'):
            for pair in c.get('screenshotPairs',[]):self.pair(pair,maxh=maxh)


def make_story(data, root, counts, page_map):
    b=Story(data,root,page_map);meta=data['meta']
    date_line='Evidence: '+meta['date']
    if meta.get('reportRevisionDate'):date_line+=' / report revised: '+meta['reportRevisionDate']
    b.section('summary',meta['title'],date_line)
    if meta['summary']:b.p(prose(meta['summary'][0]))
    b.readiness_overview()
    b.table([['Scoped pages','Block types','Variants','Block uses'],[str(counts['pages']),str(counts['bodyFamilies']),str(counts['exactVariants']),str(counts['bodyInstances'])]],[131]*4,size=10,pad=5)
    b.page_readiness_overview()
    if meta.get('openingVisual'):
        selection=meta['openingVisual'];page=next(p for p in data['pages'] if p['id']==selection['pageId'])
        b.p('<b>'+esc(selection['title'])+'</b>','small')
        b.pair({**page['screenshotPairs'][selection['pairIndex']],'caption':selection['takeaway']},maxh=100)
    b.bullets(meta['summary'][1:])
    if meta.get('readinessSummary'):b.p(prose(meta['readinessSummary']))
    b.p('<b>Baseline:</b> '+esc(meta['baseline']),'small')
    b.p('Readiness counts are not completion percentages. Shared header/footer are assessed separately.','small')
    b.section('contents','Find the detail you need','Contents / clickable PDF bookmarks')
    # Populated from the first pass; all later sections are discoverable without duplicating their narrative.
    major={'method','scope','family-matrix-0-0','variant-matrix-0-0','shared-usage','source-mapping','capabilities','work-0','records'}
    major.update('page-'+p['id'] for p in data['pages'])
    major.update('quality-'+str(i) for i in range(len(data['qualityAreas'])))
    component_first='component-'+(data['components']+data['sharedComponents'])[0]['id'] if data['components']+data['sharedComponents'] else None
    if component_first:major.add(component_first)
    toc=[(x['key'],'Block-by-block assessments' if x['key']==component_first else x['title'],x['page']) for x in page_map.get('_outline',[]) if x['key'] in major]
    b.table([['Section','Page'],*[[link(k,t),str(p)] for k,t,p in toc]],[478,46],size=9.3,pad=4)
    b.p('Every detailed component section is bookmarked. Full original check records and machine-readable assessments are embedded in audit-records.zip. Full-size evidence remains at the retained paths.','small')
    b.section('method','Reading the assessments','Scope / terms / evidence boundaries')
    b.p(prose(meta['method']));b.table([['Dimension','Meaning'],['Visual: Close / Partial / Far off / Unverified','Rendered comparison of layout, typography, spacing, color, imagery and states. A missing file alone does not establish a visual rating.'],['Functional: Complete / Partial / Missing / Unverified / Not applicable','Expected capabilities and states compared with production. Complete requires every stated required state verified. Sampled success remains bounded.'],['Readiness: Ready / Minor work / Substantial work / Capability missing / Unverified','Delivery assessment using visual, functional and required quality coverage. Ready requires completed required states/viewports and quality checks.'],['Block types, variants and uses','A block type is a distinct implementation, such as hero. A variant is an exact class combination, such as hero video. Each placement is one use; cards inside a block are not separate uses. Shared header/footer are excluded from body totals.']],[160,364],size=10,pad=7)
    b.heading('Remaining limits');b.bullets(meta['limitations'],'small')
    b.section('scope','Scope and page mappings',str(counts['pages'])+'-page inventory / source and target reference')
    b.p('<b>Comparison baseline:</b> '+esc(meta['baseline']))
    b.table([['Page','Production / target mappings'],*[[esc(p['name'])+'<br/>'+esc(p['id']),esc(p['sourceUrl'])+'<br/>'+esc(p['targetUrl'])] for p in data['pages']]],[150,374],size=9.5,pad=6)
    for page in data['pages']:
        b.section('page-'+page['id'],'Page breakdown: '+page['name'],page['id']+' / '+page['route']);b.status(page)
        for pair in page['screenshotPairs']:b.pair(pair)
        b.heading('Already retained / working');b.bullets(page['retained'])
        b.heading('Gaps and remaining work');b.bullets(page['gaps'])
        if page.get('qualityNotes'):b.heading('Page-specific quality checks');b.bullets(page['qualityNotes'],'small')
        for part in range(0,len(page['components']),8):
            b.section('page-blocks-'+page['id']+'-'+str(part),'Blocks on '+page['name'],'Page breakdown / counts and readiness')
            b.p('Counts below are authored uses of the exact class combination. Statuses apply to the noted evidence and states; review each variant and page-specific exception.','small')
            b.table([['Actual class / uses','Visual','Functional','Readiness / remaining detail'],*[[esc(c['variant'])+' / '+str(c['count']),esc(c['visualStatus']),esc(c['functionalStatus']),esc(c['readiness'])+'<br/>'+prose(c['note'])] for c in page['components'][part:part+8]]],[150,75,90,209],size=9.5,pad=6)
    b.matrix(data['components']);b.matrix(data['components'],exact=True)
    mapped=[c for c in data['components']+data['sharedComponents'] if c.get('sourceLabels')]
    if data['sharedComponents'] or mapped:
        b.section('shared-usage' if data['sharedComponents'] else 'source-mapping','Shared usage and source-to-block mapping','Actual production names / separate shared counts')
        if data['sharedComponents']:
            b.table([['Shared block type','Pages','Uses'],*[[link('component-'+c['id'],c['family']),b.names(c['usage']),str(sum(c['usage'].values()))] for c in data['sharedComponents']]],[150,280,94],size=10,pad=7)
        for start in range(0,len(mapped),12):
            if start:b.section('source-mapping-'+str(start),'Source-to-block mapping','Actual production labels/classes / continued')
            b.p('Observed production labels/classes may be nested or overlap. They identify the source regions used in the comparison; they are not invented block names or proof of a one-to-one implementation mapping.','small')
            b.table([['EDS block type','Observed production labels/classes'],*[[link('component-'+c['id'],c['family']),esc(', '.join(c['sourceLabels']))] for c in mapped[start:start+12]]],[140,384],size=9.5,pad=5)
    for c in data['components']+data['sharedComponents']:
        title='Block assessment: '+c['family'];kicker=c['id']+' / actual authored name / visual and functional readiness'
        header=Story(data,root,page_map);header.section('measure',title,kicker)
        budget=658-measured_height(header.items)-6
        card=None
        for maxh in (150,140,130,120,110):
            candidate=Story(data,root,page_map);candidate.component(c,c in data['sharedComponents'],maxh=maxh)
            if measured_height(candidate.items)<=budget:card=candidate;break
        b.section('component-'+c['id'],title,kicker)
        if card is not None:
            b.items.extend(card.items)
        else:
            core=Story(data,root,page_map);core.component(c,c in data['sharedComponents'],part='core')
            b.items.extend(core.items)
            detail=Story(data,root,page_map);detail.component(c,c in data['sharedComponents'],part='details')
            figures=Story(data,root,page_map);figures.component(c,c in data['sharedComponents'],part='figures')
            b.section('component-detail-'+c['id'],'Variants and evidence: '+c['family'],c['id']+' / assessment continued')
            b.items.extend(detail.items)
            if measured_height(detail.items+figures.items)>budget and figures.items:
                b.section('component-visual-'+c['id'],'Visual evidence: '+c['family'],c['id']+' / assessment continued')
            b.items.extend(figures.items)
    b.section('capabilities','Retained and missing capabilities','Experience gaps across blocks and services')
    for start in range(0,len(data['capabilities']),5):
        if start:b.section('capabilities-'+str(start),'Retained and missing capabilities','Continued / experience gaps')
        b.table([['Capability / affected pages','Status / what remains','Required action'],*[[esc(c['id']+' / '+c['name'])+'<br/>'+esc(b.names(c['pageIds'])),esc(c['status'])+'<br/><b>Retained:</b> '+prose(c.get('retained',''))+'<br/><b>Missing / open:</b> '+prose(c.get('missing','')),prose(c.get('action',''))+'<br/><br/>'+esc('; '.join(c.get('evidence',[])))] for c in data['capabilities'][start:start+5]]],[160,184,180],size=9.5,pad=6)
    for i,area in enumerate(data['qualityAreas']):
        b.section('quality-'+str(i),area['name'],'Quality requirements / '+area['outcome'])
        b.heading('What the evidence establishes');b.bullets(area.get('observations',[]))
        b.heading('Remaining work');b.bullets(area.get('remainingWork',[]))
        b.p('<b>Evidence:</b> '+esc('; '.join(area.get('evidence',[]))),'small')
        for pair in area.get('screenshotPairs',[]):b.pair(pair)
    for start in range(0,len(data['workItems']),5):
        b.section('work-'+str(start),'Final work board','Delivery actions / all outcomes remain evidence-bound')
        b.table([['Task / status / owner','Affected scope and action','Done when'],*[[esc(w['id']+' / '+w['title'])+'<br/>'+esc(w['status']+' / '+w['priority'])+'<br/>Owner: '+esc(w['owner']),esc(b.names(w['pageIds']))+'<br/>'+prose(w['action']),prose(w['doneWhen'])] for w in data['workItems'][start:start+5]]],[155,185,184],size=9.5,pad=6)
    for start in range(0,max(1,len(data['records'])),15):
        b.section('records' if start==0 else 'records-'+str(start),'Technical evidence and original outcomes','Appendix / supporting records'+(' / continued' if start else ''))
        if start==0:b.p('The main report explains the migrated experience. Supporting records include preserved original measurements/check outcomes, any new collection and supplemental observations, and supplied workflow references. Their dates and evidence lineage remain distinct; they are not visual-completion scores.')
        b.table([['Embedded supporting record','Purpose'],*[[esc(e.get('archiveName',Path(e['path']).name)),esc(e.get('label','Supporting evidence record'))] for e in data['records'][start:start+15]]],[230,294],size=9.5,pad=5)
        b.p('Use a PDF reader with an attachments panel to extract audit-records.zip. It includes this assessment, exact original record bytes, file hashes and any supplied additional archive. Screenshot/HTTP bodies are only embedded if supplied as record files; their retained paths do not imply every binary is inside the PDF.','small')
    return b


def build(assessment, output, font_regular=None, font_bold=None, records=None):
    assessment=Path(assessment).resolve();root=assessment.parent;output=Path(output).resolve();data=load(assessment);counts=validate_assessment(data,root)
    fontdir=Path(reportlab.__file__).parent/'fonts';regular=Path(font_regular or fontdir/'Vera.ttf');bold=Path(font_bold or fontdir/'VeraBd.ttf')
    pdfmetrics.registerFont(TTFont('Readiness',str(regular)));pdfmetrics.registerFont(TTFont('ReadinessBold',str(bold)));pdfmetrics.registerFontFamily('Readiness',normal='Readiness',bold='ReadinessBold',italic='Readiness',boldItalic='ReadinessBold')
    def render(page_map):
        buffer=BytesIO();story=make_story(data,root,counts,page_map)
        doc=ReadinessDoc(buffer,pagesize=(612,792),invariant=1,leftMargin=44,rightMargin=44,topMargin=72,bottomMargin=50,title=data['meta']['title'],author='Migration gap audit toolkit');doc.destinations=[]
        def chrome(canvas,document):
            canvas.setFillColor(TEAL);canvas.rect(44,758,28,3,fill=1,stroke=0);canvas.setFont('ReadinessBold',8);canvas.setFillColor(GRAY);canvas.drawString(81,756,'MIGRATION READINESS / PAGE AND COMPONENT AUDIT');canvas.setFont('Readiness',8);canvas.drawRightString(568,756,clean(data['meta'].get('reportRevisionDate',data['meta']['date'])))
            canvas.setStrokeColor(LINE);canvas.line(44,41,568,41);canvas.setFont('Readiness',7.8);canvas.drawString(44,27,'Visual and functional readiness are separate / open checks remain explicit');canvas.drawRightString(568,27,str(document.page))
        doc.build(story.items,onFirstPage=chrome,onLaterPages=chrome,canvasmaker=partial(Canvas,invariant=1));return buffer.getvalue(),doc.destinations
    pdf,outline=render({});mapping={'_outline':outline}
    for _ in range(4):
        pdf,new=render(mapping)
        if new==mapping['_outline']:outline=new;break
        mapping={'_outline':new}
    else:raise ValueError('Contents pagination did not stabilize')
    payload={'readiness.json':assessment.read_bytes()};manifest={}
    for entry in data['records']:
        path=path_at(root,entry['path']);name=entry.get('archiveName',path.name)
        if name in payload or Path(name).name!=name:raise ValueError('Original record archive names must be unique flat filenames')
        payload[name]=path.read_bytes();manifest[name]={'path':entry['path'],'sha256':sha(path),'label':entry.get('label','Supporting record')}
    if records:
        path=path_at(root,records);payload['additional-records.zip']=path.read_bytes();manifest['additional-records.zip']={'path':str(records),'sha256':sha(path)}
    payload['record-manifest.json']=(json.dumps({'assessmentSha256':sha(assessment),'sourceEvidenceSha256':data['meta']['sourceEvidenceSha256'],'files':manifest},indent=2)+'\n').encode()
    buffer=BytesIO()
    with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for name,content in payload.items():
            info=zipfile.ZipInfo(name,date_time=(2000,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;archive.writestr(info,content)
    writer=PdfWriter(clone_from=BytesIO(pdf));writer.add_attachment('audit-records.zip',buffer.getvalue());output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('wb') as target:writer.write(target)
    record={'rendererVersion':VERSION,'assessmentSha256':sha(assessment),'sourceEvidenceSha256':data['meta']['sourceEvidenceSha256'],'pdfSha256':sha(output),'pageCount':len(PdfReader(output).pages),'counts':counts,'outline':outline,'recordFiles':manifest,'attachmentSha256':hashlib.sha256(buffer.getvalue()).hexdigest(),'builderSha256':sha(__file__),'fontSha256':{'regular':sha(regular),'bold':sha(bold)},'componentReadiness':dict(Counter(c['readiness'] for c in data['components'])),'pythonVersion':sys.version.split()[0],'platform':sys.platform,'dependencies':{name:importlib.metadata.version(name) for name in ('reportlab','Pillow','pypdf')}}
    record['openingSummary']=opening_summary(data)
    output.with_suffix('.build.json').write_text(json.dumps(record,indent=2)+'\n');return record


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--assessment',required=True);parser.add_argument('--out');parser.add_argument('--font-regular');parser.add_argument('--font-bold');parser.add_argument('--records');parser.add_argument('--validate-only',action='store_true');args=parser.parse_args()
    try:
        if args.validate_only:print(json.dumps(validate_assessment(load(args.assessment),Path(args.assessment).resolve().parent),indent=2))
        elif not args.out:parser.error('--out is required unless --validate-only is used')
        else:
            result=build(args.assessment,args.out,args.font_regular,args.font_bold,args.records);print(f"Wrote {args.out}: {result['pageCount']} pages; {result['counts']['bodyInstances']} block uses")
    except (ValueError,OSError,KeyError,TypeError) as error:parser.exit(1,f'Readiness PDF failed: {error}\n')


if __name__=='__main__':main()
