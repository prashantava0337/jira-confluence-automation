const auditService = require('../services/auditService')

module.exports = {
  list: async (req, res) => {
    const limit = Math.min(parseInt(req.query.limit, 10) || 50, 200)
    res.json(await auditService.list({ limit, since: req.query.since }))
  },
}
