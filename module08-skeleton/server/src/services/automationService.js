const { notImplemented } = require('../utils/httpError')

module.exports = {
  list: async () => { throw notImplemented('automationService.list') },
  get: async (_id) => { throw notImplemented('automationService.get') },
  create: async (_data) => { throw notImplemented('automationService.create') },
  update: async (_id, _data) => { throw notImplemented('automationService.update') },
  remove: async (_id) => { throw notImplemented('automationService.remove') },
}
