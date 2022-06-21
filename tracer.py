from flask import Flask, request, Response, make_response
from flask.json import jsonify
import json
import subprocess
from runestone.codelens.pg_logger import exec_script_str_local
# at some point maybe worry about Access-Control-Allow-Origin: *
# but for now this isn't an issue for command line usage.

app = Flask(__name__)


@app.route("/")
def hello_world():
    return "Hello Class!"


# docker run -m 512M --rm --user=netuser --net=none --cap-drop all pgbovine/cokapi-java:v1 /tmp/run-java-backend.sh '{"usercode": "public class Test { public static void main(String[] args) { int x=42; x+=1; x+=1; x+=1;} }", "options": {}, "args": [], "stdin": ""}'
@app.route("/tracejava", methods=["POST"])
def tracejava():
    #code = request.args["src"]
    code = request.form.get("src")
    stdin = request.form.get("stdin")
    if stdin == "null" or stdin is None:
        stdin = ""
    docker_args = [
        "docker",
        "run",
        "-m",
        "512M",
        "--rm",
        "--user=netuser",
        "--net=none",
        "--cap-drop",
        "all",
        "pgbovine/cokapi-java:v1",
        "/tmp/run-java-backend.sh",
    ]
    runspec = {}
    runspec["usercode"] = code
    runspec["options"] = {}
    runspec["args"] = []
    runspec["stdin"] = stdin
    docker_args.append(json.dumps(runspec))
    res = subprocess.run(docker_args, capture_output=True)
    print(res)
    resp = make_response(res.stdout)
    resp.headers['Content-type'] = 'application/json'
    return resp

# docker run -t -i --rm --user=netuser --net=none --cap-drop all pgbovine/opt-cpp-backend:v1 python /tmp/opt-cpp-backend/run_cpp_backend.py "int main() {int x=12345;}" c


@app.route("/tracec", methods=["POST"])
def tracec():
    code = request.form.get("src")
    docker_args = [
        "docker",
        "run",
        #        "-t",  Removed these two as they caused failure and I don't know that they are needed
        #        "-i",
        "--rm",
        "--user=netuser",
        "--net=none",
        "--cap-drop",
        "all",
        "pgbovine/opt-cpp-backend:v1",
        "python",
        "/tmp/opt-cpp-backend/run_cpp_backend.py",
        code,
        "c"
    ]
    res = subprocess.run(docker_args, capture_output=True)
    resp = make_response(res.stdout)
    resp.headers['Content-type'] = 'application/json'
    return resp


@app.route("/tracecpp", methods=["POST"])
def tracecpp():
    code = request.form.get("src")
    docker_args = [
        "docker",
        "run",
        "--rm",
        "--user=netuser",
        "--net=none",
        "--cap-drop",
        "all",
        "pgbovine/opt-cpp-backend:v1",
        "python",
        "/tmp/opt-cpp-backend/run_cpp_backend.py",
        code,
        "cpp"
    ]
    done = False
    tries = 5
    while not done and tries > 0:
        res = subprocess.run(docker_args, capture_output=True)
        if len(res.stderr) != 0:
            print(f"Error: {res.stderr}")
            tries -= 1
        if len(res.stdout) == 0:
            print("No results from docker")
            tries -= 1
        if len(res.stdout) > 0:
            done = True
    resp = make_response(res.stdout)
    resp.headers['Content-type'] = 'application/json'
    return resp


def js_var_finalizer(input_code, output_trace):
    ret = dict(code=input_code, trace=output_trace)
    json_output = json.dumps(ret, indent=None)
    return json_output


@app.route("/tracepy", methods=["POST"])
def tracepy():

    code = request.form.get("src")

    tracedata = exec_script_str_local(
        code, None, False, None, js_var_finalizer
    )

    resp = make_response(tracedata)
    resp.headers['Content-type'] = 'application/json'
    return resp
