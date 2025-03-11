const { Web3 } = require("web3");
const { WebSocketProvider } = require("web3-providers-ws");
const ws_url = "ws://192.168.2.1:32000";
const path = require("path");
const fs = require("fs");

async function waitUntil(targetTime) {
  const now = Date.now();
  const waitTime = targetTime - now;
  if (waitTime > 0) {
    logToFile(`Aspettando ${waitTime / 1000} secondi per iniziare...`);
    await new Promise((resolve) => setTimeout(resolve, waitTime));
  }
}

async function main() {
  var web3 = new Web3(new WebSocketProvider(ws_url));
  const [, , intervalMon, leaderAddress, duration] = process.argv;
  const providersAccounts = await web3.eth.getAccounts();
  const defaultAccount = providersAccounts[0];

  let transaction_id = 0;
  var promises = [];
  const processItems = async () => {
    const end_time = Date.now() + duration * 1000;
    while (Date.now() < end_time) {
      console.log("Executing transaction " + transaction_id);
      promises.push(
        interact(web3, defaultAccount, transaction_id, leaderAddress),
      );
      transaction_id++;
      await new Promise((r) => setTimeout(r, 1000 / intervalMon));
    }
    await Promise.all(promises);
  };

  processItems()
    .then(() => {
      console.log("END");
    })
    .catch((err) => {
      console.error("Error precessing transactions:", err);
    })
    .finally(() => {
      console.log("Deployment process finished.");
      web3.provider.disconnect();
    });
}

async function interact(web3, defaultAccount, txId, leaderAddress) {
  //logToFile("Keys:" +p+ "\tval:"+v);
  //implementare il try per Revert Operazione
  const startT = new Date().getTime();
  const tx = await web3.eth.sendTransaction({
    from: defaultAccount,
    to: leaderAddress,
    value: 1,
    gas: 1600000000,
    gasPrice: 0,
  });
  const endT = new Date().getTime();

  logToFile("#Index: " + txId + " time: " + (endT - startT));
}

const logFilePath = path.join("/var/log/", "server.log"); // Function to write logs to the filefunction
function logToFile(message) {
  const timestamp = new Date().toISOString();
  const logMessage = `[${timestamp}] ${message}\n`;
  fs.appendFile(logFilePath, logMessage, (err) => {
    if (err) {
      console.error("Failed to write to log file:", err.message);
    }
  });
}

main();
