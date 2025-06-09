
NOTE:
TO GET THE FILES 
  brython.js
  brython_stdlib.js
=> download then from 
  https://github.com/brython-dev/brython

To run the demo, you can open the file demo.html from the browser "File/Open..." menu.

Another option is to start the built-in Python HTTP server by

    python -m http.server

The default port is 8000. To specify another port:

    python -m http.server 8080

Then load http://localhost:<port>/demo.html in the browser address bar.

For more information please visit http://brython.info.

To test from a smartphone
1) same WIFI netwok
2) ip addr | grep inet  -> get PC server IP address
3) sudo ufw allow 8000
4)  load http://<ip address>:<port>/demo.html in the browser address bar on smartphone

ADDITIONAL / IMPORTANT 
to install do not forget to run :
brython-cli make_modules
