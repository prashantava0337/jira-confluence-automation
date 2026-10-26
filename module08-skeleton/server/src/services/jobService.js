const { notImplemented } = require('../utils/httpError')

module.exports = {
  list: async (_filters) => { throw notImplemented('jobService.list') },
  get: async (_id) => { throw notImplemented('jobService.get') },
  // idempotencyKey: duplicate requests with the same key must not create a second job
  create: async (_data, _idempotencyKey) => { throw notImplemented('jobService.create') },
}
