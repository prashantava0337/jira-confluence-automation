// Responds with the spec's standard error format: { code, message, details? }
module.exports = (err, _req, res, _next) => {
  const status = err.status || 500
  res.status(status).json({
    code: err.code || 'InternalError',
    message: status === 500 ? 'Internal server error' : err.message,
    ...(err.details && { details: err.details }),
  })
}
