# -*- coding: utf-8 -*-
from pathlib import Path
import re
import collections

root=Path('.')
new_files=sorted([p for p in root.rglob('*.md') if '2026連載' in p.as_posix()])
print('NEW_FILES',len(new_files))

errors=[]
cat_counts=collections.Counter()

existing_2026_titles=set()
for p in root.rglob('*.md'):
    if p in new_files:
        continue
    txt=p.read_text(encoding='utf-8',errors='ignore')
    if 'date: 2026-' in txt[:600] or '2026' in p.name:
        m=re.search(r'^title:\s*"?(.*?)"?\s*$',txt,re.MULTILINE)
        if m:
            existing_2026_titles.add(m.group(1).strip())

for p in new_files:
    txt=p.read_text(encoding='utf-8',errors='ignore')
    mfm=re.match(r'^---\n([\s\S]*?)\n---\n',txt)
    if not mfm:
        errors.append((p,'frontmatter missing'))
        continue
    fm=mfm.group(1)
    body=txt[mfm.end():]

    for k in ['title:','date:','updated:','tags:','author:','draft:']:
        if k not in fm:
            errors.append((p,f'missing {k}'))

    mt=re.search(r'^title:\s*"?(.*?)"?\s*$',fm,re.MULTILINE)
    if not mt:
        errors.append((p,'title parse fail'))
        continue
    title=mt.group(1).strip()
    if title in existing_2026_titles:
        errors.append((p,'title duplicate with existing 2026'))

    tags_block=re.search(r'^tags:\n([\s\S]*?)(?:\n[a-zA-Z_][\w-]*:|\Z)',fm,re.MULTILINE)
    if not tags_block:
        errors.append((p,'tags block missing'))
        continue
    tags=[ln.strip()[2:].strip().strip('"').strip("'") for ln in tags_block.group(1).splitlines() if ln.strip().startswith('- ')]
    if len(tags)!=1:
        errors.append((p,f'tag count !=1 ({len(tags)})'))
        continue
    tag=tags[0]
    folder_cat=re.sub(r'^\d+_','',p.parts[0])
    if tag!=folder_cat:
        errors.append((p,f'tag-folder mismatch {tag}!={folder_cat}'))

    cat_counts[p.parts[0]] += 1

    if len(body)<1500:
        errors.append((p,f'body<1500 ({len(body)})'))

    rel=re.search(r'\n## 関連記事\n([\s\S]*?)(?:\n## |\Z)',body)
    if not rel:
        errors.append((p,'related section missing'))
    else:
        n_rel=len(re.findall(r'\-\s+\[\[',rel.group(1)))
        if n_rel<3:
            errors.append((p,f'related links<3 ({n_rel})'))

    ref=re.search(r'\n## 参考・引用元\n([\s\S]*?)\Z',body)
    if not ref:
        errors.append((p,'reference section missing'))
    else:
        n_ref=len(re.findall(r'\-\s+\[[^\]]+\]\(https?://[^\)]+\)',ref.group(1)))
        if n_ref<3:
            errors.append((p,f'references<3 ({n_ref})'))

    mi=re.search(r'!\[\[([^\]]+_infographic\.svg)\]\]',body)
    if not mi:
        errors.append((p,'infographic missing'))
    else:
        img=root/'_images'/mi.group(1)
        if not img.exists():
            errors.append((p,f'image missing {mi.group(1)}'))

for i in range(1,19):
    top=next((k for k in cat_counts if k.startswith(f'{i:02d}_')),None)
    if not top:
        errors.append((Path(f'{i:02d}_*'),'category missing'))
    elif cat_counts[top]!=12:
        errors.append((Path(top),f'count!=12 ({cat_counts[top]})'))

print('ERROR_COUNT',len(errors))
for p,e in errors[:40]:
    print('ERROR',p.as_posix(),'::',e)
print('CATEGORY_COUNTS')
for k in sorted(cat_counts):
    print(k,cat_counts[k])

img_links=[]
for p in new_files:
    t=p.read_text(encoding='utf-8',errors='ignore')
    m=re.search(r'!\[\[([^\]]+_infographic\.svg)\]\]',t)
    if m:
        img_links.append(m.group(1))
print('IMG_LINKS',len(img_links))
print('IMG_UNIQUE',len(set(img_links)))
print('IMG_MISSING',len([n for n in set(img_links) if not (root/'_images'/n).exists()]))
