# Основной адрес сайта 1C ИТС
URL = "https://its.1c.ru"
LOGIN_URL = "https://login.1c.ru"
# Ссылки с разделами документации
DB_LINKS: tuple = (
    "/db/edtdoc",
    "/db/cs27doc",
    "/db/kip",
    "/db/freshpub",
)

# Для валидации
IMAGE_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".tiff", ".ico"}
IMAGE_PATTERNS: set[str] = {"/image/", "/img/", "/images/", "/media/", "/uploads/", "image.", "img."}
