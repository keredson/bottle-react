# bottle-react

## Description
This library allows you to return react components from Bottle.  It currently powers https://www.hvst.com/.

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

## Install
```python
sudo pip install bottle-react
```
## Documentation

`bottlereact.BottleReact()` takes several keyword arguments, all of which are optional:

| KW Argument | Description | Default |
| ----------- | ----------- | ------- |
| `prod` | Are we in production?  If so, compile all JSX into pure javascript.  Otherwise serve the raw JSX with the babel-core shim. | False |
| `jsx_path` | Where bottle-react should search for JSX files. | `jsx` |
| `asset_path` | Where bottle-react should search for javascript/css/etc files. | `assets` |
| `work_path` | Where bottle-react outputs static js files when in production mode (if you want to serve them statically). | `/tmp/bottlereact` |
| `jsx_path` | Where bottle-react should search for JSX files. | `jsx` |
| `verbose` | Verbose mode. | `not prod` |
