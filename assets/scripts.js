
// Show filename near button on file uploaded
const showFilename = function () {
    const inputTag = document.getElementById("file-upload");
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


const createOrderTransaction = async function () {
    const account = await connectMetaMask();
    if (!account) {
        alert('Error: Connect to MetaMask first');
    }
    // TODO: Get propper prices and addresses
    const payload = {
      method: 'eth_sendTransaction',
      params: [
        {
          from: account,
          to: '0x2f318C334780961FB129D2a6c30D0763d9a5C970',
          value: '0x29a2241af62c0000',
          gasPrice: '0x09184e72a000',
          gas: '0x2710',
        },
      ],
    };
    window.ethereum.request(payload).then((txHash) => console.log(txHash)).catch((err) => console.error(err));
};


const startMinting = async function () {
    // TODO: Validate form fields
    await createOrderTransaction();
    // TODO: Send form to backend
    // TODO: Redirrect to order page
};


addEventListener('DOMContentLoaded', (event) => {
    connectMetaMask();
});
