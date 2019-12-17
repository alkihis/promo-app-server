from flask import Flask, jsonify
from typing import Union, Dict, Tuple

# Define a type union
ACCEPTED_CODES = Union[int, str]

class Errors:
  def __init__(self):
    self.codes: Dict[int, Tuple[str, int]] = {
      1: ('Page not found. Check the URL.', 404),
      2: ('Resource not found.', 404),
      3: ('Invalid method. Current HTTP method is not supported for this endpoint.', 405),
      4: ('Internal server error. Check detail in detail property.', 500),
      5: ('Invalid password.', 401),
      6: ('Invalid login token.', 401),
      7: ('Bad request. Check required parameters or input format.', 400),
      8: ('Your current credentials does not allow you to access this resource.', 403),
      9: ('You must be logged to do that, or your login credentials are invalid.', 401),
      10: ('Missing required parameters.', 400),
      11: ('Conflict in unique values.', 409),
      12: ('Invalid input', 400),
      13: ('Invalid input type', 400),
      14: ('Input not in expected values', 400),
      15: ('Ivalid date', 400)
    }

    # index + 1 is error code
    self.relations = (
      "PAGE_NOT_FOUND",
      "RESOURCE_NOT_FOUND",
      "INVALID_METHOD",
      "SERVER_ERROR",
      "INVALID_PASSWORD",
      "INVALID_TOKEN",
      "BAD_REQUEST",
      "INVALID_CREDENTIALS",
      "NOT_LOGGED",
      "MISSING_PARAMETERS",
      "CONFLICT",
      "INVALID_INPUT_VALUE",
      "INVALID_INPUT_TYPE",
      "UNEXPECTED_INPUT_VALUE",
      "INVALID_DATE"
    )

  def error(self, code: ACCEPTED_CODES, data: dict = None):
    if type(code) == str:
      code = self.__str_code_to_int_code(code)

    if code in self.codes:
      if data:
        return jsonify({'error': self.codes[code][0], 'code': code, 'detail': data}), self.codes[code][1]

      return jsonify({'error': self.codes[code][0], 'code': code}), self.codes[code][1]
    
    raise KeyError(f"Error code {code} does not exists")

  def __str_code_to_int_code(self, code: str) -> int:
    if code in self.relations:
      return self.relations.index(code) + 1
    
    raise KeyError(f"Unable to find error code linked to {code}.")

  def __call__(self, code: ACCEPTED_CODES, data: dict = None):
    return self.error(code, data)

  def __getattr__(self, name: str):
    name = name.upper()

    if name in self.relations:
      return self.error(name)

    raise AttributeError()

ERRORS = Errors()

def classic_errors(app: Flask):
  @app.errorhandler(400)
  def catch_400(e):
    return ERRORS.BAD_REQUEST

  @app.errorhandler(401)
  def catch_401(e):
    return ERRORS.NOT_LOGGED

  @app.errorhandler(404)
  def catch_404(e):
    return ERRORS.PAGE_NOT_FOUND

  @app.errorhandler(405)
  def catch_405(e):
    return ERRORS.INVALID_METHOD

  @app.errorhandler(500)
  def server_error(e):
    return ERRORS.error("SERVER_ERROR", {'reason': "Unexpected internal server error", 'error': repr(e)})
