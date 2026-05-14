#!/usr/bin/env python3
"""Regenerate cards.json from the MeowTarot source dataset.

Reads the 156-entry source (78 upright + 78 reversed) at
~/projects/MeowTarot/data/cards.json and emits a trimmed bilingual
structure used by veilatarot.com.

Fields per (card, orientation):
- keywords        (from tarot_imply)
- standalone      (from standalone_present)
- love            (from love_reading_single, falls back to love_present)
- career          (from career_reading_single, falls back to career_present)
- finance         (from finance_reading_single, falls back to finance_present)
- celtic_cross    (10 positions)

Plus per-card:
- id, arcana, suit, number, roman, name, archetype

    python3 scripts/regen-cards-json.py
"""
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = Path.home() / 'projects' / 'MeowTarot' / 'data' / 'cards.json'
SOURCE = Path(os.environ.get('VEILA_DECK_SOURCE', DEFAULT_SOURCE))
DEST = ROOT / 'cards.json'

POSITION_KEYS = ['present', 'challenge', 'past', 'future',
                 'above', 'below', 'self', 'environment',
                 'hopes_fears', 'outcome']


def roman(n):
    if n == 0:
        return '0'
    vals = [('M', 1000), ('CM', 900), ('D', 500), ('CD', 400),
            ('C', 100), ('XC', 90), ('L', 50), ('XL', 40),
            ('X', 10), ('IX', 9), ('V', 5), ('IV', 4), ('I', 1)]
    s = ''
    for r, v in vals:
        while n >= v:
            s += r
            n -= v
    return s


def main():
    if not SOURCE.exists():
        raise SystemExit(f'source not found: {SOURCE}')
    src = json.loads(SOURCE.read_text(encoding='utf-8'))
    by_card = {}

    for entry in src:
        cid = entry['card_id']
        m = re.match(r'^(\d{2})-(.+)-(upright|reversed)$', cid)
        if not m:
            continue
        num_str, slug, orient = m.group(1), m.group(2), m.group(3)
        num = int(num_str)
        base_id = f'{num_str}-{slug}'

        if base_id not in by_card:
            if num <= 22:
                arcana = 'major'
                suit = None
                number = num - 1
                rom = roman(number) if number > 0 else '0'
            else:
                arcana = 'minor'
                idx_in_suit = (num - 23) % 14
                number = idx_in_suit + 1
                suit_idx = (num - 23) // 14
                suit = ['wands', 'cups', 'swords', 'pentacles'][suit_idx]
                if number <= 10:
                    rom = roman(number)
                else:
                    rom = {11: 'Pg', 12: 'Kn', 13: 'Qn', 14: 'Kg'}[number]
            by_card[base_id] = {
                'id': base_id,
                'arcana': arcana,
                'suit': suit,
                'number': number,
                'roman': rom,
                'name': {
                    'en': entry.get('card_name_en'),
                    'th': entry.get('alias_th') or entry.get('card_name_en'),
                },
                'archetype': {
                    'en': entry.get('archetype_en'),
                    'th': entry.get('archetype_th'),
                },
                'upright': {},
                'reversed': {},
            }

        cell = by_card[base_id][orient]
        cell['keywords'] = {
            'en': entry.get('tarot_imply_en') or '',
            'th': entry.get('tarot_imply_th') or '',
        }
        cell['standalone'] = {
            'en': entry.get('standalone_present_en') or '',
            'th': entry.get('standalone_present_th') or '',
        }
        # Intent-specific interpretations (used by TH intent sections + scenarios).
        # Fall back through reading_single → present → standalone so we never
        # ship empty text.
        cell['love'] = {
            'en': (entry.get('love_reading_single_en')
                   or entry.get('love_present_en')
                   or cell['standalone']['en']),
            'th': (entry.get('love_reading_single_th')
                   or entry.get('love_present_th')
                   or cell['standalone']['th']),
        }
        cell['career'] = {
            'en': (entry.get('career_reading_single_en')
                   or entry.get('career_present_en')
                   or cell['standalone']['en']),
            'th': (entry.get('career_reading_single_th')
                   or entry.get('career_present_th')
                   or cell['standalone']['th']),
        }
        cell['finance'] = {
            'en': (entry.get('finance_reading_single_en')
                   or entry.get('finance_present_en')
                   or cell['standalone']['en']),
            'th': (entry.get('finance_reading_single_th')
                   or entry.get('finance_present_th')
                   or cell['standalone']['th']),
        }
        cell['celtic_cross'] = {}
        for pk in POSITION_KEYS:
            cell['celtic_cross'][pk] = {
                'en': entry.get(f'celtic_cross_{pk}_en') or cell['standalone']['en'],
                'th': entry.get(f'celtic_cross_{pk}_th') or cell['standalone']['th'],
            }

    deck = sorted(by_card.values(), key=lambda c: c['id'])
    with DEST.open('w', encoding='utf-8') as f:
        json.dump(deck, f, ensure_ascii=False, separators=(',', ':'))
    print(f'wrote {len(deck)} cards to {DEST}')
    print(f'  file size: {DEST.stat().st_size:,} bytes')


if __name__ == '__main__':
    main()
