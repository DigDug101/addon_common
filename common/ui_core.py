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

import re

from .ui_styling import UI_Styling
from .drawing import ScissorStack

from .globals import Globals
from .decorators import debug_test_call, blender_version_wrapper
from .maths import Vec2D, Color, mid, Box2D, Size2D
from .shaders import Shader


class UI_Draw:
    _initialized = False
    _stylesheet = None

    @blender_version_wrapper('<=', '2.79')
    def init_draw(self):
        # TODO: test this implementation!
        assert False, 'function implementation not tested yet!!!'
        # UI_Draw._shader = Shader.load_from_file('ui', 'uielement.glsl', checkErrors=True)
        # sizeOfFloat, sizeOfInt = 4, 4
        # pos = [(0,0),(1,0),(1,1),  (0,0),(1,1),(0,1)]
        # count = len(pos)
        # buf_pos = bgl.Buffer(bgl.GL_FLOAT, [count, 2], pos)
        # vbos = bgl.Buffer(bgl.GL_INT, 1)
        # bgl.glGenBuffers(1, vbos)
        # vbo_pos = vbos[0]
        # bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, vbo_pos)
        # bgl.glBufferData(bgl.GL_ARRAY_BUFFER, count * 2 * sizeOfFloat, buf_pos, bgl.GL_STATIC_DRAW)
        # bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, 0)
        # en = UI_Draw._shader.enable
        # di = UI_Draw._shader.disable
        # eva = UI_Draw._shader.vertexAttribPointer
        # dva = UI_Draw._shader.disableVertexAttribArray
        # a = UI_Draw._shader.assign
        # def draw(left, top, width, height, style):
        #     nonlocal vbo_pos, count, en, di, eva, dva, a
        #     en()
        #     a('left',   left)
        #     a('top',    top)
        #     a('right',  left+width-1)
        #     a('bottom', top-height+1)
        #     a('margin_left',   style.get('margin-left', 0))
        #     a('margin_right',  style.get('margin-right', 0))
        #     a('margin_top',    style.get('margin-top', 0))
        #     a('margin_bottom', style.get('margin-bottom', 0))
        #     a('border_width',        style.get('border-width', 0))
        #     a('border_radius',       style.get('border-radius', 0))
        #     a('border_left_color',   style.get('border-left-color', (0,0,0,1)))
        #     a('border_right_color',  style.get('border-right-color', (0,0,0,1)))
        #     a('border_top_color',    style.get('border-top-color', (0,0,0,1)))
        #     a('border_bottom_color', style.get('border-bottom-color', (0,0,0,1)))
        #     a('background_color', style.get('background-color', (0,0,0,1)))
        #     eva(vbo_pos, 'pos', 2, bgl.GL_FLOAT)
        #     bgl.glDrawArrays(bgl.GL_TRIANGLES, 0, count)
        #     dva('pos')
        #     di()
        # UI_Draw._draw = draw

    @blender_version_wrapper('>=', '2.80')
    def init_draw(self):
        import gpu
        from gpu_extras.batch import batch_for_shader

        vertex_positions = [(0,0),(1,0),(1,1),  (1,1),(0,1),(0,0)]
        vertex_shader, fragment_shader = Shader.parse_file('uielement.glsl', includeVersion=False)
        shader = gpu.types.GPUShader(vertex_shader, fragment_shader)
        batch = batch_for_shader(shader, 'TRIS', {"pos": vertex_positions})
        get_pixel_matrix = Globals.drawing.get_pixel_matrix
        def_color = (0,0,0,1)

        def update():
            nonlocal shader, get_pixel_matrix
            shader.bind()
            shader.uniform_float("uMVPMatrix", get_pixel_matrix())

        def draw(left, top, width, height, style):
            nonlocal shader, batch, def_color
            shader.bind()
            shader.uniform_float('left',   left)
            shader.uniform_float('top',    top)
            shader.uniform_float('right',  left+width-1)
            shader.uniform_float('bottom', top-height+1)
            shader.uniform_float('margin_left',   style.get('margin-left',   0))
            shader.uniform_float('margin_right',  style.get('margin-right',  0))
            shader.uniform_float('margin_top',    style.get('margin-top',    0))
            shader.uniform_float('margin_bottom', style.get('margin-bottom', 0))
            shader.uniform_float('border_width',        style.get('border-width',  0))
            shader.uniform_float('border_radius',       style.get('border-radius', 0))
            shader.uniform_float('border_left_color',   style.get('border-left-color',   def_color))
            shader.uniform_float('border_right_color',  style.get('border-right-color',  def_color))
            shader.uniform_float('border_top_color',    style.get('border-top-color',    def_color))
            shader.uniform_float('border_bottom_color', style.get('border-bottom-color', def_color))
            shader.uniform_float('background_color', style.get('background-color', def_color))
            batch.draw(shader)

        UI_Draw._update = update
        UI_Draw._draw = draw

    def __init__(self):
        if not UI_Draw._initialized:
            self.init_draw()
            UI_Draw._initialized = True

    @staticmethod
    def load_stylesheet(path):
        UI_Draw._stylesheet = UI_Styling.from_file(path)
    @property
    def stylesheet(self):
        return self._stylesheet

    def update(self):
        ''' only need to call once every redraw '''
        UI_Draw._update()

    def draw(self, left, top, width, height, style):
        UI_Draw._draw(left, top, width, height, style)

