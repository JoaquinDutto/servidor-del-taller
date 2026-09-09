import json
from wsgiref.simple_server import make_server

#los tasks viven solo en memoria, no se guardan
tasks = {}
next_task_id = 1


def json_response(start_response, status, payload):
    #se arma la respuesta en json
    body = json.dumps(payload).encode("utf-8")
    start_response(
        status,
        [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(body))),
        ],
    )
    return [body]


def parse_json_body(environ):
    content_length = environ.get("CONTENT_LENGTH", "0")
    try:
        length = int(content_length)
    except ValueError:
        length = 0

    if length <= 0:
        return {}

    raw_body = environ["wsgi.input"].read(length)
    if not raw_body:
        return {}

    try:
        data = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError("JSON inválido")

    if not isinstance(data, dict):
        raise ValueError("El cuerpo JSON debe ser un objeto")

    return data


def application(environ, start_response):
    method = environ.get("REQUEST_METHOD", "GET")
    path = environ.get("PATH_INFO", "/")
    path_parts = [part for part in path.split("/") if part]

    def not_found():
        return json_response(start_response, "404 Not Found", {"error": "Not found"})

    def method_not_allowed():
        return json_response(start_response, "405 Method Not Allowed", {"error": "Method not allowed"})

    def bad_request(message):
        return json_response(start_response, "400 Bad Request", {"error": message})

    if path == "/tasks":
        if method == "GET":
            return json_response(start_response, "200 OK", list(tasks.values()))

        if method == "POST":
            try:
                data = parse_json_body(environ)
            except ValueError as exc:
                return bad_request(str(exc))

            title = data.get("title")
            if not title:
                return bad_request("Falta el campo 'title'")

            task = {
                "id": next_task_id,
                "title": title,
                "done": bool(data.get("done", False)),
            }

            tasks[next_task_id] = task
            next_task_id += 1
            return json_response(start_response, "201 Created", task)

        return method_not_allowed()

    if len(path_parts) == 2 and path_parts[0] == "tasks":
        task_id_raw = path_parts[1]

        try:
            task_id = int(task_id_raw)
        except ValueError:
            return not_found()

        if method == "GET":
            task = tasks.get(task_id)
            if task is None:
                return not_found()
            return json_response(start_response, "200 OK", task)

        if method == "PATCH":
            task = tasks.get(task_id)
            if task is None:
                return not_found()

            try:
                data = parse_json_body(environ)
            except ValueError as exc:
                return bad_request(str(exc))

            for key, value in data.items():
                if key == "id":
                    continue
                task[key] = value

            return json_response(start_response, "200 OK", task)

        if method == "DELETE":
            task = tasks.pop(task_id, None)
            if task is None:
                return not_found()
            return json_response(start_response, "200 OK", {"deleted": True, "task": task})

        return method_not_allowed()

    return not_found()


if __name__ == "__main__":
    with make_server("localhost", 9292, application) as server:
        print("Servidor escuchando en http://localhost:9292")
        server.serve_forever()
