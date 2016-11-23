// require https://cdnjs.cloudflare.com/ajax/libs/react/15.4.0/react-with-addons.min.js
// require https://cdnjs.cloudflare.com/ajax/libs/react/15.4.0/react-dom.min.js


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
