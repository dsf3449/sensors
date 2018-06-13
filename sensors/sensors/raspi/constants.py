# MCP3002 ADC constants
# change these as desired
SPI_CLK = 11   # Serial Peripheral Interface Clock
SPI_MOSI = 10  # Serial Peripheral Interface data out from MCP3002 chip
SPI_MISO = 9   # Serial Peripheral Interface data in from MCP3002 chip
SPI_CS = 8     # Serial Peripheral Interface chip select

VREF = 3.3 * 1000   # V-Ref in mV (Vref = VDD for the MCP3002 and ADS1015)
RESOLUTION_MQ3002 = 2 ** 10  # for 10 bits of resolution for MCP3002
RESOLUTION_ADS1015 = 2 ** 12 # for 12 bits of resolution for ADS1015
CALIBRATION = 38    # in mV, to make up for the precision of the components

# Begin, deprecated MQ131 constants (these have been moved into the MQ131 driver)
# Equation values
# MQ131 O3 coordinates on curve
PC_CURVE_0 = 42.84561841
PC_CURVE_1 = -1.043297135
RL_MQ131 = 0.679                         # MQ131 Sainsmart Resistor Load value
READ_SAMPLE_TIMES = 5                   # Number of samples to read to get average
READ_SAMPLE_TIME = 0.1                   # Reads sample data in milliseconds
# End, deprecated MQ131 constants (these have been moved into the MQ131 driver)

SAMPLE_INTERVAL_ONE_MINUTE = 60
SCHEDULE_PRIORITY_DEFAULT = 1
