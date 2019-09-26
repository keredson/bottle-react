
class HelloWorld extends React.Component {
  render() {
    return (
      <div>
        <h1>Hello {this.props.name}!</h1>
        <bottlereact.HelloChild name={this.props.name} />
      </div>
    );
  }
}

bottlereact.register(HelloWorld)
