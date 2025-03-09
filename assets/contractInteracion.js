const { Web3 } = require("web3");
const path = require("path");
const fs = require("fs");

const { WebSocketProvider } = require("web3-providers-ws");
const ws_url = "ws://192.168.2.1:32000";

async function main() {
  var web3 = new Web3(new WebSocketProvider(ws_url));
  const [
    ,
    ,
    contractABIJson,
    deployedAddress,
    intervalMon,
    listChangJson,
    duration,
  ] = process.argv;
  const abi = JSON.parse(contractABIJson);
  const myContract = new web3.eth.Contract(abi, deployedAddress);
  myContract.handleRevert = true;
  const listChang = JSON.parse(listChangJson);
  const providersAccounts = await web3.eth.getAccounts();
  const defaultAccount = providersAccounts[0];

  let transaction_id = 0;
  const transaction = listChang[0];
  var promises = [];
  const processItems = async () => {
    const end_time = Date.now() + duration * 1000;
    while (Date.now() < end_time) {
      console.log(
        "Executing transaction " + transaction_id + ": " + transaction,
      );
      promises.push(
        interact(defaultAccount, transaction, transaction_id, myContract),
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

async function interact(defaultAccount, ele, indexT, myContract) {
  const p = ele.map((tuple) => tuple[0]);
  const v = ele.map((tuple) => tuple[1]);
  //logToFile("Keys:" +p+ "\tval:"+v);
  //implementare il try per Revert Operazione
  const startT = new Date().getTime();
  const tx = await myContract.methods.proposeNewValues(p, v).send({
    from: defaultAccount,
    gas: 1600000000,
    gasPrice: 0,
  });
  const endT = new Date().getTime();

  //logToFile('#start Time (' + indexT + '): ' + startT);
  //logToFile('#end Time (' + indexT + '): ' + endT);
  //logToFile(endT - startT);
  logToFile("#Index: " + indexT + " time: " + (endT - startT));
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
