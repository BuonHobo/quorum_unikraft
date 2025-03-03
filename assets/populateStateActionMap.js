const { Web3 } = require("web3");
const { WebSocketProvider } = require("web3-providers-ws");
const ws_url = "ws://192.168.2.1:32000";

var web3 = new Web3(new WebSocketProvider(ws_url));
const [, , contractABIJson, deployedAddress, mapStateActionJson] = process.argv;
const abi = JSON.parse(contractABIJson);
const myContract = new web3.eth.Contract(abi, deployedAddress);
myContract.handleRevert = true;
const mapStateAction = JSON.parse(mapStateActionJson);

async function main() {
  const providersAccounts = await web3.eth.getAccounts();
  const defaultAccount = providersAccounts[0];
  const p = Object.keys(mapStateAction);
  const v = Object.values(mapStateAction);

  await myContract.methods.insertMap(p, v).send({
    from: defaultAccount,
    gasPrice: 0,
  });

  //const a = await myContract.methods.state_parameters_exist(p[0]).call();
}

main()
  .then(() => {
    console.log("END");
  })
  .catch((err) => {
    console.error("Error loading stateActionMap:", err);
  })
  .finally(() => {
    console.log("PopulateStateActionMap process finished.");
    web3.provider.disconnect();
  });
