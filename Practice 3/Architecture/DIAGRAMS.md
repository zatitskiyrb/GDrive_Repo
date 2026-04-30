# Architecture Diagrams

**Product:** Dice Randomizer
**Last Updated:** 2026-04-30

---

## 1. System Architecture Diagram

Высокоуровневые компоненты и их взаимодействие.

```mermaid
graph TB
    User([Пользователь / Ребёнок])
    Browser[Браузер]
    Nginx[Nginx :80\nвнутри Docker]
    Static[Статические файлы\nindex.html / style.css / app.js / roll.mp3]

    User -->|открывает http://localhost:8080| Browser
    Browser -->|GET /| Nginx
    Nginx -->|отдаёт файлы| Static
    Static -->|загружается в браузер| Browser
    Browser -->|рендерит UI, запускает JS| User
```

---

## 2. Component Diagram

Детальная структура фронтенд-компонентов.

```mermaid
graph TD
    App[app.js\nГлавный модуль]

    App --> RollDice[rollDice\nЗапуск броска]
    App --> GetRandom[getRandomDie\nГенератор числа 1–6]
    App --> RenderDie[renderDie\nОбновление DOM кубика]
    App --> PlaySound[playSound\nЗвуковой эффект]

    RollDice --> GetRandom
    RollDice --> RenderDie
    RollDice --> PlaySound

    RollDice --> DOM1[DOM: die-1\nЭлемент кубика 1]
    RollDice --> DOM2[DOM: die-2\nЭлемент кубика 2]
    RollDice --> DOM3[DOM: sum-display\nОтображение суммы]
    RollDice --> DOM4[DOM: roll-button\nКнопка броска]
```

---

## 3. Data Flow Diagram

Как данные движутся через систему при одном броске.

```mermaid
sequenceDiagram
    actor User as Пользователь
    participant Button as Кнопка
    participant JS as app.js
    participant DOM as DOM
    participant Audio as Аудио

    User->>Button: click "Бросить кубики"
    Button->>JS: событие click
    JS->>Button: disabled = true
    JS->>DOM: добавить класс .rolling (анимация)
    JS->>Audio: playSound()
    JS->>JS: getRandomDie() → value1 (1–6)
    JS->>JS: getRandomDie() → value2 (1–6)
    JS->>JS: setTimeout(1000ms)
    JS->>DOM: renderDie(die1, value1)
    JS->>DOM: renderDie(die2, value2)
    JS->>DOM: sumDisplay.textContent = value1 + value2
    JS->>DOM: убрать класс .rolling
    JS->>Button: disabled = false
```

---

## 4. Deployment Diagram

Инфраструктура и деплой.

```mermaid
graph TD
    subgraph Host[Хост-машина]
        Port["Порт 8080 (хост)"]
        subgraph Container["Docker Container"]
            Nginx["nginx:1.25-alpine\nПорт 80"]
            subgraph Files["Статические файлы"]
                HTML[index.html]
                CSS[style.css]
                JS[app.js]
                Sound[assets/roll.mp3]
            end
        end
    end

    Browser[Браузер\nhttp://localhost:8080]
    Browser -->|HTTP запрос| Port
    Port -->|маппинг 8080:80| Nginx
    Nginx --> Files
```
