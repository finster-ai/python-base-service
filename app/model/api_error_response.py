from flask import jsonify


class ErrorDetail:
    def __init__(self, code, message):
        self.code = code
        self.message = message

    def to_dict(self):
        return {
            "code": self.code,
            "message": self.message
        }


class ApiErrorResponse:
    def __init__(self, errors):
        self.errors = errors

    def to_response(self):
        response = jsonify({"errors": [error.to_dict() for error in self.errors]})
        response.status_code = self.errors[0].code if self.errors else 500
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("ContentType", "application/json")
        return response
