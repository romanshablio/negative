# Negative To Relief

`Negative To Relief` это приложение на Python для подготовки рельефов к 3D-печати.

Оно берет изображение, превращает его в карту высот и может сохранить результат в нескольких форматах:

- `PNG` с preview карты высот;
- `G-code` для FDM-принтера;
- `OBJ` mesh;
- `STL` mesh;
- `3MF` package.

Приложение подходит для сценария, когда нужно превратить негатив или обычное grayscale-изображение в печатный рельеф.

## Что делает приложение

На вход подается изображение:

- негатив;
- обычное черно-белое изображение;
- grayscale-картинка, где яркость определяет высоту.

Дальше приложение:

1. переводит изображение в grayscale;
2. при необходимости инвертирует его;
3. сглаживает и нормализует тон;
4. строит heightmap;
5. по этой карте высот создает `G-code`, `OBJ`, `STL`, `3MF` и preview `PNG`.

## Что получается на выходе

В зависимости от выбранного режима и параметров можно получить:

- `<image>_heightmap.png` - preview карты высот;
- `<image>.gcode` - файл для печати;
- `<image>.obj` - mesh-модель;
- `<image>.stl` - mesh-модель для слайсеров и 3D-редакторов;
- `<image>.3mf` - 3MF-пакет с мешем модели.

## Требования

- Python 3.13+;
- `numpy`;
- `Pillow`;
- для GUI нужен рабочий `tkinter`.

Установка зависимостей:

```bash
python3 -m pip install -r requirements.txt
```

## Рекомендуемый запуск

Если у тебя настроено виртуальное окружение, лучше запускать из него:

```bash
source .venv/bin/activate
python main.py
```

или:

```bash
source .venv/bin/activate
python main.py image.jpg
```

## Режимы работы

Есть два режима:

- GUI;
- CLI.

## GUI

Самый удобный вариант для повседневной работы.

Запуск:

```bash
python3 main.py
```

Или сразу с выбранным файлом:

```bash
python3 main.py negative.jpg --gui
```

В интерфейсе можно:

- выбрать входное изображение;
- выбрать папку для результата;
- включить или выключить экспорт `G-code`, `OBJ`, `STL`, `3MF`;
- настроить размер рельефа;
- настроить высоту рельефа и толщину базы;
- настроить сглаживание, гамму и инверсию;
- задать параметры печати.

## CLI

CLI удобен для повторяемых запусков, автоматизации и точных параметров.

Базовый запуск:

```bash
python3 main.py negative.jpg
```

По умолчанию рядом с исходным изображением будут сохранены:

- `negative_heightmap.png`
- `negative.gcode`

## Примеры CLI

Сгенерировать только preview и `G-code`:

```bash
python3 main.py negative.jpg
```

Сгенерировать `G-code`, `OBJ`, `STL` и `3MF`:

```bash
python3 main.py negative.jpg \
  --obj-out output/relief.obj \
  --stl-out output/relief.stl \
  --3mf-out output/relief.3mf \
  --gcode-out output/relief.gcode
```

Сгенерировать только 3D-модели без `G-code`:

```bash
python3 main.py negative.jpg \
  --no-gcode \
  --obj-out output/relief.obj \
  --stl-out output/relief.stl \
  --3mf-out output/relief.3mf
```

Сгенерировать только `STL` или только `3MF` из картинки:

```bash
python3 main.py image.jpg --no-gcode --stl-out output/model.stl
python3 main.py image.jpg --no-gcode --3mf-out output/model.3mf
```

Пример с параметрами печати и обработки:

```bash
python3 main.py negative.jpg \
  --width-mm 140 \
  --relief-height-mm 2.8 \
  --base-thickness-mm 1.0 \
  --layer-height-mm 0.2 \
  --line-width-mm 0.4 \
  --autocontrast \
  --gamma 0.9 \
  --blur-radius 0.8 \
  --obj-out output/relief.obj \
  --stl-out output/relief.stl \
  --3mf-out output/relief.3mf \
  --gcode-out output/relief.gcode
```

