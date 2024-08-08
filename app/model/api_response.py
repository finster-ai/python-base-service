from collections import OrderedDict
from flask import Response
import json


class ApiResponse:
    def __init__(self, timestamp, query_id, user_id, session_id, data):
        self.timestamp = timestamp
        self.query_id = query_id
        self.user_id = user_id
        self.session_id = session_id
        self.data = data

    def to_dict(self):
        return OrderedDict([
            ("timestamp", self.timestamp),
            ("queryId", self.query_id),
            ("userId", self.user_id),
            ("sessionId", self.session_id),
            ("data", self.data)
        ])

    def to_response(self):
        json_response = json.dumps(self.to_dict(), default=dict)
        response = Response(json_response, mimetype='application/json')
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("ContentType", "application/json")
        return response



