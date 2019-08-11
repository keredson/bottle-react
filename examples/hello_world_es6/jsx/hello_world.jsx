// These are needed - bottle-react parses this file to build a javascript dependency tree.
// require https://cdnjs.cloudflare.com/ajax/libs/react/16.9.0/umd/react.development.js
// require https://cdnjs.cloudflare.com/ajax/libs/react-dom/16.8.6/umd/react-dom.development.js


class HelloWorld extends React.Component {
  render() {
    return (
      <div>
        <h1>Hello {this.props.name}!</h1>
        <div>
          Thanks for trying <a href="https://github.com/keredson/bottle-react" target='_blank'>bottle-react</a>!
        </div>
      </div>
    );
  }
}

bottlereact._register('HelloWorld', HelloWorld)
