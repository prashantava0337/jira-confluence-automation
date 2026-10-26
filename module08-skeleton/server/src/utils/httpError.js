// Error carrying the spec's standard response shape: { code, message, details? }
class HttpError extends Error {
  constructor(status, code, message, details) {
    super(message)
    this.status = status
    this.code = code
    this.details = details
  }
}

const notImplemented = (what) =>
  new HttpError(501, 'NotImplemented', `${what} is not implemented yet`)

module.exports = { HttpError, notImplemented }
