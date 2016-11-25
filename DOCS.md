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
def render_html(react_node, **options):
```
