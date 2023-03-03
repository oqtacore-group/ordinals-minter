const track_event = function (event_name) {
    gtag('event', event_name);
    ym(92487407, 'reachGoal', event_name);
};


const updatePriceOnFeeChange = async function (event) {
    window.fee_rate = +event.currentTarget.value;
    await recalc_price(window.filesize_bytes, window.fee_rate);
};


const get_past_orders = function () {
    const orders = JSON.parse(window.localStorage.getItem('mint_orders') || '{}');
    return orders;
};


const save_current_order = function () {
    const orders = get_past_orders();
    orders[window.location.pathname] = true;
    window.localStorage.setItem('mint_orders', JSON.stringify(orders));
};


// XXX: Copied from https://stackoverflow.com/questions/10420352/converting-file-size-in-bytes-to-human-readable-string
function humanFileSize(size) {
    var i = size == 0 ? 0 : Math.floor( Math.log(size) / Math.log(1024) );
    return (size / Math.pow(1024, i)).toFixed(2) * 1 + ' ' + ['B', 'kB', 'MB', 'GB', 'TB'][i];
}


const recalc_price = async function (filesize_bytes, fee_rate) {
    if (!filesize_bytes || !fee_rate) {
        return;
    }
    try {
        const prices = await estimate_price(filesize_bytes, fee_rate);
        await update_price(prices.usd, prices.service_fee_usd, prices.total_price_wei);
    } catch {
        alert("Can't process this file now. Try later or try another file");
        this.value = '';
        await update_price(0, 0, 0);
        return;
    }
};


// Show filename near button on file uploaded
const showFilename = async function () {
    track_event('file_uploaded');
    const inputTag = document.getElementById("file-upload");

    const filesizeBytes = inputTag.files?.item(0)?.size;
    const maxFilesizeBytes = 1024 * 1024 * 5;  // 5mb
    if (filesizeBytes > maxFilesizeBytes) {
        track_event('file_too_big');
        alert('File too big, select file under 20kb');
        this.value = '';
        return;
    }

    window.filesize_bytes = filesizeBytes;
    await recalc_price(window.filesize_bytes, window.fee_rate);


    const filenameTag = document.getElementById("file-selected");
    const filesize_human = humanFileSize(filesizeBytes);
    filenameTag.innerText = `${inputTag.files?.item(0)?.name} (${filesize_human})`;
};


// Check if MetaMask installed and try to connect to it's account
const connectMetaMask = async function () {
    if (typeof window.ethereum === 'undefined') {
        track_event('metamask_missing');
        alert('Install MetaMask extension first!');
        return false;
    }

    const metamaskAccTag = document.getElementById("metamask-connected");
    try {
        const accounts = await ethereum.request({ method: 'eth_requestAccounts' });
        metamaskAccTag.innerText = accounts[0];
        await ethereum.request({method: 'wallet_switchEthereumChain', params: [{ chainId: '0x1' }]});
        track_event('metamask_connected');
        return accounts[0];
    } catch {
        track_event('metamask_connection_reject');
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
        track_event('metamask_transaction_error');
        alert("Error while processing transaction");
        return false;
    }
    track_event('mint_done');
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