ui_draw = Globals.set(UI_Draw())



'''
UI_Document manages UI_Body

example hierarchy of UI

- UI_Body: (singleton!)
    - UI_Dialog: tooltips
    - UI_Dialog: menu
        - help
        - about
        - exit
    - UI_Dialog: tools
        - UI_Button: toolA
        - UI_Button: toolB
        - UI_Button: toolC
    - UI_Dialog: options
        - option1
        - option2
        - option3


clean call order

- compute_style (only if style is dirty)
    - call compute_style on all children
    - dirtied by change in style, ID, class, pseudoclass, parent, or ID/class/pseudoclass of an ancestor
    - cleaning style dirties size
- compute_preferred_size (only if size or content are dirty)
    - determines min, max, preferred size for element (override in subclass)
    - for containers that resize based on children, whether wrapped (inline), list (block), or table, ...
        - 

'''


class UI_Core_Utils:
    @staticmethod
    def defer_dirty(properties=None, parent=True, children=False):
        ''' prevents dirty propagation until the wrapped fn has finished '''
        def wrapper(fn):
            def wrapped(self, *args, **kwargs):
                self._defer_dirty = True
                ret = fn(self, *args, **kwargs)
                self._defer_dirty = False
                self.dirty(properties, parent=parent, children=children)
                return ret
            return wrapped
        return wrapper


