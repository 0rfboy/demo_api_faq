import requests
import json
from faker import Faker
from deep_translator import GoogleTranslator
from datetime import datetime

faker = Faker("en_US")
BASE_URL = "https://api.demo.tn.uz/api/v1/device-tags"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}


def translate_word(word):
    return {
        "uz": GoogleTranslator(source="en", target="uz").translate(word),
        "ru": GoogleTranslator(source="en", target="ru").translate(word),
        "en": word
    }


def fake_i18n_word():
    return translate_word(faker.word())


# POST тесты
POST_TESTS = [
    ("post_001", "Валидный", "POST", "Корректный body", {
        "color": faker.hex_color(),
        "name": fake_i18n_word()
    }, 201),
    ("post_002", "Невалидный color", "POST", "Невалидный color", {
        "color": faker.word(),
        "name": fake_i18n_word()
    }, 400),
    ("post_003", "name.en = true", "POST", "name.en = true", {
        "color": faker.hex_color(),
        "name": {"en": True}
    }, 400),
    ("post_004", "Пустой body", "POST", "Body отсутствует", None, 400)
]

# PUT тесты (шаблоны)
PUT_TESTS = [
    ("put_001", "Валидный", "PUT", "Корректный body", {
        "color": faker.hex_color(),
        "name": fake_i18n_word()
    }, 200),
    ("put_002", "Невалидный color", "PUT", "Невалидный color", {
        "color": faker.word(),
        "name": fake_i18n_word()
    }, 400),
    ("put_003", "name.en = true", "PUT", "name.en = true", {
        "color": faker.hex_color(),
        "name": {"en": True}
    }, 400),
    ("put_004", "Пустой body", "PUT", "Body отсутствует", None, 400)
]

rows = []
created_ids = []


def add_row(num, title, method, pre, body, expected, response, actual, status):
    pre_with_headers = f"Headers: Content-Type=application/json\n{pre}" if pre else "Headers: Content-Type=application/json"
    rows.append({
        "num": num,
        "title": title,
        "method": method,
        "pre": pre_with_headers,
        "body": json.dumps(body, ensure_ascii=False, indent=2) if body else "—",
        "expected": expected,
        "response": response,
        "actual": actual,
        "status": status
    })


def run_post_tests():
    """Выполнение POST тестов"""
    print("=" * 60)
    print("🔵 ЭТАП 1: Выполнение POST тестов")
    print("=" * 60)

    for num, title, method, desc, body, expected_code in POST_TESTS:
        print(f"\n📝 Тест {num}: {title}")

        if body:
            r = requests.post(BASE_URL, json=body, headers=HEADERS)
        else:
            r = requests.post(BASE_URL, headers=HEADERS)

        try:
            response_data = r.json()
            resp_body = json.dumps(response_data, ensure_ascii=False, indent=2)

            # Исправленное сохранение ID
            new_id = None
            if r.status_code == 201:
                if "id" in response_data:
                    new_id = response_data["id"]
                elif "data" in response_data and "id" in response_data["data"]:
                    new_id = response_data["data"]["id"]

            if new_id:
                created_ids.append(new_id)
                print(f"   ✅ Создан объект с ID: {new_id}")

        except:
            resp_body = r.text

        status = "PASS" if r.status_code == expected_code else "FAIL"
        result_icon = "✅" if status == "PASS" else "❌"
        print(f"   {result_icon} Ожидалось: {expected_code}, Получено: {r.status_code} - {status}")

        add_row(num, title, method, desc, body, expected_code, resp_body, r.status_code, status)

    print(f"\n📊 Создано объектов: {len(created_ids)}")


def run_put_tests():
    """Выполнение PUT тестов для каждого созданного ID"""
    print("\n" + "=" * 60)
    print("🟢 ЭТАП 2: Выполнение PUT тестов")
    print("=" * 60)

    if not created_ids:
        print("⚠️  Нет созданных объектов для PUT тестов")
        return

    for idx, obj_id in enumerate(created_ids, 1):
        print(f"\n🔷 Тестирование объекта #{idx} (ID: {obj_id})")

        for num, title, method, desc, body, expected_code in PUT_TESTS:
            test_num = f"{num}_id{idx}"
            obj_id_str = str(obj_id)
            test_title = f"{title} (ID: {obj_id_str[:8] if len(obj_id_str) > 8 else obj_id_str}...)"

            print(f"\n   📝 Тест {test_num}: {title}")

            url = f"{BASE_URL}/{obj_id}"

            if body:
                test_body = {
                    "color": faker.hex_color() if "color" in body else body.get("color"),
                    "name": fake_i18n_word() if isinstance(body.get("name"), dict) and "en" in body[
                        "name"] else body.get("name")
                }
                r = requests.put(url, json=test_body, headers=HEADERS)
            else:
                test_body = None
                r = requests.put(url, headers=HEADERS)

            try:
                resp_body = json.dumps(r.json(), ensure_ascii=False, indent=2)
            except:
                resp_body = r.text

            status = "PASS" if r.status_code == expected_code else "FAIL"
            result_icon = "✅" if status == "PASS" else "❌"
            print(f"      {result_icon} Ожидалось: {expected_code}, Получено: {r.status_code} - {status}")

            add_row(test_num, test_title, method, f"ID: {obj_id}, {desc}",
                    test_body, expected_code, resp_body, r.status_code, status)


