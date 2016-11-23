# Documentation

## `bottlereact.BottleReact()`
`bottlereact.BottleReact()` takes several keyword arguments, all of which are optional:

| KW Argument | Description | Default |
| ----------- | ----------- | ------- |
| `prod` | Are we in production?  If so, compile all JSX into pure javascript.  Otherwise serve the raw JSX with the babel-core shim. | `False` |
| `jsx_path` | Where bottle-react should search for JSX files. | `jsx` |
| `asset_path` | Where bottle-react should search for javascript/css/etc files. | `assets` |
| `work_path` | Where bottle-react outputs static js files when in production mode (if you want to serve them statically). | `/tmp/bottlereact` |
| `jsx_path` | Where bottle-react should search for JSX files. | `jsx` |
| `verbose` | Verbose mode. | `not prod` |
