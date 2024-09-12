from fastapi.responses import JSONResponse

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
        response_content = {"errors": [error.to_dict() for error in self.errors]}
        status_code = self.errors[0].code if self.errors else 500
        return JSONResponse(content=response_content, status_code=status_code, headers={"Access-Control-Allow-Origin": "*"})