## Самые важные параметры

### Геометрия

- `--width-mm` - физическая ширина модели.
- `--depth-mm` - физическая глубина модели. Если не указать, она считается по пропорциям изображения.
- `--relief-height-mm` - максимальная высота рельефа над базой.
- `--base-thickness-mm` - толщина сплошной подложки.

### Качество и детализация

- `--resolution-x` и `--resolution-y` - разрешение сетки heightmap.
- `--blur-radius` - сглаживание, полезно для шумных изображений.
- `--gamma` - усиление или ослабление контраста по высоте.
- `--autocontrast` - автоматическая растяжка тонального диапазона.

### Инверсия

По умолчанию приложение предполагает, что подается негатив, и инвертирует изображение.

Если исходник уже является обычной картой высот или позитивом, используй:

```bash
--no-invert
```

### Экспорт

- `--no-gcode` - не создавать `G-code`.
- `--obj-out` - путь к `OBJ`.
- `--stl-out` - путь к `STL`.
- `--3mf-out` - путь к `3MF`.
- `--heightmap-out` - путь к preview `PNG`.
- `--gcode-out` - путь к `G-code`.

### Параметры печати

- `--line-width-mm` - ширина линии экструзии.
- `--layer-height-mm` - высота слоя.
- `--filament-diameter-mm` - диаметр филамента.
- `--print-speed` - скорость печати.
- `--first-layer-speed` - скорость первого слоя.
- `--travel-speed` - скорость холостых перемещений.
- `--z-speed` - скорость по оси `Z`.
- `--z-hop-mm` - высота `Z-hop`.
- `--origin-x-mm`, `--origin-y-mm` - стартовая позиция на столе.
- `--nozzle-temperature`, `--bed-temperature`, `--fan-speed` - базовые параметры печати.

## Рекомендуемый порядок работы

1. Возьми изображение с хорошим контрастом.
2. Запусти GUI или CLI.
3. Сначала сгенерируй preview heightmap.
4. Проверь, что светлые и темные области дают нужный рельеф.
5. При необходимости скорректируй `gamma`, `blur`, `autocontrast`, `relief-height`.
6. После этого генерируй `G-code`, `STL` или `3MF`.
7. Перед реальной печатью открой результат в слайсере или G-code viewer.

## На что обратить внимание перед печатью

- `G-code` универсальный и не содержит стартового профиля именно под твой принтер.
- Температуры, скорости и стартовые координаты стоит проверить под свою машину.
- Перед реальной печатью обязательно посмотри превью слоев в слайсере.
- Для больших изображений `OBJ`, `STL` и `3MF` могут получаться тяжелыми.

## Troubleshooting

### Ошибка про несовместимую версию macOS

Если видишь что-то вроде:

```text
macOS 26 (...) or later required
```

обычно это значит, что `numpy`, `Pillow` или `Tk` установлены в виде бинарников, собранных под более новый macOS.

Попробуй:

```bash
python3 -m pip uninstall -y numpy pillow
python3 -m pip install --no-binary=:all: numpy pillow
```

Если проблема именно в GUI, проверь, что Python установлен с рабочим `tkinter`.

### GUI не запускается

Если приложение пишет, что GUI не может стартовать безопасно, чаще всего причина одна из этих:

- в Python нет `tkinter`;
- `Tk` несовместим с текущим macOS;
- используется не тот Python, из которого создавалось рабочее окружение.

В таком случае:

1. попробуй запуск из рабочего `venv`;
2. если не помогает, используй CLI;
3. при необходимости поставь совместимый Python и пересоздай `venv`.

## Коротко

Если нужен самый простой сценарий:

```bash
python3 main.py
```

Если нужен управляемый сценарий через консоль:

```bash
python3 main.py image.jpg --obj-out out/model.obj --stl-out out/model.stl
```
