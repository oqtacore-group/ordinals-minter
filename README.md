# Ordinals Minter

Веб сервис, для удобной загрузки файлов и картинок в сеть Bitcoin

## UseCase
- Пользователь заходит на сайт, читает инструкцию, смотрит демку
- Подключает свой метамаск
- Загружает файл
- Указывает свой кошелёк для получения результата
- Нажимает на кнопку "Mint"
- Подтверждает проведение транзакции во всплывающем окне MetaMask
- Получет страницу со спиннером для отслеживания статуса заказа
- После завершения минта, на странице появляется превью и информация о файле

## Декомпозиция
- Получить от юзера информацию и файл
- Получить от юзера оплату за minting
- Загрузить файл в сеть Bitcoin
- Выдать юзеру информацию о файле по запросу

## TODO

### root-path
- [X] Connect to MetaMask and show current account
- [ ] Send file to backend and receive it there
- [X] Create MetaMask Transaction request
- [ ] Specify proper costs and addresses for MetaMask Transaction
- [ ] Mint file into Bitcoin Network (?)
- [ ] Redirect user to order page
- [ ] Generate order page

### etc
- [ ] Validate filetype and filesize
- [ ] Validate form: MetaMask connected, propper file, propper BTC address
- [ ] Generate Ordinals BTC Wallet, if needed
- [ ] Verify payment on backed (?)
- [ ] Record Demo
