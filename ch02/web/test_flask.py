from flask import Flask, request

def shutdown_server():
  func = request.environ.get('werkzeug.server.shutdown')
  if func is None:
    raise RuntimeError('Not running with the Werkzeug Server')
  func()

app = Flask(__name__)

@app.route("/<input>")
def hello(input): 
  return input

@app.route('/shutdown')
def shutdown():
  shutdown_server()
  return 'Server shutting down...'

if __name__ == "__main__": 
  app.run(
    debug=True,
    host='0.0.0.0'
  )
