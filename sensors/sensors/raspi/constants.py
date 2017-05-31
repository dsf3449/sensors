# change these as desired
SPI_CLK = 11   # Serial Peripheral Interface Clock
SPI_MOSI = 10  # Serial Peripheral Interface data out from MCP3002 chip
SPI_MISO = 9   # Serial Peripheral Interface data in from MCP3002 chip
SPI_CS = 8     # Serial Peripheral Interface chip select

VREF = 3.3 * 1000   # V-Ref in mV (Vref = VDD for the MCP3002)
RESOLUTION = 2**10  # for 10 bits of resolution
CALIBRATION = 38    # in mV, to make up for the precision of the components

# Equation values
PC_CURVE = [42.84561841, -1.043297135]   # MQ131 O3 coordinates on curve
RL_MQ131 = 0.679                         # MQ131 Sainsmart Resistor Load value
READ_SAMPLE_VALUES = 5                   # Number of samples to read to get average
READ_SAMPLE_TIME = 0.5                   # Reads sample data in milliseconds

SAMPLE_INTERVAL_ONE_MINUTE = 60
SCHEDULE_PRIORITY_DEFAULT = 1
