class Constants:
    REMOTE_URL = "http://localhost:{port}/json"
    LOG_OUTPUT_FILENAME = "client.log"
    OS_COMPAT = "Windows"
    # DEPRECATED for now
    OPCODES = {
        0: "INIT_RPC",
        1: "UPDATE_RPC",
        2: "DELETE_RPC",
    }
