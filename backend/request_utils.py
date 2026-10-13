from flask import request, abort


def get_json_body():
    """Return the request body as a dict, or abort with 400.

    Flask already rejects malformed JSON, but valid JSON that isn't an object
    (null, a list, a bare string) would otherwise crash handlers on data.get().
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        abort(400, description="Request body must be a JSON object")
    return data


def parse_rating(value):
    """Validate a rating: a number from 0 to 5 in 0.5 steps. Returns float or None."""
    # bool is a subclass of int, so exclude it explicitly
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if value < 0 or value > 5 or (value * 2) % 1 != 0:
        return None
    return float(value)


def check_length(value, field, max_len):
    """Abort with 400 if a string field exceeds max_len."""
    if value is not None and len(value) > max_len:
        abort(400, description=f"{field} must be at most {max_len} characters")
