# Documentation

## `bottlereact.BottleReact()`
An instance of `bottlereact.BottleReact()` is how your bottle app becomes a bottle-react app.  Typically it's used like this:

```python
app = bottle.Bottle()
br = bottlereact.BottleReact(app, prod=PROD)
```

Where `PROD` is a boolean determining if the app is running in production or not.  It does a few things:

1. It registers a URL `@app.get('/__br_assets__/<path:path>')` to serve it's own assets. (These can also be statically served by NGINX.)
2. It scans the directory `jsx` to find all the defined React classes.
3. It registers Python references to them and adds them as properties of the `br` instance.
4. It scans the directory `assets` for CSS/javascript/etc.
5. It calculates dependencies between JSX files and files in `assets` (so it can serve a minimum set of dependencies to every browser, not all the javascript/CSS to everyone all the time).
6. If in `prod` mode, it translates your JSX into javascript and calculates `sha256` hashes of everything (for browser caching).

`bottlereact.BottleReact()` takes several keyword arguments, all of which are optional:

| KW Argument | Description | Default |
| ----------- | ----------- | ------- |
| `prod` | Are we in production?  If so, compile all JSX into pure javascript.  Otherwise serve the raw JSX with the babel-core shim. | `False` |
| `jsx_path` | Where bottle-react should search for JSX files. | `jsx` |
| `asset_path` | Where bottle-react should search for javascript/css/etc files. | `assets` |
| `work_path` | Where bottle-react outputs static js files when in production mode (if you want to serve them statically). | `/tmp/bottlereact` |
| `jsx_path` | Where bottle-react should search for JSX files. | `jsx` |
| `verbose` | Verbose mode. | `not prod` |
| `default_render_html_kwargs` | Default kwargs to be passed to all calls to `render_html`.  For example, `title`. Can be either a `dict` or a function that returns a `dict`. | `None` |
| `render_server` | Enable server-side rendering.  Can be a `bool` or a function.  Requires `prod=True` to have an effect. | Currently `False` but that may change. |

## `br.HelloWorld()`

For every `var HelloWorld = React.createClass({` in your `jsx` directory, a class `br.HelloWorld` will be created in Python to reflect it.  When you instantiate it it takes two optional arguments (`props` and `children`) just like their React counterparts.

Some example calls:

```python
x = br.HelloWorld() # no props or children
x = br.HelloWorld({'name':'Derek'}) # pass in a prop 'name'
x = br.HelloWorld(children=[br.HelloWorld()]) # nest a class in itself
x = br.HelloWorld({'name':'Derek'}, [br.HelloWorld({'name':'Anderson'})]) # nested with props
```

The returned value is typically either used as a child in another bottle-react component, or passed into `br.render_html()`.

## `br.render_html()`

Once you have your react component defined you need to wrap it in an HTML shell returnable from Bottle and readable by the browser.  You do this with `br.render_html()`.  It is defined as:

```python
def render_html(react_node, **kwargs):
```

By default `render_html` looks for a template in your Bottle template path (usually the directory `views`) called `bottlereact.tpl`.  This is a normal Bottle template you can define to your liking.  a minimal one would be:
```html
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <title>{{title}}</title>
    {{! deps }}
  </head>
  <body>
    <div id="__body__">
      Loading...
    </div>
  </body>
{{! init }}
</html>
```

Note the two bottle params that are passed in `deps` and `init`.  `deps` should be placed in side the `<head>` of your template.  `init` should go after the `</body>` tag.  (Note the `{{!` which tells Bottle not to HTML-escape the `<script>` tags.  The HTML-escaping of user variables is done internally in bottle-react.)  And the root element your React component will bind to will be the element with the `id="__body__"`.

In the given `HelloWorld` example, the `deps` variable will look like this (if in dev mode):
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/babel-core/5.8.24/browser.min.js"></script>
<script src="/__br_assets__/bottlereact.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/react/15.4.0/react-with-addons.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/react/15.4.0/react-dom.min.js"></script>
<script type="text/babel" src="/__br_assets__/hello_world.jsx"></script>
```

Or this (if in prod mode):

```html
<script src="/__br_assets__/af6f7e0a7c117244-bottlereact.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/react/15.4.0/react-with-addons.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/react/15.4.0/react-dom.min.js"></script>
<script src="/__br_assets__/ca436611dff6b176-c6c76af11f18e376-hello_world.js"></script>
```
The two CDN resources are there because in our `HelloWorld` example JSX file we have:
```javascript
// require https://cdnjs.cloudflare.com/ajax/libs/react/15.4.0/react-with-addons.min.js
// require https://cdnjs.cloudflare.com/ajax/libs/react/15.4.0/react-dom.min.js
```

You could just as easily have them in the `assets` folder, which could be included like:
```javascript
// require react-with-addons.min.js
// require react-dom.min.js
```

The `init` variable will look like this:
```html
<script>
  bottlereact._onLoad(["HelloWorld"], function() {
    ReactDOM.render(
      React.createElement(bottlereact.HelloWorld,{"name": "World"},[]),
      document.getElementById('__body__')
    );
  });
</script>
```

The function `bottlereact._onLoad` (defined in `bottlereact.js`) takes a list of classes that need to load before the compnent can be rendered, and a callback to be run when they are loaded.  the callback contains normal React code to initialize your component.

We talked internally about (in `prod` mode) having `render_html()` taking advantage of React's ability to pre-render the HTML, but in testing we've found the brower renders the JSX extremely fast already.  So we haven't done it yet, but it's designed to be added in the future.

If you want to use another template, pass in `template='template_fn'` into `render_html()` and bottle-react will use that template instead.

Any additional `kwargs` passed into `render_html()` will be passed through to the template.  For example, `title='My Site'` is very common.


## jsx_props.py

Sometimes you want all instances of your React component to have some default set of props.  For instance, our `<HvstApp>` JSX compnent (that renders the left nav and title bar) always have a `user={name:'Derek', id:12345}` property representing the logged in user.  It would be annoying to always have to declare it like this:

```python
br.HvstApp({'user': bottle.request.current_user.to_json()})
```

Since we have that component in almost every HTML endpoint in our app.  So for common variables like this, bottle-react will look for a module `jsx_props`.  If that module has a function defined matching `init` + the React class name, whatever that function returns will be the default props for that object.  (Any props passed in when creating the object will override these default props.)  For example, if in `jsx_props.py` we define:

```python
def initHvstApp():
  return {'user': bottle.request.current_user.to_json()}
```

Now if we create a `br.HvstApp()` it'll have the `user` prop already associated with it.
