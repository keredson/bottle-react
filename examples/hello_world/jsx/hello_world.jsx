// require hello_world.css

var HelloWorld = React.createClass({
  render: function() {
    return (
      <div className='hello_world'>
        <h1>Hello World!</h1>
        <div>
          Thanks for trying <a href="https://github.com/keredson/bottle-react" target='_blank'>bottle-react</a>!
        </div>
      </div>
    );
  }
})

bottlereact._register('HelloWorld', HelloWorld)
