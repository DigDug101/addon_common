'''
Copyright (C) 2019 CG Cookie
http://cgcookie.com
hello@cgcookie.com

Created by Jonathan Denning, Jonathan Williamson

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import os
import re
import math
import time
import struct
import random
import traceback
import functools
import urllib.request
from itertools import chain
from concurrent.futures import ThreadPoolExecutor

import bpy
import bgl
from bpy.types import BoolProperty
from mathutils import Matrix

from .parse import Parse_CharStream, Parse_Lexer
from .ui_utilities import (
    convert_token_to_string, convert_token_to_cursor,
    convert_token_to_color, convert_token_to_number,
    skip_token,
)

from .decorators import blender_version_wrapper, debug_test_call
from .maths import Point2D, Vec2D, clamp, mid, Color
from .profiler import profiler
from .drawing import Drawing, ScissorStack
from .utils import iter_head
from .shaders import Shader
from .fontmanager import FontManager



'''

CookieCutter UI Styling

This styling file is formatted _very_ similarly to CSS, but below is a list of a few important notes/differences:

- rules are applied top-down, so any later conflicting rule will override an earlier rule
    - in other words, specificity is ignored here (https://developer.mozilla.org/en-US/docs/Web/CSS/Specificity)
    - if you want to override a setting, place it lower in the styling input.
    - there is no `!important` keyword

- all units are in pixels; do not specify units (ex: `px`, `in`, `em`, `%`)
    - TODO: change to allow for %?

- colors can come in various formats
    - `rgb(<r>,<g>,<b>)` or `rgba(<r>,<g>,<b>,<a>)`, where r,g,b values in 0--255; a in 0.0--1.0
    - `hsl(<h>,<s>%,<l>%)` or `hsla(<h>,<s>%,<l>%,<a>)`, where h in 0--360; s,l in 0--100 (%); a in 0.0--1.0
    - `#RRGGBB`, where r,g,b in 00--FF
    - or by colorname

- selectors
    - all element types must be explicitly specified, except at beginning or when following a `>`; use `*` to match any type
        - ex: `elem1 .class` is the same as `elem1.class` and `elem1 . class`, but never `elem1 *.class`
    - only `>` and ` ` combinators are implemented

- spaces,tabs,newlines are completely ignored except to separate tokens

- numbers cannot begin with a decimal. instead, start with `0.` (ex: use `0.014` not `.014`)

- background has only color (no images)
    - `background: <background-color>`

- border has no style (such as dotted or dashed) and has uniform width (no left, right, top, bottom widths)
    - `border: <border-width> <border-color>`

- setting `width` or `height` will set both of the corresponding `min-*` and `max-*` properties

- `min-*` and `max-*` are used as suggestions to the UI system; they will not be strictly followed


Things to think about:

- `:scrolling` pseudoclass, for when we're scrolling through content
- `:focus` pseudoclass, for when textbox has focus, or changing a number input
- add drop shadow (draws in the margins?) and outline (for focus viz)
- allow for absolute, fixed, relative positioning?
- allow for float boxes?
- z-index (how is this done?  nodes of render tree get placed in rendering list?)
- ability to be drag-able?


'''


token_rules = [
    ('ignore', skip_token, [
        r'[ \t\r\n]',           # ignoring any tab, space, newline
        r'/[*][\s\S]*?[*]/',    # multi-line comments
    ]),
    ('special', convert_token_to_string, [
        r'[-.:*>{},();]',
    ]),
    ('key', convert_token_to_string, [
        r'display',
        r'background(-color)?',
        r'margin(-(left|right|top|bottom))?',
        r'padding(-(left|right|top|bottom))?',
        r'border(-(width|radius))?',
        r'border(-(left|right|top|bottom))?-color',
        r'((min|max)-)?width',
        r'((min|max)-)?height',
        r'cursor',
        r'overflow',
        r'position',
        r'flex(-(direction|wrap|grow|shrink|basis))?',
        r'justify-content|align-content|align-items',
    ]),
    ('value', convert_token_to_string, [
        r'auto',
        r'inline|block|none|flexbox',           # display
        r'visible|hidden|scroll|auto',          # overflow
        r'static|fixed|sticky',                 # position
        r'column|row',                          # flex-direction
        r'nowrap|wrap',                         # flex-wrap
        r'flex-start|flex-end|center|stretch',  # justify-content, align-content, align-items
    ]),
    ('cursor', convert_token_to_cursor, [
        r'default|auto|initial',
        r'none|wait|grab|crosshair|pointer',
        r'text',
        r'e-resize|w-resize|ew-resize',
        r'n-resize|s-resize|ns-resize',
        r'all-scroll',
    ]),
    ('color', convert_token_to_color, [
        r'rgb\( *(?P<red>\d+) *, *(?P<green>\d+) *, *(?P<blue>\d+) *\)',
        r'rgba\( *(?P<red>\d+) *, *(?P<green>\d+) *, *(?P<blue>\d+) *, *(?P<alpha>\d+(\.\d+)?) *\)',
        r'hsl\( *(?P<hue>\d+) *, *(?P<saturation>\d+)% *, *(?P<lightness>\d+)% *\)',
        r'hsla\( *(?P<hue>\d+) *, *(?P<saturation>\d+)% *, *(?P<lightness>\d+)% *, *(?P<alpha>\d+(\.\d+)?) *\)',
        r'#[a-fA-F0-9]{6}',

        r'transparent',

        # https://www.quackit.com/css/css_color_codes.cfm
        r'indianred|lightcoral|salmon|darksalmon|lightsalmon|crimson|red|firebrick|darkred',        # reds
        r'pink|lightpink|hotpink|deeppink|mediumvioletred|palevioletred',                           # pinks
        r'coral|tomato|orangered|darkorange|orange',                                                # oranges
        r'gold|yellow|lightyellow|lemonchiffon|lightgoldenrodyellow|papayawhip|moccasin',           # yellows
        r'peachpuff|palegoldenrod|khaki|darkkhaki',                                                 #   ^
        r'lavender|thistle|plum|violet|orchid|fuchsia|magenta|mediumorchid|mediumpurple',           # purples
        r'blueviolet|darkviolet|darkorchid|darkmagenta|purple|rebeccapurple|indigo',                #   ^
        r'mediumslateblue|slateblue|darkslateblue',                                                 #   ^
        r'greenyellow|chartreuse|lawngreen|lime|limegreen|palegreen|lightgreen',                    # greens
        r'mediumspringgreen|springgreen|mediumseagreen|seagreen|forestgreen|green',                 #   ^
        r'darkgreen|yellowgreen|olivedrab|olive|darkolivegreen|mediumaquamarine',                   #   ^
        r'darkseagreen|lightseagreen|darkcyan|teal',                                                #   ^
        r'aqua|cyan|lightcyan|paleturquoise|aquamarine|turquoise|mediumturquoise',                  # blues
        r'darkturquoise|cadetblue|steelblue|lightsteelblue|powderblue|lightblue|skyblue',           #   ^
        r'lightskyblue|deepskyblue|dodgerblue|cornflowerblue|royalblue|blue|mediumblue',            #   ^
        r'darkblue|navy|midnightblue',                                                              #   ^
        r'cornsilk|blanchedalmond|bisque|navajowhite|wheat|burlywood|tan|rosybrown',                # browns
        r'sandybrown|goldenrod|darkgoldenrod|peru|chocolate|saddlebrown|sienna|brown|maroon',       #   ^
        r'white|snow|honeydew|mintcream|azure|aliceblue|ghostwhite|whitesmoke|seashell',            # whites
        r'beige|oldlace|floralwhite|ivory|antiquewhite|linen|lavenderblush|mistyrose',              #   ^
        r'gainsboro|lightgray|lightgrey|silver|darkgray|darkgrey|gray|grey|dimgray|dimgrey',        # grays
        r'lightslategray|lightslategrey|slategray|slategrey|darkslategray|darkslategrey|black',     #   ^
    ]),
    ('pseudoclass', convert_token_to_string, [
        r'hover',
        r'active',
    ]),
    ('num', convert_token_to_number, [
        r'-?((\d+)|(\d*\.\d+))',
    ]),
    ('id', convert_token_to_string, [
        r'[a-zA-Z_][a-zA-Z_-]*',
    ]),
]


class UI_Style_Declaration:
    '''
    CSS Declarations are of the form:

        property: value;
        property: val0 val1 ...;

    Value is either a single token or a tuple if the token immediately following the first value is not ';'.

        ex: border: 1 5;

    '''

    def __init__(self, lexer):
        self.property = lexer.match_t_v('key')
        lexer.match_v_v(':')
        v = lexer.next_v();
        if lexer.peek_v() == ';':
            self.value = v
        else:
            # tuple!
            l = [v]
            while lexer.peek_v() not in {';', '}'}:
                l.append(lexer.next_v())
            self.value = tuple(l)
        lexer.match_v_v(';')
    def __str__(self):
        return '<UI_Style_Declaration "%s=%s">' % (self.property, str(self.value))
    def __repr__(self): return self.__str__()


class UI_Style_RuleSet:
    '''
    CSS RuleSets are in the form shown below.
    Note: each `property: value;` is a UI_Style_Declaration

        selector {
            property0: value;
            property1: val0 val1 val2;
            ...
        }

    '''

    def __init__(self, lexer):
        def elem():
            if lexer.peek_v() in {'.','#',':'}:
                e = '*'
            elif lexer.peek_v() == '*':
                e = lexer.match_v_v('*')
            else:
                e = lexer.match_t_v('id') #{'id','*'})
            while lexer.peek_v() in {'.','#',':'}:
                if lexer.peek_v() in {'.','#'}:
                    e += lexer.match_v_v({'.','#'})
                    e += lexer.match_t_v('id')
                else:
                    e += lexer.match_v_v(':')
                    e += lexer.match_t_v('pseudoclass')
            return e

        # get selector
        self.selectors = [[]]
        while lexer.peek_v() != '{':
            if lexer.peek_v() == '*' or 'id' in lexer.peek_t():
                self.selectors[-1].append(elem())
            elif lexer.peek_v() in {'>'}:
                # TODO: handle + and ~ combinators?
                sibling = lexer.match_v_v({'>'})
                self.selectors[-1].append(sibling)
                self.selectors[-1].append(elem())
            elif lexer.peek_v() == ',':
                lexer.match_v_v(',')
                self.selectors.append([])
            else:
                assert False, 'expected selector or "{" but saw "%s" on line %d' % (lexer.peek_v(),lexer.current_line())

        # get declarations list
        self.decllist = []
        lexer.match_v_v('{')
        while lexer.peek_v() != '}':
            while lexer.peek_v() == ';': lexer.match_v_v(';')
            if lexer.peek_v() == '}': break
            self.decllist.append(UI_Style_Declaration(lexer))
        lexer.match_v_v('}')

    def __str__(self):
        s = ', '.join(' '.join(selector) for selector in self.selectors)
        if not self.decllist: return '<UI_Style_RuleSet "%s">' % (s,)
        return '<UI_Style_RuleSet "%s"\n%s\n>' % (s,'\n'.join('  '+l for d in self.decllist for l in str(d).splitlines()))
    def __repr__(self): return self.__str__()

    def match(self, selector):
        # returns true if self.selector matches passed selector
        def splitsel(sel):
            p = {'type':'', 'class':[], 'id':'', 'pseudo':[]}
            transition = {'.':'class', '#':'id', ':':'pseudo'}
            v,m = '','type'
            for c in sel:
                if c in '.:#':
                    if type(p[m]) is list: p[m].append(v)
                    else: p[m] = v
                    v,m = '',transition[c]
                else:
                    v += c
            if type(p[m]) is list: p[m].append(v)
            else: p[m] = v
            return p
        def msel(sa, sb, cont=True):
            if len(sa) == 0: return True
            if len(sb) == 0: return False
            a0,b0 = sa[0],sb[0]
            if b0 == '>': return msel(sa, sb[1:], cont=False)
            ap,bp = splitsel(a0),splitsel(b0)
            m = True
            m &= bp['type'] == '*' or ap['type'] == bp['type']
            m &= bp['id'] == '' or ap['id'] == bp['id']
            m &= all(c in ap['class'] for c in bp['class'])
            m &= all(c in ap['pseudo'] for c in bp['pseudo'])
            if m and msel(sa[1:], sb[1:]): return True
            if cont: return msel(sa, sb[1:])
            return False
        return any(msel(selector, sel) for sel in self.selectors)


class UI_Styling:
    '''
    Parses input to a CSSOM-like object
    '''

    @staticmethod
    def from_file(filename):
        lines = open(filename, 'rt').read()
        return UI_Styling(lines)

    def __init__(self, lines):
        charstream = Parse_CharStream(lines)            # convert input into character stream
        lexer = Parse_Lexer(charstream, token_rules)    # tokenize the character stream
        self.rules = []
        while lexer.peek_t() != 'eof':
            self.rules.append(UI_Style_RuleSet(lexer))

    def __str__(self):
        if not self.rules: return '<UI_Styling>'
        return '<UI_Styling\n%s\n>' % ('\n'.join('  '+l for r in self.rules for l in str(r).splitlines()))

    def get_decllist(self, selector):
        return [d for rule in self.rules if rule.match(selector) for d in rule.decllist]

    @staticmethod
    def _trbl_split(v):
        if type(v) is not tuple: return (v, v, v, v)
        if   len(v) == 1: return (v[0], v[0], v[0], v[0])
        elif len(v) == 2: return (v[0], v[1], v[0], v[1])
        elif len(v) == 3: return (v[0], v[1], v[2], v[1])
        else:             return (v[0], v[1], v[2], v[3])

    @staticmethod
    def _expand_declarations(decls):
        decllist = {}
        for decl in decls:
            p,v = decl.property, decl.value
            if p in {'margin','padding'}:
                vals = UI_Styling._trbl_split(v)
                decllist['%s-top'%p]    = vals[0]
                decllist['%s-right'%p]  = vals[1]
                decllist['%s-bottom'%p] = vals[2]
                decllist['%s-left'%p]   = vals[3]
            elif p == 'border':
                if type(v) is not tuple: v = (v,)
                decllist['border-width'] = v[0]
                if len(v) > 1:
                    vals = UI_Styling._trbl_split(v[1:])
                    decllist['border-top-color']    = vals[0]
                    decllist['border-right-color']  = vals[1]
                    decllist['border-bottom-color'] = vals[2]
                    decllist['border-left-color']   = vals[3]
            elif p == 'border-color':
                vals = UI_Styling._trbl_split(v)
                decllist['border-top-color']    = vals[0]
                decllist['border-right-color']  = vals[1]
                decllist['border-bottom-color'] = vals[2]
                decllist['border-left-color']   = vals[3]
            elif p == 'background':
                decllist['background-color'] = v
            elif p == 'width':
                decllist['min-width'] = v
                decllist['max-width'] = v
            elif p == 'height':
                decllist['min-height'] = v
                decllist['max-height'] = v
            else:
                decllist[p] = v
        # filter out properties with `initial` values
        decllist = { k:v for (k,v) in decllist.items() if v != 'initial' }
        return decllist

    def compute_style(self, selector, initial_styling, override_styling):
        # collect all the declarations that apply to selector
        full = []
        if False:
            # Cascading not implemented correctly (only add prop+vals that are inherited)
            # see: https://developer.mozilla.org/en-US/docs/Learn/CSS/Introduction_to_CSS/Cascade_and_inheritance
            # see: https://developer.mozilla.org/en-US/docs/Web/CSS/Reference
            selector_parts = selector.split(' ')
            for i in range(len(selector_parts)):
                sub_selector = ' '.join(selector_parts[:i+1])
                full += [d for rule in self.rules if rule.match(sub_selector) for d in rule.decllist]
        else:
            full += self.get_decllist(selector)
        if override_styling: full += override_styling.get_decllist(selector)

        # expand and override declarations
        init_decllist = self._expand_declarations(initial_styling.get_decllist(selector)) if initial_styling else {}
        full_decllist = self._expand_declarations(full)

        # apply initial
        decllist = init_decllist
        decllist.update(full_decllist)
        return decllist



