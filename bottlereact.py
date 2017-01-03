# 
# MIT License
# 
# Copyright (c) 2016 Derek Anderson
# https://github.com/keredson/bottle-react
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# 

from __future__ import print_function

import collections, json, os, re, shutil, subprocess
try:
  import bottle
  import react.jsx
except ImportError:
  pass # need to not error here for setup.py to get the version


__version__='0.2.0'



__ALL__ = ['BottleReact','__version__']
BABEL_CORE = 'https://cdnjs.cloudflare.com/ajax/libs/babel-core/5.8.24/browser.min.js'

class BottleReact(object):
 
  def __init__(self, app, prod=False, jsx_path='jsx', asset_path='assets', work_path='/tmp/bottlereact', verbose=None):
    self.app = app
    self.prod = prod
    self.verbose = not prod if verbose is None else verbose
    self.jsx_path = jsx_path
    self.hashed_path = os.path.join(work_path, 'hashed-assets')
    self.genned_path = os.path.join(work_path, 'genned-assets')
    self.asset_path = asset_path
    self._reqs = collections.defaultdict(list)
    
    if not os.path.isdir(self.jsx_path):
      raise Exception('Directory %s not found - please create it or set the jsx_path parameter.' % repr(self.jsx_path))

    if self.prod:
      @app.get('/__br_assets__/<path:path>')
      def _serve__br_assets(path):
        response = bottle.static_file(path, root=self.hashed_path)
        response.set_header("Cache-Control", "public, max-age=31536000") # one year
        return response
    else:
      @app.get('/__br_assets__/<path:path>')
      def _serve__br_assets(path):
        if path=='bottlereact.js':
          bottle.response.set_header('Content-Type', 'text/javascript')
          return bottlereact_js
        elif path.endswith('.jsx'):
          bottle.response.set_header('Content-Type', 'text/babel')
          return bottle.static_file(path, root=self.jsx_path)
        else:
          return bottle.static_file(path, root=self.asset_path)


    # load all JSX files
    for fn in sorted(os.listdir(self.jsx_path)):
      if not fn.endswith('.jsx'): continue
      with open(os.path.join(self.jsx_path, fn), 'r') as f:
        for line in f.readlines():
          if 'React.createClass' in line:
            if '=' not in line: continue
            react_class = line.split('=')[0].strip().split()[-1]
            if self.verbose: print('found react class', react_class, 'in', fn)
            self.__dict__[react_class] = _ReactClass(react_class, fn)
          if 'extends React.Component' in line:
            if 'class' not in line: continue
            react_class = line[line.find('class')+5:line.find('extends')].strip()
            if self.verbose: print('found es6 react class', react_class, 'in', fn)
            self.__dict__[react_class] = _ReactClass(react_class, fn)
          if line.startswith('// require '):
            req = line[len('// require '):].strip()
            self._reqs[fn].append(req)

    self._fn2hash = {}
    if prod:
      transformer = react.jsx.JSXTransformer()
    
      # confirm tmp paths exist
      for path in [self.hashed_path, self.genned_path]:
        if not os.path.isdir(path):
          os.makedirs(path)

      # unfiltered assets
      self._fn2hash = self._load_fn_to_hash_mapping(self.asset_path, '*', dest=self.hashed_path)

      # jsx assets
      jsx2hash = self._load_fn_to_hash_mapping(self.jsx_path, '*.jsx', dest=self.genned_path)
      for jsx_fn, jsx_hashed_fn in jsx2hash.items():
        jsx_converted_fn = os.path.join(self.genned_path, jsx_hashed_fn[:-1])
        if not os.path.exists(jsx_converted_fn) or os.stat(jsx_converted_fn).st_size==0:
          transformer.transform(os.path.join(self.genned_path, jsx_hashed_fn), js_path=jsx_converted_fn)

      # bottlereact.js
      with open(os.path.join(self.genned_path, 'bottlereact.js'),'w') as f:
        f.write(bottlereact_js)
        f.write('\nbottlereact._assets = ')
        json.dump(self._fn2hash, f)
        f.write(';\n')

      # add the jsx files (which are only used server side, so not written to 'bottlereact.js')
      jsxjs2hash = self._load_fn_to_hash_mapping(self.genned_path, '*.js', dest=self.hashed_path)
      for k,v in jsx2hash.items():
        self._fn2hash[k] = jsxjs2hash[v[:-1]]

      # get the hashed name of 'bottlereact.js'
      self._fn2hash['bottlereact.js'] = jsxjs2hash['bottlereact.js']

      if self.verbose: print('_fn2hash', self._fn2hash)

    if self.verbose: print('_reqs', self._reqs)


  def _build_dep_list(self, files):
    files = set(files)
    deps = collections.OrderedDict()
    while len(files):
      fn = files.pop()
      if fn not in deps:
        deps[fn] = True
        for fn2 in self._reqs[fn]:
          files.add(fn2)
    deps['bottlereact.js'] = True
    if not self.prod:
      deps[BABEL_CORE] = True
    return list(reversed(deps.keys()))

  def get_asset_path(self, fn):
    return '/__br_assets__/%s' % self._fn2hash.get(fn, fn)

  def _load_fn_to_hash_mapping(self, path, selector, dest=None):
    path = os.path.abspath(path)
    ret = {}
    if not os.path.isdir(path): return ret
    if not os.listdir(path): return ret
    output = subprocess.check_output(['find %s -name \'%s\' -type f -print0 | xargs -0 -n 100 sha256sum' % (path, selector)], shell=True)
    for line in output.decode("utf8").split('\n'):
      line = line.strip()
      if not line: continue
      hsh, fn = line.split('  ', 1)
      hsh = hsh[:16]
      base_fn = os.path.relpath(fn, path)
      hashed_fn = '%s-%s' % (hsh, base_fn.replace('/','__'))
      ret[base_fn] = hashed_fn
      tmp_fn = os.path.join(dest, hashed_fn)
      if not os.path.exists(tmp_fn):
        shutil.copy(fn, tmp_fn)
        if self.verbose: print('copied', fn, 'to', tmp_fn)
    return ret

  def render_html(self, react_node, **kwargs):
    template = kwargs.get('kwargs', 'bottlereact')
    react_js = react_node.to_javascript()
    deps = self._build_dep_list(react_node.get_js_files())
    classes = _make_json_string_browser_safe(json.dumps(list(react_node.get_react_classes())))
    deps_html = ['']
    for dep in deps:
      path = dep if dep.startswith('http://') or dep.startswith('https://') else self.get_asset_path(dep)
      if path.endswith('.css'):
        deps_html.append('<link href="%s" rel="stylesheet">' % bottle.html_escape(path))
      elif path.endswith('.js'):
        deps_html.append('<script src="%s"></script>' % bottle.html_escape(path))
      elif path.endswith('.jsx'):
        deps_html.append('<script type="text/babel" src="%s"></script>' % bottle.html_escape(path))
      else: # assume javascript
        deps_html.append('<script src="%s"></script>' % bottle.html_escape(path))
    deps_html = '\n'.join(deps_html)
    init = '''
    <script>
      bottlereact._onLoad(%s, function() {
        ReactDOM.render(
          %s,
          document.getElementById('__body__')
        );
      });
    </script>
    ''' % (classes, react_js)
    if 'title' not in kwargs: kwargs['title'] = 'bottle-react - https://github.com/keredson/bottle-react'
    kwargs.update({
      'deps': deps_html,
      'init': init,
      'prod': self.prod,
      'asset_path': self.get_asset_path,
    })
    return bottle.template(template, **kwargs)


