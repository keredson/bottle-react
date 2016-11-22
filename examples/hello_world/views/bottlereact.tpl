<!DOCTYPE html>
<html>

  <head>
    <meta charset="UTF-8" />
    <title>{{title}}</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/react/15.4.0/react-with-addons{{'.min' if prod else ''}}.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/react/15.4.0/react-dom{{'.min' if prod else ''}}.js"></script>
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

