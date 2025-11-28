import yaml
import logging
from pathlib import Path
from code_analyzer.folder_analyzer import FolderAnalyzer
from code_analyzer.output_config import OutputConfig, OutputFormat

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger()

CURRENT_DIR = Path(__file__).parent
PROJECT_ROOT = CURRENT_DIR.parent
CONFIG_PATH = PROJECT_ROOT / "code_analyzer" / "config.yaml"
TEST_FOLDER = CURRENT_DIR / "multifile_test"
OUTPUT_DIR = CURRENT_DIR / "temp"


def run_analysis(config_path: Path, test_folder: Path) -> tuple[FolderAnalyzer, dict]:
    logger.info("=== Запуск анализа ===")
    logger.info(f"Конфигурация: {config_path}")
    logger.info(f"Анализируем папку: {test_folder}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    analyzer = FolderAnalyzer(config)
    results = analyzer.analyze_folder(str(test_folder))

    logger.info(f"Найдено элементов: {len(results)}")
    return analyzer, results


def save_results_to_json(analyzer: FolderAnalyzer, output_dir: Path):
    logger.info(f"=== Сохранение результатов в {output_dir} ===")
    output_dir.mkdir(exist_ok=True)

    output_config = OutputConfig(
        output_format=OutputFormat.JSON,
        output_directory=str(output_dir),
        indent=2,
        ensure_ascii=False
    )

    saved_files = analyzer.export_with_config(output_config)
    logger.info(f"Результаты сохранены в файлы:")
    for file_path in saved_files:
        logger.info(f"  {file_path}")


def validate_results(results: dict):
    logger.info("=== Валидация результатов ===")

    element_types = {}
    for model in results.values():
        element_type = model.element_type.value
        element_types[element_type] = element_types.get(element_type, 0) + 1

    logger.info("Типы элементов:")
    for elem_type, count in element_types.items():
        logger.info(f"  {elem_type}: {count}")

    logger.info("Проверка наследования:")
    inheritance_found = False
    for model in results.values():
        if hasattr(model, 'base_classes') and model.base_classes:
            logger.info(f"  {model.name} наследует от: {list(model.base_classes.keys())}")
            logger.info(f"    ID базовых классов: {list(model.base_classes.values())}")
            inheritance_found = True
        elif hasattr(model, 'unresolved_base_classes') and model.unresolved_base_classes:
            logger.info(f"  {model.name} наследует от (неразрешенные): {model.unresolved_base_classes}")

    if not inheritance_found:
        logger.warning("  Наследование не найдено!")

    logger.info("Проверка вызовов функций:")
    calls_found = False
    for model in results.values():
        if hasattr(model, 'outgoing_calls') and model.outgoing_calls:
            logger.info(f"  {model.name} вызывает: {model.outgoing_calls}")
            calls_found = True

    if not calls_found:
        logger.warning("  Вызовы функций не найдены!")


def test_specific_scenarios(results: dict):
    logger.info("=== Тестирование конкретных сценариев ===")

    dog_classes = [m for m in results.values() if hasattr(m, 'name') and m.name == 'Dog']
    if dog_classes:
        dog = dog_classes[0]
        logger.info(f"✓ Найден класс Dog")
        if hasattr(dog, 'base_classes') and 'Animal' in dog.base_classes:
            logger.info(f"✓ Dog наследует от Animal")
            logger.info(f"✓ ID базового класса: {dog.base_classes['Animal']}")
        else:
            logger.warning(f"✗ Dog не наследует от Animal")
    else:
        logger.error(f"✗ Класс Dog не найден")

    bird_classes = [m for m in results.values() if hasattr(m, 'name') and m.name == 'Bird']
    if bird_classes:
        bird = bird_classes[0]
        logger.info(f"✓ Найден класс Bird")
        if hasattr(bird, 'base_classes') and len(bird.base_classes) >= 2:
            logger.info(f"✓ Bird наследует от нескольких классов: {list(bird.base_classes.keys())}")
        else:
            logger.warning(f"✗ Bird не наследует от нескольких классов")
    else:
        logger.error(f"✗ Класс Bird не найден")

    functions_with_calls = [m for m in results.values()
                            if hasattr(m, 'outgoing_calls') and m.outgoing_calls]
    logger.info(f"✓ Найдено функций с вызовами: {len(functions_with_calls)}")

    for func in functions_with_calls[:3]:
        logger.info(f"  {func.name} вызывает: {func.outgoing_calls}")


def main():
    try:
        analyzer, results = run_analysis(CONFIG_PATH, TEST_FOLDER)
        save_results_to_json(analyzer, OUTPUT_DIR)
        validate_results(results)
        test_specific_scenarios(results)
        logger.info("=== Тест завершен успешно ===")
    except Exception as e:
        logger.exception(f"=== Ошибка в тесте ===")


if __name__ == "__main__":
    main()
