// require react-with-addons.js
// require react-dom.js

var HelloWorld = React.createClass({
  render: function() {
    return (
      <div>
        <h1>Hello {this.props.name}!</h1>
        <div>
          Thanks for trying <a href="https://github.com/keredson/bottle-react" target='_blank'>bottle-react</a>!
        </div>
      </div>
    );
  }
})

bottlereact._register('HelloWorld', HelloWorld)
