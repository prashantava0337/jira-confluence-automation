const integrations = require('./integrations')
const automations = require('./automations')
const jobs = require('./jobs')
const audit = require('./audit')

module.exports = (app) => {
  app.get('/health', (_req, res) => res.json({ status: 'ok' }))

  app.use('/api/v1/integrations', integrations)
  app.use('/api/v1/automations', automations)
  app.use('/api/v1/jobs', jobs)
  app.use('/api/v1/audit', audit)
}
