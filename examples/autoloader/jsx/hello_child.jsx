class HelloChild extends React.Component {
  render() {
    return (
      <div>
        Thanks {this.props.name} for trying <a href="https://github.com/keredson/bottle-react" target='_blank'>bottle-react</a>!
      </div>
    );
  }
}

bottlereact.register(HelloChild)
