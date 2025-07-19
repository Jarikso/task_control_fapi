## API Routes for Task Management

### Основные эндпойнты для работы с заданиями (партиями)
### Эндпойнт массового создания сменных заданий

**Метод:** `POST /tasks/`  
**Тело запроса (JSON):**  
Принимает список объектов, где каждый объект представляет сменное задание со следующей структурой:

```json
[
  {
    "status_close": "boolean (статус выполнения, по умолчанию false)",
    "task_description": "string (описание задания, опционально)",
    "shift": "string (название смены, опционально)",
    "shift_start": "datetime (начало смены в формате ISO 8601, например: 2023-01-01T08:00:00)",
    "shift_end": "datetime (окончание смены в формате ISO 8601)",
    "batch_number": "integer (уникальный номер партии)",
    "batch_date": "datetime (дата партии в формате ISO 8601)",
    "brigade": {
      "name": "string (название бригады)"
    },
    "work_center": {
      "name": "string (название рабочего центра)"
    },
    "product": [
      {
        "nomenclature": "string (наименование продукции)",
        "ekn_code": "string (уникальный код ЕКН, опционально)"
      }
    ]
  }
]
```

**Ответ (201 Created):**  
Возвращает список созданных заданий в формате:
```json
[
  {
    "id": "integer (ID задания)",
    "batch_number": "integer",
    "batch_date": "datetime",
    "status_close": "boolean",
    ... // остальные поля задания
  }
]
```

**Ошибки:**
- `400 Bad Request`:
  - Невалидные данные (например, `shift_start` позже `shift_end`)
  - Отсутствуют обязательные поля (`batch_number`, `batch_date`, `shift_start`, `shift_end`)
- `500 Internal Server Error`: Ошибка сервера при создании заданий

**Пример запроса:**
```bash
curl -X POST http://api/tasks/ \
  -H "Content-Type: application/json" \
  -d '[
    {
      "batch_number": 123,
      "batch_date": "2023-01-01T00:00:00",
      "shift_start": "2023-01-01T08:00:00",
      "shift_end": "2023-01-01T20:00:00",
      "brigade": {"name": "Бригада А"},
      "work_center": {"name": "Цех 1"},
      "product": [{"nomenclature": "Изделие 1"}]
    }
  ]'
```

**Примечания:**
1. Поля `brigade.name` и `work_center.name` поддерживают автоматическое создание новых бригад/рабочих центров при их отсутствии.
2. Поле `product` может быть пустым массивом или отсутствовать.
3. Дата/время должны передаваться в формате ISO 8601 (YYYY-MM-DDTHH:MM:SS).

### Эндпойнт получения сменного задания по ID

**Метод:** `GET /task/{task_id}`  
**Параметры пути:**  
- `task_id` - integer (ID сменного задания в системе)

**Успешный ответ (200 OK):**  
Возвращает полную информацию о сменном задании в формате JSON, включая список привязанных уникальных кодов продукции:

```json
{
  "id": "integer (ID задания)",
  "status_close": "boolean (статус выполнения)",
  "closed_date": "datetime|null (дата завершения)",
  "task_description": "string|null (описание)",
  "shift": "string|null (смена)",
  "shift_start": "datetime (начало смены)",
  "shift_end": "datetime (окончание смены)",
  "batch_number": "integer (номер партии)",
  "batch_date": "datetime (дата партии)",
  "brigade": {
    "id": "integer (ID бригады)",
    "name": "string (название бригады)"
  },
  "work_center": {
    "id": "integer (ID рабочего центра)",
    "name": "string (название РЦ)"
  },
  "products": [
    {
      "id": "integer (ID продукции)",
      "nomenclature": "string (наименование)",
      "ekn_code": "string|null (уникальный код ЕКН)",
      "is_aggregated": "boolean (статус агрегации)",
      "aggregated_at": "datetime|null (дата агрегации)"
    }
  ]
}
```

**Ошибки:**  
- `404 Not Found` - если сменное задание с указанным ID не существует.

**Пример запроса:**
```bash
curl -X GET http://api/task/123
```

