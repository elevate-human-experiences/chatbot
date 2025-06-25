# MIT License
#
# Copyright (c) 2025 Elevate Human Experiences, LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Custom JSON encoder for Falcon to handle datetime and other non-serializable objects."""

import json
from datetime import datetime, date, time
from decimal import Decimal
from uuid import UUID
from typing import Any


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime, UUID, Decimal, and other common types."""

    def default(self, obj: Any) -> Any:
        """Encode non-serializable objects to JSON-compatible formats."""
        if isinstance(obj, datetime):
            # Return ISO format string with timezone info
            return obj.isoformat()
        elif isinstance(obj, date):
            # Return ISO format date string
            return obj.isoformat()
        elif isinstance(obj, time):
            # Return ISO format time string
            return obj.isoformat()
        elif isinstance(obj, UUID):
            # Return string representation of UUID
            return str(obj)
        elif isinstance(obj, Decimal):
            # Return float representation of Decimal
            return float(obj)
        elif hasattr(obj, "__dict__"):
            # Handle objects with __dict__ (like custom classes)
            return obj.__dict__
        else:
            # Fall back to default JSON encoder behavior
            return super().default(obj)


def dumps(obj: Any, **kwargs) -> str:
    """JSON dumps using the custom encoder."""
    return json.dumps(obj, cls=CustomJSONEncoder, **kwargs)


def loads(s: str, **kwargs) -> Any:
    """JSON loads (standard implementation)."""
    return json.loads(s, **kwargs)
