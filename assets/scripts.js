
// Show filename near button on file uploaded
const showFilename = function () {
    const inputTag = document.getElementById("file-upload");

    const filesizeBytes = inputTag.files?.item(0)?.size;
    const maxFilesizeBytes = 1024 * 20;  // 20kb
    if (filesizeBytes > maxFilesizeBytes) {
        alert('File too big, select file under 20kb');
        this.value = '';
        return;
    }

    const filenameTag = document.getElementById("file-selected");
    filenameTag.innerText = inputTag.files?.item(0)?.name;
};


// Check if MetaMask installed and try to connect to it's account
const connectMetaMask = async function () {
    if (typeof window.ethereum === 'undefined') {
        alert('Install MetaMask extension first!');
        return false;
    }

    const metamaskAccTag = document.getElementById("metamask-connected");
    try {
        const accounts = await ethereum.request({ method: 'eth_requestAccounts' });
        metamaskAccTag.innerText = accounts[0];
        return accounts[0];
    } catch {
        metamaskAccTag.innerText = `Not Connected`;
    }
    return false;
};


// TODO: Get form jinja in html
const RECEIVER_WALLET_ADDRESS = "0x76e11ec0963db2Af995D5FC1B45Fb2d7b1Ec0890";

const createInputTag = function(key, value) {
    const inputTag = document.createElement('input');
    inputTag.type = 'hidden';
    inputTag.name = key;
    inputTag.value = value;

    return inputTag;
}


const startMinting = async function (event) {
    // TODO: Validate form fields
    event.preventDefault();
    const account = await connectMetaMask();
    if (!account) {
        alert('Error: Connect to MetaMask first');
    }

    const formTag = document.getElementById("mint-form");

    // TODO: Get propper value and gas prices and estimate
    const transactionValueWei = BigInt("15000000000000000"); // ~25$
    const transactionValueWeiHex = '0x' + transactionValueWei.toString(16);
    const payload = {
      method: "eth_sendTransaction",
      params: [
        {
          from: account,
          to: RECEIVER_WALLET_ADDRESS,
          value: transactionValueWeiHex,
        },
      ],
    };

    // TODO: Check propper network
    try {
        const txHash = await window.ethereum.request(payload);
        formTag.appendChild(createInputTag("tx_hash", txHash));
        formTag.appendChild(createInputTag("sender_wallet_addr", account));
        formTag.appendChild(createInputTag("value_wei", transactionValueWei.toString()));
    } catch (err) {
        alert("Error while processing transaction");
        return false;
    }
    formTag.submit();
};


addEventListener('DOMContentLoaded', (event) => {
    connectMetaMask();
});
