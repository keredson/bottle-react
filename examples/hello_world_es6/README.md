# Hello World

This is a minimal example of what you need to use `bottle-react` broken down by file.  It renders like:

![image](https://cloud.githubusercontent.com/assets/2049665/20573695/bbb0713a-b176-11e6-8434-5fe73a608307.png)


## `run.py`

Create your bottle app as usual:
```python
app = bottle.Bottle()
```

And then bind `bottle-react` to it.

```python
br = BottleReact(app, prod=PROD)
```
The `prod` parameter determines if you're in production or not.  (In production pure javascript is served with 
`sha256` hashes in the filenames and cache headers.  In development
`jsx` files are served with the `babel-core` shim.

When you define a route:
```python
@app.get('/')
def root():
  return br.render_html(
    br.HelloWorld({'name':'World'})
  )
```
You pass it a single `bottle-react` component to `br.render_html()`.  By the time your request is accepted 
`bottle-react` will have searched the JSX directory (`./jsx` by default) and created python classes for each.

## `hello_world.jsx`

This is a normal JSX file with two exceptions.  First:
```js
// require https://cdnjs.cloudflare.com/ajax/libs/react/15.4.0/react-with-addons.min.js
// require https://cdnjs.cloudflare.com/ajax/libs/react/15.4.0/react-dom.min.js
```

We need to specify this file's dependencies.

Second:
```js
bottlereact._register('HelloWorld', HelloWorld)
```
We need to register this class with `bottle-react`.


## `bottlereact.tpl`
This is default template `bottle-react` will look for to render your JSX component inside of.

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
      <center style='margin:4em 0;'>
        Loading...
      </center>
    </div>
  </body>
  
{{! init }}

</html>
```

Note  `{{! deps }}` and `{{! init }}` which are required.  `{{! deps }}` should go inside the `<head>` tag 
and `{{! init }}` should go after the `</body>` tag.