**Пример ответа:**
```json
{
  "id": 123,
  "status_close": false,
  "closed_date": null,
  "task_description": "Срочный заказ",
  "shift": "Дневная",
  "shift_start": "2023-01-01T08:00:00",
  "shift_end": "2023-01-01T20:00:00",
  "batch_number": 456,
  "batch_date": "2023-01-01T00:00:00",
  "brigade": {
    "id": 1,
    "name": "Бригада А"
  },
  "work_center": {
    "id": 5,
    "name": "Цех 1"
  },
  "products": [
    {
      "id": 789,
      "nomenclature": "Изделие 1",
      "ekn_code": "EKN123456",
      "is_aggregated": false,
      "aggregated_at": null
    }
  ]
}
```
### Эндпойнт изменения сменного задания по ID

**Метод:** `PUT /task/{task_id}`  
**Параметры пути:**  
- `task_id` - integer (ID сменного задания в системе)

**Тело запроса (JSON):**  
Принимает объект с полями для обновления. Все поля опциональны (кроме `id` и `closed_at`):

```json
{
  "status_close": "boolean|null (статус выполнения)",
  "task_description": "string|null (описание)",
  "shift": "string|null (смена)",
  "shift_start": "datetime|null (начало смены)",
  "shift_end": "datetime|null (окончание смены)",
  "batch_number": "integer|null (номер партии)",
  "batch_date": "datetime|null (дата партии)",
  "brigade": {
    "name": "string|null (название бригады)"
  },
  "work_center": {
    "name": "string|null (название РЦ)"
  }
}
```

**Особенности поведения:**
- Если поле не указано - его значение остаётся неизменным
- При изменении `status_close`:
  - На `true` - автоматически устанавливается текущая дата/время в `closed_date`
  - На `false` - `closed_date` устанавливается в `null`
- Обновление бригады/рабочего центра по названию (если не существует - создаётся новая запись)

**Успешный ответ (200 OK):**  
Возвращает обновлённое задание в том же формате, что и GET /task/{id}.

**Ошибки:**  
- `404 Not Found` - если задание с указанным ID не существует
- `400 Bad Request` - при невалидных данных (например, `shift_start` позже `shift_end`)

**Пример запроса:**
```bash
curl -X PUT http://api/task/123 \
  -H "Content-Type: application/json" \
  -d '{
    "status_close": true,
    "task_description": "Обновлённое описание",
    "brigade": {"name": "Новая бригада"}
  }'
```

**Пример ответа:**
```json
{
  "id": 123,
  "status_close": true,
  "closed_date": "2023-01-02T15:30:00",
  "task_description": "Обновлённое описание",
  "shift": "Дневная",
  "shift_start": "2023-01-01T08:00:00",
  "shift_end": "2023-01-01T20:00:00",
  "batch_number": 456,
  "batch_date": "2023-01-01T00:00:00",
  "brigade": {
    "id": 2,
    "name": "Новая бригада"
  },
  "work_center": {
    "id": 5,
    "name": "Цех 1"
  },
  "products": [...]
}
```

### Эндпойнт получения сменных заданий с фильтрацией

**Метод:** `GET /task/`  
**Параметры запроса:**

| Параметр          | Тип        | Описание                                                                 |
|-------------------|------------|--------------------------------------------------------------------------|
| `status_close`    | boolean    | Фильтр по статусу выполнения (true - закрытые, false - активные)        |
| `batch_number`    | integer    | Фильтр по номеру партии                                                 |
| `batch_date`      | datetime   | Фильтр по дате партии (формат: YYYY-MM-DD или YYYY-MM-DDTHH:MM:SS)      |
| `work_center_id`  | integer    | Фильтр по ID рабочего центра                                            |
| `brigade_id`      | integer    | Фильтр по ID бригады                                                    |
| `shift_start_from`| datetime   | Задания с датой начала смены >= указанной                               |
| `shift_start_to`  | datetime   | Задания с датой начала смены <= указанной                               |
| `skip`            | integer    | Количество записей для пропуска (по умолчанию 0)                        |
| `limit`           | integer    | Максимальное количество возвращаемых записей (по умолчанию 100)         |

**Успешный ответ (200 OK):**  
Возвращает список сменных заданий с полной информацией (аналогично GET /task/{id}):

```json
[
  {
    "id": 123,
    "status_close": false,
    "task_description": "Описание задания",
    "batch_number": 456,
    "batch_date": "2023-01-01T00:00:00",
    "brigade": {...},
    "work_center": {...},
    "products": [...]
  },
  ...
]
```

