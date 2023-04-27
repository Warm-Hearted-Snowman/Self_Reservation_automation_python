import logging
import proccess_data
import module

# Set up logging format
logging.basicConfig(filename='backend.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s', encoding='utf-8')


def main():
    logging.info('Starting main function')
    proccess_data.main(input('enter username: '))
    logging.info('Finished main function')


if __name__ == '__main__':
    main()
