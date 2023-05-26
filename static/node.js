const fs = require('fs')

export function read(){
    fs.readFile('counterprev.txt', (err, data) => {
        if (err) throw err;

        console.log(data.toString());
    })
}