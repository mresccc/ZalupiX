import React, { useEffect, useState } from "react";

function App() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch("http://127.0.0.1:64282")  // замените на адрес вашего backend, если нужно
      .then((res) => {
        if (!res.ok) {
          throw new Error(`Ошибка HTTP: ${res.status}`);
        }
        return res.json();
      })
      .then((data) => {
        // Если backend возвращает объект {events: [...]}, то берём data.events
        // Если просто массив — используем data напрямую
        if (Array.isArray(data)) {
          setEvents(data);
        } else if (data.events && Array.isArray(data.events)) {
          setEvents(data.events);
        } else {
          setEvents([]);
          setError("Неверный формат данных с сервера");
        }
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return (
    <div style={{ maxWidth: 700, margin: "40px auto", fontFamily: "Arial, sans-serif" }}>
      <h1>Календарь событий</h1>

      {loading && <p>Загрузка данных...</p>}
      {error && <p style={{color: "red"}}>Ошибка: {error}</p>}

      {!loading && !error && events.length === 0 && <p>Нет событий.</p>}

      <ul style={{ listStyle: "none", paddingLeft: 0 }}>
        {events.map((event, index) => (
          <li
            key={index}
            style={{
              marginBottom: 16,
              padding: 12,
              border: "1px solid #ccc",
              borderRadius: 6,
              backgroundColor: "#f9f9f9",
            }}
          >
            <div><strong>Дата:</strong> {event.date}</div>
            <div><strong>Активность:</strong> {event.activity}</div>
            <div><strong>Описание:</strong> {event.text}</div>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;
