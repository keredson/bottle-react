import unittest
import bottle
import bottlereact


class TestBottleReact(unittest.TestCase):

  def test_hello_world(self):
    app = bottle.Bottle()
    br = bottlereact.BottleReact(app, prod=True)
    html = br.render_html(br.HelloWorld())
    self.assertTrue(html.startswith('<html>'))
    self.assertTrue('-bottlereact.js"></script>' in html)
    self.assertTrue('-hello_world.js"></script>' in html)
    self.assertTrue('React.createElement(bottlereact.HelloWorld,{},[])' in html)

  def test_kwarg(self):
    app = bottle.Bottle()
    br = bottlereact.BottleReact(app, prod=True)
    html = br.render_html(br.HelloWorld(), template='title', title='xyz').strip()
    self.assertEquals(html, 'xyz')

  def test_default_kwarg(self):
    app = bottle.Bottle()
    br = bottlereact.BottleReact(app, prod=True, default_render_html_kwargs={'title':'abc'})
    html = br.render_html(br.HelloWorld(), template='title').strip()
    self.assertEquals(html, 'abc')
    html = br.render_html(br.HelloWorld(), template='title', title='xyz').strip()
    self.assertEquals(html, 'xyz')

  def test_default_kwarg_func(self):
    def default_render_html_kwargs():
      return {'title':'abc'}
    app = bottle.Bottle()
    br = bottlereact.BottleReact(app, prod=True, default_render_html_kwargs=default_render_html_kwargs)
    html = br.render_html(br.HelloWorld(), template='title').strip()
    self.assertEquals(html, 'abc')
    html = br.render_html(br.HelloWorld(), template='title', title='xyz').strip()
    self.assertEquals(html, 'xyz')


if __name__ == '__main__':
    unittest.main()


