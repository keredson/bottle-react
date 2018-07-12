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

import collections, ctypes, json, os, random, re, shutil, signal, socket, subprocess, tempfile, threading, time, urllib
try:
  import bottle
  import react.jsx
except ImportError:
  pass # need to not error here for setup.py to get the version

# python3 compat.
try:
  basestring
except NameError:
  basestring = str
try:
  from urllib.request import urlopen, urlretrieve
except ImportError:
  from urllib import urlopen, urlretrieve


__version__='16.2.3'


FLASK_AROUND = False
try:
  import flask
  FLASK_AROUND = True
except ImportError:
  pass



__ALL__ = ['BottleReact','__version__']
BABEL_CORE = 'https://cdnjs.cloudflare.com/ajax/libs/babel-standalone/6.26.0/babel.min.js'

try:
    libc = ctypes.CDLL("libc.so.6")
except OSError:
    libc = ctypes.CDLL("libc.dylib")

def set_pdeathsig(sig = signal.SIGTERM):
    def callable():
        return libc.prctl(1, sig)
    return callable


class BottleReact(object):
 
  def __init__(self, app, prod=False, jsx_path='jsx', asset_path='assets', work_path='/tmp/bottlereact', verbose=None, default_render_html_kwargs=None, harmony=True, render_server=None):
    self.app = app
    self.prod = prod
    self._render_server = render_server
    self._inited_render_server = False
    if render_server:
      self._init_render_server()
    self.verbose = not prod if verbose is None else verbose
    self.default_render_html_kwargs = default_render_html_kwargs
    self.jsx_path = jsx_path
    self.hashed_path = os.path.join(work_path, 'hashed-assets')
    self.genned_path = os.path.join(work_path, 'genned-assets')
    self.ext_path = os.path.join(work_path, 'ext-assets')
    self.asset_path = asset_path
    self.harmony = harmony
    self._reqs = collections.defaultdict(list)
    self._ctxs = {}
    self._ctx_lock = threading.Lock()
    
    if not os.path.isdir(self.jsx_path):
      raise Exception('Directory %s not found - please create it or set the jsx_path parameter.' % repr(self.jsx_path))
    
    if FLASK_AROUND and isinstance(app, flask.app.Flask):
      if self.prod:
        @app.route('/__br_assets__/<path:path>')
        def _serve__br_assets(path):
          response = flask.send_from_directory(self.hashed_path, path)
          response.headers["Cache-Control"] = "public, max-age=31536000" # one year
          return response
      else:
        @app.route('/__br_assets__/<path:path>')
        def _serve__br_assets(path):
          if path=='bottlereact.js':
            return flask.Response(BOTTLEREACT_JS, mimetype='text/javascript')
          elif path.endswith('.jsx'):
            response = flask.make_response(flask.send_from_directory(self.jsx_path, path, mimetype='text/babel'))
            return response
          else:
            return flask.send_from_directory(self.asset_path, path)
    else:
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
            return BOTTLEREACT_JS
          elif path.endswith('.jsx'):
            return bottle.static_file(path, root=self.jsx_path, mimetype='text/babel')
          else:
            return bottle.static_file(path, root=self.asset_path)


    # load all JSX files
    classes_by_file = collections.defaultdict(list)
    for fn in sorted(os.listdir(self.jsx_path)):
      if not fn.endswith('.jsx'): continue
      with open(os.path.join(self.jsx_path, fn), 'r') as f:
        for line in f.readlines():
          if 'React.createClass' in line:
            if '=' not in line: continue
            react_class = line.split('=')[0].strip().split()[-1]
            classes_by_file[fn].append(react_class)
            self.__dict__[react_class] = _ReactClass(react_class, fn)
          if 'createReactClass' in line:
            if '=' not in line: continue
            react_class = line.split('=')[0].strip().split()[-1]
            classes_by_file[fn].append(react_class)
            self.__dict__[react_class] = _ReactClass(react_class, fn)
          if 'extends React.Component' in line:
            if 'class' not in line: continue
            react_class = line[line.find('class')+5:line.find('extends')].strip()
            classes_by_file[fn].append(react_class)
            self.__dict__[react_class] = _ReactClass(react_class, fn)
          if line.startswith('// require '):
            req = line[len('// require '):].strip()
            self._reqs[fn].append(req)

    if self.verbose:
      print('BR classes by file:', dict(classes_by_file.items()))

    self._fn2hash = {}
    if prod:
      transformer = react.jsx.JSXTransformer()
    
      # confirm tmp paths exist
      for path in [self.hashed_path, self.genned_path, self.ext_path]:
        if not os.path.isdir(path):
          os.makedirs(path)
      
      # unfiltered assets
      self._fn2hash = self._load_fn_to_hash_mapping(self.asset_path, '*', dest=self.hashed_path)

      # download external resources
      for fn, deps in self._reqs.items():
        for dep in deps:
          if dep.startswith('http://') or dep.startswith('https://'):
            local_path = os.path.join(self.ext_path, _make_string_fn_safe(dep))
            if not os.path.isfile(local_path):
              if self.verbose: print('BR downloading:', dep)
              try:
                urlretrieve(dep, local_path)
              except urllib.error.HTTPError as e:
                print('BR warning could not download', dep, e)
      self._fn2hash.update(self._load_fn_to_hash_mapping(self.ext_path, '*', dest=self.hashed_path))
            
      # jsx assets
      jsx2hash = self._load_fn_to_hash_mapping(self.jsx_path, '*.jsx', dest=self.genned_path)
      for jsx_fn, jsx_hashed_fn in jsx2hash.items():
        jsx_converted_fn = os.path.join(self.genned_path, jsx_hashed_fn[:-1])
        if not os.path.exists(jsx_converted_fn) or os.stat(jsx_converted_fn).st_size==0:
          transformer.transform(os.path.join(self.genned_path, jsx_hashed_fn), js_path=jsx_converted_fn, harmony=self.harmony)

      # bottlereact.js
      with open(os.path.join(self.genned_path, 'bottlereact.js'),'w') as f:
        f.write(BOTTLEREACT_JS)
        f.write('\nbottlereact._assets = ')
        json.dump(self._fn2hash, f)
        f.write(';\n')

      # add the jsx files (which are only used server side, so not written to 'bottlereact.js')
      jsxjs2hash = self._load_fn_to_hash_mapping(self.genned_path, '*.js', dest=self.hashed_path)
      for k,v in jsx2hash.items():
        self._fn2hash[k] = jsxjs2hash[v[:-1]]

      # get the hashed name of 'bottlereact.js'
      self._fn2hash['bottlereact.js'] = jsxjs2hash['bottlereact.js']

      if self.verbose: print('BR file hashes:', self._fn2hash)

    if self.verbose: print('BR file requirements: ', dict(self._reqs.items()))

  def _init_render_server(self):
    if self._inited_render_server: return
    try:
      subprocess.check_output(['which', 'node'])
    except subprocess.CalledProcessError:
      raise Exception('Node.js is required but not found.  Please install with: sudo apt-get install nodejs')
    try:
      subprocess.check_output(['which', 'npm'])
    except subprocess.CalledProcessError:
      raise Exception('NPM is required but not found.  Please install with: sudo apt-get install npm')
    self._NODE_PATH = subprocess.check_output(['npm', 'root', '--quiet', '-g']).decode().strip()
    env = os.environ.copy()
    env["NODE_PATH"] = self._NODE_PATH
    try:
      subprocess.check_output(['node', '-e', 'require("node-jsdom")'], env=env)
    except subprocess.CalledProcessError:
      raise Exception('Node.js package "node-jsdom" was not found (but is required for server side rendering).\nPlease install it with: sudo npm install -g node-jsdom')
    self._inited_render_server = True

  def _build_dep_list(self, files):
    output = ['bottlereact.js']
    if not self.prod:
      output.append(BABEL_CORE)
    seen = set(output)
    for fn in files:
      self._build_dep_list_internal(fn, seen, output)
    return output

  def _build_dep_list_internal(self, fn, seen, output):
    if fn in seen: return
    for fn2 in self._reqs[fn]:
      self._build_dep_list_internal(fn2, seen, output)
    output.append(fn)
    seen.add(fn)
    
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
        if self.verbose: print('BR copied', fn, 'to', tmp_fn)
    return ret
  
  def calc_render_html_kwargs(self, kwargs):
    if self.default_render_html_kwargs is None:
      return kwargs
    if hasattr(self.default_render_html_kwargs, '__call__'):
      ret = self.default_render_html_kwargs()
    else:
      ret = dict(self.default_render_html_kwargs.items())
    ret.update(kwargs)
    return ret
  
  def get_js_context(self, deps):
    port, child = self._ctxs.get(deps, (None, None))
    if port: return port
    with self._ctx_lock:
      port, child = self._ctxs.get(deps, (None, None))
      if port: return port
      port, child = self.build_js_context(deps)
      self._ctxs[deps] = port, child
      return port
    
  def build_js_context(self, deps):
    port = _get_free_tcp_port()
    if self.verbose: print('BR building nodejs server http://localhost:%i'%port)
    fd, nodejs_fn = tempfile.mkstemp(suffix='.js', prefix='br_ctx_p%i_'%port)
    os.close(fd)
    if not self.prod:
      transformer = react.jsx.JSXTransformer()
    with open(nodejs_fn,'w') as of:
      of.write(FAKE_BROWSER_JS)
      for dep in deps:
        if dep.startswith('http://') or dep.startswith('https://'):
          dep = _make_string_fn_safe(dep)
        if dep=='bottlereact.js':
          of.write(BOTTLEREACT_JS)
        elif dep.endswith('_babel.js') or dep.endswith('_babel.min.js'):
          pass
        elif dep.endswith('.js'):
          if self.prod:
            js_path = os.path.join(self.hashed_path, self._fn2hash[dep])
          else:
            js_path = os.path.join(self.asset_path, dep)
          with open(js_path) as f:
            print('adding ', js_path)
            of.write('\n\n// BR importing: %s\n\n' % js_path)
            of.write(f.read())
        elif dep.endswith('.jsx'):
          if self.prod:
            js_path = os.path.join(self.hashed_path, self._fn2hash[dep])
            print('adding ', js_path)
            with open(js_path) as f:
              of.write('\n\n// BR importing: %s\n\n' % js_path)
              of.write(f.read())
          else:
            js_path = os.path.join(self.jsx_path, dep)
            with tempfile.NamedTemporaryFile(suffix='.js') as f:
              transformer.transform(js_path, js_path=f.name, harmony=self.harmony)
              with open(f.name) as f2:
                print('adding ', f.name, 'from', js_path)
                of.write('\n\n// BR importing: %s\n\n' % f.name)
                of.write(f2.read())

      of.write('''
        var ReactDOMServer;
        if('__SECRET_DOM_SERVER_DO_NOT_USE_OR_YOU_WILL_BE_FIRED' in React){
          ReactDOMServer = React.__SECRET_DOM_SERVER_DO_NOT_USE_OR_YOU_WILL_BE_FIRED;
        }else{
          ReactDOMServer = __br_original_require('react-dom/server')
        }
        
        _br_http.createServer((request, response) => { 
          var body = [];
          request.on('error', function(err) {
            console.error('BR nodejs error:', err);
          }).on('data', function(chunk) {
            body.push(chunk);
          }).on('end', function() {
            try {
              body = Buffer.concat(body).toString();
              var react_node = eval(body);
              var ret = ReactDOMServer.renderToString(react_node);
              response.writeHead(200);
              response.end(ret);
            } catch(err) {
              console.log(err)
              response.writeHead(500);
              response.end(String(err) +'\\n\\n'+ err.stack);
            }
          });
        }).listen(%i, 'localhost', (err) => {  
          if (err) {
            return console.log('something bad happened', err)
          }
          console.log(`BR nodejs server is listening on http://localhost:%i`)
        })
      ''' % (port,port))

    env = os.environ.copy()
    env["NODE_PATH"] = self._NODE_PATH
    child = subprocess.Popen(['node', nodejs_fn], env=env, preexec_fn = set_pdeathsig(signal.SIGTERM))
    def delete_nodejs_fn():
      os.remove(nodejs_fn)
    if self.prod:
      threading.Timer(2, delete_nodejs_fn).start()
    return port, child
  
  def render_server(self, deps, react_js, retry=True):
    self._init_render_server()
    deps = tuple(deps)
    port = self.get_js_context(deps)
    try:
      for i in range(10):
        try:
          with urlopen('http://localhost:%i' % port, react_js.encode()) as f:
            ret = f.read()
          return ret
        except urllib.error.URLError as e:
          if isinstance(e.reason, ConnectionRefusedError):
            time.sleep(.5)
            continue
          else:
            raise Exception(e.file.read().decode())
    except Exception as e:
      with self._ctx_lock:
        if self.verbose: print('BR nodejs server at http://localhost:%i is non-responsive - killing' % port)
        try:
          port, child = self._ctxs.pop(deps)
          child.terminate()
          child.kill()
        except KeyError: pass
        print(e)
      if retry:
        return self.render_server(deps, react_js, retry=False)
      else:
        raise e
    

  def render_html(self, react_node, **kwargs):
    kwargs = self.calc_render_html_kwargs(kwargs)
    template = kwargs.get('template', 'bottlereact')
    render_server = kwargs.get('render_server', self._render_server)
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
    init_nonce = kwargs.get('init_nonce', None)
    init_nonce = ' nonce="%s"' % init_nonce if init_nonce else ''
    init = '''
    <script%s>
      bottlereact._onLoad(%s, function() {
        ReactDOM.render(
          %s,
          document.getElementById('__body__')
        );
      });
    </script>
    ''' % (init_nonce, classes, react_js)
    if 'title' not in kwargs: kwargs['title'] = 'bottle-react - https://github.com/keredson/bottle-react'
    kwargs.update({
      'deps': deps_html,
      'init': init,
      'prod': self.prod,
      'asset_path': self.get_asset_path,
      'body': '',
    })
    if callable(render_server):
      render_server = render_server()
    if render_server:
      kwargs['body'] = self.render_server(deps, react_js)
    return bottle.template(template, **kwargs)


