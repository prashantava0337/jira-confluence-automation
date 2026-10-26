const { notImplemented } = require('../utils/httpError')

module.exports = {
  list: async (_filters) => { throw notImplemented('integrationService.list') },
  get: async (_id) => { throw notImplemented('integrationService.get') },
  create: async (_data) => { throw notImplemented('integrationService.create') },
  update: async (_id, _data) => { throw notImplemented('integrationService.update') },
  remove: async (_id) => { throw notImplemented('integrationService.remove') },
}
