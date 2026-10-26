const router = require('express').Router()
const asyncHandler = require('../utils/asyncHandler')
const c = require('../controllers/auditController')

router.get('/', asyncHandler(c.list))

module.exports = router
