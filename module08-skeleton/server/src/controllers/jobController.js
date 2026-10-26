const jobService = require('../services/jobService')

module.exports = {
  list: async (req, res) => {
    res.json(await jobService.list({
      automation_id: req.query.automation_id,
      status: req.query.status,
    }))
  },
  get: async (req, res) => {
    res.json(await jobService.get(req.params.id))
  },
  create: async (req, res) => {
    const job = await jobService.create(req.body, req.get('Idempotency-Key'))
    res.status(201).json(job)
  },
}
