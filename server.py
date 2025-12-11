# server.py
import os
import time
from flask import Flask, request, send_from_directory, make_response, Response, stream_with_context
from dotenv import load_dotenv

# Import the low-level agent functions (assumes agents.py exposes these)
# If you used a different layout, adjust imports accordingly.
from agents import agent_planner, agent_analyzer, agent_executor, agent_referee

load_dotenv()
PORT = int(os.getenv("PORT", 3000))

app = Flask(__name__, static_folder="static", static_url_path="/static")

# -------------------------------
# MANUAL CORS HANDLING (NO flask_cors)
# -------------------------------
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

@app.after_request
def after_request(response):
    return add_cors_headers(response)

# -------------------------------
# Serve frontend
# -------------------------------
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

# -------------------------------
# Helper to format SSE-like events (we use a simple text/event-stream format)
# -------------------------------
def sse_event(event: str, data: str):
    """
    Yield a single SSE event string. Data may contain newlines.
    """
    # event line
    yield f"event: {event}\n"
    # data lines (prefix each line with `data: `)
    for line in data.splitlines() or [""]:
        yield f"data: {line}\n"
    # end of event
    yield "\n"

# -------------------------------
# Streaming endpoint
# -------------------------------
@app.route("/run-stream", methods=["POST", "OPTIONS"])
def run_stream():
    # Preflight handler
    if request.method == "OPTIONS":
        return add_cors_headers(make_response("", 200))

    # Validate body
    try:
        body = request.get_json(force=True)
    except Exception as e:
        return make_response(f"Invalid JSON body: {e}", 400)

    if not body or "input" not in body:
        return make_response("Error: Provide JSON with 'input' field.", 400)

    user_input = body["input"]

    # The generator that will stream events

    def generate():
        # 1) notify start
        yield from sse_event("status", "Starting agent pipeline (planner -> analyzer -> executor -> referee)")
        # small pause to allow client to render waiting message
        yield from sse_event("status", "Waiting for planner")
        # 2) Planner
        try:
            planner_out = agent_planner(user_input)
        except Exception as e:
            # send error event and stop
            yield from sse_event("error", f"Planner failed: {e}")
            return
        yield from sse_event("planner", planner_out)

        # 3) Analyzer
        yield from sse_event("status", "Waiting for analyzer")
        try:
            analyzer_out = agent_analyzer(planner_out)
        except Exception as e:
            yield from sse_event("error", f"Analyzer failed: {e}")
            return
        yield from sse_event("analyzer", analyzer_out)

        # 4) Executor
        yield from sse_event("status", "Waiting for executor")
        try:
            executor_out = agent_executor(analyzer_out)
        except Exception as e:
            yield from sse_event("error", f"Executor failed: {e}")
            return
        yield from sse_event("executor", executor_out)

        # 5) Referee
        yield from sse_event("status", "Waiting for referee")
        try:
            referee_out = agent_referee({
                "planner": planner_out,
                "analyzer": analyzer_out,
                "executor": executor_out
            })
        except Exception as e:
            yield from sse_event("error", f"Referee failed: {e}")
            return
        yield from sse_event("referee", referee_out)

        # 6) done
        yield from sse_event("status", "All agents finished")
        # optionally provide a final summary event
        summary = {
            "planner": planner_out,
            "analyzer": analyzer_out,
            "executor": executor_out,
            "referee": referee_out
        }
        # Provide a final 'done' event with a short confirmation
        yield from sse_event("done", "Pipeline complete")

    # Return Response with mimetype text/event-stream so streaming works
    # Note: browsers won't automatically parse events for POST using EventSource;
    # the client uses fetch and reads the stream.
    return Response(stream_with_context(generate()), mimetype="text/event-stream")

# -------------------------------
# Fallback route for original /run (non-streaming)
# -------------------------------
@app.route("/run", methods=["POST", "OPTIONS"])
def run_route():
    if request.method == "OPTIONS":
        return add_cors_headers(make_response("", 200))

    try:
        body = request.get_json(force=True)
    except Exception as e:
        return make_response(f"Invalid JSON body: {e}", 400)

    if not body or "input" not in body:
        return make_response("Error: Provide JSON with 'input' field.", 400)

    user_input = body["input"]

    try:
        planner_out = agent_planner(user_input)
        analyzer_out = agent_analyzer(planner_out)
        executor_out = agent_executor(analyzer_out)
        referee_out = agent_referee({
            "planner": planner_out,
            "analyzer": analyzer_out,
            "executor": executor_out
        })
    except Exception as e:
        return make_response(f"Internal server error while running agents:\n{e}", 502)

    # Return the full formatted text (non-streaming fallback)
    output = (
        f"--- PLANNER ---\n{planner_out}\n\n"
        f"--- ANALYZER ---\n{analyzer_out}\n\n"
        f"--- EXECUTOR ---\n{executor_out}\n\n"
        f"--- REFEREE ---\n{referee_out}\n"
    )
    resp = make_response(output, 200)
    return resp

@app.route("/favicon.ico")
def favicon():
    return "", 204

@app.route("/.well-known/<path:subpath>", methods=["GET", "OPTIONS"])
def well_known(subpath):
    # return 204 No Content so it won't show up as an error in logs
    resp = make_response("", 204)
    # keep CORS headers (your after_request will already add them)
    return resp

# -------------------------------
# Start server
# -------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)