def _make_json_string_browser_safe(s):
  return s.replace('</', '<\\/')


class _ReactNode(object):
  def __init__(self, react_class, props, children):
    self.react_class = react_class
    self.props = self.react_class.default_props()
    if props: self.props.update(props)
    self.children = children if children else []

  def get_js_files(self, files=None):
    if files is None: files = set()
    files.add(self.react_class.fn)
    for child in self.children:
      if isinstance(child, _ReactNode):
        child.get_js_files(files)
    return files

  def get_react_classes(self, classes=None):
    if classes is None: classes = set()
    classes.add(self.react_class.name)
    for child in self.children:
      if isinstance(child, _ReactNode):
        child.get_react_classes(classes)
    return classes

  def to_javascript(self):
    ret = [
      'React.createElement(',
        'bottlereact.%s' % self.react_class.name, ',',
        _make_json_string_browser_safe(json.dumps(self.props)), ',',
    ]
    ret.append('[')
    count = len(ret)
    for child in self.children:
      if isinstance(child, _ReactNode):
        ret.append(child.to_javascript())
      elif isinstance(child, basestring):
        ret.append(_make_json_string_browser_safe(json.dumps(child)))
      elif child is None:
        pass
      else:
       raise Exception('unknown child %s type %s' % (repr(child), child.__class__))
      ret.append(',')
    if len(ret) > count: del ret[-1] # delete the last comma
    ret.append(']')
    ret.append(')')
    return ''.join(ret)


class _ReactClass(object):
  def __init__(self, name, fn):
    if not re.match("^[A-Za-z][_a-zA-Z0-9]*$", name):
      raise Exception('%s is not a valid javascript identifier' % name)
    self.name = name
    self.fn = fn
    self.default_props = dict
    try:
      import jsx_props
      self.default_props = jsx_props.__dict__.get('init%s'%name, dict)
    except ImportError:
      pass
  def __call__(self, props=None, children=None):
    '''
      props must be a dict or None
      children must be a list of ReactNode objects, or None
    '''
    return _ReactNode(self, props, children)



bottlereact_js = '''
var pending_deps = [];
var checkDeps = function() {
  for (var i=0; i<pending_deps.length; ++i) {
    var deps = pending_deps[i][0];
    var all_deps_met = true;
    for (var j=0; j<deps.length; ++j) {
      var dep = deps[j];
      all_deps_met &= (typeof bottlereact[dep] != 'undefined');
    }
    if (all_deps_met) {
      var f = pending_deps[i][1];
      pending_deps.splice(i,1);
      --i;
      f();
    }
  }
};

function toArray(obj) {
    var l = obj.length, out = [];
    for(var i=0; i<obj.length; ++i) out[i] = obj[i];
    return out;
}

bottlereact = {

  _register: function(name, cls) {
    bottlereact[name] = cls;
    checkDeps();
  },
  
  _onLoad: function(deps, f) {
    pending_deps.push([deps, f]);
    checkDeps();
  },
  
  _asset_path: function(fn) {
    var hashed_fn = this._assets ? this._assets[fn] : null;
    if (hashed_fn) {
      return '/__br_assets__/'+ hashed_fn
    } else {
      return '/__br_assets__/'+ fn
    }
  },

  _addCSS: function(css) {
    var style = document.createElement('style')
    style.type = 'text/css'
    style.innerHTML = css;
    document.getElementsByTagName('head')[0].appendChild(style)
  },
  
  _cloneWithProps: function(children, props) {
    var clones =  React.Children.map(children, function(child) {
      return React.cloneElement(child, props);
    });
    return clones;
  },

}
'''

