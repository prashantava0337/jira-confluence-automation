const express = require(express)
const cors = require(cors)
const app = express()
const port = process.env.PORT || 4000

app.use(cors())
app.use(express.json())

app.get(/ping, (req,res) => res.json({ok:true,env:module08-server}))

app.listen(port, ()=> console.log())
