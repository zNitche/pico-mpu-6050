import time
import struct
import machine
from micropython import const


DEVICE_ID_REG_ADDR = const(0x75)
DEVICE_ADDRESS = const(0x68)
POWER_MANAGEMENT_1_REG_ADDR = const(0x6B)

TEMP_DATA_REG_ADDR = const(0x41)

ACCELEROMETER_DATA_REG_ADDR = const(0x3B)
ACCELEROMETER_CONFIG_REG_ADDR = const(0x1C)

RANGE_2G = const(0)
RANGE_4G = const(1)
RANGE_8G = const(2)
RANGE_16G = const(3)

ACCELEROMETER_LSB_SENSITIVITY = {
    RANGE_2G: 16384,
    RANGE_4G: 8192,
    RANGE_8G: 4096,
    RANGE_16G: 2048
}

GYRO_DATA_REG_ADDR = const(0x43)
GYRO_CONFIG_REG_ADDR = const(0x1B)

RANGE_250 = const(0)
RANGE_500 = const(1)
RANGE_1000 = const(2)
RANGE_2000 = const(3)

GYRO_LSB_SENSITIVITY = {
    RANGE_250: 131,
    RANGE_500: 65.5,
    RANGE_1000: 32.8,
    RANGE_2000: 16.4
}


class MPU6050:
    def __init__(self,
                 i2c: machine.I2C,
                 address=DEVICE_ADDRESS,
                 accelerometer_range=RANGE_2G,
                 gyro_range=RANGE_250):

        self.i2c = i2c
        self.address = address

        self.accelerometer_range = accelerometer_range
        self.gyro_range = gyro_range

        self.accelerometer_lsb_sensitivity = ACCELEROMETER_LSB_SENSITIVITY[accelerometer_range]
        self.gyro_lsb_sensitivity = GYRO_LSB_SENSITIVITY[gyro_range]

    def is_device_accessible(self) -> bool:
        return True if self.address in self.i2c.scan() else False

    def check_connection(self) -> bool:
        data = self.__read_from_mem(DEVICE_ID_REG_ADDR)

        return True if data == bytearray((DEVICE_ADDRESS,)) else False

    def __wake_up(self):
        # datasheet page no.41 for clock source
        # 0 for internal oscillator
        # 1, 2, 3 use gyro as source
        self.__write_to_mem(POWER_MANAGEMENT_1_REG_ADDR, 0x01)

    def __toggle_running_state(self, state: bool):
        buff = self.__read_from_mem(POWER_MANAGEMENT_1_REG_ADDR)
        pwr_management_reg = buff[0]

        if state:
            # set sleep bit (no. 6) to 0
            pwr_management_reg = pwr_management_reg & 0xBF
        else:
            # set sleep bit (no. 6) to 1
            pwr_management_reg = pwr_management_reg | (1 << 6)

        self.__write_to_mem(POWER_MANAGEMENT_1_REG_ADDR, pwr_management_reg)

    def __reset_device(self):
        pwr_management_reg = self.__read_from_mem(POWER_MANAGEMENT_1_REG_ADDR)[0]
        pwr_management_reg = pwr_management_reg | (1 << 7)

        self.__write_to_mem(POWER_MANAGEMENT_1_REG_ADDR, pwr_management_reg)

    def reset(self):
        self.__reset_device()
        self.__wake_up()

    def __update_measurements_ranges(self):
        self.__set_measurements_range(ACCELEROMETER_CONFIG_REG_ADDR, self.accelerometer_range)
        self.__set_measurements_range(GYRO_CONFIG_REG_ADDR, self.gyro_range)

        self.accelerometer_range = self.__get_measurements_range(ACCELEROMETER_CONFIG_REG_ADDR)
        self.gyro_range = self.__get_measurements_range(GYRO_CONFIG_REG_ADDR)

        self.accelerometer_lsb_sensitivity = ACCELEROMETER_LSB_SENSITIVITY[self.accelerometer_range]
        self.gyro_lsb_sensitivity = GYRO_LSB_SENSITIVITY[self.gyro_range]

    def initialize_device(self):
        self.reset()
        self.__update_measurements_ranges()

    def __write_to_mem(self, reg_address: int, data: bytearray | int, delay=50):
        if isinstance(data, int):
            data = bytearray([data])

        self.i2c.writeto_mem(self.address, reg_address, data)
        time.sleep_ms(delay)

    def __read_from_mem(self, reg_address: int, nbytes: int = 1):
        return self.i2c.readfrom_mem(DEVICE_ADDRESS, reg_address, nbytes)

    def __get_measurements_range(self, reg_address) -> int:
        config_reg = self.__read_from_mem(reg_address)[0]

        range_b0 = (config_reg >> 3) & 1
        range_b1 = (config_reg >> 4) & 1

        return (range_b1 << 1) | range_b0

    def __set_measurements_range(self, reg_address: int, range: int):
        config_reg = self.__read_from_mem(reg_address)[0]

        # set range bits to 0
        config_reg = config_reg & ~ (1 << 3)
        config_reg = config_reg & ~ (1 << 4)

        # set proper bits for selected range
        config_reg = config_reg | (range << 3)

        self.__write_to_mem(reg_address, config_reg)

    def __get_measurements(self, data_reg: int, lsb_sensitivity: int) -> tuple[float, float, float]:
        buff = self.__read_from_mem(data_reg, 6)
        raw_data_struct = struct.unpack(">hhh", buff)
        processed_data = [val / lsb_sensitivity for val in raw_data_struct]

        return processed_data[0], processed_data[1], processed_data[2]

    def start(self):
        self.__toggle_running_state(True)

    def stop(self):
        self.__toggle_running_state(False)

    def get_temperature(self) -> float:
        buff = self.__read_from_mem(TEMP_DATA_REG_ADDR, 2)
        raw_temp = struct.unpack(">h", buff)[0]

        return raw_temp / 340 + 36.53

    def get_acceleration(self) -> tuple[float, float, float]:
        return self.__get_measurements(ACCELEROMETER_DATA_REG_ADDR, self.accelerometer_lsb_sensitivity)

    def get_gyro(self) -> tuple[float, float, float]:
        return self.__get_measurements(GYRO_DATA_REG_ADDR, self.gyro_lsb_sensitivity)
