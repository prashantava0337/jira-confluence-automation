const fs = require('fs');
const root = process.cwd();
const dirs = ['client','server'];
for (let i=0;i<dirs.length;i++){
  const dir = dirs[i];
  const p = dir + '/package.json';
  if (fs.existsSync(p)){
    try{
      const content = fs.readFileSync(p,'utf8');
      let o = JSON.parse(content);
      o.private = true;
      fs.writeFileSync(p, JSON.stringify(o,null,2)+"\n");
      console.log('Patched',p);
    }catch(e){
      console.error('Failed to patch',p,e);
    }
  } else console.log('Missing',p);
}
