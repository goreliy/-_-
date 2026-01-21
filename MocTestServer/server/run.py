#!/usr/bin/env python3
"""
Скрипт запуска Mock Test Server
"""

import argparse
import logging
import sys
import os

# Добавляем путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.app import init_app, run_server, load_config


def setup_logging(level: str = "INFO"):
    """Настройка логирования"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )


def main():
    parser = argparse.ArgumentParser(description='Mock Test Server для КВТ')
    parser.add_argument('--config', '-c', type=str, help='Путь к конфигурационному файлу')
    parser.add_argument('--port', '-p', type=int, default=8000, help='Порт веб-интерфейса')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host для веб-интерфейса')
    parser.add_argument('--debug', '-d', action='store_true', help='Режим отладки')
    parser.add_argument('--log-level', type=str, default='INFO', 
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Уровень логирования')
    
    args = parser.parse_args()
    
    # Настройка логирования
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Загрузка конфигурации
    if args.config:
        config = load_config(args.config)
        logger.info(f"Loaded config from {args.config}")
    else:
        config = None
        logger.info("Using default config")
    
    # Инициализация и запуск
    logger.info(f"Starting Mock Test Server on {args.host}:{args.port}")
    init_app(config)
    run_server(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()
