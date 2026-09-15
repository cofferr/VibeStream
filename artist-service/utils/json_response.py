def success_response(data: dict, message: str = "Operación exitosa"):
    return {"status": "success", "data": data, "message": message}


def error_response(code: int, message: str):
    return {"status": "error", "error": {"code": code, "message": message}}
