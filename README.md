# Bottle-React

***NOW SUPPORTS FLASK!*** See [examples/hello_world/run_flask.py](examples/hello_world/run_flask.py).

## Description
This library allows you to return react components from either Bottle or Flask.  It currently powers https://www.hvst.com/.

## Example (Hello World)

Assume you have a normal JSX file `hello_world.jsx`:
```js
var HelloWorld = React.createClass({
  render: function() {
    return (
      <div className='hello_world'>
        <h1>Hello {this.props.name}!</h1>
        <div>
          Thanks for trying bottle-react!
        </div>
      </div>
    );
  }
})
bottlereact._register('HelloWorld', HelloWorld)
```

And some python code:
```python
app = bottle.Bottle()
br = BottleReact(app)

@app.get('/')
def root():
  return br.render_html(
    br.HelloWorld({'name':'World'})
  )
```

When your route is called the react component will be rendered.  See [examples/hello_world](examples/hello_world) for details.

## Principles

Why did we develop this?  We had several goals:

- [x] Don't cross-compile javascript during development.

Compiling with `webpack` is too slow for non-trivial applications.  (One of the niceties about web developement it `alt-Tab`/`ctrl-R` to see your changes.)  And it causes too many subtle bugs between dev and prod that waste developer resources.

- [x] Don't merge all javascript into one ginormous bundle.

Making your user download a 1.5Mb `kitchensink.min.js` every deployment is horrible.  And 99% of it isn't used on most pages.  Loading 40kb total from multiple resources with HTTP keep-alive takes just a few ms per file and is much faster in practice.

- [x] React components should be composable from Python.

A lot of our routes look like this:

```python
@app.get('/something')
def something():
  user = bottle.request.current_user
  return br.render_html(
    br.HvstApp({'user':user.to_dict()}, [
      br.HelloWorld({'name':user.name}),
    ])
  )
```

The React component `HvstApp` (which renders the title bar and left nav) is taking two parameters.  The first is a `dict` that will be passed as the JSON props to the React component.  The second is a `list` that will become the children.  This list can (and usually does) contain other React components.


## Install
```python
sudo pip install bottle-react
```

## NGINX Integration
By default (in production mode) `bottle-react` writes to `/tmp/bottlereact/hashed-assets/`.  To make NGINX serve these files directly, use the following:

```
  location ^~ /__br_assets__/ {
    alias /tmp/bottlereact/hashed-assets/;
    expires max;
  }
```

## Documentation

See the [full documentation](DOCS.md).