def run_delete_tests():
    """Выполнение DELETE тестов для каждого ID"""
    print("\n" + "=" * 60)
    print("🔴 ЭТАП 3: Выполнение DELETE тестов")
    print("=" * 60)

    if not created_ids:
        print("⚠️  Нет объектов для DELETE тестов")
        return

    for idx, obj_id in enumerate(created_ids, 1):
        print(f"\n🗑️  Удаление объекта #{idx} (ID: {obj_id})")
        url = f"{BASE_URL}/{obj_id}"
        r = requests.delete(url, headers=HEADERS)

        try:
            resp_body = json.dumps(r.json(), ensure_ascii=False, indent=2) if r.text else "Пустой ответ"
        except:
            resp_body = r.text if r.text else "Пустой ответ"

        expected_code = 200
        status = "PASS" if r.status_code in [200, 204] else "FAIL"
        result_icon = "✅" if status == "PASS" else "❌"
        print(f"   {result_icon} DELETE: Ожидалось: 200/204, Получено: {r.status_code} - {status}")

        add_row(f"delete_{idx:03d}", f"DELETE объекта", "DELETE",
                f"Удаление ID: {obj_id}", None, expected_code, resp_body, r.status_code, status)

        r_get = requests.get(url, headers=HEADERS)
        try:
            resp_body_get = json.dumps(r_get.json(), ensure_ascii=False, indent=2) if r_get.text else "Пустой ответ"
        except:
            resp_body_get = r_get.text if r_get.text else "Пустой ответ"

        expected_get = 404
        status_get = "PASS" if r_get.status_code == 404 else "FAIL"
        result_icon_get = "✅" if status_get == "PASS" else "❌"
        print(f"   {result_icon_get} GET проверка: Ожидалось: 404, Получено: {r_get.status_code} - {status_get}")

        add_row(f"get_after_delete_{idx:03d}", f"GET после DELETE", "GET",
                f"Проверка удаления ID: {obj_id}", None, expected_get,
                resp_body_get, r_get.status_code, status_get)


def generate_html():
    """Генерация HTML отчета"""
    pass_count = sum(1 for r in rows if r["status"] == "PASS")
    fail_count = sum(1 for r in rows if r["status"] == "FAIL")
    total_count = len(rows)
    pass_rate = (pass_count / total_count * 100) if total_count > 0 else 0

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>API Test Report</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
.container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 20px; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
h1 {{ color: #333; margin-bottom: 20px; }}
.info {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
.info p {{ margin: 5px 0; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; vertical-align: top; }}
th {{ background: #f0f0f0; font-weight: bold; }}
tr:nth-child(even) {{ background: #fafafa; }}
pre {{ background: #f4f4f4; padding: 8px; border-radius: 3px; overflow-x: auto; font-size: 12px; margin: 0; max-height: 150px; overflow-y: auto; }}
.status-pass {{ color: green; font-weight: bold; }}
.status-fail {{ color: red; font-weight: bold; }}
</style>
</head>
<body>
<div class="container">
    <h1>API Test Report – Device Tags</h1>

    <div class="info">
        <p><strong>Дата:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        <p><strong>Endpoint:</strong> {BASE_URL}</p>
        <p><strong>Всего тестов:</strong> {total_count}</p>
        <p><strong>Пройдено:</strong> <span class="status-pass">{pass_count}</span></p>
        <p><strong>Провалено:</strong> <span class="status-fail">{fail_count}</span></p>
        <p><strong>Успешность:</strong> {pass_rate:.1f}%</p>
        <p><strong>Создано объектов:</strong> {len(created_ids)}</p>
    </div>

    <table>
        <thead>
            <tr>
                <th>№</th>
                <th>Название</th>
                <th>Метод</th>
                <th>Предусловия</th>
                <th>Request Body</th>
                <th>Ожидаемый код</th>
                <th>Response Body</th>
                <th>Фактический код</th>
                <th>Статус</th>
            </tr>
        </thead>
        <tbody>
"""

    for r in rows:
        status_class = "status-pass" if r["status"] == "PASS" else "status-fail"
        html += f"""
            <tr>
                <td>{r["num"]}</td>
                <td>{r["title"]}</td>
                <td><strong>{r["method"]}</strong></td>
                <td><pre>{r["pre"]}</pre></td>
                <td><pre>{r["body"]}</pre></td>
                <td>{r["expected"]}</td>
                <td><pre>{r["response"]}</pre></td>
                <td>{r["actual"]}</td>
                <td class="{status_class}">{r["status"]}</td>
            </tr>
"""

    html += """
        </tbody>
    </table>
</div>
</body>
</html>
"""

    with open("report.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("\n" + "=" * 60)
    print("✅ Отчёт успешно создан: report.html")
    print("=" * 60)
    print(f"📊 Итоговая статистика:")
    print(f"   Всего тестов: {total_count}")
    print(f"   ✅ Пройдено: {pass_count}")
    print(f"   ❌ Провалено: {fail_count}")
    print(f"   📈 Успешность: {pass_rate:.1f}%")
    print("=" * 60)


if __name__ == "__main__":
    run_post_tests()
    run_put_tests()
    run_delete_tests()
    generate_html()
