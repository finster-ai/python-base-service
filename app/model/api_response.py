from collections import OrderedDict
from fastapi.responses import JSONResponse
import json


class ApiResponse:
    def __init__(self, timestamp, request_id, query_id, user_id, session_id, data):
        self.timestamp = timestamp
        self.request_id = request_id
        self.query_id = query_id
        self.user_id = user_id
        self.session_id = session_id
        self.data = data

    def to_dict(self):
        return OrderedDict([
            ("timestamp", self.timestamp),
            ("request_id", self.request_id),
            ("queryId", self.query_id),
            ("userId", self.user_id),
            ("sessionId", self.session_id),
            ("data", self.data)
        ])

    def to_response(self):
        json_response = self.to_dict()
        return JSONResponse(content=json_response, headers={"Access-Control-Allow-Origin": "*"})



