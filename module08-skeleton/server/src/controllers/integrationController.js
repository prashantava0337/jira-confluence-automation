const integrationService = require('../services/integrationService')

module.exports = {
  list: async (req, res) => {
    res.json(await integrationService.list({ provider: req.query.provider }))
  },
  get: async (req, res) => {
    res.json(await integrationService.get(req.params.id))
  },
  create: async (req, res) => {
    res.status(201).json(await integrationService.create(req.body))
  },
  update: async (req, res) => {
    res.json(await integrationService.update(req.params.id, req.body))
  },
  remove: async (req, res) => {
    await integrationService.remove(req.params.id)
    res.status(204).end()
  },
}