class UI_Core(UI_Core_Utils):
    selector_type = ''  # filled in automatically by __init__
    default_style = ''  # override this is subclass definition

    @classmethod
    def init_default_style(cls):
        s = cls.default_style
        if type(s) is UI_Styling: return
        if type(s) is dict: s = ['%s:%s' % (k,v) for (k,v) in s.items()]
        if type(s) is list: s = ';'.join(s)
        cls.default_style = UI_Styling('*{%s;}' % s)

    def __init__(self, parent=None, id=None, classes=None, style=None):
        assert type(self) is not UI_Core, 'DO NOT INSTANTIATE DIRECTLY!'

        self.init_default_style()

        tn = type(self).__name__.lower()
        assert tn.startswith('ui_'), '%s has unhandled type name' % (type(self).__name__)
        self.selector_type = tn[3:]     # remove 'UI_' at start

        self._parent = None             # set in parent.append_child(self) below
        self._children = []             # list of all children
        self._selector = None           # full selector of self, set in compute_style()
        self._id = None                 # unique identifier for self
        self._classes = set()           # TODO: should order matter here? (make list)
        self._pseudoclasses = set()     # TODO: should order matter here? (make list)
        self._custom_style = None       # custom style UI_Style for self
        self._style_str = ''            # custom style string for self
        self._is_visible = False        # indicates if self is visible, set in compute_style()
        self._computed_styles = None    # computed style UI_Style after applying all styling

        # TODO: REPLACE WITH BETTER PROPERTIES AND DELETE!!
        self._preferred_width, self._preferred_height = 0,0
        self._content_width, self._content_height = 0,0
        self._l, self._t, self._w, self._h = 0,0,0,0

        # various sizes and boxes (set in self._position), used for layout and drawing
        self._preferred_size = Size2D()                         # computed preferred size, set in self._layout, used as suggestion to parent
        self._pref_content_size = Size2D()                      # size of content
        self._pref_full_size = Size2D()                         # _pref_content_size + margins + border + padding
        self._box_draw = Box2D(topleft=(0,0), size=(-1,-1))     # where UI will be drawn (restricted by parent)
        self._box_full = Box2D(topleft=(0,0), size=(-1,-1))     # where UI would draw if not restricted (offset for scrolling)

        self._dirty_properties = {              # set of dirty properties, add through self.dirty to force propagation of dirtiness
            'style',                            # force recalculations of style
            'size',                             # force recalculations of size
            'content',                          # content of self has changed
        }
        self._dirty_propagation = {             # contains deferred dirty propagation for parent and children; parent will be dirtied later
            'defer':    False,                  # set to True to defer dirty propagation (useful when many changes are occurring)
            'parent':   set(),                  # set of properties to dirty for parent
            'children': set(),                  # set of properties to dirty for children
        }
        self._defer_clean = False               # set to True to defer cleaning (useful when many changes are occurring)

        self.style = style
        self.id = id
        self.classes = classes

        if parent: parent.append_child(self)    # note: parent.append_child(self) will set self._parent

        self._defer_recalc = False
        self.dirty()

    def dirty(self, properties=None, parent=True, children=False):
        if properties is None: properties = {'style', 'size', 'content'}
        elif type(properties) is str: properties = {properties}
        elif type(properties) is list: properties = set(properties)
        self._dirty_properties |= properties
        if parent: self._dirty_propagation['parent'] |= properties
        if children: self._dirty_propagation['children'] |= properties
        self.propagate_dirtiness()

    @property
    def is_dirty(self):
        return bool(self._dirty_properties) or bool(self._dirty_propagation['parent']) or bool(self._dirty_propagation['children'])

    def propagate_dirtiness(self):
        if self._dirty_propagation['defer']: return
        if self._dirty_propagation['parent']:
            if self._parent:
                self._parent.dirty(self._dirty_propagation['parent'], parent=True, children=False)
            self._dirty_propagation['parent'].clear()
        if self._dirty_propagation['children']:
            for child in self._children:
                child.dirty(self._dirty_propagation['children'], parent=False, children=True)
            self._dirty_propagation['children'].clear()

    @property
    def defer_dirty_propagation(self):
        return self._dirty_propagation['defer']
    @defer_dirty_propagation.setter
    def defer_dirty_propagation(self, v):
        self._dirty_propagation['defer'] = bool(v)
        self.propagate_dirtiness()

    def clean(self):
        '''
        No need to clean if
        - already clean,
        - possibly more dirtiness to propagate,
        - if deferring cleaning.
        '''
        if not self.is_dirty or self._defer_clean: return

        # clean various properties
        self._compute_style()
        self._compute_content()
        self._compute_preferred_size()

    def _compute_style(self):
        if self._defer_clean: return
        if 'style' not in self._dirty_properties: return

        self.defer_dirty_propagation = True

        # rebuild up full selector
        sel_parent = [] if not self._parent else self._parent._selector
        sel_type = self.selector_type
        sel_id = '#%s' % self._id if self._id else ''
        sel_cls = ''.join('.%s' % c for c in self._classes)
        sel_pseudo = ''.join(':%s' % p for p in self._pseudoclasses)
        self._selector = sel_parent + [sel_type + sel_id + sel_cls + sel_pseudo]

        # compute styles applied to self based on selector
        self._computed_styles = self.default_style.compute_style(self._selector, ui_draw.stylesheet, self._custom_style)
        self._is_visible = self._computed_styles.get('display', 'auto') != 'none'

        # tell children to recompute selector
        for child in self._children: child._compute_style()

        # style changes might have changed size
        self.dirty('size')
        self._dirty_properties.discard('style')

        self.defer_dirty_propagation = False

    def _compute_content(self):
        if self._defer_clean: return
        if 'content' not in self._dirty_properties: return
        if not self.is_visible: return

        self.defer_dirty_propagation = True

        self.compute_content()
        for child in self._children: child._compute_content()

        # content changes might have changed size
        self.dirty('size')
        self._dirty_properties.discard('content')

        self.defer_dirty_propagation = False

    def _compute_preferred_size(self):
        if self._defer_clean: return
        if 'size' not in self._dirty_properties: return
        if not self.is_visible: return

        self.defer_dirty_propagation = True

        self._content_width, self._content_height = 0, 0
        for child in self._children: child._compute_preferred_size()
        self.compute_children_content_size()

        self.defer_dirty_propagation = False


    @property
    def children(self):
        return list(self._children)
    def append_child(self, child):
        assert child
        assert child not in self._children, 'attempting to add existing child?'
        if child._parent:
            child._parent.delete_child(child)
        self._children.append(child)
        child.dirty()
        self.dirty()
    def delete_child(self, child):
        assert child
        assert child in self._children, 'attempting to delete child that does not exist?'
        self._children.remove(child)
        child._parent = None
        child.dirty()
        self.dirty('content')
    @UI_Core_Utils.defer_dirty()
    def clear_children(self):
        for child in list(self._children):
            self.delete_child(child)

    @property
    def style(self):
        return self._style_str
    @style.setter
    def style(self, style):
        self._style_str = str(style or '')
        self._custom_style = UI_Styling('*{%s;}' % self._style_str)
        self.dirty()
    def add_style(self, style):
        self.style = '%s;%s' % (self.style, str(style or ''))

    @property
    def id(self):
        return self._id
    @id.setter
    def id(self, nid):
        nid = '' if nid is None else nid.strip()
        if self._id == nid: return
        self._id = id
        self.dirty(parent=True, children=True) # changing id can affect children styles!

    @property
    def classes(self):
        return ' '.join(self._classes)
    @classes.setter
    def classes(self, classes):
        classes = set(c for c in classes.split(' ') if c) if classes else set()
        if classes == self._classes: return
        self._classes = classes
        self.dirty(parent=True, children=True) # changing classes can affect children styles!
    def add_class(self, cls):
        if cls in self._classes: return
        self._classes.add(cls)
        self.dirty(parent=True, children=True) # changing classes can affect children styles!
    def del_class(self, cls):
        if cls not in self._classes: return
        self._classes.discard(cls)
        self.dirty(parent=True, children=True) # changing classes can affect children styles!

    @property
    def pseudoclasses(self):
        return set(self._pseudoclasses)
    def clear_pseudoclass(self):
        if not self._pseudoclasses: return
        self._pseudoclasses = set()
        self.dirty(parent=True, children=True)
    def add_pseudoclass(self, pseudo):
        if pseudo in self._pseudoclasses: return
        self._pseudoclasses.add(pseudo)
        self.dirty(parent=True, children=True)
    def del_pseudoclass(self, pseudo):
        if pseudo not in self._pseudoclasses: return
        self._pseudoclasses.discard(pseudo)
        self.dirty(parent=True, children=True)

    @property
    def is_visible(self):
        # MUST BE CALLED AFTER `compute_style()` METHOD IS CALLED!
        return self._is_visible

    def get_visible_children(self):
        # MUST BE CALLED AFTER `compute_style()` METHOD IS CALLED!
        # NOTE: returns list of children without `display:none` style.
        #       does _NOT_ mean that the child is going to be drawn
        #       (might still be clipped with scissor or `visibility:hidden` style)
        return [child for child in self._children if child.is_visible]


    def layout(self):
        # recalculates width and height

        if not self._is_dirty: return
        if self._defer_recalc: return
        if not self.is_visible: return

        # determine how much space we will need for all the content (children)
        for child in self._children: child.layout()

        display = self._computed_styles.get('display', 'block')
        if display == 'flexbox': self.layout_flexbox()
        elif display == 'block': self.layout_block()
        elif display == 'inline': self.layout_inline()
        else: pass

        min_width,  max_width  = self._get_style_num('min-width',  0), self._get_style_num('max-width',  float('inf'))
        min_height, max_height = self._get_style_num('min-height', 0), self._get_style_num('max-height', float('inf'))
        margin_top,  margin_right,  margin_bottom,  margin_left  = self._get_style_trbl('margin')
        padding_top, padding_right, padding_bottom, padding_left = self._get_style_trbl('padding')
        border_width = self._get_style_num('border-width', 0)

        self._preferred_width = (
            margin_left + border_width + padding_left +
            mid(self._get_style_num('width', self._content_width), min_width, max_width) +
            padding_right + border_width + margin_right
        )

        self._preferred_height = (
            margin_top + border_width + padding_top +
            mid(self._get_style_num('height', self._content_height), min_height, max_height) +
            padding_bottom + border_width + margin_bottom
        )

    def layout_flexbox(self):
        style = self._computed_styles
        direction = style.get('flex-direction', 'row')
        wrap = style.get('flex-wrap', 'nowrap')
        justify = style.get('justify-content', 'flex-start')
        align_items = style.get('align-items', 'flex-start')
        align_content = style.get('align-content', 'flex-start')

    def layout_block(self):
        pass

    def layout_inline(self):
        pass

    def layout_none(self):
        pass


    def position(self, left, top, width, height):
        # pos and size define where this element exists
        self._l, self._t = left, top
        self._w, self._h = width, height

        # might need to wrap text

        margin_top, margin_right, margin_bottom, margin_left = self._get_style_trbl('margin')
        padding_top, padding_right, padding_bottom, padding_left = self._get_style_trbl('padding')
        border_width = self._get_style_num('border-width', 0)
        self.position_children(
            left + margin_left + border_width + padding_left,
            top - margin_top - border_width - padding_top,
            width - margin_left - margin_right - border_width - border_width - padding_left - padding_right,
            height - margin_top - margin_bottom - border_width - border_width - padding_top - padding_bottom,
        )

    def draw(self):
        ScissorStack.push(self._l, self._t, self._w, self._h)
        #self.predraw()
        if True or ScissorStack.is_visible() and ScissorStack.is_box_visible(self._l, self._t, self._w, self._h):
            ui_draw.draw(self._l, self._t, self._w, self._h, self._computed_styles)
            for child in self._children: child.draw()
        ScissorStack.pop()

    def get_under_mouse(self, mx, my):
        if mx < self._l or mx >= self._l + self._w: return None
        if my > self._t or my <= self._t - self._h: return None
        for child in self._children:
            r = child.get_under_mouse(mx, my)
            if r: return r
        return self


    ################################################################################
    # the following methods can be overridden to create different types of UI

    ## Layout, Positioning, and Drawing
    # `self.layout_children()` should set `self._content_width` and `self._content_height` based on children.
    def compute_content(self): pass
    def compute_preferred_size(self): pass

    def compute_children_content_size(self): pass
    def layout_children(self): pass
    def position_children(self, left, top, width, height): pass
    def draw_children(self): pass

    # Event Handling
    def on_focus(self): pass             # self gains focus (:active is added)
    def on_blur(self): pass              # self loses focus (:active is removed)
    def on_keydown(self): pass           # key is pressed down
    def on_keyup(self): pass             # key is released
    def on_keypress(self): pass          # key is entered (down+up)
    def on_mouseenter(self): pass        # mouse enters self (:hover is added)
    def on_mousemove(self): pass         # mouse moves over self
    def on_mousedown(self): pass         # mouse left button is pressed down
    def on_mouseup(self): pass           # mouse left button is released
    def on_mouseclick(self): pass        # mouse left button is clicked (down+up while remaining on self)
    def on_mousedblclick(self): pass     # mouse left button is pressed twice in quick succession
    def on_mouseleave(self): pass        # mouse leaves self (:hover is removed)
    def on_scroll(self): pass            # self is being scrolled


    #####################################################################
    # HELPER FUNCTIONS
    # MUST BE CALLED AFTER `compute_stile()` METHOD IS CALLED!

    def _get_style_num(self, k, def_v, min_v=None, max_v=None):
        v = self._computed_styles.get(k, 'auto')
        if v == 'auto': v = def_v
        if min_v is not None: v = max(min_v, v)
        if max_v is not None: v = min(max_v, v)
        return v

    def _get_style_trbl(self, kb):
        t = self._get_style_num('%s-top' % kb, 0)
        r = self._get_style_num('%s-right' % kb, 0)
        b = self._get_style_num('%s-bottom' % kb, 0)
        l = self._get_style_num('%s-left' % kb, 0)
        return (t,r,b,l)
