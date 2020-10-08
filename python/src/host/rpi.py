import re
from subprocess import check_output, CalledProcessError


def host_get_gpu_temp():
    # Initialise temp to empty value
    temp = None

    try:
        # Use vcgencmd to measure temp
        out = check_output(
            ["/opt/vc/bin/vcgencmd", "measure_temp"]).decode('utf-8')

        # out will be a string similar to:
        # temp=48.9'C
        # Use regex to get the floating point value part
        m = re.search(r'(\d+\.{0,1}\d*)', out)

        # The value will be in the only regex group
        temp = round(float(m.group()), 3)

    except CalledProcessError as ex:
        print("Error calling vcgencmd: " + ex.output)
        raise

    return temp


def host_get_cpu_clock():
    # Initialise clock to empty value
    clock = None

    try:
        # Use vcgencmd to measure temp
        out = check_output(
            ["/opt/vc/bin/vcgencmd", "measure_clock", "arm"]).decode('utf-8')

        # out will be a string similar to:
        # frequency(1)=268750000
        # Use regex to get the frquency value part (in Hz)
        m = re.search(r'=(\d+)', out)

        # The value will be in the only regex group, convert to MHz
        clock = round(float(m.group(1)) / 1000000.0, 3)

    except CalledProcessError as ex:
        print("Error calling vcgencmd: " + ex.output)
        raise

    return clock


def host_get_cpu_temp():
    # Initialise temp to empty value
    temp = None

    try:
        # Get temp from sys file
        out = check_output(
            ["cat", "/sys/class/thermal/thermal_zone0/temp"]).decode('utf-8')

        # The temperature is in milli-degrees, so convert to degrees
        # out will be a string similar to:
        # 49852
        temp = round(float(out) / 1000.0, 3)

    except CalledProcessError as ex:
        print("Error calling vcgencmd: " + ex.output)
        raise

    return temp


def host_get_throttled_status():
    # Initialise status to empty value
    status = None

    try:
        # Use vcgencmd to measure temp
        out = check_output(
            ["/opt/vc/bin/vcgencmd", "get_throttled"]).decode('utf-8')

        # out will be a string similar to:
        # throttled=0x50000
        # Use regex to get the status value
        m = re.search(r'(0x\d+)', out)

        # The value will be in the only regex group
        status = m.group()

    except CalledProcessError as ex:
        print("Error calling vcgencmd: " + ex.output)
        raise

    return status
