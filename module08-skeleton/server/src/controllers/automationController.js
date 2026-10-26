const automationService = require('../services/automationService')

module.exports = {
  list: async (_req, res) => {
    res.json(await automationService.list())
  },
  get: async (req, res) => {
    res.json(await automationService.get(req.params.id))
  },
  create: async (req, res) => {
    res.status(201).json(await automationService.create(req.body))
  },
  update: async (req, res) => {
    res.json(await automationService.update(req.params.id, req.body))
  },
  remove: async (req, res) => {
    await automationService.remove(req.params.id)
    res.status(204).end()
  },
}
