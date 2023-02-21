// Show filename near button on file uploaded
const showFilename = async function () {
    gtag('event', 'file_uploaded');
    const inputTag = document.getElementById("file-upload");

    const filesizeBytes = inputTag.files?.item(0)?.size;
    const maxFilesizeBytes = 1024 * 1024 * 5;  // 5mb
    if (filesizeBytes > maxFilesizeBytes) {
        gtag('event', 'file_too_big');
        alert('File too big, select file under 20kb');
        this.value = '';
        return;
    }

    try {
        const prices = await estimate_price(filesizeBytes, 15);
        update_price(prices.usd, prices.service_fee_usd, prices.total_price_wei);
    } catch {
        alert("Can't process this file now. Try later or try another file");
        this.value = '';
        update_price(0, 0, 0);
        return;
    }

    const filenameTag = document.getElementById("file-selected");
    filenameTag.innerText = inputTag.files?.item(0)?.name;
};


// Check if MetaMask installed and try to connect to it's account
const connectMetaMask = async function () {
    if (typeof window.ethereum === 'undefined') {
        gtag('event', 'metamask_missing');
        alert('Install MetaMask extension first!');
        return false;
    }

    const metamaskAccTag = document.getElementById("metamask-connected");
    try {
        const accounts = await ethereum.request({ method: 'eth_requestAccounts' });
        metamaskAccTag.innerText = accounts[0];
        await ethereum.request({method: 'wallet_switchEthereumChain', params: [{ chainId: '0x1' }]});
        gtag('event', 'metamask_connected');
        return accounts[0];
    } catch {
        gtag('event', 'metamask_connection_reject');
        metamaskAccTag.innerText = `Not Connected`;
    }
    return false;
};


// TODO: Get form jinja in html
//const RECEIVER_WALLET_ADDRESS = "0x76e11ec0963db2Af995D5FC1B45Fb2d7b1Ec0890"; // Dev
const RECEIVER_WALLET_ADDRESS = "0x1ab373A9791A9D44f6065CA522d22eD0d8eDD3C7"; // Prod

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

    const transactionValueWei = BigInt(window.price_wei);
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
        gtag('event', 'metamask_transaction_error');
        alert("Error while processing transaction");
        return false;
    }
    gtag('event', 'mint_done');
    formTag.submit();
};


const estimate_price = async function (filesize_bytes, fee_rate) {
    const url = `/api/estimate_price?filesize_bytes=${filesize_bytes}&fee_rate=${fee_rate}`;
    const resp = await fetch(url);
    if (resp.status != 200) {
        throw new Error('Bad response from server');
    }
    const data = await resp.json();
    return data;
}

const round = function (num) {
    return Math.round(num * 100) / 100;
}

const update_price = async function (price_usd, service_fee_usd, total_price_wei) {
    window.price_usd = round(price_usd);
    window.service_fee_usd = round(service_fee_usd);
    window.price_wei = total_price_wei;

    const price_tag = document.querySelector('#price_tag');
    price_tag.innerText = `(~${window.price_usd}$ mint + ~${window.service_fee_usd}$ service fee)`;
}


addEventListener('DOMContentLoaded', (event) => {
    //connectMetaMask();
});
