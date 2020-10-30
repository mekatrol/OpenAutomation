import os.path


class OneWire:
    @staticmethod
    def __read_file(device_file_name):
        try:
            f = open(device_file_name, 'r')
            lines = f.readlines()
            f.close()
            return lines
        except:
            return ''

    @staticmethod
    def read_temp(device_file_name):
        lines = OneWire.__read_file(device_file_name)
        if lines == '':
            return -1000.0

        if lines[0].strip()[-3:] != 'YES':
            return -1000.0

        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            return temp_c

        return -1000.0