**Примеры запросов:**
```bash
# Получить первые 100 активных заданий
curl "http://api/task/?status_close=false"

# Получить задания партии №123 с пагинацией
curl "http://api/task/?batch_number=123&skip=20&limit=50"

# Получить задания за 1 января 2023 года
curl "http://api/task/?batch_date=2023-01-01"

# Получить задания в период с 1 по 10 января 2023
curl "http://api/task/?shift_start_from=2023-01-01&shift_start_to=2023-01-10"
```

**Особенности:**
1. Все параметры фильтрации являются опциональными
2. Максимальное значение `limit` - 1000 (для предотвращения перегрузки)
3. Даты можно передавать как в формате YYYY-MM-DD, так и с временем
4. Результаты возвращаются с привязкой продукции, бригад и рабочих центров
5. По умолчанию возвращаются первые 100 записей (`skip=0`, `limit=100`)

**Ошибки:**
- `400 Bad Request` - невалидные параметры запроса
- `500 Internal Server Error` - ошибка сервера при обработке запроса

### Эндпойнт добавления продукции к сменным заданиям

**Метод:** `POST /task/products`  
**Тело запроса (JSON):**  
Принимает массив объектов с информацией о продукции и привязке к партиям:

```json
[
  {
    "УникальныйКодПродукта": "string (уникальный код)",
    "НомерПартии": "integer (номер партии)",
    "ДатаПартии": "date (дата партии в формате YYYY-MM-DD)"
  },
  ...
]
```

**Логика обработки:**
1. Для каждой записи в запросе:
   - Ищется сменное задание по `НомерПартии` и `ДатаПартии`
   - Если задание не найдено - запись пропускается
   - Если продукт с таким кодом уже существует - запись пропускается
2. Для новых продуктов создаются записи со значениями:
   - `is_aggregated = false`
   - `aggregated_at = null`
   - Привязка к найденному сменному заданию

**Успешный ответ (200 OK):**  
Возвращает массив добавленных продуктов:

```json
[
  {
    "ekn_code": "string (уникальный код)",
    "task_id": "integer (ID сменного задания)"
  },
  ...
]
```

**Пример запроса:**
```bash
curl -X POST http://api/task/products \
  -H "Content-Type: application/json" \
  -d '[
    {
      "УникальныйКодПродукта": "12gRV60MMsn1",
      "НомерПартии": 22222,
      "ДатаПартии": "2024-01-30"
    },
    {
      "УникальныйКодПродукта": "12gRV60MMsn2",
      "НомерПартии": 33333,
      "ДатаПартии": "2024-01-31"
    }
  ]'
```

**Пример ответа:**
```json
[
  {
    "ekn_code": "12gRV60MMsn1",
    "task_id": 123
  },
  {
    "ekn_code": "12gRV60MMsn2", 
    "task_id": 124
  }
]
```

### Эндпойнт агрегации продукции

**Метод:** `POST /task/aggregate`  
**Тело запроса (JSON):**  
```json
{
  "task_id": "integer (ID партии)",
  "ekn_code": "string (уникальный код продукции)"
}
```

**Логика работы:**
1. Проверяет существование продукции с указанным `ekn_code`
2. Проверяет привязку продукции к указанной партии (`task_id`)
3. Проверяет статус агрегации продукции
4. При успешных проверках:
   - Устанавливает `is_aggregated = true`
   - Записывает текущую дату/время в `aggregated_at`

**Успешный ответ (200 OK):**  
```json
{
  "ekn_code": "string (агрегированный код)"
}
```

**Ошибки:**
- `404 Not Found` - если продукция с указанным кодом не найдена
- `400 Bad Request` с сообщениями:
  - `"unique code already used at {datetime}"` - если код уже был агрегирован
  - `"unique code is attached to another batch"` - если код привязан к другой партии

**Пример запроса:**
```bash
curl -X POST http://api/task/aggregate \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": 123,
    "ekn_code": "12gRV60MMsn1"
  }'
```

**Примеры ответов:**

Успешная агрегация:
```json
{
  "ekn_code": "12gRV60MMsn1"
}
```

Ошибка - код уже использован:
```json
{
  "detail": "unique code already used at 2024-01-30T14:25:00"
}
```

Ошибка - код привязан к другой партии:
```json
{
  "detail": "unique code is attached to another batch"
}