def _make_json_string_browser_safe(s):
  return s.replace('</', '<\\/')
  
def _make_string_fn_safe(s):
  return "".join([c if re.match(r'[\w.]', c) else '_' for c in s])

def _get_free_tcp_port():
  tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  tcp.bind(('localhost', 0))
  addr, port = tcp.getsockname()
  tcp.close()
  return port

def _dedup(seq):
  seen = set()
  seen_add = seen.add
  return [x for x in seq if not (x in seen or seen_add(x))]


class _ReactNode(object):
  def __init__(self, react_class, props, children):
    self.react_class = react_class
    self.props = self.react_class.default_props()
    if props: self.props.update(props)
    if 'key' not in self.props:
      self.props['key'] = '_br_%f' % random.random()
    self.children = children if children else []

  def get_js_files(self, files=None):
    if files is None: files = []
    files.append(self.react_class.fn)
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


FAKE_BROWSER_JS = '''
// don't look like nodejs
const _br_http = require('http');
const _br_jsdom = require("node-jsdom").jsdom;
const document = new _br_jsdom();
const window = document.parentWindow;
const navigator = window.navigator;
const HTMLElement = window.HTMLElement;
const Element = window.Element;
const history = window.history;
var __br_original_require = require;
exports = define = require = undefined;
'''

BOTTLEREACT_JS = '''
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
      setTimeout(f, 0);
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

};
'''
