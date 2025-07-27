const tg = window.Telegram.WebApp;
// tg.expand();

document.getElementById("send").onclick = () => {
  tg.sendData("Соси");
  tg.showAlert("Данные отправлены боту!");
};
