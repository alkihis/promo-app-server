from flask import Flask, jsonify
from typing import Union, Dict

# Define a type union
ACCEPTED_CODES = Union[int, str]

class Errors:
  def __init__(self):
    self.codes: Dict[str, str] = {
      1: ['Page not found. Check the URL.', 404],
      2: ['Resource not found.', 404],
      3: ['Invalid method. Current HTTP method is not supported for this endpoint.', 405],
      4: ['Internal server error. Check detail in detail property.', 500],
    }

    self.relations = {
      "PAGE_NOT_FOUND": 1,
      "RESOURCE_NOT_FOUND": 2,
      "INVALID_METHOD": 3,
      "SERVER_ERROR": 4,
    }

  def error(self, code: ACCEPTED_CODES, data: dict = None):
    if type(code) == str:
      code = self.__str_code_to_int_code(code)

    if code in self.codes:
      if data:
        return jsonify({ 'error': self.codes[code][0], 'code': code, 'detail': data }), self.codes[code][1]

      return jsonify({ 'error': self.codes[code][0], 'code': code }), self.codes[code][1]
    
    raise KeyError(f"Error code {code} does not exists")

  def __str_code_to_int_code(self, code: str) -> int:
    if code in self.relations:
      return self.relations[code]
    
    raise KeyError(f"Unable to find error code linked to {code}.")

ERRORS = Errors()

def classic_errors(app: Flask):
  @app.errorhandler(404)
  def catch_404(e):
    return ERRORS.error("PAGE_NOT_FOUND")

  @app.errorhandler(405)
  def catch_405(e):
    return ERRORS.error("INVALID_METHOD")

  @app.errorhandler(500)
  def server_error(e):
    return ERRORS.error("SERVER_ERROR", { 'reason': "Unexpected internal server error", 'error': repr(e) })
