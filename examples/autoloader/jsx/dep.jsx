class Dep extends React.Component {
  render() {
    console.log('rendering real Dep')
    return (
      <div>
        Thanks for trying <a href="https://github.com/keredson/bottle-react" target='_blank'>bottle-react</a>!
      </div>
    );
  }
}

bottlereact._register('Dep', Dep)
