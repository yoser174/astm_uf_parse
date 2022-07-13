

import logging.config
import yaml
import configparser
import socket

VERSION = '0.0.1'
ENCODING = 'latin-1'
NULL = b'\x00'
STX = b'\x02'
ETX = b'\x03'
EOT = b'\x04'
ENQ = b'\x05'
ACK = b'\x06'
NAK = b'\x15'
ETB = b'\x17'
LF  = b'\x0A'
CR  = b'\x0D'
CRLF = CR + LF
RECORD_SEP    = b'\x0D' # \r #
FIELD_SEP     = b'\x7C' # |  #
REPEAT_SEP    = b'\x5C' # \  #
COMPONENT_SEP = b'\x5E' # ^  #
ESCAPE_SEP    = b'\x26' # &  #
BUFFER_SIZE = 1024


config = configparser.ConfigParser()
config.read('astm_uf_parse.ini')
INST_PORT = config.get('General','INST_PORT')
CIT_PORT = config.get('General','CIT_PORT')
CIT_IP = config.get('General','CIT_IP')


def  make_checksum(message):
        if not isinstance(message[0], int):
            message = map(ord, message)
        return hex(sum(message) & 0xFF)[2:].upper().zfill(2).encode()

def convert_msg(msg):
    logging.info('convert_msg ...')
    msg = msg.decode(ENCODING)
    logging.info(msg)
    logging.info(msg[1:2])
    if msg[1:2] == 'O':
        #order
        msg_sp = msg.split('|')
        logging.info(msg_sp)
        sampleno = msg_sp[2]
        logging.info('sampleno [%s]' % sampleno)
        msg_sp[3] = '^^'+sampleno+'^M'
        msg = '|'.join(msg_sp)
        logging.info(msg)
    if msg[1:2] == 'R':
        #result
        try:
            msg_sp = msg.split('|')
            logging.info(msg_sp)
            test_code = msg_sp[2].split('^')[3]
            result = msg_sp[3].split('^')[0]
            logging.info('test_code [%s]' % test_code)
            logging.info('result [%s]' % result)
            msg_sp[2] = '^^^^'+test_code+'^1'
            msg_sp[3] = result
            msg = '|'.join(msg_sp)
            logging.info(msg)
        except Exception as e:
            logging.warning('gagal parsing Result [%s]' % str(e))
        

    return STX+msg.encode(ENCODING)+CR+ETB+make_checksum(msg.encode(ENCODING)+CR+ETB)+CRLF
    


def main(): 
    logging.info('VERSION:%s' % VERSION)
    logging.info('INST_PORT [%s]' % INST_PORT)
    logging.info('CIT_PORT [%s]' % CIT_PORT)
    logging.info('CIT_IP [%s]' % CIT_IP)

    logging.info('connection to [%s:%s] ...' % (CIT_IP,CIT_PORT))
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cit:
        cit.connect((CIT_IP, int(CIT_PORT)))
        logging.info('Ready.')

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as inst:
            inst.bind(('0.0.0.0', int(INST_PORT)))
            inst.listen()
            conn, addr = inst.accept()
            with conn:
                logging.info(f"Instrument connected by {addr}")
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    logging.info(data)                    
                    if len(data) > 1:
                        logging.debug(data[2:3])
                        if data[2:3] in [ b'O', b'R']:
                            logging.info('converting O message...')
                            data = convert_msg(data[1:-6])
                        
                    cit.sendall(data)
                    if data != EOT:
                        data_cit = cit.recv(1024)
                        logging.info(data_cit)
                        conn.sendall(data_cit)


if __name__ == "__main__":
    with open('astm_uf_parse.yaml', 'rt') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    main()
    
