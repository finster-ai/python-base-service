from app.model.api_response import ApiResponse
from app_instance import logger
from datetime import datetime


def create_api_response(response_data, g):
    response = ApiResponse(
        timestamp=datetime.utcnow().isoformat(),
        query_id=g.get("query_id", ""),
        user_id=g.get("user_id", ""),
        session_id=g.get("session_id", ""),
        data=response_data
    )
    return response.to_response()


def sorting(entry, request):
    # Get query parameters for pagination and sorting
    sort_by = request.args.get('sort_by', 'created_at')  # Default sort by timestamp
    sort_order = request.args.get('sort_order', 'asc')  # Default sort order is ascending
    # Log a warning if the sort field is not present in any report entries
    if all(sort_by not in report for report in entry):
        # logger.warning(f"Sort field '{sort_by}' not found in any report entries. Sorting may not work as expected " + g_query_tracking_values_to_str(g))
        logger.warning(f"Sort field '{sort_by}' not found in any report entries. Sorting may not work as expected" )
    # Sort the reports
    reverse = (sort_order == 'desc')
    return sorted(entry, key=lambda x: x.get(sort_by) or '', reverse=reverse)


def pagination(entry, request):
    # Get query parameters for pagination and sorting
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))

    # Pagination
    if page == 0 and page_size == 0:
        paginated_entry = entry
    else:
        start = (page - 1) * page_size
        end = start + page_size
        paginated_entry = entry[start:end]
    return paginated_entry


def g_query_tracking_values_to_str(g):
    # session_id = g.get("session_id", "SESSION_ID_MISSING")
    query_id = g.get("query_id", "QUERY_ID_MISSING")
    user_id = g.get("user_id", "USER_ID_MISSING")
    backend_call_id = g.get("backend_call_id", "BACKEND_CALL_ID_MISSING")
    # response = f"call_id: {backend_call_id}  - user_id: {user_id} - session_id: {session_id} - query_id: {query_id}"
    response = f"call_id: {backend_call_id}  - user_id: {user_id} -query_id: {query_id}"
    return response

