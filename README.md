# bottle-react

## Description
This library allows you to return react components from Bottle.  It currently powers https://www.hvst.com/.

Example:

Assume you have a normal JSX file `hello_world.jsx`:
```js
// require hello_world.css

var HelloWorld = React.createClass({
  render: function() {
    return (
      <div className='hello_world'>
        <h1>Hello World!</h1>
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
    br.HelloWorld()
  )
```


## Install
```python
sudo pip install bottle-react
```
