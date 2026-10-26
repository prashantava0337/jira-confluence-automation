const router = require('express').Router()
const asyncHandler = require('../utils/asyncHandler')
const c = require('../controllers/jobController')

router.get('/', asyncHandler(c.list))
router.get('/:id', asyncHandler(c.get))
router.post('/', asyncHandler(c.create))

module.exports = router
