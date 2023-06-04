class Constants:
    REMOTE_URL = "http://localhost:{port}/json"
    PRESENCES_ENDPOINT = (
        "https://api.github.com/repos/Presencify/Presences/contents/presences?ref=main"
    )
    PRESENCES_ENDPOINT_CONTENT = "https://raw.githubusercontent.com/Presencify/Presences/main/presences/{name}/{file}"

    ALLOWED_MODULES = {
        "time": __import__("time"),
        "datetime": __import__("datetime"),
        "random": __import__("random"),
        "math": __import__("math"),
        "re": __import__("re"),
        "json": __import__("json"),
        "urllib": __import__("urllib"),
        "httpx": __import__("httpx"),
        "requests": __import__("requests"),
    }

    # DEPRECATED for now
    OPCODES = {
        0: "INIT_RPC",
        1: "UPDATE_RPC",
        2: "DELETE_RPC",
    }

    LOG_OUTPUT_FILENAME = "client.log"
    OS_COMPAT = "Windows"
