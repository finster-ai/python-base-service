from collections import OrderedDict
from fastapi.responses import JSONResponse
import datetime
import json


def serialize_datetime(obj):
    """
    Custom function to serialize datetime.datetime objects.
    Args:
        obj: object to be JSON serialized
    Returns:
        JSON serializable version of obj
    """
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    raise TypeError("Type not serializable")

class ApiResponse:
    def __init__(self, timestamp, request_id, query_id, user_id, session_id, current_page, page_size, total_pages, total_elements, data):
        self.timestamp = timestamp
        self.request_id = request_id
        self.query_id = query_id
        self.user_id = user_id
        self.session_id = session_id
        self.current_page = current_page
        self.page_size = page_size
        self.total_pages = total_pages
        self.total_elements = total_elements
        self.data = data

    def to_dict(self):
        return OrderedDict([
            ("timestamp", self.timestamp),
            ("requestId", self.request_id),
            ("queryId", self.query_id),
            ("userId", self.user_id),
            ("sessionId", self.session_id),
            ("currentPage", self.current_page),
            ("pageSize", self.page_size),
            ("totalPages", self.total_pages),
            ("totalElements", self.total_elements),
            ("data", self.data)
        ])

    def to_response(self):
        # Serialize the response dictionary to JSON, using the custom datetime serializer
        json_response = json.dumps(self.to_dict(), default=serialize_datetime)
        return JSONResponse(content=json.loads(json_response), headers={"Access-Control-Allow-Origin": "*"})



